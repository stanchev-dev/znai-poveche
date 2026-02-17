from django.db import migrations, models

import apps.marketplace.models


def migrate_online_only_to_lesson_mode(apps, schema_editor):
    Listing = apps.get_model("marketplace", "Listing")
    Listing.objects.filter(online_only=True).update(lesson_mode="online")
    Listing.objects.filter(online_only=False).update(
        lesson_mode="online_and_in_person"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0003_alter_listing_contact_fields_defaults"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="lesson_mode",
            field=models.CharField(
                choices=[
                    ("online", "Онлайн"),
                    ("in_person", "Присъствено"),
                    ("online_and_in_person", "Онлайн + присъствено"),
                ],
                default="online_and_in_person",
                max_length=24,
            ),
        ),
        migrations.AddField(
            model_name="listing",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to=apps.marketplace.models.listing_image_upload_to,
            ),
        ),
        migrations.RunPython(
            migrate_online_only_to_lesson_mode,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="listing",
            name="online_only",
        ),
    ]
