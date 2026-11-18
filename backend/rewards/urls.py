from django.urls import path

from .views import (CheckInView, ClaimNFTView, EventDiscountView, LoyaltyView, MyDiscountsView, MyVisitsView,
                    NFTMetadataView, RedeemDiscountView)

urlpatterns = [
    path('checkin/', CheckInView.as_view(), name='checkin'),
    path('visits/', MyVisitsView.as_view(), name='visits'),
    path('visits/<int:pk>/claim/', ClaimNFTView.as_view(), name='claim-nft'),
    path('nft/metadata/<int:pk>/', NFTMetadataView.as_view(), name='nft-metadata'),
    path('loyalty/', LoyaltyView.as_view(), name='loyalty'),
    path('events/<int:pk>/discount/', EventDiscountView.as_view(), name='event-discount'),
    path('discounts/', MyDiscountsView.as_view(), name='discounts'),
    path('discounts/redeem/', RedeemDiscountView.as_view(), name='redeem-discount'),
]
