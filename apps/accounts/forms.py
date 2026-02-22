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
    role = forms.ChoiceField(
        required=True,
        label="Роля",
        choices=Profile.Role.choices,
        initial=Profile.Role.LEARNER,
        widget=forms.Select(attrs={"class": "form-select zp-role-select"}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "password1", "password2", "role")

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Това потребителско име вече е заето.")
        return username

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Потребител с този имейл вече съществува.")
        return email

    def save(self, commit=True):
        self.instance.email = self.cleaned_data["email"]
        user = super().save(commit=commit)
        selected_role = self.cleaned_data.get("role", Profile.Role.LEARNER)

        if commit:
            profile = Profile.objects.filter(user=user).first()
            if profile is not None:
                profile.role = selected_role
                profile.save(update_fields=["role"])
            return user

        user.email = self.cleaned_data["email"]
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
