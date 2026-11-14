# AlmaPass

A unified platform for aggregating city events in Almaty and rewarding visits with NFTs.

Stack: Django + PostgreSQL (backend), Angular (frontend), ERC-721 on a test network (NFT).

## Backend: запуск

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # впишите пароль своей PostgreSQL
createdb almapass               # или создайте базу через pgAdmin
python manage.py migrate
python manage.py setup_roles    # группы Moderators и Support для админки
python manage.py createsuperuser
python manage.py runserver
```

Админ-панель: http://127.0.0.1:8000/admin/

Тесты: `python manage.py test`

## Структура

| Приложение | Модели |
|---|---|
| `accounts` | User (роль, кошелёк, язык) |
| `events` | Category, Venue, Organizer, Event, Favorite |
| `rewards` | Visit (check-in), NFTReward |
