from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CategoryViewSet, EventViewSet, FavoriteListView, OrganizerViewSet, SearchView, VenueViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('venues', VenueViewSet)
router.register('organizers', OrganizerViewSet)
router.register('events', EventViewSet, basename='event')

urlpatterns = [
    path('favorites/', FavoriteListView.as_view(), name='favorites'),
    path('search/', SearchView.as_view(), name='search'),
    path('', include(router.urls)),
]
