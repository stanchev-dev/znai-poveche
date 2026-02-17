from django.urls import path

from .views import (
    login_view,
    logout_view,
    profile_delete_view,
    profile_view,
    register_view,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("register/", register_view, name="register"),
    path("logout/", logout_view, name="logout"),
    path("profile/", profile_view, name="profile"),
    path("profile/delete/", profile_delete_view, name="profile-delete"),
]
