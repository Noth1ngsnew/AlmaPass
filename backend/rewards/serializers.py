from rest_framework import serializers

from events.serializers import EventSerializer

from .models import NFTReward, Visit


class NFTRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFTReward
        fields = ('id', 'status', 'wallet_address', 'contract_address', 'token_id', 'tx_hash',
                  'metadata_uri', 'minted_at')


class VisitSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    nft_reward = NFTRewardSerializer(read_only=True)

    class Meta:
        model = Visit
        fields = ('id', 'event', 'checked_in_at', 'nft_reward')
