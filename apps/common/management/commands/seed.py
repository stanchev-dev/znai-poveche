from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
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
    ("student_iva", "demo12345", False, False, "Ива Георгиева"),
    ("student_niki", "demo12345", False, False, "Никола Димитров"),
]

DISCUSSION_SCENARIOS = {
    "matematika": [
        {
            "author": "student_iva",
            "title": f"Квадратни уравнения преди контролно {SEED_MARKER}",
            "body": f"{SEED_MARKER} На задачите с параметър се обърквам кога дискриминантата трябва да е > 0 и кога >= 0. Имате ли лесен алгоритъм как подхождате?",
            "grade": 10,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Направи си кратка проверка в 3 стъпки: област на допустимост, знак на дискриминанта, и после проверка с примерни стойности."},
                {"author": "student_niki", "body": f"{SEED_MARKER} На мен много ми помогна да си пиша отделно случаите D=0 и D>0 с по една решена задача."},
                {"author": "demo", "body": f"{SEED_MARKER} Ако искаш, качи конкретна задача и ще я разбием на стъпки."},
            ],
        },
        {
            "author": "student_niki",
            "title": f"Как тренирате текстови задачи за движение? {SEED_MARKER}",
            "body": f"{SEED_MARKER} В тестове губя точки на задачи с влакове/срещи, защото бъркам величините. Някой ползва ли шаблон на таблица?",
            "grade": 8,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Да — време, скорост, път в три колони. Попълваш две, третата се намира веднага и намалява грешките."},
                {"author": "student_iva", "body": f"{SEED_MARKER} Аз добавям и единици до всяко число, иначе лесно смесвам км/ч с м/с."},
            ],
        },
    ],
    "bulgarski": [
        {
            "author": "student_niki",
            "title": f"Аргументативен текст: как да звучи по-убедително? {SEED_MARKER}",
            "body": f"{SEED_MARKER} Учителката казва, че тезата ми е добра, но аргументите са общи. Как конкретизирате примери, без да става прекалено дълго?",
            "grade": 9,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Ползвай схема твърдение → доказателство → извод. Един конкретен пример тежи повече от три общи изречения."},
                {"author": "demo", "body": f"{SEED_MARKER} Ако имаш чернова, можеш да махнеш всяко второ прилагателно и текстът става по-ясен."},
            ],
        },
    ],
    "literatura": [
        {
            "author": "student_iva",
            "title": f"Сравнение между герои в интерпретативно съчинение {SEED_MARKER}",
            "body": f"{SEED_MARKER} Трудно ми е да направя плавен преход между двама герои, без да звучи като две отделни части. Как го структурирате?",
            "grade": 11,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Пробвай по критерии: ценности, избори, последици. За всеки критерий сравняваш и двамата, вместо да ги описваш отделно."},
                {"author": "student_niki", "body": f"{SEED_MARKER} Ползвам и кратко изречение-предход: „Подобно на..., но за разлика от...“ и ми държи логиката."},
            ],
        },
    ],
    "biologiq": [
        {
            "author": "student_niki",
            "title": f"Клетъчно делене: как помните фазите на митоза? {SEED_MARKER}",
            "body": f"{SEED_MARKER} При профаза/метафаза ги обърквам на тест. Имате ли асоциации или визуални трикове, които работят?",
            "grade": 7,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Запомни „П-МА-ТА“ и си рисувай по една скица към всяка фаза. Визуалната памет помага много."},
                {"author": "demo", "body": f"{SEED_MARKER} В YouTube има хубави 3D анимации, след тях въпросите от учебника са по-лесни."},
            ],
        },
    ],
    "himiq": [
        {
            "author": "student_iva",
            "title": f"Стехиометрия: откъде почвате при по-дълги задачи? {SEED_MARKER}",
            "body": f"{SEED_MARKER} Знам формулите, но на задачи с няколко реакции се губя. Подреждате ли ги в някакъв стандартен ред?",
            "grade": 10,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Първо изравнявам уравненията, после отбелязвам известните молове и едва след това минавам към маси/обеми."},
                {"author": "student_niki", "body": f"{SEED_MARKER} На мен ми помага да ограждам „ограничаващ реагент“ с различен цвят."},
            ],
        },
    ],
    "fizika": [
        {
            "author": "student_niki",
            "title": f"Кинематика: кога да ползвам графики вместо формули? {SEED_MARKER}",
            "body": f"{SEED_MARKER} На задачи с променлива скорост губя време. По-бързо ли е първо с v(t) графика и после сметки?",
            "grade": 9,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Ако има етапи на движение, графиката е супер начало. Площта под v(t) веднага дава изминат път."},
                {"author": "demo", "body": f"{SEED_MARKER} Направи си шаблон за оси и мащаб, за да не губиш време на контролно."},
            ],
        },
    ],
    "istoriq": [
        {
            "author": "student_iva",
            "title": f"Най-добър начин за учене на дати и събития {SEED_MARKER}",
            "body": f"{SEED_MARKER} Когато уча само по списък, бързо ги забравям. Някой прави ли времеви линии или карти на причините?",
            "grade": 8,
            "comments": [
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Комбинирай дата + причина + последица в една карта. Така не учиш сухи факти, а връзки между тях."},
                {"author": "student_niki", "body": f"{SEED_MARKER} Аз си правя мини тест в края на седмицата с 10 въпроса и помага много."},
            ],
        },
    ],
    "informacionni-tehnologii": [
        {
            "author": "student_iva",
            "title": f"Python проект за училище: идеи за по-добра структура {SEED_MARKER}",
            "body": f"{SEED_MARKER} Имам малко приложение, но всичко е в един файл. Как бихте го разделили, за да е по-четимо за предаване?",
            "grade": 11,
            "comments": [
                {"author": "teacher_ani", "body": f"{SEED_MARKER} Отдели логика, вход/изход и данни в различни модули. Добави README с как се стартира проектът."},
                {"author": "demo", "body": f"{SEED_MARKER} И сложи поне 2-3 теста за основните функции — прави много добро впечатление."},
            ],
        },
    ],
    "drugo": [
        {
            "author": "demo",
            "title": f"Как комбинирате подготовка по много предмети в една седмица? {SEED_MARKER}",
            "body": f"{SEED_MARKER} Имам натоварена програма и все не ми стига време за преговор. Търся реален график, който работи в училищен ритъм.",
            "grade": 10,
            "comments": [
                {"author": "student_iva", "body": f"{SEED_MARKER} Ползвам 45/10 блокове и в неделя планирам само 3 приоритета за седмицата."},
                {"author": "teacher_mario", "body": f"{SEED_MARKER} Оставяй буфер за непредвидени домашни, иначе планът се чупи още във вторник."},
            ],
        },
    ],
}

