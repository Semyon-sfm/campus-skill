"""Наполняет базу демо-данными из дизайн-макета.

Идемпотентна: повторный запуск ничего не дублирует. Даты воркшопов
привязаны к сегодняшнему дню, чтобы каталог и история всегда выглядели
осмысленно, когда бы сид ни запускали.
"""

from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.enrollments.models import Enrollment, Review
from apps.notifications.models import Notification
from apps.workshops.models import Skill, Workshop

DEMO_PASSWORD = "campus123"

SKILLS = [
    ("code", "Программирование", "code-2", "Python", "{ API }", "#eeebfb", "#6c58ba", 1),
    ("design", "Дизайн", "panels-top-left", "Figma", "Aa", "#fae9e3", "#ab6149", 2),
    ("language", "Языки", "messages-square", "English", "Hello!", "#e7f1e6", "#4b7956", 3),
    ("music", "Музыка", "music-2", "Гитара", "A / D / E", "#e5edf7", "#527ba0", 4),
    ("cooking", "Кулинария", "chef-hat", "Готовим вместе", "Pasta", "#faf0d9", "#946f2d", 5),
]

MENTORS = [
    (
        "mikhail@campusskill.ru",
        "Михаил Соколов",
        "ПИ-401",
        "Python-разработчик · 3 года практики",
        "Учусь на программной инженерии и разрабатываю небольшие веб-сервисы. "
        "На воркшопах разбираем рабочие примеры, много практикуемся и обсуждаем ошибки. "
        "Провожу занятия по Python, API и Git.",
        "code",
    ),
    (
        "darya@campusskill.ru",
        "Дарья Смирнова",
        "ДЗ-301",
        "Дизайнер интерфейсов · 2 года практики",
        "Проектирую интерфейсы учебных и студенческих проектов. Помогаю освоить Figma, "
        "компоненты и кликабельные прототипы. Объясняю решения через задачи пользователя "
        "и практику.",
        "design",
    ),
    (
        "alina@campusskill.ru",
        "Алина Лебедева",
        "ЛИ-202",
        "Английский C1 · ведущая разговорного клуба",
        "Организую разговорные встречи небольшими группами. На занятиях тренируем ситуации "
        "из повседневной жизни, учимся задавать вопросы и поддерживать разговор. "
        "Даю спокойную и конкретную обратную связь.",
        "language",
    ),
    (
        "ilya@campusskill.ru",
        "Илья Громов",
        "ИВТ-302",
        "Играю на гитаре 6 лет",
        "Играю в студенческой группе и помогаю новичкам освоить гитару. Начинаем с постановки "
        "рук, простых аккордов и первой песни. Для практики нужна своя акустическая гитара.",
        "music",
    ),
    (
        "olga@campusskill.ru",
        "Ольга Чернова",
        "ПИ-305",
        "Веду студенческий кулинарный клуб",
        "Учу готовить понятные блюда из доступных продуктов. На встречах вместе готовим, "
        "разбираем технику и пробуем результат. В стоимость платных встреч входят ингредиенты.",
        "cooking",
    ),
]

STUDENTS = [
    ("anna@campusskill.ru", "Анна Павлова", "ПИ-301"),
    ("alexey@campusskill.ru", "Алексей Кузнецов", "ПИ-302"),
    ("maria@campusskill.ru", "Мария Волкова", "ДЗ-201"),
    ("dmitry@campusskill.ru", "Дмитрий Орлов", "ИВТ-303"),
    ("ekaterina@campusskill.ru", "Екатерина Белова", "ПИ-301"),
    ("nikita@campusskill.ru", "Никита Морозов", "ИБ-202"),
    ("sofya@campusskill.ru", "Софья Васильева", "ПИ-302"),
    ("artem@campusskill.ru", "Артём Новиков", "ИВТ-304"),
    ("polina@campusskill.ru", "Полина Фёдорова", "ДЗ-202"),
    ("ivan@campusskill.ru", "Иван Мельников", "ПИ-303"),
    ("viktoria@campusskill.ru", "Виктория Егорова", "ПИ-301"),
    ("maxim@campusskill.ru", "Максим Зайцев", "ИБ-201"),
    ("elizaveta@campusskill.ru", "Елизавета Андреева", "ИВТ-303"),
    ("gleb@campusskill.ru", "Глеб Тихонов", "ПИ-304"),
    ("anastasia@campusskill.ru", "Анастасия Сергеева", "ПИ-302"),
    ("roman@campusskill.ru", "Роман Алексеев", "ИБ-203"),
    ("kseniya@campusskill.ru", "Ксения Николаева", "ДЗ-201"),
]

