from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Category, Event, Organizer, Venue

User = get_user_model()

CATEGORIES = [
    ('music', 'Music', 'Музыка', 'Музыка'),
    ('theatre', 'Theatre', 'Театр', 'Театр'),
    ('exhibitions', 'Exhibitions', 'Выставки', 'Көрмелер'),
    ('sport', 'Sport', 'Спорт', 'Спорт'),
    ('education', 'Education', 'Образование', 'Білім'),
    ('festivals', 'Festivals', 'Фестивали', 'Фестивальдар'),
    ('kids', 'Kids', 'Детям', 'Балаларға'),
]

# Проверьте адреса перед показом: они внесены для демо
VENUES = {
    'palace': ('Palace of the Republic', 'Dostyk Ave 56, Almaty'),
    'opera': ('Abay Opera House', 'Kabanbay Batyr St 110, Almaty'),
    'kasteev': ('Kasteev State Museum of Arts', 'Koktem-3 22/1, Almaty'),
    'museum': ('Central State Museum of Kazakhstan', 'Samal-1 44, Almaty'),
    'esentai': ('Esentai Mall', 'Al-Farabi Ave 77/8, Almaty'),
    'medeu': ('Medeu Skating Rink', 'Gornaya St 465, Almaty'),
    'koktobe': ('Kok Tobe Park', 'Dostyk Ave 104B, Almaty'),
}

ORGANIZERS = {
    'demo_organizer': ('Almaty Events Lab', 'Concerts, festivals and city tours.'),
    'demo_culture': ('Culture Hub Almaty', 'Exhibitions, theatre and lectures.'),
}

# (организатор, категория, площадка, через сколько дней, час, длительность ч, цена, en, ru, kk)
EVENTS = [
    ('demo_organizer', 'music', 'palace', 3, 19, 2, 8000, 'Symphony of the Steppe', 'Симфония степи', 'Дала симфониясы'),
    ('demo_organizer', 'music', 'esentai', 5, 20, 3, 0, 'Open-Air Jazz Evening', 'Джазовый вечер под открытым небом', 'Ашық аспан астындағы джаз кеші'),
    ('demo_culture', 'theatre', 'opera', 6, 18, 3, 6000, 'Abai: Opera Night', 'Абай: вечер оперы', 'Абай: опера кеші'),
    ('demo_culture', 'theatre', 'opera', 12, 18, 2, 5000, 'Ballet Gala', 'Гала-концерт балета', 'Балет гала-концерті'),
    ('demo_culture', 'exhibitions', 'kasteev', 1, 10, 8, 1500, 'Modern Kazakh Painting', 'Современная казахская живопись', 'Қазіргі қазақ кескіндемесі'),
    ('demo_culture', 'exhibitions', 'museum', 2, 10, 8, 1000, 'Treasures of the Great Steppe', 'Сокровища Великой степи', 'Ұлы дала қазыналары'),
    ('demo_culture', 'exhibitions', 'kasteev', 9, 11, 7, 0, 'Young Artists of Almaty', 'Молодые художники Алматы', 'Алматының жас суретшілері'),
    ('demo_organizer', 'sport', 'medeu', 4, 9, 4, 3000, 'Mass Skating Day', 'День массового катания', 'Жаппай сырғанау күні'),
    ('demo_organizer', 'sport', 'koktobe', 8, 8, 3, 0, 'Morning Run to Kok Tobe', 'Утренний забег на Кок-Тобе', 'Көктөбеге таңғы жүгіріс'),
    ('demo_organizer', 'sport', 'medeu', 15, 10, 5, 2000, 'Winter Sports Fest', 'Фестиваль зимних видов спорта', 'Қысқы спорт фестивалі'),
    ('demo_culture', 'education', 'museum', 7, 15, 2, 0, 'Lecture: History of the Silk Road', 'Лекция: история Шёлкового пути', 'Дәріс: Жібек жолының тарихы'),
    ('demo_organizer', 'education', 'esentai', 10, 12, 6, 5000, 'Almaty Tech Meetup', 'Алматы Tech Meetup', 'Алматы Tech Meetup'),
    ('demo_organizer', 'education', 'esentai', 14, 14, 3, 0, 'Web3 and NFT Workshop', 'Воркшоп по Web3 и NFT', 'Web3 және NFT шеберханасы'),
    ('demo_organizer', 'festivals', 'koktobe', 11, 12, 9, 0, 'City Street Food Festival', 'Городской фестиваль уличной еды', 'Қалалық көше тағамдары фестивалі'),
    ('demo_organizer', 'festivals', 'palace', 20, 17, 5, 4000, 'Almaty Apple Fest', 'Фестиваль яблок Алматы', 'Алматы алма фестивалі'),
    ('demo_culture', 'kids', 'museum', 6, 11, 2, 500, 'Dinosaur Quest for Kids', 'Квест с динозаврами для детей', 'Балаларға арналған динозавр квесті'),
    ('demo_culture', 'kids', 'kasteev', 13, 12, 2, 0, 'Family Drawing Workshop', 'Семейный мастер-класс по рисованию', 'Отбасылық сурет салу шеберханасы'),
    ('demo_organizer', 'music', 'koktobe', 18, 19, 3, 3500, 'Sunset Acoustic Session', 'Акустика на закате', 'Күн батқандағы акустика'),
]

