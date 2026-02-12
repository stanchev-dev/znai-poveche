from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.discussions.models import Subject
from apps.marketplace.models import Listing


User = get_user_model()


class ListingAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner",
            password="testpass123",
        )
        self.other_user = User.objects.create_user(
            username="other",
            password="testpass123",
        )
        self.math = Subject.objects.create(name="Math")
        self.physics = Subject.objects.create(name="Physics")

        self.listing = Listing.objects.create(
            subject=self.math,
            owner=self.owner,
            price_per_hour="45.00",
            online_only=False,
            description="A" * 250,
            contact_phone="+359000000",
        )

    def test_guest_can_list_and_detail_without_contacts(self):
        list_response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        result = list_response.data["results"][0]
        self.assertNotIn("contact_phone", result)
        self.assertNotIn("contact_email", result)
        self.assertNotIn("contact_url", result)
        self.assertIn("description_excerpt", result)
        self.assertLessEqual(len(result["description_excerpt"]), 160)

        detail_response = self.client.get(
            reverse("listing-detail", kwargs={"pk": self.listing.pk})
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("contact_phone", detail_response.data)
        self.assertNotIn("contact_email", detail_response.data)
        self.assertNotIn("contact_url", detail_response.data)

    def test_guest_cannot_get_contact(self):
        response = self.client.get(
            reverse("listing-contact", kwargs={"pk": self.listing.pk})
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    def test_auth_user_can_create_listing(self):
        self.client.force_authenticate(self.other_user)
        payload = {
            "subject": self.physics.slug,
            "price_per_hour": "60.50",
            "online_only": True,
            "description": "Experienced tutor",
            "contact_email": "teacher@example.com",
        }

        response = self.client.post(
            reverse("listing-list-create"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created = Listing.objects.get(pk=response.data["id"])
        self.assertEqual(created.owner, self.other_user)
        self.assertEqual(created.subject, self.physics)

    def test_create_fails_when_all_contacts_missing(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30.00",
            "online_only": False,
            "description": "No contacts provided",
        }

        response = self.client.post(
            reverse("listing-list-create"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vip_ordering_returns_active_vip_first(self):
        vip_listing = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="50.00",
            online_only=True,
            description="VIP listing",
            contact_phone="+359111111",
            vip_until=timezone.now() + timedelta(days=2),
        )

        response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(result_ids[0], vip_listing.id)
        self.assertTrue(response.data["results"][0]["is_vip"])

    def test_filters_subject_online_only_and_price(self):
        listing_two = Listing.objects.create(
            subject=self.physics,
            owner=self.owner,
            price_per_hour="90.00",
            online_only=True,
            description="Physics listing",
            contact_email="physics@example.com",
        )

        subject_response = self.client.get(
            reverse("listing-list-create"), {"subject": self.physics.slug}
        )
        self.assertEqual(subject_response.status_code, status.HTTP_200_OK)
        self.assertEqual(subject_response.data["count"], 1)
        self.assertEqual(subject_response.data["results"][0]["id"], listing_two.id)

        invalid_subject = self.client.get(
            reverse("listing-list-create"), {"subject": "missing-subject"}
        )
        self.assertEqual(invalid_subject.status_code, status.HTTP_200_OK)
        self.assertEqual(invalid_subject.data["count"], 0)

        online_only_response = self.client.get(
            reverse("listing-list-create"), {"online_only": "1"}
        )
        self.assertEqual(online_only_response.status_code, status.HTTP_200_OK)
        self.assertEqual(online_only_response.data["count"], 1)
        self.assertEqual(
            online_only_response.data["results"][0]["id"],
            listing_two.id,
        )

        online_only_invalid = self.client.get(
            reverse("listing-list-create"), {"online_only": "2"}
        )
        self.assertEqual(
            online_only_invalid.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        price_response = self.client.get(
            reverse("listing-list-create"),
            {"price_min": "40.00", "price_max": "70.00"},
        )
        self.assertEqual(price_response.status_code, status.HTTP_200_OK)
        self.assertEqual(price_response.data["count"], 1)
        self.assertEqual(price_response.data["results"][0]["id"], self.listing.id)

        invalid_price_min = self.client.get(
            reverse("listing-list-create"),
            {"price_min": "abc"},
        )
        self.assertEqual(
            invalid_price_min.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        invalid_price_max = self.client.get(
            reverse("listing-list-create"),
            {"price_max": "abc"},
        )
        self.assertEqual(
            invalid_price_max.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_list_has_excerpt_and_detail_has_full_description(self):
        list_response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        excerpt = list_response.data["results"][0]["description_excerpt"]
        self.assertLessEqual(len(excerpt), 160)

        detail_response = self.client.get(
            reverse("listing-detail", kwargs={"pk": self.listing.pk})
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_response.data["description"], self.listing.description)
