import apps.discussions.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discussions", "0007_post_grade"),
    ]

    operations = [
        migrations.CreateModel(
            name="PostImage",
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
                ("image", models.ImageField(upload_to=apps.discussions.models.post_image_upload_to)),
                ("position", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "post",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="images",
                        to="discussions.post",
                    ),
                ),
            ],
            options={"ordering": ["position", "id"]},
        ),
    ]
