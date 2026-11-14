from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'language')

    def create(self, validated_data):
        # Роль всегда user: организатором становятся через /api/organizers/apply/
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    organizer_id = serializers.IntegerField(source='organizer.id', read_only=True, default=None)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role',
                  'wallet_address', 'language', 'avatar_url', 'organizer_id', 'date_joined')
        read_only_fields = ('id', 'username', 'email', 'role', 'date_joined')

    def validate_wallet_address(self, value):
        if value and not (value.startswith('0x') and len(value) == 42):
            raise serializers.ValidationError('Expected an address like 0x… (42 characters).')
        return value
