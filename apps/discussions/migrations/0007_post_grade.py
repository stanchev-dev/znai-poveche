from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("discussions", "0006_update_subject_theme_colors"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="grade",
            field=models.SmallIntegerField(
                blank=True,
                choices=[
                    (1, "1. клас"),
                    (2, "2. клас"),
                    (3, "3. клас"),
                    (4, "4. клас"),
                    (5, "5. клас"),
                    (6, "6. клас"),
                    (7, "7. клас"),
                    (8, "8. клас"),
                    (9, "9. клас"),
                    (10, "10. клас"),
                    (11, "11. клас"),
                    (12, "12. клас"),
                ],
                null=True,
                verbose_name="Клас",
            ),
        ),
    ]
