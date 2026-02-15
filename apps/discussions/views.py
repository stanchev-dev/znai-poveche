from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def subjects_page(request, slug):
    return render(request, "discussions/subjects.html", {"subject_slug": slug})


@ensure_csrf_cookie
def post_detail_page(request, post_id):
    return render(request, "discussions/post_detail.html", {"post_id": post_id})
