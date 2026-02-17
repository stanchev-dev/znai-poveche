from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.discussions.models import Subject
from apps.marketplace.models import Listing


User = get_user_model()


class ListingAdminTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="testpass123",
        )
        self.subject = Subject.objects.create(name="Math")
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )
        self.listing = Listing.objects.create(
            subject=self.subject,
            owner=self.owner,
            price_per_hour="45.00",
            lesson_mode=Listing.LessonMode.ONLINE,
            description="Tutor listing",
            contact_email="owner@example.com",
        )

    def test_admin_can_save_listing_with_empty_email_and_url(self):
        self.client.force_login(self.admin_user)

        change_url = reverse("admin:marketplace_listing_change", args=[self.listing.pk])
        response = self.client.post(
            change_url,
            {
                "subject": self.subject.pk,
                "owner": self.owner.pk,
                "price_per_hour": "45.00",
                "lesson_mode": Listing.LessonMode.ONLINE,
                "description": "Tutor listing",
                "contact_phone": "",
                "contact_email": "",
                "contact_url": "",
                "vip_until_0": "",
                "vip_until_1": "",
                "_save": "Save",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.listing.refresh_from_db()
        self.assertFalse(self.listing.contact_email)
        self.assertFalse(self.listing.contact_url)

    def test_admin_changelist_shows_listing(self):
        self.client.force_login(self.admin_user)

        response = self.client.get(reverse("admin:marketplace_listing_changelist"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.listing.pk))
        self.assertContains(response, self.owner.username)
