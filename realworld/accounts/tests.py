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
    password = "testpass1"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="profile@gmail.com", name="ProfileUser")
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(email="other@gmail.com", name="OtherUser")
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

    def test_get_profile(self):
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["profile"], self.user)
        self.assertIn("articles", response.context)

    def test_get_profile_not_found(self):
        url = reverse("profile", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

    def test_profile_with_articles(self):
        article = Article.objects.create(
            title="Test Article",
            summary="Summary",
            content="Content",
            author=self.user,
        )
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn(article, response.context["articles"])

    def test_profile_favorites_filter(self):
        article = Article.objects.create(
            title="Fav Article",
            summary="Summary",
            content="Content",
            author=self.user,
        )
        article.favorites.add(self.other_user)

        unfav_article = Article.objects.create(
            title="Unfav Article",
            summary="Summary",
            content="Content",
            author=self.user,
        )

        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url, {"favorites": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["favorites"])
        articles = list(response.context["articles"])
        self.assertIn(article, articles)
        self.assertNotIn(unfav_article, articles)

    def test_profile_is_following_true(self):
        self.user.followers.add(self.other_user)
        self.client.force_login(self.other_user)
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertTrue(response.context["is_following"])

    def test_profile_is_following_false(self):
        self.client.force_login(self.other_user)
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertFalse(response.context["is_following"])

    def test_profile_anonymous(self):
        url = reverse("profile", args=[self.user.id])
        response = self.client.get(url)
        self.assertFalse(response.context["is_following"])


class TestSettingsView(TestCase):
    password = "testpass1"
    url = reverse_lazy("settings")

    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="settings@gmail.com", name="SettingsUser")
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_get_settings(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)

    def test_get_settings_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_post_settings_valid(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "name": "Updated Name",
                "email": "updated@gmail.com",
                "bio": "New bio",
            },
        )
        self.assertIn("HX-Redirect", response.headers)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.email, "updated@gmail.com")
        self.assertEqual(self.user.bio, "New bio")

    def test_post_settings_invalid(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "name": "Updated Name",
                "email": "",
            },
        )
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["form"].errors)

    def test_post_settings_with_password(self):
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "name": self.user.name,
                "email": self.user.email,
                "password": "newpass123",
            },
        )
        self.assertIn("HX-Redirect", response.headers)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))

    def test_post_settings_without_password(self):
        self.client.force_login(self.user)
        old_password = self.user.password
        response = self.client.post(
            self.url,
            {
                "name": self.user.name,
                "email": self.user.email,
            },
        )
        self.assertIn("HX-Redirect", response.headers)
        self.user.refresh_from_db()
        self.assertEqual(self.user.password, old_password)


class TestSettingsForm(TestCase):
    password = "testpass1"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(email="formuser@gmail.com", name="FormUser")
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_save_with_password(self):
        form = SettingsForm(
            {"email": self.user.email, "name": self.user.name, "password": "newpass1"},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("newpass1"))

    def test_save_without_password(self):
        old_password = self.user.password
        form = SettingsForm(
            {"email": self.user.email, "name": self.user.name},
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.password, old_password)

    def test_save_updates_fields(self):
        form = SettingsForm(
            {
                "email": "newemail@gmail.com",
                "name": "New Name",
                "bio": "Updated bio",
            },
            instance=self.user,
        )
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "newemail@gmail.com")
        self.assertEqual(user.name, "New Name")
        self.assertEqual(user.bio, "Updated bio")


class TestUserAbsoluteUrl(TestCase):
    def test_get_absolute_url(self):
        user = User.objects.create_user(
            "urluser@gmail.com", name="UrlUser", password="testpass1"
        )
        expected = reverse("profile", args=[user.id])
        self.assertEqual(user.get_absolute_url(), expected)
