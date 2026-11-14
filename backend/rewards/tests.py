from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from events.models import Category, Event, Organizer, Venue

from .models import NFTReward, Visit

User = get_user_model()


class CheckInTest(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('org', 'org@example.com', 'pass12345', role=User.Role.ORGANIZER)
        self.user = User.objects.create_user('aida', 'aida@example.com', 'pass12345',
                                             wallet_address='0x' + 'a' * 40)
        self.common = dict(
            category=Category.objects.create(slug='music', name_en='Music'),
            venue=Venue.objects.create(name='Esentai', address='Al-Farabi 77/8'),
            organizer=Organizer.objects.create(user=self.owner, name='Org'),
            status=Event.Status.PUBLISHED,
        )
        now = timezone.now()
        self.live = self.make('Live', now - timedelta(hours=1), now + timedelta(hours=1))

    def make(self, title, start, end, **extra):
        return Event.objects.create(title_en=title, start_at=start, end_at=end, **{**self.common, **extra})

    def checkin(self, event):
        return self.client.post('/api/checkin/', {'token': str(event.checkin_token)})

    def test_requires_login(self):
        self.assertEqual(self.checkin(self.live).status_code, 401)

    def test_checkin_creates_visit_and_pending_nft(self):
        self.client.force_authenticate(self.user)
        r = self.checkin(self.live)
        self.assertEqual(r.status_code, 201)
        self.assertFalse(r.data['already_checked_in'])
        self.assertEqual(r.data['nft_reward']['status'], 'pending')
        self.assertEqual(r.data['nft_reward']['wallet_address'], self.user.wallet_address)
        self.assertTrue(r.data['event']['is_visited'])

        r = self.checkin(self.live)  # повтор не создаёт дубль
        self.assertEqual((r.status_code, r.data['already_checked_in']), (200, True))
        self.assertEqual((Visit.objects.count(), NFTReward.objects.count()), (1, 1))

    def test_invalid_codes(self):
        self.client.force_authenticate(self.user)
        for token in ('', 'not-a-code', '00000000-0000-0000-0000-000000000000'):
            r = self.client.post('/api/checkin/', {'token': token})
            self.assertEqual((r.status_code, r.data['code']), (400, 'invalid'))
        hidden = self.make('Hidden', self.live.start_at, self.live.end_at, status=Event.Status.PENDING)
        self.assertEqual(self.checkin(hidden).data['code'], 'invalid')

    def test_only_during_event(self):
        self.client.force_authenticate(self.user)
        now = timezone.now()
        future = self.make('Future', now + timedelta(days=2), now + timedelta(days=2, hours=2))
        past = self.make('Past', now - timedelta(days=2), now - timedelta(days=2) + timedelta(hours=2))
        soon = self.make('Soon', now + timedelta(minutes=30), now + timedelta(hours=3))
        self.assertEqual(self.checkin(future).data['code'], 'not_started')
        self.assertEqual(self.checkin(past).data['code'], 'ended')
        self.assertEqual(self.checkin(soon).status_code, 201)  # за час до начала уже можно

    def test_my_visits(self):
        self.client.force_authenticate(self.user)
        self.checkin(self.live)
        r = self.client.get('/api/visits/')
        self.assertEqual(r.data['count'], 1)
        self.assertEqual(r.data['results'][0]['event']['title_en'], 'Live')
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.get('/api/visits/').data['count'], 0)

    def test_checkin_code_only_for_owner(self):
        url = f'/api/events/{self.live.id}/checkin-code/'
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertNotIn(str(self.live.checkin_token), str(self.client.get(f'/api/events/{self.live.id}/').data))
        self.checkin(self.live)
        self.client.force_authenticate(self.owner)
        r = self.client.get(url)
        self.assertEqual((r.data['token'], r.data['visits_count']), (str(self.live.checkin_token), 1))
