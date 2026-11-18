"""Уровни владельцев NFT и коды скидок."""

import secrets

from .models import DiscountCode, LoyaltyLevel, NFTReward

# Без похожих символов (0/O, 1/I/L), чтобы код было легко продиктовать
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'


def nft_count(user):
    """Сколько NFT пользователь реально получил (только выданные в сети)."""
    return NFTReward.objects.filter(visit__user=user, status=NFTReward.Status.MINTED).count()


def progress(user):
    """Текущий и следующий уровень пользователя."""
    count = nft_count(user)
    levels = list(LoyaltyLevel.objects.all())
    current = next((level for level in reversed(levels) if level.min_nfts <= count), None)
    upcoming = next((level for level in levels if level.min_nfts > count), None)
    return {
        'nft_count': count,
        'current': current,
        'next': upcoming,
        'nfts_to_next': upcoming.min_nfts - count if upcoming else 0,
    }


def first_discount_level():
    return LoyaltyLevel.objects.filter(discount_percent__gt=0).order_by('min_nfts').first()


def generate_code():
    while True:
        part = ''.join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        code = f'ALMA-{part[:4]}-{part[4:]}'
        if not DiscountCode.objects.filter(code=code).exists():
            return code


def normalize_code(text):
    return str(text or '').strip().upper()
