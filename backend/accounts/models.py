from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользователь платформы. Роль определяет доступ в API и кабинетах."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ORGANIZER = 'organizer', 'Organizer'
        ADMIN = 'admin', 'Admin'

    class Language(models.TextChoices):
        EN = 'en', 'English'
        RU = 'ru', 'Русский'
        KK = 'kk', 'Қазақша'

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.USER)
    # Адрес кошелька (MetaMask), на который выдаются NFT
    wallet_address = models.CharField(max_length=42, blank=True)
    language = models.CharField(max_length=2, choices=Language.choices, default=Language.EN)
    avatar_url = models.URLField(blank=True)

    def __str__(self):
        return self.username
