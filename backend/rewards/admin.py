from django.contrib import admin

from .models import DiscountCode, LoyaltyLevel, NFTReward, Visit


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


@admin.register(LoyaltyLevel)
class LoyaltyLevelAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_ru', 'name_kk', 'min_nfts', 'discount_percent')
    list_editable = ('min_nfts', 'discount_percent')
    search_fields = ('name_en', 'name_ru', 'name_kk')


@admin.register(DiscountCode)
class DiscountCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'user', 'event', 'discount_percent', 'status', 'created_at', 'used_at')
    list_filter = ('status', 'discount_percent')
    search_fields = ('code', 'user__username', 'event__title_en')
    autocomplete_fields = ('user', 'event')
    readonly_fields = ('created_at', 'used_at', 'redeemed_by')
