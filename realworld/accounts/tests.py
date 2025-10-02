import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from .forms import UserCreationForm

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
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        from realworld.articles.models import Article

        cls.user = User(
            email="author@test.com",
            name="Author",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(
            email="other@test.com",
            name="Other",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="Test Article",
            summary="Summary",
            content="Body",
            author=cls.user,
        )

        cls.url = reverse("profile", args=[cls.user.id])

    def test_profile_view_displays_user_articles(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Test Article")
        self.assertIn("articles", response.context)

    def test_profile_view_with_favorites_filter(self):
        from realworld.articles.models import Article

        article_with_fav = Article.objects.create(
            title="Popular",
            summary="Sum",
            content="Body",
            author=self.user,
        )
        Article.objects.create(
            title="Unpopular",
            summary="Sum",
            content="Body",
            author=self.user,
        )

        article_with_fav.favorites.add(self.other_user)

        response = self.client.get(self.url + "?favorites")

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["favorites"])
        self.assertContains(response, "Popular")

    def test_profile_view_shows_following_status(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("profile", args=[self.other_user.id]))
        self.assertFalse(response.context["is_following"])

        self.other_user.followers.add(self.user)

        response = self.client.get(reverse("profile", args=[self.other_user.id]))
        self.assertTrue(response.context["is_following"])


class TestSettingsView(TestCase):
    password = "testpass"
    url = reverse_lazy("settings")

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="user@test.com",
            name="User",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_settings_view_get_displays_form(self):
        from .forms import SettingsForm

        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], SettingsForm)

    def test_settings_view_post_with_valid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "email": "updated@test.com",
                "name": "Updated Name",
                "bio": "My new bio",
                "image": "",
                "password": "",
            },
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@test.com")
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.bio, "My new bio")

    def test_settings_view_post_with_invalid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "email": "not-an-email",
                "name": "",
                "bio": "",
                "image": "",
                "password": "",
            },
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)


class TestSettingsForm(TestCase):
    def test_settings_form_updates_password_when_provided(self):
        from .forms import SettingsForm

        user = User.objects.create_user(
            "user@test.com", name="User", password="oldpass"
        )

        form = SettingsForm(
            data={
                "email": "user@test.com",
                "name": "User",
                "bio": "",
                "image": "",
                "password": "newpass123",
            },
            instance=user,
        )

        self.assertTrue(form.is_valid())
        updated_user = form.save()

        self.assertTrue(updated_user.check_password("newpass123"))
        self.assertFalse(updated_user.check_password("oldpass"))

    def test_settings_form_does_not_update_password_when_empty(self):
        from .forms import SettingsForm

        user = User.objects.create_user(
            "user@test.com", name="User", password="oldpass"
        )

        form = SettingsForm(
            data={
                "email": "newemail@test.com",
                "name": "New Name",
                "bio": "New bio",
                "image": "",
                "password": "",
            },
            instance=user,
        )

        self.assertTrue(form.is_valid())
        updated_user = form.save()

        self.assertTrue(updated_user.check_password("oldpass"))
