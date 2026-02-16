from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplace", "0002_alter_listing_contact_email_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="listing",
            name="contact_email",
            field=models.EmailField(blank=True, default="", max_length=254),
        ),
        migrations.AlterField(
            model_name="listing",
            name="contact_url",
            field=models.URLField(blank=True, default=""),
        ),
    ]
