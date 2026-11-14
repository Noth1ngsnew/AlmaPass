"""Тесты выдачи NFT на локальной тестовой сети (нужен пакет из requirements-dev.txt)."""

import unittest
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from events.models import Category, Event, Organizer, Venue

from . import nft
from .models import NFTReward

try:
    from eth_account import Account
    from web3 import EthereumTesterProvider, Web3
    HAS_TESTER = True
except ImportError:  # pragma: no cover
    HAS_TESTER = False

User = get_user_model()
WALLET = '0x' + 'a1' * 20


@unittest.skipUnless(HAS_TESTER, 'install requirements-dev.txt to run NFT tests')
class NFTFlowTest(APITestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Локальная сеть в памяти: серверный кошелёк с монетами и опубликованный контракт
        cls.w3 = Web3(EthereumTesterProvider())
        cls.server = Account.create()
        cls.w3.eth.send_transaction({'from': cls.w3.eth.accounts[0], 'to': cls.server.address,
                                     'value': cls.w3.to_wei(10, 'ether')})
        cls.patch = mock.patch.object(nft, 'get_web3', return_value=cls.w3)
        cls.patch.start()
        cls.settings = override_settings(NFT_PRIVATE_KEY=cls.server.key.to_0x_hex(), NFT_MINT_ASYNC=False)
        cls.settings.enable()
        cls.contract_address = nft.deploy_contract()
        cls.contract_settings = override_settings(NFT_CONTRACT_ADDRESS=cls.contract_address)
        cls.contract_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls.contract_settings.disable()
        cls.settings.disable()
        cls.patch.stop()
        super().tearDownClass()

    def setUp(self):
        owner = User.objects.create_user('org', 'org@example.com', 'pass12345')
        now = timezone.now()
        self.event = Event.objects.create(
            title_en='Live', status=Event.Status.PUBLISHED,
            category=Category.objects.create(slug='music', name_en='Music'),
            venue=Venue.objects.create(name='Esentai', address='Al-Farabi 77/8'),
            organizer=Organizer.objects.create(user=owner, name='Org'),
            start_at=now - timedelta(hours=1), end_at=now + timedelta(hours=1),
            image_url='https://example.com/a.png',
        )
        self.contract = nft.get_contract(self.w3)

    def login(self, username, wallet=''):
        user = User.objects.create_user(username, f'{username}@example.com', 'pass12345', wallet_address=wallet)
        self.client.force_authenticate(user)
        return user

    def checkin(self):
        return self.client.post('/api/checkin/', {'token': str(self.event.checkin_token)})

    def test_checkin_with_wallet_mints_nft(self):
        self.login('aida', WALLET)
        r = self.checkin()
        reward = r.data['nft_reward']
        self.assertEqual(reward['status'], 'minted', NFTReward.objects.get().error)
        self.assertEqual(reward['contract_address'], self.contract_address)
        self.assertTrue(reward['explorer_url'].endswith(reward['tx_hash']))

        # Сверяем с тем, что реально записано в сети
        token_id = reward['token_id']
        self.assertEqual(self.contract.functions.ownerOf(token_id).call(), Web3.to_checksum_address(WALLET))
        self.assertEqual(self.contract.functions.eventOf(token_id).call(), self.event.id)
        self.assertEqual(self.contract.functions.tokenURI(token_id).call(), reward['metadata_uri'])

        meta = self.client.get(f'/api/nft/metadata/{reward["id"]}/').data
        self.assertEqual((meta['name'], meta['image']), ('AlmaPass: Live', 'https://example.com/a.png'))

    def test_no_wallet_then_claim(self):
        user = self.login('bek')
        visit = self.checkin().data
        self.assertEqual(visit['nft_reward']['status'], 'pending')
        url = f'/api/visits/{visit["id"]}/claim/'
        r = self.client.post(url)
        self.assertEqual((r.status_code, r.data['code']), (400, 'no_wallet'))

        user.wallet_address = '0x' + 'b2' * 20
        user.save()
        r = self.client.post(url)
        self.assertEqual(r.data['nft_reward']['status'], 'minted')
        before = self.contract.functions.totalMinted().call()
        self.assertEqual(self.client.post(url).data['nft_reward']['status'], 'minted')  # повтор ничего не выдаёт
        self.assertEqual(self.contract.functions.totalMinted().call(), before)

    def test_cannot_claim_someone_elses_visit(self):
        self.login('aida', WALLET)
        visit_id = self.checkin().data['id']
        self.login('eve', '0x' + 'c3' * 20)
        self.assertEqual(self.client.post(f'/api/visits/{visit_id}/claim/').status_code, 404)

    def test_network_error_is_saved_and_retry_works(self):
        self.login('dana', '0x' + 'd4' * 20)
        with mock.patch.object(nft, 'send_transaction', side_effect=ConnectionError('rpc is down')):
            visit = self.checkin().data
        self.assertEqual(visit['nft_reward']['status'], 'failed')
        self.assertIn('rpc is down', NFTReward.objects.get().error)
        r = self.client.post(f'/api/visits/{visit["id"]}/claim/')
        self.assertEqual(r.data['nft_reward']['status'], 'minted')

    @override_settings(NFT_CONTRACT_ADDRESS='')
    def test_not_configured(self):
        self.login('emil', '0x' + 'e5' * 20)
        visit = self.checkin().data
        self.assertEqual(visit['nft_reward']['status'], 'pending')
        r = self.client.post(f'/api/visits/{visit["id"]}/claim/')
        self.assertEqual((r.status_code, r.data['code']), (503, 'not_configured'))
