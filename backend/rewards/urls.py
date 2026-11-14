from django.urls import path

from .views import CheckInView, MyVisitsView

urlpatterns = [
    path('checkin/', CheckInView.as_view(), name='checkin'),
    path('visits/', MyVisitsView.as_view(), name='visits'),
]
