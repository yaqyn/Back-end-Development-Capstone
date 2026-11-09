from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from concert.models import Concert, ConcertAttending


class SignUpTests(TestCase):
    def test_signup_rejects_mismatched_passwords(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "student",
                "password1": "learning-pass-42",
                "password2": "different-pass-42",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The two password fields didn’t match")
        self.assertFalse(User.objects.filter(username="student").exists())

    def test_signup_creates_and_logs_in_valid_user(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "student",
                "password1": "learning-pass-42",
                "password2": "learning-pass-42",
            },
        )

        self.assertRedirects(response, reverse("index"))
        user = User.objects.get(username="student")
        self.assertTrue(user.check_password("learning-pass-42"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.id)


class RsvpTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("student", password="learning-pass-42")
        self.concert = Concert.objects.create(
            concert_name="Learning Live",
            duration=2,
            city="Riyadh",
            date="2026-11-09",
        )
        self.url = reverse("concert_attendee")

    def test_rsvp_requires_login(self):
        response = self.client.post(
            self.url,
            {"concert_id": self.concert.id, "attendee_choice": "Attending"},
        )

        self.assertRedirects(response, f"{reverse('login')}?next={self.url}")
        self.assertFalse(ConcertAttending.objects.exists())

    def test_rsvp_rejects_get_requests(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_rsvp_returns_not_found_for_unknown_concert(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"concert_id": self.concert.id + 1, "attendee_choice": "Attending"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ConcertAttending.objects.exists())

    def test_rsvp_rejects_unknown_status(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {"concert_id": self.concert.id, "attendee_choice": "Maybe"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ConcertAttending.objects.exists())

    def test_rsvp_updates_existing_choice(self):
        self.client.force_login(self.user)

        first_response = self.client.post(
            self.url,
            {"concert_id": self.concert.id, "attendee_choice": "Attending"},
        )
        second_response = self.client.post(
            self.url,
            {"concert_id": self.concert.id, "attendee_choice": "Not Attending"},
        )

        self.assertRedirects(first_response, reverse("concerts"))
        self.assertRedirects(second_response, reverse("concerts"))
        attendance = ConcertAttending.objects.get(
            concert=self.concert, user=self.user
        )
        self.assertEqual(attendance.attending, "Not Attending")
        self.assertEqual(ConcertAttending.objects.count(), 1)
