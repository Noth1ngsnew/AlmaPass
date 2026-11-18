from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from events.models import Event
from rewards import loyalty, nft
from rewards.models import NFTReward, Visit

User = get_user_model()


class Command(BaseCommand):
    help = ('Подготовка к показу: отмечает пользователя на нескольких опубликованных событиях и выдаёт '
            'ему настоящие NFT в сети, чтобы сразу показать уровень и скидку.')

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--count', type=int, default=3, help='Сколько NFT выдать (по умолчанию 3 — уровень Silver)')

    def handle(self, username, count, **options):
        user = User.objects.filter(username=username).first()
        if user is None:
            raise CommandError(f'Пользователь {username} не найден.')
        if not nft.is_valid_wallet(user.wallet_address):
            raise CommandError('У пользователя нет адреса кошелька. Укажите его в профиле на сайте.')
        if not nft.is_configured():
            raise CommandError('Выдача NFT не настроена: нужны NFT_PRIVATE_KEY и NFT_CONTRACT_ADDRESS в .env.')

        events = (Event.objects.filter(status=Event.Status.PUBLISHED)
                  .exclude(visits__user=user).order_by('start_at')[:count])
        if len(events) < count:
            raise CommandError(f'Недостаточно событий, где пользователь ещё не отмечался: есть {len(events)}.')

        for event in events:
            visit = Visit.objects.create(user=user, event=event)
            reward = NFTReward.objects.create(visit=visit, wallet_address=user.wallet_address)
            self.stdout.write(f'{event.title_en}: выдаю NFT…')
            result = nft.mint_reward(reward.id)
            if result.status == NFTReward.Status.MINTED:
                self.stdout.write(self.style.SUCCESS(f'  токен #{result.token_id}, транзакция {result.tx_hash}'))
            else:
                self.stdout.write(self.style.ERROR(f'  ошибка: {result.error}'))

        info = loyalty.progress(user)
        level = info['current']
        self.stdout.write(self.style.SUCCESS(
            f'\nУ {username} теперь NFT: {info["nft_count"]}, уровень: '
            f'{level.name_en if level else "нет"} (скидка {level.discount_percent if level else 0}%).'))
