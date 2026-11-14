from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from rewards.models import NFTReward, Visit

from .models import Category, Event, Favorite, Organizer, Venue

User = get_user_model()


class ModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('aida', 'aida@example.com', 'pass12345')
        owner = User.objects.create_user('org', 'org@example.com', 'pass12345', role=User.Role.ORGANIZER)
        self.event = Event.objects.create(
            title_en='Jazz night', title_ru='Ночь джаза',
            category=Category.objects.create(slug='music', name_en='Music'),
            venue=Venue.objects.create(name='Esentai', address='Al-Farabi 77/8'),
            organizer=Organizer.objects.create(user=owner, name='Org'),
            start_at=timezone.now(), end_at=timezone.now() + timedelta(hours=2),
        )

    def test_translation_fallback(self):
        self.assertEqual(self.event.translated('title', 'ru'), 'Ночь джаза')
        self.assertEqual(self.event.translated('title', 'kk'), 'Jazz night')

    def test_one_visit_and_favorite_per_user_event(self):
        Visit.objects.create(user=self.user, event=self.event)
        Favorite.objects.create(user=self.user, event=self.event)
        for model in (Visit, Favorite):
            with self.assertRaises(IntegrityError), transaction.atomic():
                model.objects.create(user=self.user, event=self.event)

    def test_end_before_start_rejected(self):
        self.event.end_at = self.event.start_at - timedelta(hours=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.event.save()

    def test_reward_defaults_to_pending(self):
        visit = Visit.objects.create(user=self.user, event=self.event)
        self.assertEqual(NFTReward.objects.create(visit=visit).status, NFTReward.Status.PENDING)

    def test_setup_roles_creates_groups(self):
        call_command('setup_roles', stdout=StringIO())
        moderators = Group.objects.get(name='Moderators')
        self.assertTrue(moderators.permissions.filter(codename='change_event').exists())
        self.assertFalse(Group.objects.get(name='Support').permissions.filter(codename='delete_event').exists())
