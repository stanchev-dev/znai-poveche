from django.db import migrations


SUBJECT_THEME_COLORS = {
    "bulgarski-ezik": "#FB923C",
    "literatura": "#BEEA00",
    "biologiq": "#10B981",
    "informacionni-tehnologii": "#2563EB",
    "istoriq": "#EF4444",
    "matematika": "#0EA5E9",
    "fizika": "#FF725E",
    "himiq": "#7C3AED",
    "drugi": "#64748B",
}


def set_subject_theme_colors(apps, schema_editor):
    Subject = apps.get_model("discussions", "Subject")
    for slug, color in SUBJECT_THEME_COLORS.items():
        Subject.objects.filter(slug=slug).update(theme_color=color)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("discussions", "0005_alter_subject_theme_color"),
    ]

    operations = [
        migrations.RunPython(set_subject_theme_colors, noop_reverse),
    ]
