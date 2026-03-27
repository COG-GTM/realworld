import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy

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

    def test_get_absolute_url(self):
        user = User.objects.create_user(
            "testurl@example.com", name="URL User", password="testpass1"
        )
        self.assertEqual(user.get_absolute_url(), reverse("profile", args=[user.id]))


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
        cls.user = User.objects.create_user(
            "profile@example.com", name="Profile User", password="testpass1"
        )
        cls.other_user = User.objects.create_user(
            "other@example.com", name="Other User", password="testpass1"
        )
        cls.url = reverse("profile", args=[cls.user.id])

    def test_get_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, self.user.name)

    def test_get_other_profile(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_get_profile_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_profile_not_found(self):
        url = reverse("profile", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

    def test_profile_with_favorites_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url + "?favorites")
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_profile_shows_following_status(self):
        self.user.followers.add(self.other_user)
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)


class TestSettingsView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "settings@example.com", name="Settings User", password="testpass1"
        )
        cls.url = reverse("settings")

    def test_get_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_get_authenticated(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid_update_name(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "name": "New Name",
                "bio": "",
                "image": "",
                "password": "",
            },
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "New Name")

    def test_post_valid_update_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "name": self.user.name,
                "bio": "",
                "image": "",
                "password": "newpassword123",
            },
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

    def test_post_invalid_email(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "email": "",
                "name": "",
                "bio": "",
                "image": "",
                "password": "",
            },
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)


class TestSettingsForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            "form@example.com", name="Form User", password="testpass1"
        )

    def test_save_without_password(self):
        form = SettingsForm(
            {
                "email": "new@example.com",
                "name": "New",
                "bio": "",
                "image": "",
                "password": "",
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.check_password("testpass1"))

    def test_save_with_password(self):
        form = SettingsForm(
            {
                "email": "form@example.com",
                "name": "Form User",
                "bio": "",
                "image": "",
                "password": "newpass456",
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("newpass456"))

    def test_invalid_email(self):
        form = SettingsForm(
            {
                "email": "not-an-email",
                "name": "",
                "bio": "",
                "image": "",
                "password": "",
            },
            instance=self.user,
        )
        self.assertFalse(form.is_valid())
