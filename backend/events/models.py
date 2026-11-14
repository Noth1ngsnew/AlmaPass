import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import get_language


class TranslatedFieldsMixin:
    """Поля вида title_en / title_ru / title_kk с откатом на английский."""

    def translated(self, field, lang=None):
        lang = (lang or get_language() or 'en')[:2]
        return getattr(self, f'{field}_{lang}', '') or getattr(self, f'{field}_en')


class Category(TranslatedFieldsMixin, models.Model):
    slug = models.SlugField(unique=True)
    name_en = models.CharField(max_length=100)
    name_ru = models.CharField(max_length=100, blank=True)
    name_kk = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name_en']

    def __str__(self):
        return self.name_en


class Venue(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    website = models.URLField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Organizer(models.Model):
    """Профиль организатора, привязан к пользователю с ролью organizer."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='organizer')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Event(TranslatedFieldsMixin, models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PENDING = 'pending', 'Pending review'
        PUBLISHED = 'published', 'Published'
        REJECTED = 'rejected', 'Rejected'

    title_en = models.CharField(max_length=200)
    title_ru = models.CharField(max_length=200, blank=True)
    title_kk = models.CharField(max_length=200, blank=True)
    description_en = models.TextField(blank=True)
    description_ru = models.TextField(blank=True)
    description_kk = models.TextField(blank=True)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='events')
    venue = models.ForeignKey(Venue, on_delete=models.PROTECT, related_name='events')
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, related_name='events')

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text='В тенге; 0 — бесплатно')
    image_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True, help_text='Ссылка на первоисточник или продажу билетов')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Секрет для QR-кода check-in; показывается только организатору
    checkin_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    # Картинка/метаданные NFT, который выдаётся за посещение
    nft_image_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_at']
        indexes = [models.Index(fields=['status', 'start_at'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(end_at__gte=models.F('start_at')), name='event_end_after_start'),
        ]

    def __str__(self):
        return self.title_en


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['user', 'event'], name='unique_favorite')]

    def __str__(self):
        return f'{self.user} ♥ {self.event}'
