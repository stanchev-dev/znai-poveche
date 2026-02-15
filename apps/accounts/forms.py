from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegistrationForm(UserCreationForm):
    display_name = forms.CharField(max_length=50, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "display_name", "password1", "password2")

    def clean_display_name(self):
        display_name = (self.cleaned_data.get("display_name") or "").strip()
        if not display_name:
            raise forms.ValidationError("Display name is required.")
        return display_name

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.profile.display_name = self.cleaned_data["display_name"]
            user.profile.save(update_fields=["display_name"])
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name", "avatar")
        widgets = {
            "display_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Въведи име за показване"}
            ),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class DeleteAccountForm(forms.Form):
    confirmation = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Напиши DELETE",
                "autocomplete": "off",
            }
        ),
        help_text="За потвърждение напиши DELETE.",
    )

    def clean_confirmation(self):
        confirmation = (self.cleaned_data.get("confirmation") or "").strip()
        if confirmation != "DELETE":
            raise forms.ValidationError("Трябва да въведеш DELETE.")
        return confirmation
