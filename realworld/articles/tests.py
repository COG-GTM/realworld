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

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            "user@test.com", name="User", password="testpass"
        )
        cls.other_user = User.objects.create_user(
            "other@test.com", name="Other", password="testpass"
        )

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_home_view_with_own_feed_filter(self):
        my_article = Article.objects.create(
            title="My Article",
            summary="Sum",
            content="Body",
            author=self.user,
        )
        other_article = Article.objects.create(
            title="Other Article",
            summary="Sum",
            content="Body",
            author=self.other_user,
        )

        self.client.force_login(self.user)

        response = self.client.get(self.url + "?own")

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertTrue(response.context["own_feed"])
        self.assertContains(response, "My Article")
        self.assertNotContains(response, "Other Article")

    def test_home_view_with_tag_filter(self):
        article1 = Article.objects.create(
            title="Python Article",
            summary="Sum",
            content="Body",
            author=self.user,
        )
        article1.tags.add("python", "coding")

        article2 = Article.objects.create(
            title="Django Article",
            summary="Sum",
            content="Body",
            author=self.user,
        )
        article2.tags.add("django", "web")

        response = self.client.get(self.url + "?tag=python")

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "Python Article")
        self.assertNotContains(response, "Django Article")


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


class TestEditArticleView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="user@test.com",
            name="User",
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
            title="Original Title",
            summary="Original Summary",
            content="Original Body",
            author=cls.user,
        )

        cls.url = reverse("edit_article", args=[cls.article.id])

    def test_edit_article_get_displays_form(self):
        from .forms import ArticleForm

        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertIn("article", response.context)
        self.assertIsInstance(response.context["form"], ArticleForm)
        self.assertEqual(response.context["article"], self.article)

    def test_edit_article_post_with_valid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "title": "Updated Title",
                "summary": "Updated Summary",
                "content": "Updated Body",
                "tags": "python, django",
            },
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Updated Title")
        self.assertEqual(self.article.summary, "Updated Summary")
        self.assertEqual(self.article.content, "Updated Body")

    def test_edit_article_post_with_invalid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(
            self.url,
            {
                "title": "",
                "summary": "",
                "content": "",
            },
        )

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)

        self.article.refresh_from_db()
        self.assertEqual(self.article.title, "Original Title")

    def test_edit_article_only_author_can_edit(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestDeleteArticleView(TestCase):
    password = "testpass"

    @classmethod
    def setUpTestData(cls):
        cls.user = User(
            email="user@test.com",
            name="User",
        )
        cls.user.set_password(cls.password)
        cls.user.save()

        cls.other_user = User(
            email="other@test.com",
            name="Other",
        )
        cls.other_user.set_password(cls.password)
        cls.other_user.save()

    def test_delete_article_removes_article(self):
        article = Article.objects.create(
            title="Article to Delete",
            summary="Summary",
            content="Body",
            author=self.user,
        )

        self.client.force_login(self.user)

        article_id = article.id
        url = reverse("delete_article", args=[article_id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

        self.assertFalse(Article.objects.filter(pk=article_id).exists())

    def test_delete_article_only_author_can_delete(self):
        article = Article.objects.create(
            title="User's Article",
            summary="Summary",
            content="Body",
            author=self.user,
        )

        self.client.force_login(self.other_user)

        url = reverse("delete_article", args=[article.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        self.assertTrue(Article.objects.filter(pk=article.id).exists())
