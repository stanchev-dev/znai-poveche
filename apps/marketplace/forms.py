from decimal import Decimal, InvalidOperation
from pathlib import Path
import re

from django import forms

from .models import Listing


PRICE_PATTERN = re.compile(r"^\d+(?:[\.,]\d{1,2})?$")
PHONE_ALLOWED_PATTERN = re.compile(r"^\+?\d+$")
MAX_LISTING_IMAGES = 4
MAX_LISTING_IMAGE_SIZE_BYTES = 2 * 1024 * 1024
ALLOWED_LISTING_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


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


class ListingEditForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            "subject",
            "price_per_hour",
            "lesson_mode",
            "description",
            "contact_name",
            "contact_phone",
        ]
        widgets = {
            "subject": forms.Select(attrs={"class": "form-select"}),
            "price_per_hour": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "lesson_mode": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={"class": "form-control"}),
        }


class ListingImagesEditForm(forms.Form):
    images = forms.FileField(required=False)
    deleted_image_ids = forms.CharField(required=False)
    ordering_image_ids = forms.CharField(required=False)

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing
        self.new_images = []
        self.delete_ids = set()
        self.ordering_ids = []

    def clean(self):
        cleaned_data = super().clean()
        if self.listing is None:
            raise forms.ValidationError("Липсва обява за редакция на снимки.")

        self.new_images = list(self.files.getlist("images"))
        self.delete_ids = self._parse_csv_ids(cleaned_data.get("deleted_image_ids") or "")
        self.ordering_ids = self._parse_csv_ids(cleaned_data.get("ordering_image_ids") or "", as_list=True)

        existing_ids = set(self.listing.images.values_list("id", flat=True))
        if self.delete_ids - existing_ids:
            raise forms.ValidationError("Невалиден избор на снимки за изтриване.")

        remaining_existing_count = len(existing_ids - self.delete_ids)
        if remaining_existing_count + len(self.new_images) > MAX_LISTING_IMAGES:
            raise forms.ValidationError(f"Можеш да качиш до {MAX_LISTING_IMAGES} снимки.")

        for image in self.new_images:
            extension = Path(image.name or "").suffix.lower()
            if extension not in ALLOWED_LISTING_IMAGE_EXTENSIONS or image.size > MAX_LISTING_IMAGE_SIZE_BYTES:
                raise forms.ValidationError("Невалиден файл. Приемаме само jpg, jpeg, png до 2MB.")

        return cleaned_data

    def _parse_csv_ids(self, raw_value, as_list=False):
        parsed = []
        for chunk in raw_value.split(','):
            chunk = chunk.strip()
            if chunk.isdigit():
                parsed.append(int(chunk))
        return parsed if as_list else set(parsed)
