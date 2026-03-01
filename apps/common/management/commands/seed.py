from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
import math
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import Profile
from apps.discussions.models import Comment, Post, PostVote, Subject
from apps.marketplace.models import Listing, ListingImage
from apps.moderation.models import Report

SEED_MARKER = "[seed-demo]"
SUBJECTS = [
    {"name": "Български език", "slug": "bulgarski", "theme_color": "#FB923C", "tile_image": "img/bulgarski.svg"},
    {"name": "Литература", "slug": "literatura", "theme_color": "#BEEA00", "tile_image": "img/literatura.svg"},
    {"name": "Биология", "slug": "biologiq", "theme_color": "#10B981", "tile_image": "img/biologiq.svg"},
    {"name": "Информационни технологии", "slug": "informacionni-tehnologii", "theme_color": "#2563EB", "tile_image": "img/informacionni-tehnologii.svg"},
    {"name": "История", "slug": "istoriq", "theme_color": "#EF4444", "tile_image": "img/istoriq.svg"},
    {"name": "Математика", "slug": "matematika", "theme_color": "#0EA5E9", "tile_image": "img/matematika.svg"},
    {"name": "Физика", "slug": "fizika", "theme_color": "#FF725E", "tile_image": "img/fizika.svg"},
    {"name": "Химия", "slug": "himiq", "theme_color": "#7C3AED", "tile_image": "img/himiq.svg"},
    {"name": "Други", "slug": "drugo", "theme_color": "#64748B", "tile_image": "img/drugo.svg"},
]

DEMO_USERS = [
    ("admin", "admin12345", True, True, "Админ"),
    ("demo", "demo12345", False, False, "Демо"),
    ("teacher_ani", "demo12345", False, False, "Ани Петрова"),
    ("teacher_mario", "demo12345", False, False, "Марио Тодоров"),
    ("teacher_elena", "demo12345", False, False, "Елена Стоянова"),
    ("student_iva", "demo12345", False, False, "Ива Георгиева"),
    ("student_niki", "demo12345", False, False, "Никола Димитров"),
    ("student_maria", "demo12345", False, False, "Мария Иванова"),
    ("student_dani", "demo12345", False, False, "Даниел Колев"),
]

