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


class TestSettingsForm(TestCase):
    """Tests for the SettingsForm used in user profile settings."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "tester@gmail.com",
            name="Test User",
            password="testpass1",
        )
        cls.user.bio = "Original bio"
        cls.user.image = "https://example.com/image.jpg"
        cls.user.save()

    def setUp(self):
        self.user.refresh_from_db()

    # Form Validation Tests

    def test_valid_form_with_all_fields(self):
        """Test form is valid with all fields provided."""
        form_data = {
            "email": "newemail@gmail.com",
            "name": "New Name",
            "bio": "New bio content",
            "image": "https://example.com/newimage.jpg",
            "password": "newpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_new_password(self):
        """Test form is valid when updating password."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "brandnewpass123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_partial_data(self):
        """Test form is valid with only some fields updated."""
        form_data = {
            "email": self.user.email,
            "name": "Updated Name Only",
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_valid_form_with_empty_optional_fields(self):
        """Test form is valid with empty bio and image fields."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": "",
            "image": "",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_invalid_email_format(self):
        """Test form is invalid with malformed email."""
        form_data = {
            "email": "not-an-email",
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_email(self):
        """Test form is invalid when email is already used by another user."""
        User.objects.create_user(
            "other@gmail.com",
            name="Other User",
            password="testpass1",
        )
        form_data = {
            "email": "other@gmail.com",
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_accepts_any_value(self):
        """Test form accepts any password value (no validation on form level).

        Note: The SettingsForm does not validate passwords using Django's
        password validators. It only displays help text from the validators.
        Password validation would need to be added to the form's clean method
        if stricter validation is required.
        """
        # Short password is accepted
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "short",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        # All-numeric password is accepted
        form_data["password"] = "12345678"
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

        # Common password is accepted
        form_data["password"] = "password"
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    # Password Field Specific Tests

    def test_password_field_is_optional(self):
        """Test form is valid without providing a password."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_password_updated_when_provided(self):
        """Test password is updated when a new password is provided."""
        original_password = self.user.password
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "newvalidpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertNotEqual(user.password, original_password)
        self.assertTrue(user.check_password("newvalidpassword123"))

    def test_password_not_changed_when_empty(self):
        """Test password is NOT changed when password field is empty."""
        original_password = self.user.password
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.password, original_password)
        self.assertTrue(user.check_password("testpass1"))

    def test_password_changed_when_whitespace(self):
        """Test password IS changed when password field contains whitespace.

        Note: The password field has strip=False, so whitespace is preserved
        and treated as a valid (non-empty) password value.
        """
        original_password = self.user.password
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "   ",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        # Password field has strip=False, so whitespace is treated as a password
        self.assertNotEqual(user.password, original_password)
        self.assertTrue(user.check_password("   "))

    # Field-Specific Tests

    def test_email_uniqueness_validation(self):
        """Test that email must be unique across users."""
        User.objects.create_user(
            "unique@gmail.com",
            name="Unique User",
            password="testpass1",
        )
        form_data = {
            "email": "unique@gmail.com",
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_can_keep_same_value(self):
        """Test user can keep their own email without uniqueness error."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_name_field_with_various_inputs(self):
        """Test name field accepts various valid inputs."""
        test_names = ["John Doe", "A", "Name With Numbers 123", "Name-With-Dashes"]
        for name in test_names:
            form_data = {
                "email": self.user.email,
                "name": name,
                "bio": self.user.bio,
                "image": self.user.image,
            }
            form = SettingsForm(form_data, instance=self.user)
            self.assertTrue(form.is_valid(), f"Name '{name}' should be valid")

    def test_bio_field_with_long_content(self):
        """Test bio field accepts long content."""
        long_bio = "A" * 1000
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": long_bio,
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_bio_field_with_empty_value(self):
        """Test bio field accepts empty value."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": "",
            "image": self.user.image,
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_image_field_with_valid_url(self):
        """Test image field accepts valid URLs."""
        valid_urls = [
            "https://example.com/image.jpg",
            "http://example.com/image.png",
            "https://cdn.example.com/path/to/image.gif",
        ]
        for url in valid_urls:
            form_data = {
                "email": self.user.email,
                "name": self.user.name,
                "bio": self.user.bio,
                "image": url,
            }
            form = SettingsForm(form_data, instance=self.user)
            self.assertTrue(form.is_valid(), f"URL '{url}' should be valid")

    def test_image_field_with_invalid_url(self):
        """Test image field rejects invalid URLs."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": "not-a-valid-url",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)

    def test_image_field_with_empty_value(self):
        """Test image field accepts empty value."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": "",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())

    # Model Integration Tests

    def test_save_with_commit_true(self):
        """Test save() method with commit=True (default) persists to database."""
        form_data = {
            "email": "saved@gmail.com",
            "name": "Saved User",
            "bio": "Saved bio",
            "image": "https://example.com/saved.jpg",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        form.save()

        # Verify changes are persisted
        user_from_db = User.objects.get(pk=self.user.pk)
        self.assertEqual(user_from_db.email, "saved@gmail.com")
        self.assertEqual(user_from_db.name, "Saved User")
        self.assertEqual(user_from_db.bio, "Saved bio")
        self.assertEqual(user_from_db.image, "https://example.com/saved.jpg")

    def test_save_with_commit_false(self):
        """Test save() method with commit=False does not persist to database."""
        form_data = {
            "email": "notsaved@gmail.com",
            "name": "Not Saved User",
            "bio": "Not saved bio",
            "image": "https://example.com/notsaved.jpg",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save(commit=False)

        # Verify changes are NOT persisted
        user_from_db = User.objects.get(pk=self.user.pk)
        self.assertNotEqual(user_from_db.email, "notsaved@gmail.com")
        self.assertEqual(user_from_db.email, "tester@gmail.com")

        # But the returned user object has the new values
        self.assertEqual(user.email, "notsaved@gmail.com")

    def test_password_is_properly_hashed_when_updated(self):
        """Test that password is properly hashed when updated via save()."""
        form_data = {
            "email": self.user.email,
            "name": self.user.name,
            "bio": self.user.bio,
            "image": self.user.image,
            "password": "newhashedpassword123",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()

        # Password should be hashed, not stored as plain text
        self.assertNotEqual(user.password, "newhashedpassword123")
        self.assertTrue(user.check_password("newhashedpassword123"))
        # Verify it's a proper hash (starts with algorithm identifier)
        self.assertTrue(
            user.password.startswith("pbkdf2_sha256$")
            or user.password.startswith("argon2")
            or user.password.startswith("bcrypt")
        )

    def test_other_fields_saved_correctly(self):
        """Test that all non-password fields are saved correctly."""
        form_data = {
            "email": "updated@gmail.com",
            "name": "Updated Name",
            "bio": "Updated bio content",
            "image": "https://example.com/updated.jpg",
        }
        form = SettingsForm(form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()

        self.assertEqual(user.email, "updated@gmail.com")
        self.assertEqual(user.name, "Updated Name")
        self.assertEqual(user.bio, "Updated bio content")
        self.assertEqual(user.image, "https://example.com/updated.jpg")


class TestSettingsView(TestCase):
    """Tests for the settings view function."""

    password = "testpass1"
    url = reverse_lazy("settings")

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "tester@gmail.com",
            name="Test User",
            password=cls.password,
        )
        cls.user.bio = "Original bio"
        cls.user.image = "https://example.com/image.jpg"
        cls.user.save()

    def test_get_returns_form_with_user_data(self):
        """Test GET request returns form pre-filled with user data."""
        self.client.force_login(self.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.name)

    def test_post_valid_redirects_to_profile(self):
        """Test POST with valid form redirects to user profile."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "email": self.user.email,
                "name": "Updated Name",
                "bio": self.user.bio,
                "image": self.user.image,
            },
        )

        self.assertEqual(
            response.headers.get("HX-Redirect"), self.user.get_absolute_url()
        )

    def test_post_invalid_returns_errors(self):
        """Test POST with invalid form returns form with errors."""
        self.client.force_login(self.user)
        response = self.client.post(
            self.url,
            {
                "email": "invalid-email",
                "name": self.user.name,
                "bio": self.user.bio,
                "image": self.user.image,
            },
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Enter a valid email address")

    def test_unauthenticated_user_redirected(self):
        """Test unauthenticated users are redirected to login."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        self.assertIn("/login/", response.url)
