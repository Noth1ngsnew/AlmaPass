from django.db import migrations

# Начальные уровни; администратор может менять их в админ-панели
LEVELS = [
    # (min_nfts, discount_percent, en, ru, kk)
    (1, 0, 'Bronze', 'Бронза', 'Қола'),
    (3, 10, 'Silver', 'Серебро', 'Күміс'),
    (5, 15, 'Gold', 'Золото', 'Алтын'),
    (10, 20, 'Platinum', 'Платина', 'Платина'),
]


def create_levels(apps, schema_editor):
    LoyaltyLevel = apps.get_model('rewards', 'LoyaltyLevel')
    for min_nfts, percent, en, ru, kk in LEVELS:
        LoyaltyLevel.objects.update_or_create(
            min_nfts=min_nfts,
            defaults={'discount_percent': percent, 'name_en': en, 'name_ru': ru, 'name_kk': kk},
        )


def remove_levels(apps, schema_editor):
    apps.get_model('rewards', 'LoyaltyLevel').objects.filter(min_nfts__in=[row[0] for row in LEVELS]).delete()


class Migration(migrations.Migration):
    dependencies = [('rewards', '0003_loyaltylevel_discountcode')]
    operations = [migrations.RunPython(create_levels, remove_levels)]
