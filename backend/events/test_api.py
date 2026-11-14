from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APITestCase

from .models import Category, Event, Organizer, Venue

User = get_user_model()


class ApiTest(APITestCase):
    def setUp(self):
        self.category = Category.objects.create(slug='music', name_en='Music', name_ru='Музыка')
        self.venue = Venue.objects.create(name='Esentai', address='Al-Farabi 77/8')
        self.owner = User.objects.create_user('org', 'org@example.com', 'pass12345', role=User.Role.ORGANIZER)
        self.organizer = Organizer.objects.create(user=self.owner, name='Org')
        self.admin = User.objects.create_superuser('boss', 'boss@example.com', 'pass12345')
        self.user = User.objects.create_user('aida', 'aida@example.com', 'pass12345')
        now = timezone.now()
        common = dict(category=self.category, venue=self.venue, organizer=self.organizer,
                      start_at=now, end_at=now + timedelta(hours=2))
        self.published = Event.objects.create(title_en='Jazz night', title_ru='Ночь джаза',
                                              status=Event.Status.PUBLISHED, **common)
        self.draft = Event.objects.create(title_en='Secret', status=Event.Status.PENDING, **common)

    def payload(self, **extra):
        now = timezone.now()
        return {'title_en': 'New', 'category_id': self.category.id, 'venue_id': self.venue.id,
                'start_at': now.isoformat(), 'end_at': (now + timedelta(hours=1)).isoformat(), **extra}

    def test_register_login_me(self):
        r = self.client.post('/api/auth/register/', {'username': 'new', 'email': 'new@example.com',
                                                     'password': 'Str0ng-pass!', 'role': 'admin'})
        self.assertEqual(r.status_code, 201)
        self.assertNotIn('password', r.data)
        r = self.client.post('/api/auth/login/', {'username': 'new', 'password': 'Str0ng-pass!'})
        self.assertEqual(r.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {r.data["access"]}')
        r = self.client.get('/api/auth/me/')
        self.assertEqual(r.data['role'], 'user')  # роль нельзя назначить себе при регистрации
        self.assertIsNone(r.data['organizer_id'])
        r = self.client.patch('/api/auth/me/', {'wallet_address': 'nope', 'role': 'admin'})
        self.assertEqual(r.status_code, 400)
        r = self.client.patch('/api/auth/me/', {'wallet_address': '0x' + 'a' * 40, 'role': 'admin'})
        self.assertEqual((r.status_code, r.data['role']), (200, 'user'))

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get('/api/auth/me/').status_code, 401)

    def test_public_sees_only_published_and_translated(self):
        r = self.client.get('/api/events/?lang=ru')
        self.assertEqual([e['title'] for e in r.data['results']], ['Ночь джаза'])
        self.assertEqual(r.data['results'][0]['category']['name'], 'Музыка')
        self.assertNotIn('checkin_token', r.data['results'][0])
        self.assertEqual(self.client.get(f'/api/events/{self.draft.id}/').status_code, 404)
        r = self.client.get('/api/events/', HTTP_ACCEPT_LANGUAGE='kk')
        self.assertEqual(r.data['results'][0]['title'], 'Jazz night')  # откат на английский

    def test_filters(self):
        self.assertEqual(self.client.get('/api/events/?category=music').data['count'], 1)
        self.assertEqual(self.client.get('/api/events/?category=sport').data['count'], 0)
        self.assertEqual(self.client.get('/api/events/?date_from=2100-01-01').data['count'], 0)

    def test_only_organizer_creates_events(self):
        self.assertEqual(self.client.post('/api/events/', self.payload()).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/api/events/', self.payload()).status_code, 403)
        self.assertEqual(self.client.post('/api/venues/', {'name': 'X', 'address': 'Y'}).status_code, 403)
        self.client.force_authenticate(self.owner)
        r = self.client.post('/api/events/', self.payload(status='published'))
        self.assertEqual((r.status_code, r.data['status']), (201, 'pending'))
        self.assertEqual(self.client.get('/api/events/?mine=1').data['count'], 3)
        r = self.client.post('/api/events/', self.payload(end_at='2000-01-01T00:00:00Z'))
        self.assertEqual(r.status_code, 400)

    def test_only_owner_edits(self):
        other = User.objects.create_user('other', 'other@example.com', 'pass12345')
        Organizer.objects.create(user=other, name='Other')
        self.client.force_authenticate(other)
        url = f'/api/events/{self.published.id}/'
        self.assertEqual(self.client.patch(url, {'title_en': 'Hacked'}).status_code, 403)
        self.assertEqual(self.client.delete(url).status_code, 403)
        self.client.force_authenticate(self.owner)
        r = self.client.patch(url, {'title_en': 'Jazz night 2'})
        self.assertEqual((r.status_code, r.data['status']), (200, 'pending'))

    def test_moderation(self):
        url = f'/api/events/{self.draft.id}/moderate/'
        self.client.force_authenticate(self.owner)
        self.assertEqual(self.client.post(url, {'status': 'published'}).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.post(url, {'status': 'draft'}).status_code, 400)
        self.assertEqual(self.client.post(url, {'status': 'published'}).data['status'], 'published')

    def test_favorites(self):
        url = f'/api/events/{self.published.id}/favorite/'
        self.assertEqual(self.client.post(url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.client.post(url)
        self.client.post(url)  # повтор не создаёт дубль
        self.assertEqual(self.client.get('/api/favorites/').data['count'], 1)
        self.assertTrue(self.client.get('/api/events/').data['results'][0]['is_favorite'])
        self.client.delete(url)
        self.assertEqual(self.client.get('/api/favorites/').data['count'], 0)

    def test_apply_as_organizer(self):
        self.client.force_authenticate(self.user)
        r = self.client.post('/api/organizers/apply/', {'name': 'Aida Events'})
        self.assertEqual(r.status_code, 201)
        self.user.refresh_from_db()
        self.assertEqual(self.user.role, 'organizer')
        self.assertEqual(self.client.post('/api/organizers/apply/', {'name': 'Again'}).status_code, 400)
        self.assertEqual(self.client.post('/api/events/', self.payload()).status_code, 201)

    def test_search_covers_three_entity_types(self):
        r = self.client.get('/api/search/?q=джаз')  # русское название, регистр не важен
        self.assertEqual([e['title_en'] for e in r.data['events']], ['Jazz night'])
        r = self.client.get('/api/search/?q=ESENTAI')
        self.assertEqual((len(r.data['venues']), r.data['venues'][0]['events_count']), (1, 1))
        r = self.client.get('/api/search/?q=org')
        self.assertEqual([o['name'] for o in r.data['organizers']], ['Org'])
        self.assertEqual(r.data['total'], 1)

    def test_search_hides_unpublished_and_ignores_short_query(self):
        self.assertEqual(self.client.get('/api/search/?q=secret').data['total'], 0)
        self.assertEqual(self.client.get('/api/search/?q=j').data['total'], 0)
        self.assertEqual(self.client.get('/api/search/').data['total'], 0)

    def test_search_by_category_name(self):
        self.assertEqual(len(self.client.get('/api/search/?q=музыка').data['events']), 1)