# day_offset — сдвиг от сегодня, чтобы демо не «протухало».
WORKSHOPS = [
    {
        "key": "api",
        "title": "Первый API на FastAPI",
        "skill": "code",
        "tag": "Python",
        "art": "{ API }",
        "mentor": "mikhail@campusskill.ru",
        "description": "Соберём небольшой сервис и проверим запросы в Swagger.",
        "outcome": "У тебя будет работающий API с валидацией данных и понятная схема, "
        "как развивать его дальше.",
        "day_offset": 2,
        "time": time(18, 0),
        "duration": 120,
        "capacity": 16,
        "format": "offline",
        "place": "Корпус C · аудитория 214",
        "amount": 0,
        "level": "basic",
        "requires_approval": False,
        "status": "published",
        "program": [
            "Разберём структуру небольшого API.",
            "Добавим эндпоинты и валидацию данных.",
            "Проверим запросы и обработку ошибок.",
        ],
        "requirements": "Ноутбук, установленный Python 3.12 или новее и базовые знания языка.",
        "fill": 12,
    },
    {
        "key": "figma",
        "title": "Интерфейс с нуля в Figma",
        "skill": "design",
        "tag": "Figma",
        "art": "Aa",
        "mentor": "darya@campusskill.ru",
        "description": "Создадим экран приложения и свяжем его с прототипом.",
        "outcome": "Соберёшь свой первый экран, освоишь компоненты и настроишь переходы "
        "в прототипе.",
        "day_offset": 3,
        "time": time(17, 30),
        "duration": 90,
        "capacity": 12,
        "format": "online",
        "place": "Онлайн · ссылка после подтверждения",
        "amount": 500,
        "level": "start",
        "requires_approval": True,
        "status": "published",
        "program": [
            "Разберём сетку и визуальную иерархию.",
            "Соберём экран из компонентов.",
            "Настроим переходы и проверим прототип.",
        ],
        "requirements": "Ноутбук и аккаунт Figma. Опыт работы не требуется.",
        "fill": 6,
    },
    {
        "key": "git",
        "title": "Git без страха",
        "skill": "code",
        "tag": "Git",
        "art": "git / push",
        "mentor": "mikhail@campusskill.ru",
        "description": "Ветки, коммиты и решение конфликтов на одном проекте.",
        "outcome": "Сможешь работать с ветками и разбирать простой конфликт слияния.",
        "day_offset": 4,
        "time": time(14, 0),
        "duration": 90,
        "capacity": 20,
        "format": "online",
        "place": "Онлайн · учебная видеовстреча",
        "amount": 0,
        "level": "basic",
        "requires_approval": False,
        "status": "published",
        "program": [
            "Повторим базовые команды Git.",
            "Создадим отдельную ветку для задачи.",
            "Разберём и решим конфликт слияния.",
        ],
        "requirements": "Ноутбук с установленным Git. Ссылку на учебный репозиторий дадим "
        "на встрече.",
        "fill": 9,
    },
    {
        "key": "english",
        "title": "Английский: говорим о себе",
        "skill": "language",
        "tag": "English",
        "art": "Hello!",
        "mentor": "alina@campusskill.ru",
        "description": "Тренируем знакомство и разговор об учёбе и интересах.",
        "outcome": "Подготовишь рассказ о себе и потренируешь диалоги, которые пригодятся "
        "на новых встречах.",
        "day_offset": 5,
        "time": time(16, 0),
        "duration": 60,
        "capacity": 10,
        "format": "offline",
        "place": "Корпус B · разговорный клуб",
        "amount": 0,
        "level": "basic",
        "requires_approval": False,
        "status": "published",
        "program": [
            "Подготовим короткий рассказ о себе.",
            "Потренируем диалоги в парах.",
            "Разберём полезные фразы и обратную связь.",
        ],
        "requirements": "Уровень A2–B1. Материалы выдаются на встрече.",
        # Полный зал — чтобы в демо работал лист ожидания.
        "fill": 10,
    },
    {
        "key": "guitar",
        "title": "Три аккорда и первая песня",
        "skill": "music",
        "tag": "Гитара",
        "art": "A / D / E",
        "mentor": "ilya@campusskill.ru",
        "description": "Освоим базовые аккорды и сыграем простой бой.",
        "outcome": "Сыграешь первую песню и получишь упражнения для самостоятельной практики.",
        "day_offset": 6,
        "time": time(18, 0),
        "duration": 90,
        "capacity": 8,
        "format": "offline",
        "place": "Корпус D · музыкальная комната",
        "amount": 0,
        "level": "start",
        "requires_approval": False,
        "status": "published",
        "program": [
            "Настроим гитару и разберём постановку рук.",
            "Выучим три базовых аккорда.",
            "Соединим аккорды в песню.",
        ],
        "requirements": "Своя акустическая гитара. Предварительный опыт не нужен.",
        "fill": 3,
    },
    {
        "key": "pasta",
        "title": "Паста для студенческого ужина",
        "skill": "cooking",
        "tag": "Кулинария",
        "art": "Pasta",
        "mentor": "olga@campusskill.ru",
        "description": "Приготовим пасту и два соуса из доступных продуктов.",
        "outcome": "Узнаешь базовые приёмы и приготовишь ужин вместе с группой.",
        "day_offset": 7,
        "time": time(17, 0),
        "duration": 120,
        "capacity": 12,
        "format": "offline",
        "place": "Студенческий центр · учебная кухня",
        "amount": 350,
        "level": "start",
        "requires_approval": True,
        "status": "published",
        "program": [
            "Разберём ингредиенты и правила работы на кухне.",
            "Приготовим томатный и сливочный соусы.",
            "Соберём блюда и обсудим результат.",
        ],
        "requirements": "Фартук и контейнер для готового блюда. При записи сообщи ментору "
        "об аллергиях.",
        "fill": 8,
    },
    {
        "key": "draft-pytest",
        "title": "Тестируем API с pytest",
        "skill": "code",
        "tag": "Python",
        "art": "assert OK",
        "mentor": "mikhail@campusskill.ru",
        "description": "Напишем первые проверки для небольшого API.",
        "outcome": "Получишь набор тестов и научишься разбирать результаты запуска.",
        "day_offset": 9,
        "time": time(18, 0),
        "duration": 90,
        "capacity": 12,
        "format": "offline",
        "place": "Корпус C · аудитория 216",
        "amount": 0,
        "level": "basic",
        "requires_approval": False,
        "status": "draft",
        "program": [
            "Разберём структуру теста.",
            "Проверим ответы API.",
            "Добавим негативный сценарий.",
        ],
        "requirements": "Ноутбук, базовые знания Python и знакомство с HTTP.",
        "fill": 0,
    },
    {
        "key": "past-figma",
        "title": "Figma: компоненты и стили",
        "skill": "design",
        "tag": "Figma",
        "art": "Aa",
        "mentor": "darya@campusskill.ru",
        "description": "Практика создания компонентов для интерфейса.",
        "outcome": "Набор компонентов для своего макета.",
        "day_offset": -5,
        "time": time(17, 0),
        "duration": 90,
        "capacity": 12,
        "format": "online",
        "place": "Онлайн",
        "amount": 500,
        "level": "basic",
        "requires_approval": True,
        "status": "finished",
        "program": [
            "Создание компонента.",
            "Настройка вариантов.",
            "Стили и их использование.",
        ],
        "requirements": "Ноутбук и аккаунт Figma.",
        "fill": 11,
    },
    {
        "key": "past-python",
        "title": "Python: от скрипта к проекту",
        "skill": "code",
        "tag": "Python",
        "art": "def main",
        "mentor": "mikhail@campusskill.ru",
        "description": "Разобрали структуру учебного Python-проекта.",
        "outcome": "Небольшой проект с понятной структурой.",
        "day_offset": -8,
        "time": time(18, 0),
        "duration": 120,
        "capacity": 16,
        "format": "offline",
        "place": "Корпус C · аудитория 214",
        "amount": 0,
        "level": "basic",
        "requires_approval": False,
        "status": "finished",
        "program": [
            "Структура проекта.",
            "Зависимости и окружение.",
            "Рефакторинг учебного скрипта.",
        ],
        "requirements": "Ноутбук и базовые знания Python.",
        "fill": 13,
    },
    {
        "key": "past-git",
        "title": "Первые шаги с Git",
        "skill": "code",
        "tag": "Git",
        "art": "git init",
        "mentor": "mikhail@campusskill.ru",
        "description": "Разобрали коммиты, историю и удалённый репозиторий.",
        "outcome": "Первый учебный репозиторий.",
        "day_offset": -12,
        "time": time(16, 0),
        "duration": 90,
        "capacity": 16,
        "format": "online",
        "place": "Онлайн",
        "amount": 0,
        "level": "start",
        "requires_approval": False,
        "status": "finished",
        "program": [
            "Первый репозиторий.",
            "Коммиты и история.",
            "Работа с удалённым репозиторием.",
        ],
        "requirements": "Ноутбук и установленный Git.",
        "fill": 12,
    },
]

