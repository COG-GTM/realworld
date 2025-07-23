import http

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from realworld.articles.models import Article

from .models import Comment

User = get_user_model()


class TestAddCommentView(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.url = reverse("add_comment", args=[cls.article.id])

    def test_add_comment(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": "test"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        comment = Comment.objects.get()

        self.assertEqual(comment.article, self.article)
        self.assertEqual(comment.author, self.author)

    def test_add_comment_invalid(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "content")
        self.assertEqual(Comment.objects.count(), 0)

    def test_add_comment_not_authenticated(self):
        response = self.client.post(self.url, {"content": "test"})
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), 0)


class TestCommentModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(
            email="tester@gmail.com",
            name="tester",
            password="testpass"
        )

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.comment = Comment.objects.create(
            content="Test comment content",
            author=cls.author,
            article=cls.article,
        )

    def test_comment_creation(self):
        self.assertEqual(self.comment.content, "Test comment content")
        self.assertEqual(self.comment.author, self.author)
        self.assertEqual(self.comment.article, self.article)
        self.assertIsNotNone(self.comment.created)
        self.assertIsNotNone(self.comment.updated)

    def test_comment_relationships(self):
        self.assertEqual(self.comment.author.email, "tester@gmail.com")
        self.assertEqual(self.comment.article.title, "test")

    def test_comment_timestamps(self):
        original_updated = self.comment.updated
        self.comment.content = "Updated content"
        self.comment.save()
        self.comment.refresh_from_db()
        self.assertGreater(self.comment.updated, original_updated)


class TestEditCommentView(TestCase):
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
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.comment = Comment.objects.create(
            content="Original comment",
            author=cls.author,
            article=cls.article,
        )

        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def setUp(self):
        self.client.force_login(self.author)

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertEqual(response.context["comment"], self.comment)
        form = response.context["form"]
        self.assertEqual(form.instance, self.comment)

    def test_get_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

    def test_get_not_authenticated(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)

    def test_post_valid(self):
        response = self.client.post(self.url, {
            "content": "Updated comment content"
        })
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment content")

    def test_post_invalid(self):
        response = self.client.post(self.url, {
            "content": ""
        })
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "content")
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Original comment")

    def test_post_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.url, {
            "content": "Hacked content"
        })
        
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Original comment")


class TestDeleteCommentView(TestCase):
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
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.comment = Comment.objects.create(
            content="Test comment",
            author=cls.author,
            article=cls.article,
        )

        cls.url = reverse("delete_comment", args=[cls.comment.id])

    def setUp(self):
        self.client.force_login(self.author)

    def test_delete_success(self):
        comment_id = self.comment.id
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(id=comment_id).exists())

    def test_delete_permission_denied(self):
        self.client.force_login(self.other_user)
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_not_authenticated(self):
        self.client.logout()
        response = self.client.delete(self.url)
        
        self.assertEqual(response.status_code, http.HTTPStatus.FOUND)
        self.assertTrue(Comment.objects.filter(id=self.comment.id).exists())

    def test_delete_nonexistent_comment(self):
        url = reverse("delete_comment", args=[99999])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
