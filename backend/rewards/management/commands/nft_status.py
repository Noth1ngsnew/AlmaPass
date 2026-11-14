from django.conf import settings
from django.core.management.base import BaseCommand

from rewards import nft
from rewards.models import NFTReward


class Command(BaseCommand):
    help = 'Показывает состояние выдачи NFT: сеть, кошелёк, контракт. С --retry повторяет незавершённые выдачи.'

    def add_arguments(self, parser):
        parser.add_argument('--retry', action='store_true', help='Повторить выдачу для pending, failed и minting')

    def handle(self, *args, **options):
        ok, bad = self.style.SUCCESS('да'), self.style.ERROR('нет')
        self.stdout.write(f'RPC: {settings.NFT_RPC_URL}')
        self.stdout.write(f'Ключ кошелька задан: {ok if settings.NFT_PRIVATE_KEY else bad}')
        self.stdout.write(f'Адрес контракта задан: {ok if settings.NFT_CONTRACT_ADDRESS else bad}')

        if settings.NFT_PRIVATE_KEY:
            w3 = nft.get_web3()
            connected = w3.is_connected()
            self.stdout.write(f'Связь с сетью: {ok if connected else bad}')
            if connected:
                account = nft.get_account(w3)
                balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
                self.stdout.write(f'Chain id: {w3.eth.chain_id}\nКошелёк: {account.address}\nБаланс: {balance} POL')
                if settings.NFT_CONTRACT_ADDRESS:
                    contract = nft.get_contract(w3)
                    self.stdout.write(f'Контракт: {contract.address}\n'
                                      f'Выдано токенов: {contract.functions.totalMinted().call()}')

        self.stdout.write('\nЗаписи NFT в базе:')
        for value, label in NFTReward.Status.choices:
            self.stdout.write(f'  {label}: {NFTReward.objects.filter(status=value).count()}')

        if options['retry']:
            rewards = NFTReward.objects.exclude(status=NFTReward.Status.MINTED)
            for reward in rewards:
                if not reward.wallet_address:
                    reward.wallet_address = reward.visit.user.wallet_address
                    reward.save(update_fields=['wallet_address'])
                result = nft.mint_reward(reward.id)
                self.stdout.write(f'  #{reward.id}: {result.status} {result.error}')
