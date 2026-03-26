import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from realworld.articles.models import Article

from .forms import SettingsForm, UserCreationForm

User = get_user_model()


class TestUserModel(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )
        self.assertEqual(user.email, "tester@gmail.com")
        self.assertTrue(user.check_password("testpass1"))

    def test_create_user_without_password(self):
        user = User.objects.create_user(
            "tester@gmail.com", name="Test User", password=None
        )
        self.assertEqual(user.email, "tester@gmail.com")
        self.assertTrue(user.password)
        self.assertFalse(user.check_password("testpass1"))

    def test_get_full_name(self):
        self.assertEqual(User(name="Test User").get_full_name(), "Test User")

    def test_get_short_name(self):
        self.assertEqual(User(name="Test User").get_short_name(), "Test User")


class TestUserCreationForm(TestCase):
    form_data = {
        "name": "Tester",
        "email": "tester@gmail.com",
        "password": "testpass1",
    }

    def test_save(self):
        form = UserCreationForm(self.form_data)
        self.assertTrue(form.is_valid())

        user = form.save()
        self.assertTrue(user.check_password("testpass1"))


class TestFollowView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):

        cls.user = User(
            email="tester1@gmail.com",
            name="tester1",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(
            email="tester2@gmail.com",
            name="tester2",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

        cls.url = reverse("follow", args=[cls.user.id])

    def test_follow(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(self.user.followers.filter(pk=self.other_user.id).exists())

    def test_same_user(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        self.assertFalse(self.user.followers.filter(pk=self.user.id).exists())

    def test_unfollow(self):
        self.client.force_login(self.other_user)
        self.user.followers.add(self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertFalse(self.user.followers.filter(pk=self.other_user.id).exists())


class TestRegisterView(TestCase):
    url = reverse_lazy("register")

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_invalid(self):
        response = self.client.post(self.url, {"email": "invalid"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid(self):
        response = self.client.post(
            self.url,
            {
                "name": "Tester",
                "email": "tester@gmail.com",
                "password": "testpass1",
            },
        )
        self.assertEqual(response.headers["HX-Redirect"], reverse("home"))
        self.assertTrue(User.objects.filter(email="tester@gmail.com").exists())


class TestCheckEmailView(TestCase):
    url = reverse_lazy("check_email")

    def test_not_exists(self):
        response = self.client.get(self.url, {"email": "tester@gmail.com"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertNotContains(response, "Email is in use")

    def test_exists(self):
        User.objects.create_user(
            "tester@gmail.com", name="Test User", password="testpass1"
        )

        response = self.client.get(self.url, {"email": "tester@gmail.com"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "This email is in use")


class TestProfileView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="tester@gmail.com", name="tester")
        cls.user.set_password("testpass")
        cls.user.save()

        cls.article = Article.objects.create(
            title="test", summary="test", content="test", author=cls.user
        )
        cls.url = reverse("profile", args=[cls.user.id])

    def test_get_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["profile"], self.user)
        self.assertFalse(response.context["favorites"])

    def test_get_profile_favorites_filter(self):
        response = self.client.get(self.url + "?favorites")
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["favorites"])

    def test_profile_not_found(self):
        response = self.client.get(reverse("profile", args=[9999]))
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestSettingsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="tester@gmail.com", name="tester")
        cls.user.set_password("testpass")
        cls.user.save()
        cls.url = reverse("settings")

    def setUp(self):
        self.client.force_login(self.user)

    def test_get_settings(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid_settings(self):
        response = self.client.post(self.url, {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "My bio",
        })
        self.assertEqual(response.headers["HX-Redirect"], self.user.get_absolute_url())
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@gmail.com")

    def test_post_invalid_settings(self):
        response = self.client.post(self.url, {"email": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)


class TestSettingsForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="tester@gmail.com", name="tester")
        cls.user.set_password("testpass")
        cls.user.save()

    def test_save_with_password(self):
        form = SettingsForm(
            {"email": "tester@gmail.com", "name": "tester", "password": "newpass123"},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("newpass123"))

    def test_save_without_password(self):
        form = SettingsForm(
            {"email": "tester@gmail.com", "name": "tester", "password": ""},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("testpass"))
