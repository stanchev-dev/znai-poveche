from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import PostBodyEditForm
from .models import Post


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


@login_required
def my_discussions_page(request):
    posts = (
        Post.objects.filter(author=request.user)
        .select_related("subject")
        .order_by("-created_at")
    )
    return render(request, "discussions/my_discussions.html", {"posts": posts})


@login_required
def edit_my_discussion_page(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author"), pk=post_id)
    if post.author_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да редактираш тази дискусия.")

    if request.method == "POST":
        form = PostBodyEditForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Дискусията е редактирана успешно.")
            return redirect("my-discussions-page")
    else:
        form = PostBodyEditForm(instance=post)

    return render(
        request,
        "discussions/edit_my_discussion.html",
        {"form": form, "post": post},
    )


@login_required
def delete_my_discussion_page(request, post_id):
    post = get_object_or_404(Post.objects.select_related("author", "subject"), pk=post_id)
    if post.author_id != request.user.id:
        return HttpResponseForbidden("Нямаш достъп да изтриеш тази дискусия.")

    if request.method == "POST":
        post.delete()
        messages.success(request, "Дискусията беше изтрита.")
        return redirect("my-discussions-page")

    return render(request, "discussions/delete_my_discussion_confirm.html", {"post": post})
