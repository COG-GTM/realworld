import http

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TestCase
from django.urls import reverse, reverse_lazy
from taggit.models import Tag

from .models import Article

User = get_user_model()


class TestArticleModel(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.author = User.objects.create(
            email="tester1@gmail.com", name="tester1", password="testpass"
        )

        cls.other_user = User.objects.create(
            email="tester2@gmail.com", name="tester2", password="testpass"
        )

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

    def test_with_favorites_anonymous_false(self):
        article = Article.objects.with_favorites(AnonymousUser()).first()
        self.assertEqual(article.num_favorites, 0)
        self.assertFalse(article.is_favorite)

    def test_with_favorites_anonymous_true(self):
        self.article.favorites.add(self.other_user)

        article = Article.objects.with_favorites(AnonymousUser()).first()
        self.assertEqual(article.num_favorites, 1)
        self.assertFalse(article.is_favorite)

    def test_with_favorites_same_user_false(self):
        article = Article.objects.with_favorites(self.author).first()
        self.assertEqual(article.num_favorites, 0)
        self.assertFalse(article.is_favorite)

    def test_with_favorites_same_user_true(self):
        self.article.favorites.add(self.other_user)

        article = Article.objects.with_favorites(self.author).first()
        self.assertEqual(article.num_favorites, 1)
        self.assertFalse(article.is_favorite)

    def test_with_favorites_other_user_false(self):
        article = Article.objects.with_favorites(self.other_user).first()
        self.assertEqual(article.num_favorites, 0)
        self.assertFalse(article.is_favorite)

    def test_with_favorites_other_user_true(self):
        self.article.favorites.add(self.other_user)

        article = Article.objects.with_favorites(self.other_user).first()
        self.assertEqual(article.num_favorites, 1)
        self.assertTrue(article.is_favorite)


class TestHomeView(TestCase):
    url = reverse_lazy("home")

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)


