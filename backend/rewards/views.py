import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event
from events.permissions import is_admin

from . import loyalty, nft
from .models import DiscountCode, LoyaltyLevel, NFTReward, Visit
from .serializers import DiscountCodeSerializer, LoyaltyLevelSerializer, VisitSerializer


def visit_context(request):
    ids = set(request.user.visits.values_list('event_id', flat=True))
    favorites = set(request.user.favorites.values_list('event_id', flat=True))
    return {'request': request, 'visited_ids': ids, 'favorite_ids': favorites}


class CheckInView(APIView):
    """POST /api/checkin/ {"token": "..."} — отметка посещения по коду из QR."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = uuid.UUID(str(request.data.get('token', '')).strip())
        except ValueError:
            return self.fail('invalid')

        event = Event.objects.filter(checkin_token=token, status=Event.Status.PUBLISHED).first()
        if event is None:
            return self.fail('invalid')

        # Отметиться можно только во время события (с небольшим запасом)
        now = timezone.now()
        window = timedelta(minutes=settings.CHECKIN_WINDOW_MINUTES)
        if now < event.start_at - window:
            return self.fail('not_started')
        if now > event.end_at + window:
            return self.fail('ended')

        visit, created = Visit.objects.get_or_create(user=request.user, event=event)
        if created:
            reward = NFTReward.objects.create(visit=visit, wallet_address=request.user.wallet_address)
            # Если сервер настроен и кошелёк указан, NFT выдаётся сразу; иначе ждёт кнопки «Получить NFT»
            if nft.is_configured() and nft.is_valid_wallet(reward.wallet_address):
                nft.start_mint(reward)
                visit.refresh_from_db()

        data = VisitSerializer(visit, context=visit_context(request)).data
        data['already_checked_in'] = not created
        return Response(data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @staticmethod
    def fail(code):
        messages = {
            'invalid': 'This check-in code is not valid.',
            'not_started': 'Check-in opens shortly before the event starts.',
            'ended': 'This event has already ended.',
        }
        return Response({'code': code, 'detail': messages[code]}, status=status.HTTP_400_BAD_REQUEST)


class MyVisitsView(generics.ListAPIView):
    """GET /api/visits/ — мои посещения и статус NFT."""

    serializer_class = VisitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (Visit.objects.filter(user=self.request.user)
                .select_related('event__category', 'event__venue', 'event__organizer', 'nft_reward'))

    def get_serializer_context(self):
        return visit_context(self.request)


class ClaimNFTView(APIView):
    """POST /api/visits/<id>/claim/ — получить NFT за посещение (или повторить после ошибки)."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        visit = get_object_or_404(Visit.objects.select_related('nft_reward'), pk=pk, user=request.user)
        reward, _ = NFTReward.objects.get_or_create(visit=visit)

        if reward.status not in (NFTReward.Status.MINTED, NFTReward.Status.MINTING):
            if not nft.is_configured():
                return Response({'code': 'not_configured', 'detail': 'NFT issuing is not configured on the server.'},
                                status=status.HTTP_503_SERVICE_UNAVAILABLE)
            # Берём кошелёк из профиля на момент запроса: пользователь мог указать его после check-in
            reward.wallet_address = request.user.wallet_address
            reward.save(update_fields=['wallet_address'])
            if not nft.is_valid_wallet(reward.wallet_address):
                return Response({'code': 'no_wallet', 'detail': 'Add a wallet address to your profile first.'},
                                status=status.HTTP_400_BAD_REQUEST)
            nft.start_mint(reward)

        visit = Visit.objects.select_related('event__category', 'event__venue', 'event__organizer',
                                             'nft_reward').get(pk=visit.pk)
        return Response(VisitSerializer(visit, context=visit_context(request)).data)


