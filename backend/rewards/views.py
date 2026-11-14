import uuid
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from events.models import Event

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
            # NFT создаётся в статусе pending; выдача в сеть — отдельный шаг
            NFTReward.objects.create(visit=visit, wallet_address=request.user.wallet_address)

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
