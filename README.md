# Учебный проект devman "Сервис FoodPlan" 

## Описание
Телеграм-бот позволяет получить список блюд для приготовления по типу меню и 
аллергиям.

### Имя бота в Telegram

[foodplabot](http://t.me/Team8_foodplan_bot)

### Команды бота в Telegram
Запуск бота
```
/start
```

## Установка

- Скачать код
```
git clone git@github.com:redbor24/FoodPlan.git
```
- Создать виртуальное окружение

*nix или MacOS:
```bash
python3 -m venv venv
source venv/bin/activate
```
Windows:
```bash
python -m venv venv
source venv/bin/activate
```

- Установить зависимости
```bash
pip install -r requirements.txt
```
- Создать файл .env и вставить в него следующие строки:
```bash
DJANGO_DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
TELEGRAM_TOKEN=<Токен вашего бота>
```

Запустите миграцию для настройки базы данных SQLite:

*nix или MacOS:
```bash
python3 manage.py migrate
```
Windows:
```bash
python manage.py migrate
```
- Создайте суперпользователя, чтобы получить доступ к панели администратора:

*nix или MacOS:
```bash
python3 manage.py createsuperuser
```
Windows:
```bash
python manage.py createsuperuser
```

## Запуск бота
*nix или MacOS:
```bash
python3 run_pooling.py
```
Windows:
```bash
python run_pooling.py 
```
## Запуск панели администратора:
*nix или MacOS:
```bash
python3 manage.py runserver
```
Windows:
```bash
python manage.py runserver
```

Затем перейдите по [ссылке](http://127.0.0.1:8000/tgadmin/).
