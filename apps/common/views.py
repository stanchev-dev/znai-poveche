from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie


@ensure_csrf_cookie
def home(request):
    return render(request, "common/home.html")


@ensure_csrf_cookie
def leaderboard(request):
    return render(request, "common/leaderboard.html")