DISCUSSION_SCENARIOS = {
    "matematika": [
        {
            "author": "student_iva",
            "title": f"Квадратни неравенства: как избирате правилния метод? {SEED_MARKER}",
            "body": f"{SEED_MARKER} За контролното имаме задачи, в които едни ги решаваме с парабола, а други с интервали. Кога е по-надеждно да ползвам всеки метод, за да не губя време?",
            "grade": 10,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Ако изразът е лесен за разлагане, методът с интервали е най-бърз. Ако има параметър или трудни корени, скицата на парабола дава по-сигурна проверка."},
                {"author": "student_dani", "body": f"{SEED_MARKER} Аз първо гледам дали мога да намеря корените за под 1 минута. Ако не, минавам на парабола и не се чудя излишно."},
            ],
        },
        {
            "author": "student_niki",
            "title": f"Задачи за смеси: постоянно бъркам уравнението {SEED_MARKER}",
            "body": f"{SEED_MARKER} При задачи с проценти (разтвор + вода) често обърквам кое е начално и кое крайно количество. Имате ли шаблон, който ползвате на чернова?",
            "grade": 8,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Направи таблица „количество / концентрация / чисто вещество“ за начало и край. Уравнението идва директно от колоната за чистото вещество."},
                {"author": "student_maria", "body": f"{SEED_MARKER} На мен помага да си отбележа крайния процент в рамка, за да не вкарам стария процент във финалното уравнение."},
            ],
        },
    ],
    "bulgarski": [
        {
            "author": "student_maria",
            "title": f"Преразказ от името на герой: как пазите стил? {SEED_MARKER}",
            "body": f"{SEED_MARKER} Получавам забележка, че преразказът ми звучи „като преразказвач\", а не като герой. Как го правите по-личен, без да измисляте нов сюжет?",
            "grade": 7,
            "comments": [
                {"author": "teacher_elena", "body": f"{SEED_MARKER} Избери 2-3 характерни думи и нагласа на героя, които повтаряш последователно. Така гласът остава разпознаваем, а сюжетът не се променя."},
                {"author": "demo", "body": f"{SEED_MARKER} Провери и глаголните времена — ако скачат, текстът веднага губи убедителност."},
            ],
        }
    ],
    "literatura": [
        {
            "author": "student_iva",
            "title": f"План за интерпретативно съчинение за 90 минути {SEED_MARKER}",
            "body": f"{SEED_MARKER} На пробната матура успях да напиша много, но не ми остана време за редакция. Как си разпределяте минутите между план, писане и проверка?",
            "grade": 12,
            "comments": [
                {"author": "teacher_elena", "body": f"{SEED_MARKER} Пробвай 15 мин план, 60 мин писане, 15 мин редакция. Планирай поне 3 опорни аргумента още в началото, за да не импровизираш в средата."},
                {"author": "student_niki", "body": f"{SEED_MARKER} Аз си оставям последните 10 мин само за пунктуация и повторения на думи — качи ми оценката с цяла единица."},
            ],
        }
    ],
    "biologiq": [
        {
            "author": "student_dani",
            "title": f"Генетични задачи: как четете родословно дърво без грешки? {SEED_MARKER}",
            "body": f"{SEED_MARKER} На тестовете по биология губя точки, защото прибързвам и приемам, че белегът е доминантен. Как проверявате систематично преди да решите задачата?",
            "grade": 9,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Започни от двойка родители с засегнато дете или обратното — там най-бързо се вижда дали моделът е доминантен/рецесивен. После провери и пола за X-свързано унаследяване."},
                {"author": "student_maria", "body": f"{SEED_MARKER} Ползвам цветни символи за известен и предполагаем генотип. Така по-лесно виждам къде правя допускане."},
            ],
        }
    ],
    "himiq": [
        {
            "author": "student_niki",
            "title": f"Редокс уравнения: йонно-електронен метод стъпка по стъпка {SEED_MARKER}",
            "body": f"{SEED_MARKER} Знам теорията, но при реални задачи пропускам коефициенти и накрая не излиза зарядът. Има ли кратък чеклист за проверка преди финален отговор?",
            "grade": 11,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} След балансиране винаги провери 3 неща: атоми, заряд, среда (кисела/основна). Ако едното не излиза, върни се до полуреакциите, не поправяй на око."},
                {"author": "student_iva", "body": f"{SEED_MARKER} На мен ми помогна да пиша електроните с различен цвят на черновата. Така веднага виждам дали се съкращават коректно."},
            ],
        }
    ],
    "fizika": [
        {
            "author": "student_maria",
            "title": f"Задачи за електрични вериги: еквивалентно съпротивление {SEED_MARKER}",
            "body": f"{SEED_MARKER} В смесени схеми с последователно и паралелно свързване се обърквам от къде да започна. Има ли стратегия, която да работи и при по-сложни варианти?",
            "grade": 9,
            "comments": [
                {"author": "teacher_elena", "body": f"{SEED_MARKER} Намери най-вътрешната проста група резистори и я замени стъпка по стъпка. След всяка замяна прерисувай схемата, иначе лесно се губят връзките."},
                {"author": "demo", "body": f"{SEED_MARKER} Ако ти остава време, провери с граничен случай — дали еквивалентното съпротивление е в логичен диапазон спрямо отделните резистори."},
            ],
        }
    ],
    "istoriq": [
        {
            "author": "student_dani",
            "title": f"История: как учите причини/последици без сухо зубрене? {SEED_MARKER}",
            "body": f"{SEED_MARKER} За следващото изпитване трябва да свързваме събития, а аз помня само отделни дати. Как си правите преговор, за да можете да аргументирате отговор?",
            "grade": 10,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Работи с карта „причина → събитие → последица“ за всяка тема и добавяй по един конкретен исторически пример. Така отговорът става аналитичен, не само фактологичен."},
                {"author": "student_iva", "body": f"{SEED_MARKER} Аз записвам и „какво се променя след това“ в едно изречение. Това много помага за устен изпит."},
            ],
        }
    ],
    "informacionni-tehnologii": [
        {
            "author": "student_iva",
            "title": f"Python за училищен проект: кога да ползвам класове? {SEED_MARKER}",
            "body": f"{SEED_MARKER} Проектът ми е система за библиотека. Засега е само с функции и речници, но кодът става труден за поддръжка. На какъв етап има смисъл да мина към класове?",
            "grade": 11,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Щом имаш обекти с състояние (книга, потребител, заем), класовете ще ти изчистят структурата. Започни с 2-3 основни класа, не преработвай всичко наведнъж."},
                {"author": "student_niki", "body": f"{SEED_MARKER} Добави и отделен модул за четене/запис на данни, за да не смесваш логика и файлове в едни и същи функции."},
            ],
        }
    ],
    "drugo": [
        {
            "author": "demo",
            "title": f"Реален учебен график при тренировки 4 пъти седмично {SEED_MARKER}",
            "body": f"{SEED_MARKER} След училище съм на тренировки и вечер трудно започвам учене. Търся работещ режим за домашни и подготовка за контролни без да прегарям.",
            "grade": 10,
            "comments": [
                {"author": "teacher_elena", "body": f"{SEED_MARKER} Планирай 2 кратки блока преди тренировка и 1 лек блок след нея (само преговор/четене). Тежките задачи ги мести в дни без спорт."},
                {"author": "student_maria", "body": f"{SEED_MARKER} На мен ми помогна фиксиран „праг за минимум“ — дори в натоварен ден правя поне 25 мин математика."},
            ],
        }
    ],
}

