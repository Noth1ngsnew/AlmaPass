from django.contrib import admin

from .models import Category, Event, Favorite, Organizer, Venue


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ru', 'name_kk', 'slug')
    search_fields = ('name_en', 'name_ru', 'name_kk')
    prepopulated_fields = {'slug': ('name_en',)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'website')
    search_fields = ('name', 'address')


@admin.register(Organizer)
class OrganizerAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_verified', 'created_at')
    list_filter = ('is_verified',)
    search_fields = ('name', 'user__username', 'user__email')
    autocomplete_fields = ('user',)
    actions = ['verify']

    @admin.action(description='Подтвердить выбранных организаторов')
    def verify(self, request, queryset):
        self.message_user(request, f'Подтверждено: {queryset.update(is_verified=True)}')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title_en', 'category', 'venue', 'organizer', 'start_at', 'status')
    list_filter = ('status', 'category', 'start_at')
    search_fields = ('title_en', 'title_ru', 'title_kk', 'venue__name', 'organizer__name')
    autocomplete_fields = ('category', 'venue', 'organizer')
    date_hierarchy = 'start_at'
    readonly_fields = ('checkin_token', 'created_at', 'updated_at')
    actions = ['publish', 'reject']
    fieldsets = (
        ('English', {'fields': ('title_en', 'description_en')}),
        ('Русский', {'fields': ('title_ru', 'description_ru')}),
        ('Қазақша', {'fields': ('title_kk', 'description_kk')}),
        ('Details', {'fields': ('category', 'venue', 'organizer', 'start_at', 'end_at', 'price',
                                'image_url', 'source_url', 'status')}),
        ('NFT / check-in', {'fields': ('nft_image_url', 'nft_discount', 'checkin_token')}),
        ('System', {'fields': ('created_at', 'updated_at')}),
    )

    @admin.action(description='Опубликовать выбранные события')
    def publish(self, request, queryset):
        self.message_user(request, f'Опубликовано: {queryset.update(status=Event.Status.PUBLISHED)}')

    @admin.action(description='Отклонить выбранные события')
    def reject(self, request, queryset):
        self.message_user(request, f'Отклонено: {queryset.update(status=Event.Status.REJECTED)}')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'created_at')
    search_fields = ('user__username', 'event__title_en')
    autocomplete_fields = ('user', 'event')