EXTRA_REVIEWS = [
    (
        "ekaterina@campusskill.ru",
        5,
        5,
        "Понравилось, что большую часть встречи практиковались. После занятия смогла "
        "повторить всё самостоятельно.",
    ),
    (
        "alexey@campusskill.ru",
        4,
        4,
        "Понятные примеры и небольшая группа. На вопросы хватило времени.",
    ),
]


class Command(BaseCommand):
    help = "Загружает демо-данные CampusSkill из дизайн-макета"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Удалить существующие воркшопы, записи и отзывы перед загрузкой",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["flush"]:
            Review.objects.all().delete()
            Enrollment.objects.all().delete()
            Notification.objects.all().delete()
            Workshop.objects.all().delete()
            self.stdout.write("Прежние воркшопы и записи удалены.")

        skills = self._seed_skills()
        users = self._seed_users(skills)
        workshops = self._seed_workshops(skills, users)
        self._seed_enrollments(workshops, users)
        self._seed_reviews(workshops, users)
        self._seed_notifications(workshops, users)

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {len(skills)} навыков, {len(users)} пользователей, "
                f"{len(workshops)} воркшопов. Пароль у всех: {DEMO_PASSWORD}"
            )
        )

    def _seed_skills(self):
        skills = {}
        for slug, label, icon, tag, art, bg, ink, order in SKILLS:
            skills[slug], _ = Skill.objects.update_or_create(
                slug=slug,
                defaults={
                    "label": label,
                    "icon": icon,
                    "tag": tag,
                    "art": art,
                    "color_bg": bg,
                    "color_ink": ink,
                    "order": order,
                },
            )
        return skills

    def _seed_users(self, skills):
        users = {}
        for email, name, group, experience, bio, skill_slug in MENTORS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": name,
                    "study_group": group,
                    "experience": experience,
                    "bio": bio,
                    "is_mentor": True,
                },
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
                user.interests.set([skills[skill_slug]])
            users[email] = user

        for email, name, group in STUDENTS:
            user, created = User.objects.get_or_create(
                email=email, defaults={"full_name": name, "study_group": group}
            )
            if created:
                user.set_password(DEMO_PASSWORD)
                user.save()
            users[email] = user

        anna = users["anna@campusskill.ru"]
        if not anna.bio:
            anna.bio = (
                "Изучаю разработку и дизайн интерфейсов. Люблю практические занятия "
                "в небольших группах."
            )
            anna.save()
        anna.interests.set([skills["code"], skills["design"]])

        if not User.objects.filter(email="admin@campusskill.ru").exists():
            User.objects.create_superuser("admin@campusskill.ru", DEMO_PASSWORD)

        return users

    def _seed_workshops(self, skills, users):
        today = timezone.localdate()
        workshops = {}
        for item in WORKSHOPS:
            workshops[item["key"]], _ = Workshop.objects.update_or_create(
                title=item["title"],
                mentor=users[item["mentor"]],
                defaults={
                    "skill": skills[item["skill"]],
                    "tag": item["tag"],
                    "art": item["art"],
                    "description": item["description"],
                    "outcome": item["outcome"],
                    "program": item["program"],
                    "requirements": item["requirements"],
                    "date": today + timedelta(days=item["day_offset"]),
                    "time": item["time"],
                    "duration": item["duration"],
                    "capacity": item["capacity"],
                    "format": item["format"],
                    "place": item["place"],
                    "amount": item["amount"],
                    "level": item["level"],
                    "requires_approval": item["requires_approval"],
                    "status": item["status"],
                },
            )
        return workshops

    def _seed_enrollments(self, workshops, users):
        """Заполняет группы студентами так, чтобы счётчики мест совпали с макетом."""
        anna = users["anna@campusskill.ru"]
        filler = [users[email] for email, _, _ in STUDENTS[1:]]

        for item in WORKSHOPS:
            workshop = workshops[item["key"]]
            mentor_id = workshop.mentor_id
            pool = [user for user in filler if user.pk != mentor_id]
            for user in pool[: item["fill"]]:
                Enrollment.objects.get_or_create(
                    workshop=workshop,
                    participant=user,
                    defaults={"status": "confirmed"},
                )

        # Личные записи Анны: подтверждённая встреча, история и лист ожидания.
        Enrollment.objects.get_or_create(
            workshop=workshops["git"], participant=anna, defaults={"status": "confirmed"}
        )
        Enrollment.objects.get_or_create(
            workshop=workshops["english"], participant=anna, defaults={"status": "waitlist"}
        )
        for key in ("past-figma", "past-python", "past-git"):
            Enrollment.objects.get_or_create(
                workshop=workshops[key], participant=anna, defaults={"status": "confirmed"}
            )

    def _seed_reviews(self, workshops, users):
        anna = users["anna@campusskill.ru"]
        Review.objects.get_or_create(
            workshop=workshops["past-git"],
            author=anna,
            defaults={
                "workshop_score": 5,
                "mentor_score": 5,
                "text": "Стало понятнее, как устроена история проекта и зачем нужны "
                "небольшие коммиты.",
            },
        )
        # Отзывы других участников, чтобы рейтинги не были пустыми.
        for key in ("past-figma", "past-python", "past-git"):
            workshop = workshops[key]
            for email, w_score, m_score, text in EXTRA_REVIEWS:
                author = users[email]
                if not Enrollment.objects.filter(
                    workshop=workshop, participant=author
                ).exists():
                    continue
                Review.objects.get_or_create(
                    workshop=workshop,
                    author=author,
                    defaults={
                        "workshop_score": w_score,
                        "mentor_score": m_score,
                        "text": text,
                    },
                )

    def _seed_notifications(self, workshops, users):
        anna = users["anna@campusskill.ru"]
        if Notification.objects.filter(recipient=anna).exists():
            return
        git = workshops["git"]
        Notification.objects.create(
            recipient=anna,
            title=f"Ближайшая встреча — «{git.title}»",
            body=f"{git.date.strftime('%d.%m')} в {git.time.strftime('%H:%M')} · "
            f"{'Онлайн' if git.format == 'online' else 'Офлайн'}. Участие подтверждено.",
            workshop=git,
        )
        Notification.objects.create(
            recipient=anna,
            title="Поделись впечатлениями о Figma",
            body="Воркшоп завершён. Твой отзыв поможет другим участникам.",
            workshop=workshops["past-figma"],
        )
        mentor = users["mikhail@campusskill.ru"]
        api = workshops["api"]
        Notification.objects.create(
            recipient=mentor,
            title=f"Скоро воркшоп «{api.title}»",
            body=f"{api.date.strftime('%d.%m')} в {api.time.strftime('%H:%M')} · "
            f"{api.registered} участников, ещё {api.free_seats} мест свободно.",
            workshop=api,
        )
