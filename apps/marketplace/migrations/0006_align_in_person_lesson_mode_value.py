from django.db import migrations, models


def migrate_offline_to_in_person(apps, schema_editor):
    Listing = apps.get_model("marketplace", "Listing")
    Listing.objects.filter(lesson_mode="offline").update(lesson_mode="in_person")


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0005_listingimage_listing_contact_name"),
    ]

    operations = [
        migrations.RunPython(
            migrate_offline_to_in_person,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
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
    ]