class TestCreateArticleView(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.set_password("testpass")
        cls.author.save()

        cls.url = reverse("create_article")

    def setUp(self):
        self.client.force_login(self.author)

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_invalid(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_invalid_missing_title(self):
        response = self.client.post(self.url, {
            "summary": "test summary",
            "content": "test content",
            "tags": "python"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "This field is required")

    def test_post_valid_missing_content(self):
        response = self.client.post(self.url, {
            "title": "Test Title",
            "summary": "test summary",
            "tags": "python"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        
        article = Article.objects.get(title="Test Title")
        self.assertEqual(article.author, self.author)
        self.assertEqual(article.summary, "test summary")
        self.assertEqual(article.content, "")

    def test_post_invalid_title_too_long(self):
        long_title = "x" * 121
        response = self.client.post(self.url, {
            "title": long_title,
            "summary": "test summary",
            "content": "test content",
            "tags": "python"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Ensure this value has at most 120 characters")

    def test_post_valid(self):
        response = self.client.post(
            self.url,
            {
                "title": "First Post",
                "summary": "test",
                "content": "test",
                "tags": "python django html",
            },
        )

        article = Article.objects.get()

        self.assertEqual(response.headers["HX-Redirect"], article.get_absolute_url())
        self.assertEqual(article.author, self.author)
        self.assertEqual(article.title, "First Post")
        self.assertEqual(set(article.tags.names()), {"python", "django", "html"})


class TestArticleDetailView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):

        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.set_password(cls.password)
        cls.author.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.url = cls.article.get_absolute_url()

    def test_get_is_anonymous(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["article"], self.article)
        self.assertNotIn("is_author", response.context)

    def test_get_is_author(self):
        self.client.force_login(self.author)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["article"], self.article)
        self.assertTrue(response.context["is_author"])


class TestFavoriteView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):

        cls.author = User(
            email="tester1@gmail.com",
            name="tester1",
        )
        cls.author.set_password(cls.password)
        cls.author.save()

        cls.other_user = User(
            email="tester2@gmail.com",
            name="tester2",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )
        cls.url = reverse("favorite", args=[cls.article.id])

    def test_add_favorite(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(self.article.favorites.filter(pk=self.other_user.id).exists())

        self.assertTrue(response.context["is_favorite"])
        self.assertTrue(response.context["is_detail"])

    def test_same_user(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        self.assertFalse(self.article.favorites.filter(pk=self.other_user.id).exists())

    def test_not_detail(self):
        self.client.force_login(self.other_user)
        response = self.client.post(
            self.url, HTTP_HX_TARGET=f"favorite-{self.article.id}"
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertTrue(self.article.favorites.filter(pk=self.other_user.id).exists())

        self.assertTrue(response.context["is_favorite"])
        self.assertFalse(response.context["is_detail"])

    def test_remove_favorite(self):
        self.client.force_login(self.other_user)

        self.article.favorites.add(self.other_user)

        response = self.client.delete(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertFalse(self.article.favorites.filter(pk=self.other_user.id).exists())

        self.assertFalse(response.context["is_favorite"])
        self.assertTrue(response.context["is_detail"])


class TestEditArticleView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.set_password(cls.password)
        cls.author.save()

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
            author=cls.author,
        )
        cls.article.tags.add("python", "django")

        cls.url = reverse("edit_article", args=[cls.article.id])

    def setUp(self):
        self.client.force_login(self.author)

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["article"], self.article)
        form = response.context["form"]
        self.assertEqual(form.instance, self.article)
        self.assertEqual(form.initial["title"], "Test Article")

    def test_get_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

    def test_get_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_get_nonexistent_article(self):
        url = reverse("edit_article", args=[99999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

    def test_post_valid(self):
        response = self.client.post(self.url, {
            "title": "Updated Title",
            "summary": "Updated summary",
            "content": "Updated content",
            "tags": "python django updated"
        })
        
        self.article.refresh_from_db()
        self.assertEqual(response.headers["HX-Redirect"], self.article.get_absolute_url())
        self.assertEqual(self.article.title, "Updated Title")
        self.assertEqual(self.article.summary, "Updated summary")
        self.assertEqual(self.article.content, "Updated content")
        self.assertEqual(set(self.article.tags.names()), {"python", "django", "updated"})

    def test_post_invalid(self):
        response = self.client.post(self.url, {
            "title": "",
            "summary": "Updated summary",
            "content": "Updated content",
            "tags": "python"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "This field is required")
        
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Test Article")

    def test_post_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url, {
            "title": "Hacked Title",
            "summary": "Hacked summary",
            "content": "Hacked content",
            "tags": "hacked"
        })
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        
        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Test Article")


class TestDeleteArticleView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.set_password(cls.password)
        cls.author.save()

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
            author=cls.author,
        )

        cls.url = reverse("delete_article", args=[cls.article.id])

    def setUp(self):
        self.client.force_login(self.author)

    def test_delete_success(self):
        article_id = self.article.id
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        self.assertEqual(response.url, reverse("home"))
        self.assertFalse(Article.objects.filter(id=article_id).exists())

    def test_delete_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        self.assertTrue(Article.objects.filter(id=self.article.id).exists())

    def test_delete_not_authenticated(self):
        self.client.logout()
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        self.assertTrue(Article.objects.filter(id=self.article.id).exists())

    def test_delete_nonexistent_article(self):
        url = reverse("delete_article", args=[99999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestTagsAutocomplete(TestCase):
    url = reverse_lazy("tags_autocomplete")

    @classmethod
    def setUpTestData(cls):
        Tag.objects.create(name="Python")

    def test_with_tags(self):
        response = self.client.get(self.url, {"tags": "Python"})
        self.assertEqual(len(response.context["tags"]), 1)

    def test_with_no_tags(self):
        response = self.client.get(self.url, {"tags": "Django"})
        self.assertEqual(len(response.context["tags"]), 0)

    def test_empty_query_string(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["tags"]), 0)
