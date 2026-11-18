from django.conf import settings
from django.db import models

from django.core.validators import MaxValueValidator

from events.models import Event, TranslatedFieldsMixin


class Visit(models.Model):
    """Подтверждённое посещение события (check-in по QR-коду)."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='visits')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='visits')
    checked_in_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_in_at']
        constraints = [models.UniqueConstraint(fields=['user', 'event'], name='unique_visit')]

    def __str__(self):
        return f'{self.user} @ {self.event}'


class NFTReward(models.Model):
    """NFT за посещение. Статус хранится в БД, чтобы интерфейс не зависел от скорости сети."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        MINTING = 'minting', 'Minting'
        MINTED = 'minted', 'Minted'
        FAILED = 'failed', 'Failed'

    visit = models.OneToOneField(Visit, on_delete=models.CASCADE, related_name='nft_reward')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    wallet_address = models.CharField(max_length=42, blank=True)
    contract_address = models.CharField(max_length=42, blank=True)
    token_id = models.PositiveBigIntegerField(null=True, blank=True)
    tx_hash = models.CharField(max_length=66, blank=True)
    metadata_uri = models.URLField(blank=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    minted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'NFT reward'
        ordering = ['-created_at']

    def __str__(self):
        return f'NFT #{self.token_id or "—"} ({self.status}) for {self.visit}'


class LoyaltyLevel(TranslatedFieldsMixin, models.Model):
    """Уровень владельца NFT: чем больше NFT за посещения, тем больше скидка."""

    name_en = models.CharField(max_length=50)
    name_ru = models.CharField(max_length=50, blank=True)
    name_kk = models.CharField(max_length=50, blank=True)
    min_nfts = models.PositiveIntegerField(unique=True, help_text='Сколько NFT нужно для уровня')
    discount_percent = models.PositiveSmallIntegerField(default=0, validators=[MaxValueValidator(90)])

    class Meta:
        ordering = ['min_nfts']

    def __str__(self):
        return f'{self.name_en} ({self.min_nfts}+ NFT, -{self.discount_percent}%)'


class DiscountCode(models.Model):
    """Одноразовый код скидки на платное событие. Выдаётся по уровню, гасится организатором."""

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        USED = 'used', 'Used'

    code = models.CharField(max_length=16, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='discount_codes')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='discount_codes')
    level = models.ForeignKey(LoyaltyLevel, on_delete=models.SET_NULL, null=True, related_name='discount_codes')
    # Процент фиксируется в момент выдачи, даже если уровень потом изменится
    discount_percent = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(null=True, blank=True)
    redeemed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='redeemed_discount_codes')

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['user', 'event'], name='unique_discount_per_event')]

    @property
    def final_price(self):
        return (self.event.price * (100 - self.discount_percent) / 100).quantize(self.event.price)

    def __str__(self):
        return f'{self.code} (-{self.discount_percent}%, {self.status})'