LISTING_SCENARIOS = {
    "matematika": {
        "owner": "teacher_ani",
        "price": Decimal("44.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} Индивидуална подготовка по математика за 7.–12. клас и НВО/ДЗИ. Започваме с входящ тест, правим месечен план и всяка седмица следим прогреса по конкретни критерии.",
    },
    "bulgarski": {
        "owner": "teacher_elena",
        "price": Decimal("37.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Български език за ученици с фокус върху граматика, преразказ и аргументативен текст. След всеки урок изпращам кратка обратна връзка с типични грешки и точни упражнения за корекция.",
    },
    "literatura": {
        "owner": "teacher_elena",
        "price": Decimal("39.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} Литература за 11.–12. клас: анализ на произведения, писане на интерпретативно съчинение и подготовка за матура. Работим с примерни теми и персонални рубрики за оценяване.",
    },
    "biologiq": {
        "owner": "teacher_ani",
        "price": Decimal("41.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Биология за училищна и кандидатстудентска подготовка (МУ/ФМИ профили). Обяснявам темите със схеми и клинични примери, а след всеки модул правим кратък тест с разбор на грешките.",
    },
    "himiq": {
        "owner": "teacher_mario",
        "price": Decimal("42.00"),
        "mode": Listing.LessonMode.IN_PERSON,
        "description": f"{SEED_MARKER} Химия за 8.–12. клас с акцент върху стехиометрия, разтвори и редокс процеси. Получаваш листове със задачи по нива и ясна стратегия как да решаваш под време.",
    },
    "fizika": {
        "owner": "teacher_mario",
        "price": Decimal("40.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} Уроци по физика (8.–12. клас): механика, електричество и термодинамика. Всеки урок включва теория + задачи от изпити + домашно с проверка на подхода, не само на крайния резултат.",
    },
    "istoriq": {
        "owner": "demo",
        "price": Decimal("34.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} История и цивилизации за текуща подготовка и НВО. Помагам с изграждане на причинно-следствени връзки, структуриране на писмени отговори и бърз преговор преди изпитване.",
    },
    "informacionni-tehnologii": {
        "owner": "teacher_ani",
        "price": Decimal("46.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} ИТ и Python за ученици: от базови концепции до учебни проекти и подготовка за състезания. Работим с Git, структура на код и добри практики за представяне на проект пред комисия.",
    },
    "drugo": {
        "owner": "demo",
        "price": Decimal("33.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Учебен коучинг за ученици: управление на време, седмично планиране и техника за учене преди контролни. Подходящо за ученици с натоварен график и много извънкласни дейности.",
    },
}

REPORT_REASONS = [
    Report.REASON_SPAM,
    Report.REASON_ABUSE,
    Report.REASON_OFF_TOPIC,
    Report.REASON_OTHER,
]


@dataclass
class SeedContext:
    users: dict[str, object]
    subjects: dict[str, Subject]
    image_paths: list[Path]


class Command(BaseCommand):
    help = "Seed demo data for local development"

    def add_arguments(self, parser):
        parser.add_argument("--users", action="store_true")
        parser.add_argument("--subjects", action="store_true")
        parser.add_argument("--discussions", action="store_true")
        parser.add_argument("--marketplace", action="store_true")
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--force", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("Seed is allowed only in DEBUG mode. Use --force to override.")

        sections = {
            "users": options["users"],
            "subjects": options["subjects"],
            "discussions": options["discussions"],
            "marketplace": options["marketplace"],
        }
        if not any(sections.values()):
            sections = {key: True for key in sections}

        stats = Counter()

        if options["wipe"]:
            self._wipe_seeded(stats)

        users = self._seed_users(stats, force_password_reset=options["force"]) if sections["users"] else self._load_users()
        subjects = self._seed_subjects(stats) if sections["subjects"] else self._load_subjects()
        image_paths = self._seed_image_paths()

        context = SeedContext(users=users, subjects=subjects, image_paths=image_paths)

        if sections["discussions"]:
            self._seed_discussions(context, stats)

        if sections["marketplace"]:
            self._seed_marketplace(context, stats)

        self._print_summary(stats)

    def _seed_subjects(self, stats: Counter) -> dict[str, Subject]:
        seeded = {}
        for index, subject_data in enumerate(SUBJECTS, start=1):
            subject, created = Subject.objects.get_or_create(
                name=subject_data["name"],
                defaults={"slug": subject_data["slug"]},
            )
            changed_fields = []
            if subject.slug != subject_data["slug"]:
                subject.slug = subject_data["slug"]
                changed_fields.append("slug")
            if subject.theme_color != subject_data["theme_color"]:
                subject.theme_color = subject_data["theme_color"]
                changed_fields.append("theme_color")
            if subject.tile_image != subject_data["tile_image"]:
                subject.tile_image = subject_data["tile_image"]
                changed_fields.append("tile_image")
            if subject.sort_order != index:
                subject.sort_order = index
                changed_fields.append("sort_order")
            if changed_fields:
                subject.save(update_fields=changed_fields)
            stats["subjects_created" if created else "subjects_updated"] += 1
            seeded[subject.slug] = subject
        return seeded

    def _seed_users(self, stats: Counter, force_password_reset: bool) -> dict[str, object]:
        user_model = get_user_model()
        users = {}

        for username, password, is_staff, is_superuser, display_name in DEMO_USERS:
            user, created = user_model.objects.get_or_create(
                username=username,
                defaults={"is_staff": is_staff, "is_superuser": is_superuser},
            )

            update_fields = []
            if user.is_staff != is_staff:
                user.is_staff = is_staff
                update_fields.append("is_staff")
            if user.is_superuser != is_superuser:
                user.is_superuser = is_superuser
                update_fields.append("is_superuser")

            should_set_password = created or force_password_reset
            if should_set_password:
                user.set_password(password)
                update_fields.append("password")

            if update_fields:
                user.save(update_fields=update_fields)

            Profile.objects.get_or_create(
                user=user,
                defaults={"display_name": display_name},
            )
            users[username] = user
            stats["users_created" if created else "users_existing"] += 1
            if not should_set_password and not created:
                stats["passwords_kept"] += 1

        return users

    def _load_users(self) -> dict[str, object]:
        user_model = get_user_model()
        return {
            user.username: user
            for user in user_model.objects.filter(
                username__in=[username for username, *_ in DEMO_USERS]
            )
        }

    def _load_subjects(self) -> dict[str, Subject]:
        slugs = [subject_data["slug"] for subject_data in SUBJECTS]
        return {subject.slug: subject for subject in Subject.objects.filter(slug__in=slugs)}

    def _seed_discussions(self, context: SeedContext, stats: Counter) -> None:
        if not context.subjects:
            return

        voters = [user for key, user in context.users.items() if key not in {"admin"}]
        total_posts = self._count_seedable_discussion_posts(context)
        posts_with_images = self._discussion_image_post_indices(total_posts)
        global_post_index = 0
        discussion_image_counter = 0

        for subject_index, subject in enumerate(context.subjects.values(), start=1):
            scenarios = DISCUSSION_SCENARIOS.get(subject.slug)
            if not scenarios:
                continue

            for post_index, scenario in enumerate(scenarios, start=1):
                author = context.users.get(scenario.get("author", ""))
                if author is None:
                    continue
                global_post_index += 1

                title = scenario["title"]
                body = scenario["body"]
                post, created = Post.objects.get_or_create(
                    subject=subject,
                    author=author,
                    title=title,
                    defaults={"body": body, "grade": scenario.get("grade", min(12, 5 + post_index))},
                )
                stats["posts_created" if created else "posts_existing"] += 1

                updates = []
                if post.body != body:
                    post.body = body
                    updates.append("body")
                desired_grade = scenario.get("grade", post.grade)
                if post.grade != desired_grade:
                    post.grade = desired_grade
                    updates.append("grade")
                if updates:
                    post.save(update_fields=updates)

                if global_post_index in posts_with_images:
                    image_path = context.image_paths[(global_post_index + discussion_image_counter) % len(context.image_paths)]
                    self._attach_image_if_needed(
                        post,
                        image_path,
                        f"post-{subject.slug}-{post_index}.png",
                        stats,
                        "post_images",
                    )
                    discussion_image_counter += 1

                for comment in scenario.get("comments", []):
                    commenter = context.users.get(comment.get("author", ""))
                    if commenter is None:
                        continue
                    _, comment_created = Comment.objects.get_or_create(
                        post=post,
                        author=commenter,
                        body=comment["body"],
                    )
                    stats["comments_created" if comment_created else "comments_existing"] += 1

                self._seed_post_votes(post, voters, stats)
                self._seed_report(post, context.users.get("admin"), "post", stats)
                first_comment = post.comments.order_by("id").first()
                if first_comment is not None:
                    self._seed_report(first_comment, context.users.get("admin"), "comment", stats)

    def _seed_post_votes(self, post: Post, voters: list, stats: Counter) -> None:
        vote_pattern = [1, 1, -1, 1]
        for index, voter in enumerate(voters[: len(vote_pattern)]):
            if voter is None or voter == post.author:
                continue
            value = vote_pattern[index]
            vote, created = PostVote.objects.update_or_create(
                voter=voter,
                post=post,
                defaults={"value": value},
            )
            stats["post_votes_created" if created else "post_votes_existing"] += 1

        score = max(0, sum(post.votes.values_list("value", flat=True)))
        if post.score != score:
            post.score = score
            post.save(update_fields=["score"])

    def _seed_marketplace(self, context: SeedContext, stats: Counter) -> None:
        if not context.subjects:
            return

        owners = [
            context.users.get("demo"),
            context.users.get("teacher_ani"),
            context.users.get("teacher_mario"),
        ]
        owners = [owner for owner in owners if owner is not None]
        if not owners:
            return

        for idx, subject in enumerate(context.subjects.values(), start=1):
            scenario = LISTING_SCENARIOS.get(subject.slug)
            if scenario:
                owner = context.users.get(scenario.get("owner", ""))
            else:
                owner = owners[idx % len(owners)]

            if owner is None:
                continue

            lesson_mode = scenario["mode"] if scenario else Listing.LessonMode.ONLINE_AND_IN_PERSON
            description = scenario["description"] if scenario else (
                f"{SEED_MARKER} Индивидуални уроци по {subject.name}. "
                "Работя с план за всяка седмица, домашни и обратна връзка след всеки урок. "
                "Локация: София / онлайн според режима на обучение."
            )
            price_per_hour = scenario["price"] if scenario else Decimal(30 + idx)

            listing, created = Listing.objects.get_or_create(
                subject=subject,
                owner=owner,
                lesson_mode=lesson_mode,
                defaults={
                    "price_per_hour": price_per_hour,
                    "description": description,
                    "contact_name": owner.username,
                    "contact_phone": "+359888123456",
                    "contact_email": f"{owner.username}@example.dev",
                },
            )
            stats["listings_created" if created else "listings_existing"] += 1

            update_fields = []
            if listing.description != description:
                listing.description = description
                update_fields.append("description")
            if listing.price_per_hour != price_per_hour:
                listing.price_per_hour = price_per_hour
                update_fields.append("price_per_hour")
            if update_fields:
                listing.save(update_fields=update_fields)

            desired_gallery_count = 2 + ((idx - 1) % 3)
            listing_cover_path, gallery_paths = self._listing_image_selection(
                context.image_paths,
                idx,
                desired_gallery_count,
            )
            self._attach_image_if_needed(
                listing,
                listing_cover_path,
                f"listing-{subject.slug}.png",
                stats,
                "listing_cover_images",
            )

            for position in range(desired_gallery_count):
                gallery_image, image_created = ListingImage.objects.get_or_create(
                    listing=listing,
                    position=position,
                )
                if image_created or not gallery_image.image:
                    with gallery_paths[position].open("rb") as image_file:
                        gallery_image.image.save(
                            f"listing-{subject.slug}-{position}.png",
                            File(image_file),
                            save=True,
                        )
                    stats["listing_gallery_images_created"] += 1
                else:
                    stats["listing_gallery_images_existing"] += 1

            self._seed_report(listing, context.users.get("admin"), "listing", stats)

    def _seed_report(self, target, reporter, target_key: str, stats: Counter) -> None:
        if reporter is None:
            return
        content_type = ContentType.objects.get_for_model(target.__class__)
        reason = REPORT_REASONS[target.pk % len(REPORT_REASONS)]
        message = f"{SEED_MARKER} Автоматично създаден сигнал за демонстрация ({target_key})."
        report, created = Report.objects.get_or_create(
            reporter=reporter,
            content_type=content_type,
            object_id=target.pk,
            defaults={"reason": reason, "message": message},
        )
        if not created:
            updates = []
            if report.reason != reason:
                report.reason = reason
                updates.append("reason")
            if report.message != message:
                report.message = message
                updates.append("message")
            if updates:
                report.save(update_fields=updates)
        stats["reports_created" if created else "reports_existing"] += 1

    def _attach_image_if_needed(self, instance, image_path: Path, filename: str, stats: Counter, key: str) -> None:
        image_field = instance.image
        if image_field:
            stats[f"{key}_existing"] += 1
            return
        with image_path.open("rb") as image_file:
            image_field.save(filename, File(image_file), save=True)
        stats[f"{key}_created"] += 1

    def _count_seedable_discussion_posts(self, context: SeedContext) -> int:
        total_posts = 0
        for subject in context.subjects.values():
            scenarios = DISCUSSION_SCENARIOS.get(subject.slug, [])
            total_posts += sum(1 for scenario in scenarios if context.users.get(scenario.get("author", "")) is not None)
        return total_posts

    def _discussion_image_post_indices(self, total_posts: int) -> set[int]:
        if total_posts <= 0:
            return set()
        if total_posts == 1:
            return {1}
        if total_posts == 2:
            return {1, 2}

        middle_post = math.ceil(total_posts / 2)
        return {2, middle_post, total_posts}

    def _listing_image_selection(self, image_paths: list[Path], listing_index: int, gallery_count: int) -> tuple[Path, list[Path]]:
        image_count = len(image_paths)
        start_idx = ((listing_index - 1) * 3) % image_count
        cover_idx = (start_idx - 1) % image_count
        gallery_paths = [image_paths[(start_idx + offset) % image_count] for offset in range(gallery_count)]
        return image_paths[cover_idx], gallery_paths

    def _seed_image_paths(self) -> list[Path]:
        seed_dir = Path(settings.BASE_DIR) / "static" / "seed_images"
        image_paths = sorted(path for path in seed_dir.glob("*") if path.is_file())
        if image_paths:
            return image_paths

        fallback_image = Path(settings.BASE_DIR) / "static" / "img" / "logo-mark.png"
        if fallback_image.exists():
            return [fallback_image]

        raise CommandError("No seed images found. Add files in static/seed_images or ensure static/img/logo-mark.png exists.")

    def _wipe_seeded(self, stats: Counter) -> None:
        listing_qs = Listing.objects.filter(description__contains=SEED_MARKER)
        post_qs = Post.objects.filter(title__contains=SEED_MARKER)
        comment_qs = Comment.objects.filter(body__contains=SEED_MARKER)
        report_qs = Report.objects.filter(message__contains=SEED_MARKER)

        stats["wipe_reports_deleted"], _ = report_qs.delete()
        stats["wipe_comments_deleted"], _ = comment_qs.delete()
        stats["wipe_posts_deleted"], _ = post_qs.delete()
        stats["wipe_listings_deleted"], _ = listing_qs.delete()

    def _print_summary(self, stats: Counter) -> None:
        self.stdout.write(self.style.SUCCESS("Seed summary:"))
        for key in sorted(stats.keys()):
            self.stdout.write(f"- {key}: {stats[key]}")

        self.stdout.write("Credentials (dev):")
        self.stdout.write("- admin / admin12345")
        self.stdout.write("- demo / demo12345")
