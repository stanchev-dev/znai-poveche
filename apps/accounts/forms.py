from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile, TeacherVerificationRequest


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


class TeacherVerificationRequestForm(forms.ModelForm):
    MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}

    class Meta:
        model = TeacherVerificationRequest
        fields = ("subjects", "school_email", "school_url", "proof_file", "note")
        widgets = {
            "subjects": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Напр. математика, физика",
                }
            ),
            "school_email": forms.EmailInput(attrs={"class": "form-control"}),
            "school_url": forms.URLInput(attrs={"class": "form-control"}),
            "proof_file": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": ".pdf,.jpg,.jpeg,.png"}
            ),
            "note": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "maxlength": "300"}
            ),
        }
        help_texts = {
            "subjects": "По избор, но препоръчително.",
            "proof_file": "Закрий ЕГН и адрес. Не качвай лична карта.",
            "note": "По избор (до 300 символа).",
        }

    def clean_note(self):
        note = (self.cleaned_data.get("note") or "").strip()
        if len(note) > 300:
            raise forms.ValidationError("Полето може да съдържа най-много 300 символа.")
        return note

    def clean_proof_file(self):
        proof_file = self.cleaned_data.get("proof_file")
        if not proof_file:
            return proof_file

        extension = Path(proof_file.name or "").suffix.lower()
        if extension not in self.ALLOWED_EXTENSIONS:
            raise forms.ValidationError("Разрешени са само PDF, JPG и PNG файлове.")

        if proof_file.size > self.MAX_FILE_SIZE_BYTES:
            raise forms.ValidationError("Файлът трябва да е до 5MB.")

        content_type = (getattr(proof_file, "content_type", "") or "").lower()
        allowed_types = {
            "application/pdf",
            "image/jpeg",
            "image/jpg",
            "image/png",
        }
        if content_type and content_type not in allowed_types:
            raise forms.ValidationError("Разрешени са само PDF, JPG и PNG файлове.")

        return proof_file

    def clean(self):
        cleaned_data = super().clean()
        school_email = cleaned_data.get("school_email")
        school_url = cleaned_data.get("school_url")
        proof_file = cleaned_data.get("proof_file")

        if not school_email and not school_url and not proof_file:
            raise forms.ValidationError(
                "Моля, добави поне един начин за доказателство: имейл, линк или документ."
            )

        return cleaned_data
