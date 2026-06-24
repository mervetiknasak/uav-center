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

    def test_register_logs_user_in_with_csrf(self):
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            reverse("register"),
            data={"username": "operator", "password": "StrongPass123!"},
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()["authenticated"])
        self.assertEqual(response.json()["user"]["username"], "operator")

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

    def test_documents_require_authenticated_session(self):
        response = self.client.get(reverse("document-list"))

        self.assertEqual(response.status_code, 403)
