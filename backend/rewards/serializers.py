from django.conf import settings
from rest_framework import serializers

from events.serializers import EventSerializer

from .models import NFTReward, Visit


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
