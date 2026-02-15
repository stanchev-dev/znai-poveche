from django import template
from django.templatetags.static import static
from django.db.utils import OperationalError, ProgrammingError

from apps.accounts.models import Profile
from apps.accounts.utils import profile_has_avatar_column

register = template.Library()


@register.simple_tag
def user_avatar_url(user):
    default_avatar = static("img/default-avatar.svg")

    if not getattr(user, "is_authenticated", False):
        return default_avatar

    if not profile_has_avatar_column():
        return default_avatar

    try:
        profile = user.profile
        if getattr(profile, "avatar", None):
            return profile.avatar.url
    except (AttributeError, OperationalError, ProgrammingError, ValueError):
        return default_avatar

    return default_avatar


@register.simple_tag
def user_nav_label(user):
    if not getattr(user, "is_authenticated", False):
        return "Акаунт"

    username = user.get_username()

    try:
        display_name = (
            Profile.objects.filter(user=user)
            .values_list("display_name", flat=True)
            .first()
        )
    except (OperationalError, ProgrammingError, ValueError):
        return username

    return (display_name or "").strip() or username
