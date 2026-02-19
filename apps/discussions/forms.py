from django import forms

from .models import Post


class PostBodyEditForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["body"]
        labels = {"body": "Описание"}
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 7,
                }
            )
        }

    def clean_body(self):
        body = (self.cleaned_data.get("body") or "").strip()
        if not body:
            raise forms.ValidationError("Описанието не може да е празно.")
        return body
