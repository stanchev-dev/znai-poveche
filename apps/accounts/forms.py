from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="Имейл адрес",
        widget=forms.EmailInput(
            attrs={
                "autocomplete": "email",
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2")

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Потребител с този имейл вече съществува.")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            user.email = self.cleaned_data["email"]
            user.save(update_fields=["email"])
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


class DisplayNameUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("display_name",)
        widgets = {
            "display_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Въведи име за показване"}
            ),
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
