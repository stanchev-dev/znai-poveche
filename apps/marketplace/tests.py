from datetime import timedelta
from decimal import Decimal
from io import BytesIO
import os

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

from apps.discussions.models import Subject
from apps.accounts.models import Profile
from apps.marketplace.models import Listing, ListingImage


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
        self.owner.profile.role = Profile.Role.TEACHER
        self.owner.profile.save(update_fields=["role"])
        self.math = Subject.objects.create(name="Math")
        self.physics = Subject.objects.create(name="Physics")

        self.listing = Listing.objects.create(
            subject=self.math,
            owner=self.owner,
            price_per_hour="45.00",
            lesson_mode=Listing.LessonMode.ONLINE_AND_IN_PERSON,
            description="A" * 250,
            contact_phone="+359000000",
        )


    def _image_file(self, name="img.jpg", size=(20, 20), image_format="JPEG", noisy=False):
        buffer = BytesIO()
        if noisy:
            raw = os.urandom(size[0] * size[1] * 3)
            image = Image.frombytes("RGB", size, raw)
        else:
            image = Image.new("RGB", size, color=(123, 45, 67))
        image.save(buffer, format=image_format)
        buffer.seek(0)
        content_type = "image/jpeg" if image_format == "JPEG" else "image/png"
        return SimpleUploadedFile(name=name, content=buffer.read(), content_type=content_type)

    def test_guest_can_list_and_detail_without_contacts(self):
        list_response = self.client.get(reverse("listing-list-create"))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        result = list_response.data["results"][0]
        self.assertNotIn("contact_phone", result)
        self.assertNotIn("contact_email", result)
        self.assertNotIn("contact_url", result)
        self.assertIn("description_excerpt", result)
        self.assertLessEqual(len(result["description_excerpt"]), 160)
        self.assertEqual(result["owner"]["role"], Profile.Role.TEACHER)
        self.assertEqual(result["owner"]["role_label"], "Учител")
        self.assertEqual(result["author_role"], Profile.Role.TEACHER)
        self.assertEqual(result["author_role_label"], "Учител")

        detail_response = self.client.get(
            reverse("listing-detail", kwargs={"pk": self.listing.pk})
        )
        self.assertEqual(detail_response.status_code, status.HTTP_200_OK)
        self.assertNotIn("contact_phone", detail_response.data)
        self.assertNotIn("contact_email", detail_response.data)
        self.assertNotIn("contact_url", detail_response.data)
        self.assertEqual(detail_response.data["owner"]["role"], Profile.Role.TEACHER)
        self.assertEqual(detail_response.data["owner"]["role_label"], "Учител")
        self.assertEqual(detail_response.data["author_role"], Profile.Role.TEACHER)
        self.assertEqual(detail_response.data["author_role_label"], "Учител")

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
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Experienced tutor with structured lessons for exam preparation.",
            "contact_name": "Иван Иванов",
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
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Experienced tutor with structured lessons for exam preparation.",
            "contact_name": "Иван Иванов",
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
        self.assertEqual(response.data["owner"]["role"], Profile.Role.LEARNER)
        self.assertEqual(response.data["owner"]["role_label"], "Учащ")
        self.assertEqual(response.data["author_role"], Profile.Role.LEARNER)
        self.assertEqual(response.data["author_role_label"], "Учащ")

    def test_create_fails_when_required_contact_fields_missing(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30.00",
            "lesson_mode": Listing.LessonMode.ONLINE_AND_IN_PERSON,
            "description": "No contacts provided but otherwise the listing has enough detail.",
        }

        response = self.client.post(
            reverse("listing-list-create"),
            payload,
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_name", response.data)
        self.assertIn("contact_phone", response.data)

    def test_create_fails_when_price_is_not_numeric(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "asjodnajodnsando",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Подробно описание за уроците и начина на провеждане.",
            "contact_name": "Иван Иванов",
            "contact_phone": "+359888777666",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price_per_hour", response.data)

    def test_create_accepts_price_with_comma_separator(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "25,50",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Подробно описание за уроците и начина на провеждане.",
            "contact_name": "Иван Иванов",
            "contact_phone": "+359888777666",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_fails_when_phone_is_invalid(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Подробно описание за уроците и начина на провеждане.",
            "contact_name": "Иван Иванов",
            "contact_phone": "123",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_phone", response.data)


    def test_create_fails_when_description_is_too_short(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Кратко инфо",
            "contact_name": "Иван Иванов",
            "contact_phone": "+359888777666",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("description", response.data)
        self.assertIn("Въведи поне 20 символа.", response.data["description"][0])

    def test_create_fails_when_contact_name_is_only_digits(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Подробно описание за уроците и начина на провеждане.",
            "contact_name": "12345",
            "contact_phone": "+359888777666",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("contact_name", response.data)
        self.assertIn("Лицето за контакт не може да бъде само числа.", response.data["contact_name"][0])

    def test_create_accepts_phone_with_dashes(self):
        self.client.force_authenticate(self.owner)
        payload = {
            "subject": self.math.slug,
            "price_per_hour": "30",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Подробно описание за уроците и начина на провеждане.",
            "contact_name": "Иван Иванов",
            "contact_phone": "088-599-5855",
        }

        response = self.client.post(reverse("listing-list-create"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_rejects_more_than_four_images(self):
        self.client.force_authenticate(self.other_user)
        payload = {
            "subject": self.physics.slug,
            "price_per_hour": "60.50",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Experienced tutor with structured lessons for exam preparation.",
            "contact_name": "Иван Иванов",
            "contact_phone": "+359123456",
        }
        files = [
            self._image_file(name=f"img-{index}.jpg")
            for index in range(5)
        ]

        response = self.client.post(
            reverse("listing-list-create"),
            {**payload, "images": files},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", response.data)
        self.assertIn("Можеш да качиш до 4 снимки.", response.data["images"][0])

    def test_create_rejects_image_larger_than_two_mb(self):
        self.client.force_authenticate(self.other_user)
        payload = {
            "subject": self.physics.slug,
            "price_per_hour": "60.50",
            "lesson_mode": Listing.LessonMode.ONLINE,
            "description": "Experienced tutor with structured lessons for exam preparation.",
            "contact_name": "Иван Иванов",
            "contact_phone": "+359123456",
        }
        oversized_image = self._image_file(
            name="too-large.png",
            size=(1200, 1200),
            image_format="PNG",
            noisy=True,
        )
        self.assertGreater(oversized_image.size, 2 * 1024 * 1024)

        response = self.client.post(
            reverse("listing-list-create"),
            {**payload, "images": [oversized_image]},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("images", response.data)
        self.assertIn(
            "Невалиден файл. Приемаме само jpg, jpeg, png до 2MB.",
            response.data["images"][0],
        )

    def test_vip_ordering_returns_active_vip_first(self):
        vip_listing = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="50.00",
            lesson_mode=Listing.LessonMode.ONLINE,
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
            lesson_mode=Listing.LessonMode.ONLINE,
            description="VIP listing",
            contact_phone="+359111111",
            vip_until=timezone.now() + timedelta(days=2),
        )
        newer_non_vip = Listing.objects.create(
            subject=self.math,
            owner=self.other_user,
            price_per_hour="65.00",
            lesson_mode=Listing.LessonMode.ONLINE_AND_IN_PERSON,
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
            lesson_mode=Listing.LessonMode.ONLINE,
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
            lesson_mode=Listing.LessonMode.ONLINE,
            description="Active VIP",
            contact_phone="+359444444",
            vip_until=timezone.now() + timedelta(hours=6),
        )
        expired_vip = Listing.objects.create(
            subject=self.math,
            owner=self.owner,
            price_per_hour="35.00",
            lesson_mode=Listing.LessonMode.ONLINE_AND_IN_PERSON,
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
            lesson_mode=Listing.LessonMode.ONLINE,
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
                lesson_mode=(
                    Listing.LessonMode.ONLINE
                    if bool(index % 2)
                    else Listing.LessonMode.ONLINE_AND_IN_PERSON
                ),
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


class MyListingsPageTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner", password="testpass123")
        self.other = User.objects.create_user(username="other", password="testpass123")
        self.subject = Subject.objects.create(name="Math")
        self.listing = Listing.objects.create(
            subject=self.subject,
            owner=self.owner,
            price_per_hour="45.00",
            lesson_mode=Listing.LessonMode.ONLINE,
            description="A" * 120,
            contact_name="Owner",
            contact_phone="+359888777666",
        )

    def test_my_listings_requires_login(self):
        response = self.client.get(reverse("marketplace-my-listings-page"))
        self.assertEqual(response.status_code, 302)

    def test_my_listings_shows_only_owners_listings(self):
        Listing.objects.create(
            subject=self.subject,
            owner=self.other,
            price_per_hour="50.00",
            lesson_mode=Listing.LessonMode.ONLINE,
            description="B" * 120,
            contact_name="Other",
            contact_phone="+359999777666",
        )
        self.client.force_login(self.owner)
        response = self.client.get(reverse("marketplace-my-listings-page"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Уроци по Math")
        self.assertContains(response, "Редактирай")
        self.assertContains(response, "Изтрий")

    def test_owner_checks_for_edit_and_delete(self):
        self.client.force_login(self.other)
        edit_response = self.client.get(reverse("marketplace-edit-page", kwargs={"listing_id": self.listing.id}))
        delete_response = self.client.get(reverse("marketplace-delete-page", kwargs={"listing_id": self.listing.id}))
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(delete_response.status_code, 403)

    def test_edit_page_hides_contact_email_and_contact_url_fields(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse("marketplace-edit-page", kwargs={"listing_id": self.listing.id}))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Contact email")
        self.assertNotContains(response, "Contact url")

    def test_edit_listing_save_still_works_without_contact_email_and_contact_url(self):
        self.listing.contact_email = "owner@example.com"
        self.listing.contact_url = "https://example.com/profile"
        self.listing.save(update_fields=["contact_email", "contact_url", "updated_at"])

        self.client.force_login(self.owner)
        response = self.client.post(
            reverse("marketplace-edit-page", kwargs={"listing_id": self.listing.id}),
            {
                "subject": self.subject.id,
                "price_per_hour": "55.00",
                "lesson_mode": Listing.LessonMode.OFFLINE,
                "description": "C" * 120,
                "contact_name": "Updated Owner",
                "contact_phone": "+359888123456",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.price_per_hour, Decimal("55.00"))
        self.assertEqual(self.listing.lesson_mode, Listing.LessonMode.OFFLINE)
        self.assertEqual(self.listing.contact_name, "Updated Owner")
        self.assertEqual(self.listing.contact_phone, "+359888123456")
        self.assertEqual(self.listing.contact_email, "owner@example.com")
        self.assertEqual(self.listing.contact_url, "https://example.com/profile")


class ListingImageEditPageTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username="owner2", password="testpass123")
        self.other = User.objects.create_user(username="other2", password="testpass123")
        self.subject = Subject.objects.create(name="Chemistry")
        self.listing = Listing.objects.create(
            subject=self.subject,
            owner=self.owner,
            price_per_hour="30.00",
            lesson_mode=Listing.LessonMode.ONLINE,
            description="A" * 30,
            contact_name="Owner",
            contact_phone="+359888777666",
        )
        self.image1 = ListingImage.objects.create(listing=self.listing, image=self._image_file(name="a.jpg"), position=0)
        self.image2 = ListingImage.objects.create(listing=self.listing, image=self._image_file(name="b.jpg"), position=1)
        self.listing.image = self.image1.image
        self.listing.save(update_fields=["image", "updated_at"])

    def _image_file(self, name="img.jpg", size=(20, 20), image_format="JPEG", noisy=False):
        buffer = BytesIO()
        if noisy:
            raw = os.urandom(size[0] * size[1] * 3)
            image = Image.frombytes("RGB", size, raw)
        else:
            image = Image.new("RGB", size, color=(120, 40, 90))
        image.save(buffer, format=image_format)
        buffer.seek(0)
        content_type = "image/jpeg" if image_format == "JPEG" else "image/png"
        return SimpleUploadedFile(name=name, content=buffer.read(), content_type=content_type)

    def test_owner_can_open_images_edit_page(self):
        self.client.login(username="owner2", password="testpass123")
        response = self.client.get(reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}))
        self.assertEqual(response.status_code, 200)

    def test_non_owner_gets_403(self):
        self.client.login(username="other2", password="testpass123")
        response = self.client.get(reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}))
        self.assertEqual(response.status_code, 403)

    def test_can_reorder_delete_and_add_images(self):
        self.client.login(username="owner2", password="testpass123")
        new_image = self._image_file(name="c.png", image_format="PNG")
        response = self.client.post(
            reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}),
            {
                "deleted_image_ids": str(self.image1.id),
                "ordering_image_ids": str(self.image2.id),
                "images": [new_image],
            },
        )
        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        ordered = list(self.listing.images.order_by("position", "id"))
        self.assertEqual(ordered[0].id, self.image2.id)
        self.assertEqual(len(ordered), 2)
        self.assertEqual(self.listing.image.name, ordered[0].image.name)

    def test_can_save_with_zero_images(self):
        self.client.login(username="owner2", password="testpass123")
        response = self.client.post(
            reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}),
            {
                "deleted_image_ids": f"{self.image1.id},{self.image2.id}",
                "ordering_image_ids": "",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.images.count(), 0)
        self.assertFalse(self.listing.image)

    def test_rejects_more_than_four_total_images(self):
        self.client.login(username="owner2", password="testpass123")
        response = self.client.post(
            reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}),
            {
                "deleted_image_ids": "",
                "ordering_image_ids": f"{self.image1.id},{self.image2.id}",
                "images": [
                    self._image_file(name="1.jpg"),
                    self._image_file(name="2.jpg"),
                    self._image_file(name="3.jpg"),
                ],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Можеш да качиш до 4 снимки.")

    def test_rejects_invalid_extension(self):
        self.client.login(username="owner2", password="testpass123")
        bad_file = SimpleUploadedFile(name="bad.gif", content=b"GIF89a", content_type="image/gif")
        response = self.client.post(
            reverse("marketplace-edit-images-page", kwargs={"listing_id": self.listing.id}),
            {
                "deleted_image_ids": "",
                "ordering_image_ids": f"{self.image1.id},{self.image2.id}",
                "images": [bad_file],
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Невалиден файл. Приемаме само jpg, jpeg, png до 2MB.")
