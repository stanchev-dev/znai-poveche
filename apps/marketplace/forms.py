from decimal import Decimal, InvalidOperation
import re

from django import forms

from .models import Listing


PRICE_PATTERN = re.compile(r"^\d+(?:[\.,]\d{1,2})?$")
PHONE_ALLOWED_PATTERN = re.compile(r"^\+?\d+$")


class ListingPublishForm(forms.Form):
    subject = forms.CharField(
        required=True,
        error_messages={"required": "Избери предмет."},
    )
    price_per_hour = forms.CharField(required=True)
    lesson_mode = forms.ChoiceField(
        required=True,
        choices=Listing.LessonMode.choices,
        error_messages={"required": "Избери режим на обучение.", "invalid_choice": "Избери режим на обучение."},
    )
    description = forms.CharField(
        required=True,
        min_length=20,
        error_messages={"required": "Попълни описание.", "min_length": "Въведи поне 20 символа."},
    )
    contact_name = forms.CharField(
        required=True,
        max_length=120,
        error_messages={"required": "Попълни лице за контакт."},
    )
    contact_phone = forms.CharField(
        required=True,
        max_length=30,
        error_messages={"required": "Въведи валиден телефон."},
    )
    contact_email = forms.EmailField(required=False)

    def clean_subject(self):
        value = (self.cleaned_data.get("subject") or "").strip()
        if not value:
            raise forms.ValidationError("Избери предмет.")
        return value

    def clean_price_per_hour(self):
        raw_value = (self.cleaned_data.get("price_per_hour") or "").strip()
        if not raw_value or not PRICE_PATTERN.fullmatch(raw_value):
            raise forms.ValidationError("Въведи валидна цена на час (само число).")

        normalized = raw_value.replace(",", ".")
        try:
            value = Decimal(normalized)
        except InvalidOperation as exc:
            raise forms.ValidationError("Въведи валидна цена на час (само число).") from exc

        if value < 0:
            raise forms.ValidationError("Въведи валидна цена на час (само число).")

        return value

    def clean_description(self):
        return (self.cleaned_data.get("description") or "").strip()

    def clean_contact_name(self):
        value = (self.cleaned_data.get("contact_name") or "").strip()
        if not value:
            raise forms.ValidationError("Попълни лице за контакт.")

        normalized = re.sub(r"[\s-]+", "", value)
        if normalized.isdigit():
            raise forms.ValidationError("Лицето за контакт не може да бъде само числа.")

        return value

    def clean_contact_phone(self):
        raw_value = (self.cleaned_data.get("contact_phone") or "").strip()
        collapsed = re.sub(r"[\s-]+", "", raw_value)

        if collapsed.startswith("+"):
            digits_only = collapsed[1:]
        else:
            digits_only = collapsed

        if not digits_only or len(digits_only) < 9 or len(digits_only) > 13:
            raise forms.ValidationError("Въведи валиден телефон.")

        if not (collapsed.startswith("0") or collapsed.startswith("+359")):
            raise forms.ValidationError("Въведи валиден телефон.")

        if not PHONE_ALLOWED_PATTERN.fullmatch(collapsed):
            raise forms.ValidationError("Въведи валиден телефон.")

        return raw_value
