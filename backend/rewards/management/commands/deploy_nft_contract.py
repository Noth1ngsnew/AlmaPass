from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rewards import nft


class Command(BaseCommand):
    help = 'Публикует смарт-контракт AlmaPassNFT в сети из NFT_RPC_URL.'

    def handle(self, *args, **options):
        w3 = nft.get_web3()
        try:
            account = nft.get_account(w3)
        except nft.NFTError as exc:
            raise CommandError(str(exc)) from exc
        if not w3.is_connected():
            raise CommandError(f'Нет связи с сетью: {settings.NFT_RPC_URL}')

        balance = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
        self.stdout.write(f'Сеть: chain id {w3.eth.chain_id}\nКошелёк: {account.address}\nБаланс: {balance} POL')
        if balance == 0:
            raise CommandError('На кошельке нет монет. Получите тестовые POL: https://faucet.polygon.technology/')

        self.stdout.write('Публикую контракт, это занимает до минуты…')
        try:
            address = nft.deploy_contract()
        except Exception as exc:  # noqa: BLE001
            raise CommandError(f'Не удалось опубликовать контракт: {exc}') from exc

        self.stdout.write(self.style.SUCCESS(f'\nКонтракт опубликован: {address}'))
        self.stdout.write(f'Посмотреть: {settings.NFT_EXPLORER_URL}/address/{address}')
        self.stdout.write(f'\nВпишите в backend/.env строку и перезапустите сервер:\n  NFT_CONTRACT_ADDRESS={address}')
