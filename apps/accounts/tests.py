from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class SignInTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(
            email="editor@example.com", password="test-password-928!", display_name="Editor",
        )

    def test_anonymous_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, "/login/?next=/dashboard/", fetch_redirect_response=False)

    def test_login_normalizes_email_and_uses_browser_session(self):
        response = self.client.post(reverse("login"), {
            "username": "  EDITOR@EXAMPLE.COM  ", "password": "test-password-928!",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_remember_me_and_external_next(self):
        response = self.client.post(reverse("login"), {
            "username": self.user.email, "password": "test-password-928!",
            "remember_me": "on", "next": "https://example.org/",
        })
        self.assertRedirects(response, reverse("dashboard"))
        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertEqual(self.client.session.get_expiry_age(), 1209600)

    def test_invalid_and_inactive_users_cannot_sign_in(self):
        for active, password in [(True, "wrong"), (False, "test-password-928!")]:
            self.user.is_active = active
            self.user.save(update_fields=["is_active"])
            response = self.client.post(reverse("login"), {
                "username": self.user.email, "password": password,
            })
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.context["form"].non_field_errors())
            self.assertNotIn("_auth_user_id", self.client.session)

    def test_csrf_required_for_login_and_logout(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse("login"), {}).status_code, 403)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("logout")).status_code, 403)

    def test_logout_requires_post_and_ends_session(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("logout")), reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
