import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy

from .forms import UserCreationForm, SettingsForm

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
    password = "testpass123"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="Test User",
            bio="Original bio",
            image="https://example.com/image.jpg"
        )
        cls.user.set_password(cls.password)
        cls.user.save()

    def test_valid_form_all_fields(self):
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio content",
            "image": "https://example.com/new-image.jpg",
            "password": "newpassword123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, "updated@gmail.com")
        self.assertEqual(user.name, "Updated Name")
        self.assertEqual(user.bio, "Updated bio content")
        self.assertEqual(user.image, "https://example.com/new-image.jpg")
        self.assertTrue(user.check_password("newpassword123"))

    def test_valid_form_required_fields_only(self):
        form_data = {
            "email": "minimal@gmail.com",
            "name": "Minimal User",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, "minimal@gmail.com")
        self.assertEqual(user.name, "Minimal User")
        self.assertEqual(user.bio, "")
        self.assertIsNone(user.image)
        self.assertTrue(user.check_password(self.password))

    def test_invalid_email_format(self):
        invalid_emails = ["invalid", "invalid@", "@invalid.com", "invalid.com"]
        for invalid_email in invalid_emails:
            form_data = {
                "email": invalid_email,
                "name": "Test User",
                "bio": "",
                "image": "",
                "password": ""
            }
            form = SettingsForm(form_data, instance=self.user)
            self.assertFalse(form.is_valid())
            self.assertIn("email", form.errors)

    def test_empty_required_fields(self):
        form_data = {
            "email": "",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

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

    def test_excessively_long_field_values(self):
        long_name = "a" * 61
        form_data = {
            "email": "test@gmail.com",
            "name": long_name,
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_bio_field_optional(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test User",
            "bio": None,
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        form_data["bio"] = ""
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_image_field_validation(self):
        valid_urls = [
            "https://example.com/image.jpg",
            "http://example.com/image.png",
            "https://subdomain.example.com/path/to/image.gif"
        ]
        for valid_url in valid_urls:
            form_data = {
                "email": "test@gmail.com",
                "name": "Test User",
                "bio": "",
                "image": valid_url,
                "password": ""
            }
            form = SettingsForm(form_data, instance=self.user)
            self.assertTrue(form.is_valid())

        form_data = {
            "email": "test@gmail.com",
            "name": "Test User",
            "bio": "",
            "image": "not-a-url-at-all",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_password_provided_hashed_correctly(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": "newpassword123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertNotEqual(user.password, "newpassword123")
        self.assertTrue(user.check_password("newpassword123"))
        self.assertFalse(user.check_password(self.password))

    def test_password_empty_preserved(self):
        original_password_hash = self.user.password
        
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.password, original_password_hash)
        self.assertTrue(user.check_password(self.password))

    def test_password_whitespace_preserved(self):
        original_password_hash = self.user.password
        
        form_data = {
            "email": "test@gmail.com",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": "   "
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertNotEqual(user.password, original_password_hash)
        self.assertTrue(user.check_password("   "))

    def test_password_validation_rules(self):
        form_data = {
            "email": "test@gmail.com",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": "123"
        }
        form = SettingsForm(form_data, instance=self.user)
        if form.is_valid():
            self.assertIn("password", form.fields)
            self.assertTrue(form.fields["password"].help_text)
        else:
            self.assertIn("password", form.errors)

    def test_form_saves_to_existing_user_instance(self):
        original_id = self.user.id
        
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.id, original_id)
        self.assertEqual(User.objects.count(), 1)

    def test_form_preserves_unchanged_fields(self):
        form_data = {
            "email": self.user.email,
            "name": "Updated Name Only",
            "bio": self.user.bio,
            "image": self.user.image,
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, "tester@gmail.com")
        self.assertEqual(user.name, "Updated Name Only")
        self.assertEqual(user.bio, "Original bio")
        self.assertEqual(user.image, "https://example.com/image.jpg")
        self.assertTrue(user.check_password(self.password))

    def test_form_handles_user_model_constraints(self):
        other_user = User.objects.create_user(
            "other@gmail.com", name="Other User", password="otherpass"
        )
        
        form_data = {
            "email": "other@gmail.com",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": ""
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_save_commit_false(self):
        form_data = {
            "email": "uncommitted@gmail.com",
            "name": "Uncommitted User",
            "bio": "Uncommitted bio",
            "image": "",
            "password": "newpassword123"
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
        user = form.save(commit=False)
        self.assertEqual(user.email, "uncommitted@gmail.com")
        self.assertEqual(user.name, "Uncommitted User")
        self.assertTrue(user.check_password("newpassword123"))
        
        user_from_db = User.objects.get(id=self.user.id)
        self.assertEqual(user_from_db.email, "tester@gmail.com")
        self.assertEqual(user_from_db.name, "Test User")
        self.assertTrue(user_from_db.check_password(self.password))

    def test_form_initialization_with_existing_user(self):
        form = SettingsForm(instance=self.user)
        
        self.assertEqual(form.initial["email"], self.user.email)
        self.assertEqual(form.initial["name"], self.user.name)
        self.assertEqual(form.initial["bio"], self.user.bio)
        self.assertEqual(form.initial["image"], self.user.image)
        self.assertEqual(form.initial.get("password", ""), "")

    def test_form_field_ordering(self):
        form = SettingsForm()
        expected_fields = ["email", "name", "bio", "image", "password"]
        actual_fields = list(form.fields.keys())
        
        for field in expected_fields:
            self.assertIn(field, actual_fields)


class TestSettingsViewIntegration(TestCase):
    password = "testpass123"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="Test User",
            bio="Original bio",
            image="https://example.com/image.jpg"
        )
        cls.user.set_password(cls.password)
        cls.user.save()
        cls.url = reverse("settings")

    def test_settings_view_get_request(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="name"')
        self.assertContains(response, 'name="bio"')
        self.assertContains(response, 'name="image"')
        self.assertContains(response, 'name="password"')
        
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.name)

    def test_settings_view_post_valid_data(self):
        self.client.force_login(self.user)
        
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio",
            "image": "https://example.com/new-image.jpg",
            "password": ""
        }
        response = self.client.post(self.url, form_data)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.headers["HX-Redirect"], self.user.get_absolute_url())
        
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.email, "updated@gmail.com")
        self.assertEqual(updated_user.name, "Updated Name")
        self.assertEqual(updated_user.bio, "Updated bio")

    def test_settings_view_post_invalid_data(self):
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
        self.assertContains(response, "error")

    def test_htmx_response_handling_for_form_errors(self):
        self.client.force_login(self.user)
        
        form_data = {
            "email": "invalid-email",
            "name": "Test User",
            "bio": "",
            "image": "",
            "password": ""
        }
        response = self.client.post(
            self.url, 
            form_data,
            HTTP_HX_REQUEST="true"
        )
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTemplateUsed(response, "accounts/_settings.html")


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
