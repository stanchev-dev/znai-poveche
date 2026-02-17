from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.accounts.models import Profile
from apps.discussions.models import Subject


class Command(BaseCommand):
    help = "Seed demo data for local development"

    def handle(self, *args, **options):
        subjects = [
            ("Български език", "#FB923C"),
            ("Литература", "#BEEA00"),
            ("Биология", "#10B981"),
            ("Информационни технологии", "#2563EB"),
            ("История", "#EF4444"),
            ("Математика", "#0EA5E9"),
            ("Физика", "#FF725E"),
            ("Химия", "#7C3AED"),
            ("Други", "#64748B"),
        ]
        for index, (name, theme_color) in enumerate(subjects, start=1):
            desired_slug = slugify(name) or f"subject-{index}"
            Subject.objects.update_or_create(
                slug=desired_slug,
                defaults={"name": name, "theme_color": theme_color},
            )

        user_model = get_user_model()
        admin, admin_created = user_model.objects.get_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True},
        )
        if admin_created:
            admin.set_password("admin12345")
            admin.save(update_fields=["password"])
        else:
            admin.is_staff = True
            admin.is_superuser = True
            admin.set_password("admin12345")
            admin.save(update_fields=["is_staff", "is_superuser", "password"])

        demo, demo_created = user_model.objects.get_or_create(username="demo")
        if demo_created:
            demo.set_password("demo12345")
            demo.save(update_fields=["password"])
        else:
            demo.set_password("demo12345")
            demo.save(update_fields=["password"])

        Profile.objects.get_or_create(user=admin, defaults={"display_name": "Админ"})
        Profile.objects.get_or_create(user=demo, defaults={"display_name": "Демо"})

        self.stdout.write(self.style.SUCCESS("Seed completed."))
        self.stdout.write("Credentials:")
        self.stdout.write("- admin / admin12345")
        self.stdout.write("- demo / demo12345")
