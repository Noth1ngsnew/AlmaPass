from django.db.models import Q
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.models import User

from .models import Category, Event, Favorite, Organizer, Venue
from .permissions import IsOrganizerOwnerOrReadOnly, is_admin
from .serializers import CategorySerializer, EventSerializer, OrganizerSerializer, VenueSerializer


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    pagination_class = None


class VenueViewSet(mixins.CreateModelMixin, viewsets.ReadOnlyModelViewSet):
    """Список площадок открыт всем; добавлять могут организаторы и админы."""

    queryset = Venue.objects.all()
    serializer_class = VenueSerializer
    pagination_class = None

    def perform_create(self, serializer):
        user = self.request.user
        if not (is_admin(user) or hasattr(user, 'organizer')):
            self.permission_denied(self.request, message='Only organizers can add venues.')
        serializer.save()


class OrganizerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organizer.objects.all()
    serializer_class = OrganizerSerializer

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def apply(self, request):
        """Пользователь создаёт профиль организатора и получает роль organizer."""
        if hasattr(request.user, 'organizer'):
            raise ValidationError('Organizer profile already exists.')
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        if request.user.role == User.Role.USER:
            request.user.role = User.Role.ORGANIZER
            request.user.save(update_fields=['role'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsOrganizerOwnerOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params
        qs = Event.objects.select_related('category', 'venue', 'organizer')

        if params.get('mine') and user.is_authenticated:
            # Кабинет организатора: свои события в любом статусе
            qs = qs.filter(organizer__user=user)
        elif is_admin(user):
            pass
        elif user.is_authenticated:
            qs = qs.filter(Q(status=Event.Status.PUBLISHED) | Q(organizer__user=user))
        else:
            qs = qs.filter(status=Event.Status.PUBLISHED)

        if params.get('category'):
            qs = qs.filter(category__slug=params['category'])
        if params.get('venue'):
            qs = qs.filter(venue_id=params['venue'])
        if params.get('organizer'):
            qs = qs.filter(organizer_id=params['organizer'])
        if params.get('date_from'):
            qs = qs.filter(end_at__date__gte=params['date_from'])
        if params.get('date_to'):
            qs = qs.filter(start_at__date__lte=params['date_to'])
        if params.get('free'):
            qs = qs.filter(price=0)
        return qs

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorite_ids'] = set(user.favorites.values_list('event_id', flat=True))
        return context

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'organizer'):
            raise ValidationError('Create an organizer profile first: POST /api/organizers/apply/')
        # Новое событие уходит на модерацию
        serializer.save(organizer=self.request.user.organizer, status=Event.Status.PENDING)

    def perform_update(self, serializer):
        # После правки организатором событие снова проходит модерацию
        if is_admin(self.request.user):
            serializer.save()
        else:
            serializer.save(status=Event.Status.PENDING)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        event = self.get_object()
        if request.method == 'POST':
            Favorite.objects.get_or_create(user=request.user, event=event)
            return Response({'is_favorite': True})
        Favorite.objects.filter(user=request.user, event=event).delete()
        return Response({'is_favorite': False})

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def moderate(self, request, pk=None):
        """Админ публикует или отклоняет событие: {"status": "published" | "rejected"}."""
        if not is_admin(request.user):
            self.permission_denied(request)
        new_status = request.data.get('status')
        if new_status not in (Event.Status.PUBLISHED, Event.Status.REJECTED):
            raise ValidationError({'status': 'Use "published" or "rejected".'})
        event = self.get_object()
        event.status = new_status
        event.save(update_fields=['status', 'updated_at'])
        return Response(self.get_serializer(event).data)


class FavoriteListView(generics.ListAPIView):
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (Event.objects.filter(favorites__user=self.request.user)
                .select_related('category', 'venue', 'organizer'))

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['favorite_ids'] = set(self.request.user.favorites.values_list('event_id', flat=True))
        return context
