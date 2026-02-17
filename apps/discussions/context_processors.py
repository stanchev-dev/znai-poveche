from apps.discussions.models import Subject


def nav_subjects(request):
    return {
        "nav_subjects": Subject.objects.all().only("id", "name", "slug"),
    }
