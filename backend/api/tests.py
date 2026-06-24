from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)

    def get_csrf_token(self):
        response = self.client.get(reverse("csrf-token"))
        self.assertEqual(response.status_code, 200)
        return response.json()["csrfToken"]

    def test_register_creates_pending_user_with_csrf(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            reverse("register"),
            data={
                "username": "operator",
                "email": "operator@example.com",
                "password": "StrongPass123!",
                "password_confirm": "StrongPass123!",
            },
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["username"], "operator")
        self.assertEqual(response.json()["user"]["email"], "operator@example.com")
        self.assertFalse(response.json()["user"]["is_active"])

        user = get_user_model().objects.get(username="operator")
        self.assertFalse(user.is_active)

    def test_login_requires_valid_credentials_and_csrf(self):
        user_model = get_user_model()
        user_model.objects.create_user(username="pilot", password="StrongPass123!")
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            reverse("login"),
            data={"username": "pilot", "password": "StrongPass123!"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["username"], "pilot")

    def test_pending_user_cannot_login_until_admin_approves(self):
        user_model = get_user_model()
        admin = user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="StrongPass123!",
            is_staff=True,
        )
        user = user_model.objects.create_user(
            username="candidate",
            email="candidate@example.com",
            password="StrongPass123!",
            is_active=False,
        )
        csrf_token = self.get_csrf_token()

        pending_login = self.client.post(
            reverse("login"),
            data={"username": "candidate", "password": "StrongPass123!"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(pending_login.status_code, 400)

        self.client.force_login(admin)
        approval = self.client.patch(
            reverse("admin-user-status", kwargs={"user_id": user.id}),
            data={"is_active": True},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(approval.status_code, 200)
        self.assertTrue(approval.json()["is_active"])

        self.client.logout()
        approved_login = self.client.post(
            reverse("login"),
            data={"username": "candidate", "password": "StrongPass123!"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(approved_login.status_code, 200)
        self.assertTrue(approved_login.json()["authenticated"])

    def test_documents_require_authenticated_session(self):
        response = self.client.get(reverse("document-list"))

        self.assertEqual(response.status_code, 403)

    def test_deactivated_session_cannot_access_documents(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="operator",
            email="operator@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)

        user.is_active = False
        user.save(update_fields=["is_active"])

        response = self.client.get(reverse("document-list"))

        self.assertEqual(response.status_code, 403)