LISTING_SCENARIOS = {
    "matematika": {
        "owner": "teacher_ani",
        "price": Decimal("42.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} Подготовка за НВО и матури по математика (7.–12. клас). Работим с диагностичен тест, седмичен план и целенасочени задачи по темите, в които ученикът губи най-много точки.",
    },
    "bulgarski": {
        "owner": "teacher_mario",
        "price": Decimal("36.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Уроци по български език с фокус върху преразказ, аргументативен текст и граматика. Давам кратка писмена обратна връзка след всяко домашно.",
    },
    "literatura": {
        "owner": "teacher_ani",
        "price": Decimal("38.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Литература за 11.–12. клас: анализ на произведения, теми и структура на интерпретативно съчинение. Подходящо за системна подготовка преди матура.",
    },
    "biologiq": {
        "owner": "demo",
        "price": Decimal("34.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} Уроци по биология за кандидат-студентска подготовка и училищни изпити. Работим с кратки тестове, схеми и преговор на пропуските след всеки модул.",
    },
    "himiq": {
        "owner": "teacher_mario",
        "price": Decimal("40.00"),
        "mode": Listing.LessonMode.IN_PERSON,
        "description": f"{SEED_MARKER} Химия с практика върху задачи от реални изпити. Подготвям индивидуални листове по стехиометрия, разтвори и органична химия.",
    },
    "fizika": {
        "owner": "teacher_ani",
        "price": Decimal("39.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Физика за 8.–12. клас с акцент върху кинематика, динамика и електричество. Всеки урок завършва с мини тест и план за самостоятелна работа.",
    },
    "istoriq": {
        "owner": "demo",
        "price": Decimal("33.00"),
        "mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
        "description": f"{SEED_MARKER} История и цивилизации с фокус върху разбиране на причинно-следствени връзки, а не механично учене на дати. Подходящо за текущи оценки и НВО.",
    },
    "informacionni-tehnologii": {
        "owner": "teacher_mario",
        "price": Decimal("45.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Програмиране и ИТ за ученици: Python основи, проекти и подготовка за състезания/изпити. Помагам и с портфолио за кандидатстване.",
    },
    "drugo": {
        "owner": "demo",
        "price": Decimal("32.00"),
        "mode": Listing.LessonMode.ONLINE,
        "description": f"{SEED_MARKER} Менторство по учебни навици и организация на подготовката. Изграждаме реалистичен седмичен график и стратегия за контролни и изпити.",
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

        for subject_index, subject in enumerate(context.subjects.values(), start=1):
            scenarios = DISCUSSION_SCENARIOS.get(subject.slug)
            if not scenarios:
                continue

            for post_index, scenario in enumerate(scenarios, start=1):
                author = context.users.get(scenario.get("author", ""))
                if author is None:
                    continue

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

                if post_index % 2 == 0:
                    self._attach_image_if_needed(post, context.image_paths[post_index % len(context.image_paths)], f"post-{subject.slug}-{post_index}.png", stats, "post_images")

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

            self._attach_image_if_needed(
                listing,
                context.image_paths[idx % len(context.image_paths)],
                f"listing-{subject.slug}.png",
                stats,
                "listing_cover_images",
            )

            desired_gallery_count = 1 + (idx % 3)
            for position in range(desired_gallery_count):
                gallery_image, image_created = ListingImage.objects.get_or_create(
                    listing=listing,
                    position=position,
                )
                if image_created or not gallery_image.image:
                    with context.image_paths[(idx + position) % len(context.image_paths)].open("rb") as image_file:
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
