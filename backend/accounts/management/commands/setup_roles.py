from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

# Группа -> {модель: [действия]}. Суперпользователь имеет все права и без групп.
GROUPS = {
    'Moderators': {
        'event': ['add', 'change', 'delete', 'view'],
        'venue': ['add', 'change', 'delete', 'view'],
        'category': ['add', 'change', 'delete', 'view'],
        'organizer': ['change', 'view'],
        'favorite': ['view'],
        'visit': ['view'],
        'nftreward': ['view'],
        'user': ['view'],
        'loyaltylevel': ['view', 'change'],
        'discountcode': ['view'],
    },
    'Support': {
        'event': ['view'],
        'venue': ['view'],
        'category': ['view'],
        'organizer': ['view'],
        'visit': ['view'],
        'nftreward': ['view', 'change'],
        'user': ['view'],
        'loyaltylevel': ['view'],
        'discountcode': ['view', 'change'],
    },
}


class Command(BaseCommand):
    help = 'Создаёт группы админ-панели (Moderators, Support) и назначает им права.'

    def handle(self, *args, **options):
        for group_name, models in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=group_name)
            codenames = [f'{action}_{model}' for model, actions in models.items() for action in actions]
            permissions = Permission.objects.filter(codename__in=codenames)
            missing = set(codenames) - set(permissions.values_list('codename', flat=True))
            if missing:
                self.stderr.write(f'{group_name}: не найдены права {sorted(missing)}')
            group.permissions.set(permissions)
            self.stdout.write(self.style.SUCCESS(f'{group_name}: назначено прав — {permissions.count()}'))
