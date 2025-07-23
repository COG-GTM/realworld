import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from realworld.articles.models import Article
from realworld.comments.models import Comment

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


class TestSettingsView(TestCase):
    password = "testpass"
    url = reverse_lazy("settings")

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="tester",
            bio="Original bio",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

    def setUp(self):
        self.client.force_login(self.user)

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "tester")
        self.assertContains(response, "Original bio")

    def test_get_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_post_valid(self):
        response = self.client.post(self.url, {
            "name": "Updated Name",
            "email": "updated@gmail.com",
            "bio": "Updated bio",
            "image": "",
        })
        
        self.assertEqual(response.headers["HX-Redirect"], self.user.get_absolute_url())
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Updated Name")
        self.assertEqual(self.user.email, "updated@gmail.com")
        self.assertEqual(self.user.bio, "Updated bio")

    def test_post_invalid_email(self):
        response = self.client.post(self.url, {
            "name": "Updated Name",
            "email": "invalid-email",
            "bio": "Updated bio",
            "image": "",
        })
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Enter a valid email address")
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "tester@gmail.com")


class TestLoginEdgeCases(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            email="tester@gmail.com",
            name="tester",
            password=cls.password
        )

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": "tester@gmail.com",
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Please enter a correct")

    def test_login_nonexistent_user(self):
        response = self.client.post(reverse("login"), {
            "username": "nonexistent@gmail.com",
            "password": "testpass"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Please enter a correct")

    def test_login_empty_credentials(self):
        response = self.client.post(reverse("login"), {
            "username": "",
            "password": ""
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "This field is required")


class TestProfileView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="tester@gmail.com",
            name="tester",
            bio="Test bio",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(
            email="other@gmail.com",
            name="other",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="Test Article",
            summary="Test summary",
            content="Test content",
            author=cls.user,
        )

        cls.url = reverse("profile", args=[cls.user.id])

    def test_get_own_profile(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["profile"], self.user)
        self.assertContains(response, "tester")
        self.assertContains(response, "Test bio")

    def test_get_other_profile(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["profile"], self.user)
        self.assertContains(response, "tester")

    def test_get_profile_anonymous(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["profile"], self.user)

    def test_get_nonexistent_profile(self):
        url = reverse("profile", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestHTMXIntegration(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.author = User(
            email="author@gmail.com",
            name="author",
        )
        cls.author.set_password(cls.password)
        cls.author.save()

        cls.user = User(
            email="user@gmail.com",
            name="user",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.article = Article.objects.create(
            title="Test Article",
            summary="Test summary",
            content="Test content",
            author=cls.author,
        )

    def test_favorite_htmx_target_specific(self):
        self.client.force_login(self.user)
        url = reverse("favorite", args=[self.article.id])
        
        response = self.client.post(
            url, 
            HTTP_HX_TARGET=f"favorite-{self.article.id}"
        )
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["is_favorite"])
        self.assertFalse(response.context["is_detail"])

    def test_favorite_htmx_out_of_band(self):
        self.client.force_login(self.user)
        url = reverse("favorite", args=[self.article.id])
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["is_favorite"])
        self.assertTrue(response.context["is_detail"])

    def test_register_htmx_redirect(self):
        response = self.client.post(reverse("register"), {
            "name": "New User",
            "email": "newuser@gmail.com",
            "password": "testpass1",
        })
        
        self.assertEqual(response.headers["HX-Redirect"], reverse("home"))

    def test_article_creation_htmx_redirect(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("create_article"), {
            "title": "HTMX Test Article",
            "summary": "test summary",
            "content": "test content",
            "tags": "htmx test"
        })
        
        article = Article.objects.get(title="HTMX Test Article")
        self.assertEqual(response.headers["HX-Redirect"], article.get_absolute_url())


class TestIntegrationWorkflows(TestCase):
    password = "testpass"

    def test_complete_user_journey(self):
        register_response = self.client.post(reverse("register"), {
            "name": "Journey User",
            "email": "journey@gmail.com",
            "password": "testpass1",
        })
        self.assertEqual(register_response.headers["HX-Redirect"], reverse("home"))
        
        user = User.objects.get(email="journey@gmail.com")
        self.client.force_login(user)
        
        create_response = self.client.post(reverse("create_article"), {
            "title": "My First Article",
            "summary": "This is my first article",
            "content": "# Hello World\n\nThis is my first article content.",
            "tags": "first blog"
        })
        
        article = Article.objects.get(title="My First Article")
        self.assertEqual(create_response.headers["HX-Redirect"], article.get_absolute_url())
        
        other_user = User.objects.create_user(
            email="commenter@gmail.com",
            name="Commenter",
            password="testpass1"
        )
        self.client.force_login(other_user)
        
        comment_response = self.client.post(
            reverse("add_comment", args=[article.id]),
            {"content": "Great article!"}
        )
        self.assertEqual(comment_response.status_code, http.HTTPStatus.OK)
        
        comment = Comment.objects.get(content="Great article!")
        self.assertEqual(comment.author, other_user)
        self.assertEqual(comment.article, article)
        
        self.client.force_login(user)
        edit_response = self.client.post(
            reverse("edit_article", args=[article.id]),
            {
                "title": "My Updated First Article",
                "summary": "This is my updated first article",
                "content": "# Hello Updated World\n\nThis is my updated article content.",
                "tags": "first blog updated"
            }
        )
        
        article.refresh_from_db()
        self.assertEqual(article.title, "My Updated First Article")
        self.assertEqual(edit_response.headers["HX-Redirect"], article.get_absolute_url())

    def test_permission_edge_cases(self):
        author = User.objects.create_user(
            email="author@gmail.com",
            name="Author",
            password="testpass1"
        )
        
        unauthorized_user = User.objects.create_user(
            email="unauthorized@gmail.com",
            name="Unauthorized",
            password="testpass1"
        )
        
        article = Article.objects.create(
            title="Protected Article",
            summary="Protected summary",
            content="Protected content",
            author=author,
        )
        
        comment = Comment.objects.create(
            content="Protected comment",
            author=author,
            article=article,
        )
        
        self.client.force_login(unauthorized_user)
        
        edit_article_response = self.client.get(reverse("edit_article", args=[article.id]))
        self.assertEqual(edit_article_response.status_code, http.HTTPStatus.NOT_FOUND)
        
        delete_article_response = self.client.delete(reverse("delete_article", args=[article.id]))
        self.assertEqual(delete_article_response.status_code, http.HTTPStatus.NOT_FOUND)
        
        edit_comment_response = self.client.get(reverse("edit_comment", args=[comment.id]))
        self.assertEqual(edit_comment_response.status_code, http.HTTPStatus.NOT_FOUND)
        
        delete_comment_response = self.client.delete(reverse("delete_comment", args=[comment.id]))
        self.assertEqual(delete_comment_response.status_code, http.HTTPStatus.NOT_FOUND)
        
        favorite_own_article_response = self.client.post(reverse("favorite", args=[article.id]))
        self.assertEqual(favorite_own_article_response.status_code, http.HTTPStatus.OK)

    def test_cross_model_interactions(self):
        user1 = User.objects.create_user(
            email="user1@gmail.com",
            name="User One",
            password="testpass1"
        )
        
        user2 = User.objects.create_user(
            email="user2@gmail.com",
            name="User Two",
            password="testpass1"
        )
        
        article = Article.objects.create(
            title="Interactive Article",
            summary="Test summary",
            content="Test content",
            author=user1,
        )
        
        self.client.force_login(user2)
        
        follow_response = self.client.post(reverse("follow", args=[user1.id]))
        self.assertEqual(follow_response.status_code, http.HTTPStatus.OK)
        self.assertTrue(user1.followers.filter(pk=user2.id).exists())
        
        favorite_response = self.client.post(reverse("favorite", args=[article.id]))
        self.assertEqual(favorite_response.status_code, http.HTTPStatus.OK)
        self.assertTrue(article.favorites.filter(pk=user2.id).exists())
        
        comment_response = self.client.post(
            reverse("add_comment", args=[article.id]),
            {"content": "Great work from someone I follow!"}
        )
        self.assertEqual(comment_response.status_code, http.HTTPStatus.OK)
        
        comment = Comment.objects.get(content="Great work from someone I follow!")
        self.assertEqual(comment.author, user2)
        self.assertEqual(comment.article, article)
        
        unfollow_response = self.client.delete(reverse("follow", args=[user1.id]))
        self.assertEqual(unfollow_response.status_code, http.HTTPStatus.OK)
        self.assertFalse(user1.followers.filter(pk=user2.id).exists())
        
        unfavorite_response = self.client.delete(reverse("favorite", args=[article.id]))
        self.assertEqual(unfavorite_response.status_code, http.HTTPStatus.OK)
        self.assertFalse(article.favorites.filter(pk=user2.id).exists())
