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
    ("teacher_ani", "demo12345", False, False, "Ани П."),
    ("teacher_mario", "demo12345", False, False, "Марио Т."),
    ("student_iva", "demo12345", False, False, "Ива"),
    ("student_niki", "demo12345", False, False, "Ники"),
]

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

        authors = [
            context.users.get("demo"),
            context.users.get("student_iva"),
            context.users.get("teacher_ani"),
        ]
        commenters = [
            context.users.get("demo"),
            context.users.get("student_niki"),
            context.users.get("teacher_mario"),
        ]
        voters = [user for key, user in context.users.items() if key not in {"admin"}]

        if not all(authors) or not all(commenters):
            return

        for subject_index, subject in enumerate(context.subjects.values(), start=1):
            for post_index in range(1, 4):
                author = authors[(subject_index + post_index) % len(authors)]
                title = f"{subject.name}: подготовка за тест {post_index} {SEED_MARKER}"
                body = (
                    f"{SEED_MARKER} Търся идеи за по-ефективна подготовка по {subject.name}. "
                    "Кои задачи и ресурси ви помогнаха най-много през последната седмица?"
                )
                post, created = Post.objects.get_or_create(
                    subject=subject,
                    author=author,
                    title=title,
                    defaults={"body": body, "grade": min(12, 5 + post_index)},
                )
                stats["posts_created" if created else "posts_existing"] += 1

                if post.body != body:
                    post.body = body
                    post.save(update_fields=["body"])

                if post_index % 2 == 0:
                    self._attach_image_if_needed(post, context.image_paths[post_index % len(context.image_paths)], f"post-{subject.slug}-{post_index}.png", stats, "post_images")

                for comment_index in range(1, 4):
                    commenter = commenters[(post_index + comment_index) % len(commenters)]
                    comment_body = (
                        f"{SEED_MARKER} Според мен пробвай с 30 минути задачи и кратко обобщение след всяка тема. "
                        f"(коментар {comment_index})"
                    )
                    _, comment_created = Comment.objects.get_or_create(
                        post=post,
                        author=commenter,
                        body=comment_body,
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

        lesson_modes = [
            Listing.LessonMode.ONLINE,
            Listing.LessonMode.IN_PERSON,
            Listing.LessonMode.ONLINE_AND_IN_PERSON,
        ]

        for idx, subject in enumerate(context.subjects.values(), start=1):
            owner = owners[idx % len(owners)]
            description = (
                f"{SEED_MARKER} Индивидуални уроци по {subject.name}. "
                "Работя с план за всяка седмица, домашни и обратна връзка след всеки урок. "
                "Локация: София / онлайн според режима на обучение."
            )
            listing, created = Listing.objects.get_or_create(
                subject=subject,
                owner=owner,
                lesson_mode=lesson_modes[idx % len(lesson_modes)],
                defaults={
                    "price_per_hour": Decimal(30 + idx),
                    "description": description,
                    "contact_name": owner.username,
                    "contact_phone": "+359888123456",
                    "contact_email": f"{owner.username}@example.dev",
                },
            )
            stats["listings_created" if created else "listings_existing"] += 1

            if listing.description != description:
                listing.description = description
                listing.save(update_fields=["description"])

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
