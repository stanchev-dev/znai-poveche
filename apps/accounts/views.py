from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    DeleteAccountForm,
    DisplayNameUpdateForm,
    ProfileUpdateForm,
    RegistrationForm,
)
from .models import Profile
from .utils import profile_has_avatar_column


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("/")
    else:
        form = AuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password1"],
            )
            if user is not None:
                login(request, user)
            return redirect("/")
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def logout_view(request):
    if request.method == "POST":
        logout(request)
    return redirect("/")


@login_required
def profile_view(request):
    avatar_enabled = profile_has_avatar_column()

    profile_qs = Profile.objects.filter(user=request.user)
    if not avatar_enabled:
        profile_qs = profile_qs.defer("avatar")
    profile = profile_qs.first()

    if profile is None:
        messages.error(request, "Профилът не беше намерен.")
        return redirect("home")

    form_class = ProfileUpdateForm if avatar_enabled else DisplayNameUpdateForm

    if request.method == "POST":
        form = form_class(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Профилът е обновен успешно.")
            return redirect("profile")
    else:
        form = form_class(instance=profile)

    delete_form = DeleteAccountForm()
    return render(
        request,
        "accounts/profile.html",
        {
            "form": form,
            "delete_form": delete_form,
            "avatar_enabled": avatar_enabled,
        },
    )


@login_required
@require_POST
def profile_delete_view(request):
    form = DeleteAccountForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Потвърждението за изтриване е невалидно.")
        return redirect("profile")

    request.user.delete()
    messages.success(request, "Профилът беше изтрит.")
    return redirect("home")
