import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event

from . import nft
from .models import NFTReward, Visit
from .serializers import VisitSerializer


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
