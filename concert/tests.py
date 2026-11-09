from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


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
