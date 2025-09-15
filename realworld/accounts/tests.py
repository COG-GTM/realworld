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


class TestSettingsForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="Test User",
            bio="Test bio",
            image="https://example.com/image.jpg"
        )
        cls.user.set_password("testpass")
        cls.user.save()

        cls.other_user = User(
            email="other@gmail.com",
            name="Other User"
        )
        cls.other_user.set_password("testpass")
        cls.other_user.save()

    def test_valid_form_all_fields(self):
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "https://example.com/updated.jpg",
            "password": "newpass123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_form_minimal_fields(self):
        form_data = {
            "email": "minimal@gmail.com",
            "name": "Minimal Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_email_format(self):
        form_data = {
            "email": "invalid-email",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email_validation(self):
        form_data = {
            "email": "other@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_required_field_validation_email(self):
        form_data = {
            "email": "",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_required_field_validation_name(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_optional_password_field_empty(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_optional_password_field_provided(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": "newpass123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_form_save_updates_all_fields(self):
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "https://example.com/updated.jpg",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, "updated@gmail.com")
        self.assertEqual(updated_user.name, "Updated Name")
        self.assertEqual(updated_user.bio, "Updated bio")
        self.assertEqual(updated_user.image, "https://example.com/updated.jpg")

    def test_form_save_password_hashed_when_provided(self):
        original_password = self.user.password
        form_data = {
            "email": "test@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": "newpass123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertNotEqual(updated_user.password, original_password)
        self.assertTrue(updated_user.check_password("newpass123"))

    def test_form_save_password_unchanged_when_empty(self):
        original_password = self.user.password
        form_data = {
            "email": "test@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.password, original_password)
        self.assertTrue(updated_user.check_password("testpass"))


class TestSettingsView(TestCase):
    url = reverse_lazy("settings")
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="Test User",
            bio="Test bio",
            image="https://example.com/image.jpg"
        )
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_get_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Your Settings")
        self.assertIsInstance(response.context["form"], SettingsForm)
        self.assertEqual(response.context["form"].instance, self.user)

    def test_get_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_post_valid_data_saves_and_redirects(self):
        self.client.force_login(self.user)
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "https://example.com/updated.jpg",
            "password": ""
        }
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.headers["HX-Redirect"], self.user.get_absolute_url())
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "updated@gmail.com")
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.bio, "Updated bio")
        self.assertEqual(self.user.image, "https://example.com/updated.jpg")

    def test_post_invalid_data_returns_form_with_errors(self):
        self.client.force_login(self.user)
        form_data = {
            "email": "invalid-email",
            "name": "",
            "bio": "",
            "image": "",
            "password": ""
        }
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(response, "accounts/_settings.html")
        self.assertIsInstance(response.context["form"], SettingsForm)
        self.assertFalse(response.context["form"].is_valid())

    def test_post_unauthenticated_user(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test Name",
            "bio": "",
            "image": "",
            "password": ""
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)


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
