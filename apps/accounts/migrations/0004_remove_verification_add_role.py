from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_profile_is_verified_teacher_teacherverificationrequest"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="profile",
            name="is_verified_teacher",
        ),
        migrations.AddField(
            model_name="profile",
            name="role",
            field=models.CharField(
                choices=[("learner", "Учащ"), ("teacher", "Учител")],
                default="learner",
                max_length=20,
            ),
        ),
        migrations.DeleteModel(
            name="TeacherVerificationRequest",
        ),
    ]
