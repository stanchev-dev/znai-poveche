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

    def test_auth_user_can_create_listing_with_only_phone(self):
        self.client.force_authenticate(self.other_user)
        payload = {
            "subject": self.physics.slug,
            "price_per_hour": "60.50",
            "online_only": True,
            "description": "Experienced tutor",
            "contact_phone": "+359123456",
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
        self.assertEqual(created.contact_phone, payload["contact_phone"])
        self.assertEqual(created.contact_email, "")
        self.assertEqual(created.contact_url, "")

    def test_create_listing_succeeds_even_when_owner_profile_missing(self):
        self.client.force_authenticate(self.other_user)
        self.other_user.profile.delete()
        payload = {
            "subject": self.physics.slug,
            "price_per_hour": "60.50",
            "online_only": True,
            "description": "Experienced tutor",
            "contact_phone": "+359123456",
        }

        response = self.client.post(
            reverse("listing-list-create"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["owner"]["username"], self.other_user.username)
        self.assertEqual(response.data["owner"]["display_name"], self.other_user.username)
        self.assertEqual(response.data["owner"]["level"], 1)

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
        self.assertIn("non_field_errors", response.data)

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

    def test_vip_created_before_newer_non_vip_stays_first(self):
        vip_listing = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="50.00",
            online_only=True,
            description="VIP listing",
            contact_phone="+359111111",
            vip_until=timezone.now() + timedelta(days=2),
        )
        newer_non_vip = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="65.00",
            online_only=False,
            description="New non-VIP listing",
            contact_phone="+359333333",
        )

        response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data["results"]]
        self.assertEqual(result_ids[0], vip_listing.id)
        self.assertLess(result_ids.index(vip_listing.id), result_ids.index(newer_non_vip.id))

    def test_non_vip_ordering_uses_created_at_desc(self):
        older_non_vip = self.listing
        newer_non_vip = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="55.00",
            online_only=True,
            description="Newer non-VIP",
            contact_phone="+359222222",
            vip_until=timezone.now() - timedelta(days=1),
        )

        response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        result_ids = [item["id"] for item in response.data["results"]]
        self.assertLess(result_ids.index(newer_non_vip.id), result_ids.index(older_non_vip.id))
        self.assertFalse(response.data["results"][result_ids.index(newer_non_vip.id)]["is_vip"])

    def test_expired_vip_is_treated_as_non_vip(self):
        active_vip = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="48.00",
            online_only=True,
            description="Active VIP",
            contact_phone="+359444444",
            vip_until=timezone.now() + timedelta(hours=6),
        )
        expired_vip = Listing.objects.create(
            subject=self.math,
            owner=self.owner,
            price_per_hour="35.00",
            online_only=False,
            description="Expired VIP",
            contact_phone="+359555555",
            vip_until=timezone.now() - timedelta(hours=1),
        )

        response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        result_ids = [item["id"] for item in results]
        self.assertEqual(result_ids[0], active_vip.id)
        self.assertFalse(results[result_ids.index(expired_vip.id)]["is_vip"])

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


    def test_listing_pagination_is_stable_with_id_tiebreaker(self):
        Listing.objects.all().delete()
        base_time = timezone.now() - timedelta(days=1)
        created_ids = []
        for index in range(25):
            listing = Listing.objects.create(
                subject=self.math,
                owner=self.owner if index % 2 == 0 else self.other_user,
                price_per_hour="40.00",
                online_only=bool(index % 2),
                description=f"Listing {index}",
                contact_phone=f"+359000{index:03d}",
            )
            Listing.objects.filter(pk=listing.pk).update(created_at=base_time)
            created_ids.append(listing.pk)

        expected_desc_ids = sorted(created_ids, reverse=True)

        page_one = self.client.get(reverse("listing-list-create"), {"page": 1})
        self.assertEqual(page_one.status_code, status.HTTP_200_OK)
        page_one_ids = [item["id"] for item in page_one.data["results"]]
        self.assertEqual(page_one_ids, expected_desc_ids[:20])

        page_two = self.client.get(reverse("listing-list-create"), {"page": 2})
        self.assertEqual(page_two.status_code, status.HTTP_200_OK)
        page_two_ids = [item["id"] for item in page_two.data["results"]]
        self.assertEqual(page_two_ids, expected_desc_ids[20:])

    def test_owner_can_upgrade_listing_to_vip(self):
        self.client.force_authenticate(self.owner)
        vip_until = (timezone.now() + timedelta(days=3)).isoformat()

        response = self.client.patch(
            reverse("listing-vip-upgrade", kwargs={"pk": self.listing.pk}),
            {"vip_until": vip_until},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.listing.refresh_from_db()
        self.assertIsNotNone(self.listing.vip_until)
        self.assertTrue(self.listing.vip_until > timezone.now())

    def test_non_owner_cannot_upgrade_listing_to_vip(self):
        self.client.force_authenticate(self.other_user)
        vip_until = (timezone.now() + timedelta(days=3)).isoformat()

        response = self.client.patch(
            reverse("listing-vip-upgrade", kwargs={"pk": self.listing.pk}),
            {"vip_until": vip_until},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_upgrade_requires_future_vip_until(self):
        self.client.force_authenticate(self.owner)
        vip_until = (timezone.now() - timedelta(hours=1)).isoformat()

        response = self.client.patch(
            reverse("listing-vip-upgrade", kwargs={"pk": self.listing.pk}),
            {"vip_until": vip_until},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("vip_until", response.data)

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
