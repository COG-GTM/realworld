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


class TestSettingsForm(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="testuser@example.com",
            name="Test User",
            password="oldpassword123"
        )

    def test_all_fields_filled(self):
        form_data = {
            "email": "updated@example.com",
            "name": "Updated Name",
            "bio": "This is my updated bio",
            "image": "https://example.com/avatar.jpg",
            "password": "newpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, "updated@example.com")
        self.assertEqual(updated_user.name, "Updated Name")
        self.assertEqual(updated_user.bio, "This is my updated bio")
        self.assertEqual(updated_user.image, "https://example.com/avatar.jpg")
        self.assertTrue(updated_user.check_password("newpassword123"))

    def test_partial_fields_filled(self):
        form_data = {
            "email": "partial@example.com",
            "name": "Partial Name",
            "bio": "",
            "image": "",
            "password": "",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, "partial@example.com")
        self.assertEqual(updated_user.name, "Partial Name")
        self.assertEqual(updated_user.bio, "")
        self.assertIsNone(updated_user.image)
        self.assertTrue(updated_user.check_password("oldpassword123"))

    def test_valid_form_uncommitted_save(self):
        form_data = {
            "email": "uncommitted@example.com",
            "name": "Uncommitted Name",
            "bio": "Uncommitted bio",
            "image": "https://example.com/uncommitted.jpg",
            "password": "uncommittedpass123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save(commit=False)
        self.assertEqual(updated_user.email, "uncommitted@example.com")
        self.assertEqual(updated_user.name, "Uncommitted Name")
        self.assertEqual(updated_user.bio, "Uncommitted bio")
        self.assertEqual(updated_user.image, "https://example.com/uncommitted.jpg")
        self.assertTrue(updated_user.check_password("uncommittedpass123"))
        
        db_user = User.objects.get(pk=self.user.pk)
        self.assertEqual(db_user.email, "testuser@example.com")
        self.assertTrue(db_user.check_password("oldpassword123"))


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
