from django.conf import settings
from django.db import models

from events.models import Event


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
