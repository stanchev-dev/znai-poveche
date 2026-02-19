from django.db import migrations, models
import django.db.models.deletion
import apps.marketplace.models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0004_listing_lesson_mode_image"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="contact_name",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.CreateModel(
            name="ListingImage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "image",
                    models.ImageField(upload_to=apps.marketplace.models.listing_image_upload_to),
                ),
                ("position", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "listing",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="images",
                        to="marketplace.listing",
                    ),
                ),
            ],
            options={"ordering": ["position", "id"]},
        ),
    ]
