from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from events.models import Category, Event, Organizer, Venue

from . import loyalty
from .models import DiscountCode, LoyaltyLevel, NFTReward, Visit

User = get_user_model()


class LoyaltyBase(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user('org', 'org@example.com', 'pass12345', role=User.Role.ORGANIZER)
        self.organizer = Organizer.objects.create(user=self.owner, name='Org')
        self.user = User.objects.create_user('aida', 'aida@example.com', 'pass12345')
        self.common = dict(category=Category.objects.create(slug='music', name_en='Music'),
                           venue=Venue.objects.create(name='Esentai', address='Al-Farabi 77/8'),
                           organizer=self.organizer, status=Event.Status.PUBLISHED)
        self.concert = self.event('Concert', price=8000)

    def event(self, title, price=0, days=5, **extra):
        start = timezone.now() + timedelta(days=days)
        return Event.objects.create(title_en=title, price=Decimal(price), start_at=start,
                                    end_at=start + timedelta(hours=2), **{**self.common, **extra})

    def give_nfts(self, user, n, status=NFTReward.Status.MINTED):
        for i in range(n):
            visit = Visit.objects.create(user=user, event=self.event(f'Past {user.username} {i}', days=-10))
            NFTReward.objects.create(visit=visit, status=status)


class LevelsTest(LoyaltyBase):
    def test_default_levels_are_seeded(self):
        self.assertEqual(list(LoyaltyLevel.objects.values_list('min_nfts', 'discount_percent')),
                         [(1, 0), (3, 10), (5, 15), (10, 20)])

    def test_only_minted_nfts_count(self):
        self.give_nfts(self.user, 2)
        self.give_nfts(self.user, 3, status=NFTReward.Status.PENDING)
        info = loyalty.progress(self.user)
        self.assertEqual((info['nft_count'], info['current'].name_en, info['next'].name_en, info['nfts_to_next']),
                         (2, 'Bronze', 'Silver', 1))

    def test_loyalty_endpoint(self):
        r = self.client.get('/api/loyalty/?lang=ru')
        self.assertEqual([lvl['name'] for lvl in r.data['levels']], ['Бронза', 'Серебро', 'Золото', 'Платина'])
        self.assertIsNone(r.data['nft_count'])
        self.give_nfts(self.user, 3)
        self.client.force_authenticate(self.user)
        r = self.client.get('/api/loyalty/')
        self.assertEqual((r.data['nft_count'], r.data['current_level']['name'], r.data['next_level']['name'],
                          r.data['nfts_to_next']), (3, 'Silver', 'Gold', 2))
        me = self.client.get('/api/auth/me/').data['loyalty']
        self.assertEqual(me, {'nft_count': 3, 'level': 'Silver', 'discount_percent': 10})

    def test_no_nfts_means_no_level(self):
        self.client.force_authenticate(self.user)
        r = self.client.get('/api/loyalty/')
        self.assertEqual((r.data['nft_count'], r.data['current_level'], r.data['nfts_to_next']), (0, None, 1))


class DiscountTest(LoyaltyBase):
    def url(self, event):
        return f'/api/events/{event.id}/discount/'

    def test_requires_login(self):
        self.assertEqual(self.client.post(self.url(self.concert)).status_code, 401)

    def test_level_too_low(self):
        self.give_nfts(self.user, 2)
        self.client.force_authenticate(self.user)
        r = self.client.post(self.url(self.concert))
        self.assertEqual((r.status_code, r.data['code'], r.data['nfts_needed']), (400, 'level_too_low', 1))
        self.assertFalse(DiscountCode.objects.exists())

    def test_silver_gets_ten_percent_once(self):
        self.give_nfts(self.user, 3)
        self.client.force_authenticate(self.user)
        r = self.client.post(self.url(self.concert))
        self.assertEqual((r.status_code, r.data['discount_percent'], r.data['final_price']), (201, 10, '7200.00'))
        self.assertRegex(r.data['code'], r'^ALMA-[A-Z2-9]{4}-[A-Z2-9]{4}$')
        again = self.client.post(self.url(self.concert))
        self.assertEqual((again.status_code, again.data['code']), (200, r.data['code']))
        self.assertEqual(DiscountCode.objects.count(), 1)
        event = self.client.get(f'/api/events/{self.concert.id}/').data
        self.assertEqual(event['my_discount']['code'], r.data['code'])
        self.assertEqual(self.client.get('/api/discounts/').data['count'], 1)

    def test_percent_is_fixed_at_issue_time(self):
        self.give_nfts(self.user, 5)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.url(self.concert)).data['discount_percent'], 15)
        LoyaltyLevel.objects.filter(min_nfts=5).update(discount_percent=50)
        self.assertEqual(DiscountCode.objects.get().discount_percent, 15)

    def test_not_for_free_disabled_ended_or_unpublished(self):
        self.give_nfts(self.user, 3)
        self.client.force_authenticate(self.user)
        cases = [(self.event('Free'), 'free_event'),
                 (self.event('No discount', price=5000, nft_discount=False), 'not_offered'),
                 (self.event('Past', price=5000, days=-3), 'ended')]
        for event, code in cases:
            r = self.client.post(self.url(event))
            self.assertEqual((r.status_code, r.data['code']), (400, code))
        hidden = self.event('Hidden', price=5000, status=Event.Status.PENDING)
        self.assertEqual(self.client.post(self.url(hidden)).status_code, 404)


class RedeemTest(LoyaltyBase):
    def setUp(self):
        super().setUp()
        self.give_nfts(self.user, 3)
        self.client.force_authenticate(self.user)
        self.code = self.client.post(f'/api/events/{self.concert.id}/discount/').data['code']

    def redeem(self, who, code=None):
        self.client.force_authenticate(who)
        return self.client.post('/api/discounts/redeem/', {'code': code or self.code})

    def test_owner_redeems_once(self):
        r = self.redeem(self.owner, '  ' + self.code.lower())
        self.assertEqual((r.status_code, r.data['status'], r.data['username'], r.data['final_price']),
                         (200, 'used', 'aida', '7200.00'))
        stored = DiscountCode.objects.get()
        self.assertEqual((stored.status, stored.redeemed_by), ('used', self.owner))
        self.assertIsNotNone(stored.used_at)
        r = self.redeem(self.owner)
        self.assertEqual((r.status_code, r.data['code']), (400, 'already_used'))

    def test_other_organizer_and_unknown_codes_look_the_same(self):
        other = User.objects.create_user('other', 'other@example.com', 'pass12345')
        Organizer.objects.create(user=other, name='Other')
        for who, code in ((other, None), (self.owner, 'ALMA-XXXX-XXXX'), (self.user, None)):
            r = self.redeem(who, code)
            self.assertEqual((r.status_code, r.data['code']), (404, 'not_found'))
        self.assertEqual(DiscountCode.objects.get().status, 'active')

    def test_admin_can_redeem(self):
        admin = User.objects.create_superuser('boss', 'boss@example.com', 'pass12345')
        self.assertEqual(self.redeem(admin).status_code, 200)


class GiveDemoNftsCommandTest(TestCase):
    def test_refuses_without_wallet_or_setup(self):
        User.objects.create_user('aida', 'aida@example.com', 'pass12345')
        with self.assertRaisesMessage(CommandError, 'кошелька'):
            call_command('give_demo_nfts', 'aida')
        with self.assertRaisesMessage(CommandError, 'не найден'):
            call_command('give_demo_nfts', 'nobody')
