from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="contact_email",
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name="listing",
            name="contact_url",
            field=models.URLField(blank=True, null=True),
        ),
    ]
