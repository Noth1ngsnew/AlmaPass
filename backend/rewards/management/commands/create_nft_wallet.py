from django.core.management.base import BaseCommand
from eth_account import Account


class Command(BaseCommand):
    help = 'Создаёт новый серверный кошелёк для выдачи NFT и показывает, что вписать в .env.'

    def handle(self, *args, **options):
        account = Account.create()
        self.stdout.write(self.style.SUCCESS('Новый кошелёк создан.'))
        self.stdout.write(f'\nАдрес (на него нужно получить тестовые POL из крана):\n  {account.address}')
        self.stdout.write(f'\nВпишите в backend/.env строку:\n  NFT_PRIVATE_KEY={account.key.to_0x_hex()}')
        self.stdout.write(self.style.WARNING(
            '\nКлюч показывается один раз. Никому его не отправляйте и не добавляйте в Git.'))
