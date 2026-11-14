from rest_framework import serializers

from .models import Category, Event, Organizer, Venue


def request_lang(serializer):
    """Язык ответа: ?lang=ru, иначе заголовок Accept-Language, иначе en."""
    request = serializer.context.get('request')
    if not request:
        return 'en'
    lang = request.query_params.get('lang') or getattr(request, 'LANGUAGE_CODE', 'en')
    return lang[:2]


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ('id', 'slug', 'name', 'name_en', 'name_ru', 'name_kk')

    def get_name(self, obj):
        return obj.translated('name', request_lang(self))


class VenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Venue
        fields = ('id', 'name', 'address', 'latitude', 'longitude', 'website')


class OrganizerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organizer
        fields = ('id', 'name', 'description', 'website', 'is_verified')
        read_only_fields = ('is_verified',)


class EventSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    venue = VenueSerializer(read_only=True)
    organizer = OrganizerSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(source='category', queryset=Category.objects.all(), write_only=True)
    venue_id = serializers.PrimaryKeyRelatedField(source='venue', queryset=Venue.objects.all(), write_only=True)
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = (
            'id', 'title', 'description',
            'title_en', 'title_ru', 'title_kk', 'description_en', 'description_ru', 'description_kk',
            'category', 'venue', 'organizer', 'category_id', 'venue_id',
            'start_at', 'end_at', 'price', 'image_url', 'source_url', 'nft_image_url',
            'status', 'is_favorite', 'created_at',
        )
        read_only_fields = ('status', 'created_at')

    def get_title(self, obj):
        return obj.translated('title', request_lang(self))

    def get_description(self, obj):
        return obj.translated('description', request_lang(self))

    def get_is_favorite(self, obj):
        return obj.id in self.context.get('favorite_ids', ())

    def validate(self, attrs):
        start = attrs.get('start_at', getattr(self.instance, 'start_at', None))
        end = attrs.get('end_at', getattr(self.instance, 'end_at', None))
        if start and end and end < start:
            raise serializers.ValidationError({'end_at': 'End time must be after start time.'})
        return attrs
