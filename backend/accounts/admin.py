from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'wallet_address', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'language')
    search_fields = ('username', 'email', 'wallet_address')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('AlmaPass', {'fields': ('role', 'wallet_address', 'language', 'avatar_url')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('AlmaPass', {'fields': ('email', 'role')}),
    )
