from django.conf import settings
from rest_framework import serializers

from events.serializers import EventSerializer, request_lang

from .models import DiscountCode, LoyaltyLevel, NFTReward, Visit


class NFTRewardSerializer(serializers.ModelSerializer):
    explorer_url = serializers.SerializerMethodField()

    class Meta:
        model = NFTReward
        fields = ('id', 'status', 'wallet_address', 'contract_address', 'token_id', 'tx_hash',
                  'explorer_url', 'metadata_uri', 'minted_at')

    def get_explorer_url(self, obj):
        return f'{settings.NFT_EXPLORER_URL}/tx/{obj.tx_hash}' if obj.tx_hash else ''


class VisitSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    nft_reward = NFTRewardSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = ('id', 'event', 'checked_in_at', 'nft_reward')


class LoyaltyLevelSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = LoyaltyLevel
        fields = ('id', 'name', 'min_nfts', 'discount_percent')

    def get_name(self, obj):
        return obj.translated('name', request_lang(self))


class DiscountCodeSerializer(serializers.ModelSerializer):
    level = serializers.SerializerMethodField()
    event = serializers.SerializerMethodField()
    username = serializers.CharField(source='user.username', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = DiscountCode
        fields = ('id', 'code', 'status', 'discount_percent', 'level', 'event', 'username', 'final_price',
                  'created_at', 'used_at')

    def get_level(self, obj):
        return obj.level.translated('name', request_lang(self)) if obj.level else ''

    def get_event(self, obj):
        event = obj.event
        return {'id': event.id, 'title': event.translated('title', request_lang(self)),
                'start_at': event.start_at, 'price': str(event.price)}
