from apps.discussions.models import Subject


def nav_subjects(request):
    return {
        "nav_subjects": Subject.objects.order_by("name").only("id", "name", "slug"),
    }
