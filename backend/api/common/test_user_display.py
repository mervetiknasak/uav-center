from types import SimpleNamespace

from django.test import SimpleTestCase

from .user_display import format_user_display_name


class UserDisplayNameTests(SimpleTestCase):
    def test_formats_full_name_with_username(self):
        user = SimpleNamespace(
            first_name="  Ayşe ",
            last_name=" Yılmaz  ",
            username="ayse.yilmaz",
        )

        self.assertEqual(format_user_display_name(user), "Ayşe Yılmaz (ayse.yilmaz)")

    def test_falls_back_to_username_when_full_name_is_incomplete(self):
        for first_name, last_name in (("", ""), ("Ayşe", ""), ("", "Yılmaz")):
            with self.subTest(first_name=first_name, last_name=last_name):
                user = SimpleNamespace(
                    first_name=first_name,
                    last_name=last_name,
                    username="ayse.yilmaz",
                )

                self.assertEqual(format_user_display_name(user), "ayse.yilmaz")

    def test_returns_none_for_missing_user(self):
        self.assertIsNone(format_user_display_name(None))