class NFTMetadataView(APIView):
    """GET /api/nft/metadata/<id>/ — метаданные токена в формате ERC-721 (на них ссылается tokenURI)."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        reward = get_object_or_404(NFTReward.objects.select_related('visit__event__venue'), pk=pk)
        event = reward.visit.event
        return Response({
            'name': f'AlmaPass: {event.title_en}',
            'description': f'Proof of attendance. {event.title_en}, {event.venue.name}, Almaty.',
            'image': event.nft_image_url or event.image_url,
            'external_url': f'{settings.PUBLIC_API_URL}/api/events/{event.id}/',
            'attributes': [
                {'trait_type': 'Event', 'value': event.title_en},
                {'trait_type': 'Venue', 'value': event.venue.name},
                {'trait_type': 'Date', 'value': event.start_at.date().isoformat()},
                {'trait_type': 'City', 'value': 'Almaty'},
            ],
        })


class LoyaltyView(APIView):
    """GET /api/loyalty/ — все уровни и, для вошедшего, сколько у него NFT и до какого уровня осталось."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        context = {'request': request}
        data = {'levels': LoyaltyLevelSerializer(LoyaltyLevel.objects.all(), many=True, context=context).data,
                'nft_count': None, 'current_level': None, 'next_level': None, 'nfts_to_next': None}
        if request.user.is_authenticated:
            info = loyalty.progress(request.user)
            level = lambda item: LoyaltyLevelSerializer(item, context=context).data if item else None  # noqa: E731
            data.update(nft_count=info['nft_count'], current_level=level(info['current']),
                        next_level=level(info['next']), nfts_to_next=info['nfts_to_next'])
        return Response(data)


class EventDiscountView(APIView):
    """POST /api/events/<id>/discount/ — получить код скидки на платное событие по своему уровню."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        event = get_object_or_404(Event, pk=pk, status=Event.Status.PUBLISHED)
        existing = DiscountCode.objects.filter(user=request.user, event=event).first()
        if existing:
            return Response(DiscountCodeSerializer(existing, context={'request': request}).data)

        if event.price <= 0:
            return self.fail('free_event', 'This event is free.')
        if not event.nft_discount:
            return self.fail('not_offered', 'The organizer does not offer an NFT discount for this event.')
        if event.end_at < timezone.now():
            return self.fail('ended', 'This event has already ended.')

        info = loyalty.progress(request.user)
        level = info['current']
        if not level or level.discount_percent == 0:
            target = loyalty.first_discount_level()
            return self.fail('level_too_low', 'Collect more NFTs to unlock a discount.', nft_count=info['nft_count'],
                             nfts_needed=(target.min_nfts - info['nft_count']) if target else None)

        code = DiscountCode.objects.create(code=loyalty.generate_code(), user=request.user, event=event, level=level,
                                           discount_percent=level.discount_percent)
        return Response(DiscountCodeSerializer(code, context={'request': request}).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def fail(code, detail, **extra):
        return Response({'code': code, 'detail': detail, **extra}, status=status.HTTP_400_BAD_REQUEST)


class MyDiscountsView(generics.ListAPIView):
    """GET /api/discounts/ — мои коды скидок."""

    serializer_class = DiscountCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DiscountCode.objects.filter(user=self.request.user).select_related('event', 'level')


class RedeemDiscountView(APIView):
    """POST /api/discounts/redeem/ {"code": "ALMA-…"} — организатор гасит код на своём событии."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = loyalty.normalize_code(request.data.get('code'))
        item = DiscountCode.objects.select_related('event__organizer', 'user', 'level').filter(code=code).first()
        # Чужие коды выглядят так же, как несуществующие
        if not item or not (is_admin(request.user) or item.event.organizer.user_id == request.user.id):
            return Response({'code': 'not_found', 'detail': 'Code not found for your events.'},
                            status=status.HTTP_404_NOT_FOUND)
        data = DiscountCodeSerializer(item, context={'request': request}).data
        if item.status == DiscountCode.Status.USED:
            return Response({'code': 'already_used', 'detail': 'This code has already been used.', 'discount': data},
                            status=status.HTTP_400_BAD_REQUEST)
        item.status = DiscountCode.Status.USED
        item.used_at = timezone.now()
        item.redeemed_by = request.user
        item.save(update_fields=['status', 'used_at', 'redeemed_by'])
        return Response(DiscountCodeSerializer(item, context={'request': request}).data)
