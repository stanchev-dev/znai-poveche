from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie




@ensure_csrf_cookie
def discussions_page(request):
    return render(
        request,
        "discussions/subjects.html",
        {"subject_slug": "all", "active_subject_slug": "all"},
    )

@ensure_csrf_cookie
def subjects_page(request, slug):
    return render(
        request,
        "discussions/subjects.html",
        {"subject_slug": slug, "active_subject_slug": slug},
    )


@ensure_csrf_cookie
def post_detail_page(request, post_id):
    return render(request, "discussions/post_detail.html", {"post_id": post_id})


@login_required
@ensure_csrf_cookie
def publish_post_page(request):
    return render(
        request,
        "discussions/publish.html",
        {"prefill_subject": request.GET.get("subject", "")},
    )
