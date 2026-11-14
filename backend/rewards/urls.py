from django.urls import path

from .views import CheckInView, ClaimNFTView, MyVisitsView, NFTMetadataView

urlpatterns = [
    path('checkin/', CheckInView.as_view(), name='checkin'),
    path('visits/', MyVisitsView.as_view(), name='visits'),
    path('visits/<int:pk>/claim/', ClaimNFTView.as_view(), name='claim-nft'),
    path('nft/metadata/<int:pk>/', NFTMetadataView.as_view(), name='nft-metadata'),
]