DESCRIPTION = {
    'en': 'Demo event for the AlmaPass platform. Visit, scan the QR code at the venue and collect your NFT.',
    'ru': 'Демо-событие платформы AlmaPass. Приходите, сканируйте QR-код на площадке и получайте NFT.',
    'kk': 'AlmaPass платформасының демо-іс-шарасы. Келіңіз, QR-кодты сканерлеп, NFT алыңыз.',
}


class Command(BaseCommand):
    help = ('Наполняет базу демо-данными: категории, площадки, организаторы, события. Повторный запуск безопасен '
            'и переносит даты демо-событий на ближайшие дни.')

    def handle(self, *args, **options):
        categories = {}
        for slug, en, ru, kk in CATEGORIES:
            categories[slug], _ = Category.objects.update_or_create(
                slug=slug, defaults={'name_en': en, 'name_ru': ru, 'name_kk': kk})

        venues = {}
        for key, (name, address) in VENUES.items():
            venues[key], _ = Venue.objects.get_or_create(name=name, defaults={'address': address})

        organizers = {}
        for username, (name, description) in ORGANIZERS.items():
            user, created = User.objects.get_or_create(
                username=username, defaults={'email': f'{username}@almapass.local', 'role': User.Role.ORGANIZER})
            if created:
                user.set_password('demo12345')
                user.save()
            organizers[username], _ = Organizer.objects.get_or_create(
                user=user, defaults={'name': name, 'description': description, 'is_verified': True})

        today = timezone.localtime().replace(minute=0, second=0, microsecond=0)
        created_count = 0
        for i, (org, cat, venue, days, hour, hours, price, en, ru, kk) in enumerate(EVENTS):
            start = (today + timedelta(days=days)).replace(hour=hour)
            event, created = Event.objects.get_or_create(
                title_en=en,
                defaults={
                    'title_ru': ru, 'title_kk': kk,
                    'description_en': DESCRIPTION['en'], 'description_ru': DESCRIPTION['ru'],
                    'description_kk': DESCRIPTION['kk'],
                    'category': categories[cat], 'venue': venues[venue], 'organizer': organizers[org],
                    'start_at': start, 'end_at': start + timedelta(hours=hours), 'price': Decimal(price),
                    'image_url': f'https://picsum.photos/seed/almapass{i}/800/500',
                    # последнее событие оставляем на модерации, чтобы было что показать в админке
                    'status': Event.Status.PENDING if i == len(EVENTS) - 1 else Event.Status.PUBLISHED,
                },
            )
            created_count += created
            if not created and (event.start_at != start):
                # Повторный запуск: переносим демо-событие на ближайшие дни, чтобы оно не оказалось в прошлом
                event.start_at, event.end_at = start, start + timedelta(hours=hours)
                event.save(update_fields=['start_at', 'end_at', 'updated_at'])

        # Событие, которое идёт прямо сейчас: на нём показывают check-in.
        # Время обновляется при каждом запуске команды, поэтому запускайте её перед показом.
        now = timezone.now()
        Event.objects.update_or_create(
            title_en='AlmaPass Demo Day',
            defaults={
                'title_ru': 'Демо-день AlmaPass', 'title_kk': 'AlmaPass демо күні',
                'description_en': 'Live presentation of the AlmaPass platform. Scan the QR code to check in.',
                'description_ru': 'Живая презентация платформы AlmaPass. Отсканируйте QR-код, чтобы отметиться.',
                'description_kk': 'AlmaPass платформасының тікелей таныстырылымы. Белгілену үшін QR-кодты сканерлеңіз.',
                'category': categories['education'], 'venue': venues['esentai'],
                'organizer': organizers['demo_organizer'],
                'start_at': now - timedelta(hours=1), 'end_at': now + timedelta(hours=8), 'price': Decimal(0),
                'image_url': 'https://picsum.photos/seed/almapassdemo/800/500',
                'status': Event.Status.PUBLISHED,
            },
        )

        self.stdout.write(self.style.SUCCESS(
            f'Готово: категорий {len(categories)}, площадок {len(venues)}, '
            f'организаторов {len(organizers)}, новых событий {created_count}.'))
        self.stdout.write('Событие для показа check-in: «AlmaPass Demo Day» (идёт сейчас, ещё 8 часов).')
        self.stdout.write('Вход организатора для демо: demo_organizer / demo12345')
