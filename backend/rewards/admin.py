from django.contrib import admin

from .models import NFTReward, Visit


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'checked_in_at')
    list_filter = ('checked_in_at',)
    search_fields = ('user__username', 'event__title_en')
    autocomplete_fields = ('user', 'event')


@admin.register(NFTReward)
class NFTRewardAdmin(admin.ModelAdmin):
    list_display = ('visit', 'status', 'token_id', 'wallet_address', 'minted_at')
    list_filter = ('status',)
    search_fields = ('visit__user__username', 'visit__event__title_en', 'tx_hash', 'wallet_address')
    autocomplete_fields = ('visit',)
    readonly_fields = ('created_at',)
