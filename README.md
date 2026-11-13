# CampusSkill

Платформа обмена навыками и воркшопов внутри кампуса. Студенты проводят
воркшопы друг для друга: ментор создаёт встречу, участники записываются,
после занятия оставляют отзывы.


## Архитектура

MPA с элементами SPA — раздельные бэкенд и фронтенд в одном Django-проекте:

| Слой | Чем занимается |
|---|---|
| Django views + templates | отдают **страницы**: структуру, навигацию, SEO-текст, формы |
| Django REST Framework (`/api/`) | отдаёт и принимает **данные**: списки, фильтры, CRUD |
| Ванильный JS (`static/js/`) | ходит в API через `fetch`, перерисовывает списки на месте |

Правило, по которому разделены обязанности:

* **Переход на другую страницу** — обычный HTTP-запрос, Django рендерит шаблон.
* **Любая работа с данными** — только REST API: загрузка и обновление списков,
  фильтрация, поиск, пагинация, создание, изменение, удаление.

Поэтому карточки воркшопов, списки записей, участников, менторов и уведомлений
приходят из API и рендерятся из `<template>`-блоков, лежащих в Django-шаблонах —
разметка не дублируется между сервером и клиентом.

Никаких React/Vue и сборщиков нет: только HTML, CSS и JS без зависимостей.

## Стек

* Python 3.12, Django 5.1, Django REST Framework
* PostgreSQL 16
* Docker + docker compose
* Фронтенд: ванильный JS, CSS из макета (без Bootstrap — у макета своя
  дизайн-система, Bootstrap бы с ней конфликтовал)

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

Приложение: <http://localhost:8000>. При старте контейнер сам применяет
миграции, загружает демо-данные и собирает статику.

### Демо-доступы

Пароль у всех пользователей — `campus123`.

| Роль | Email |
|---|---|
| Участник | `anna@campusskill.ru` |
| Ментор | `mikhail@campusskill.ru` |
| Админ | `admin@campusskill.ru` |

Один пользователь может быть и участником, и ментором: кабинет ментора
открывается кнопкой «Стать ментором» (флаг `is_mentor`).

### Запуск без Docker

Если переменная `POSTGRES_HOST` не задана, проект работает на SQLite:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

## Структура

```
config/           настройки, роутинг страниц и api_urls.py
apps/
  accounts/       пользователь (email-логин), профиль, интересы, менторы
  workshops/      навыки, воркшопы, каталог, кабинет ментора
  enrollments/    записи, лист ожидания, отзывы
  notifications/  уведомления, настройки, напоминания
templates/
  base.html       каркас: шапка, навигация, флеш-сообщения
  pages/          15 экранов из макета
  partials/       шаблон карточки воркшопа (используется из JS)
static/
  css/campusskill.css   дизайн-система, перенесена из макета 1:1
  css/app.css           добавления: reset, ссылки-кнопки, экраны входа
  js/api.js             обёртка над fetch: CSRF, разбор ошибок DRF
  js/*.js               по модулю на экран
```

`campusskill.css` намеренно не правится — он перенесён из макета без
изменений, чтобы вёрстку можно было сверять с оригиналом. Всё, что добавилось
при переносе прототипа в настоящее приложение, лежит в `app.css`.

## REST API

Все ответы — JSON, авторизация через сессию Django, запись требует CSRF-токен
(его подставляет `api.js`).

### Воркшопы

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/workshops/` | каталог; фильтры `skill, q, format, date, price, level, mentor, limit, offset` |
| POST | `/api/workshops/` | создать (`intent=draft\|publish`) |
| GET | `/api/workshops/<id>/` | один воркшоп |
| PATCH | `/api/workshops/<id>/` | изменить |
| DELETE | `/api/workshops/<id>/` | удалить (запрещено, если есть участники) |
| GET | `/api/workshops/mine/` | воркшопы текущего ментора |
| GET | `/api/workshops/<id>/related/` | похожие по навыку |
| POST | `/api/workshops/<id>/publish/` | опубликовать черновик |
| POST | `/api/workshops/<id>/enroll/` | записаться |
| GET | `/api/workshops/<id>/participants/` | участники, фильтр `q` |

### Записи, отзывы, профиль

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/enrollments/?tab=upcoming\|history\|waitlist` | мои записи |
| DELETE | `/api/enrollments/<id>/` | отменить запись |
| PATCH | `/api/enrollment-status/<id>/` | ментор меняет статус заявки |
| GET/POST | `/api/reviews/` | отзывы |
| GET | `/api/skills/`, `/api/mentors/` | справочники |
| GET/PATCH | `/api/profile/` | профиль |
| GET/PUT | `/api/profile/interests/` | интересующие навыки |
| GET/PATCH | `/api/profile/settings/` | настройки уведомлений |
| POST | `/api/profile/become-mentor/` | открыть кабинет ментора |
| GET | `/api/profile/skill-progress/` | прогресс по навыкам |
| GET | `/api/notifications/` | лента уведомлений |
| POST | `/api/notifications/read/` | отметить прочитанными |

## Бизнес-логика записи

Статус записи выбирается автоматически:

| Условие | Статус |
|---|---|
| мест нет | `waitlist` — лист ожидания |
| ментор подтверждает вручную | `pending` — ждёт подтверждения |
| иначе | `confirmed` — участие подтверждено |

При отмене подтверждённой записи освободившееся место автоматически
получает первый участник из листа ожидания — он переходит в `confirmed`
(или в `pending`, если ментор подтверждает заявки вручную) и получает
уведомление.

«Прогресс по навыкам» считается как число посещённых завершённых воркшопов
по каждому навыку.

## Напоминания

Напоминания о встречах рассылает management-команда (без Celery):

```bash
python manage.py send_reminders            # разослать
python manage.py send_reminders --dry-run  # посмотреть, кому ушло бы
```

Учитывает личную настройку «за сколько напомнить» (24 / 2 / 1 час) и не
дублирует отправленное. Для регулярного запуска — cron:

```cron
*/15 * * * * cd /app && python manage.py send_reminders
```

## Команды

```bash
python manage.py seed_demo            # демо-данные (идемпотентно)
python manage.py seed_demo --flush    # пересоздать воркшопы и записи
python manage.py send_reminders       # напоминания
python manage.py createsuperuser      # свой админ
```

Админка — `/admin/`.

## Иконки

Макет использовал lucide с CDN. В проекте лежит сгенерированное подмножество
только из используемых иконок (`static/js/icons.js`, 7 КБ вместо 600 КБ) со
своим рендерером — внешних запросов нет.
