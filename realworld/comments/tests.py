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


class TestEditCommentView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User(email="tester@gmail.com", name="tester")
        cls.author.save()

        cls.other_user = User(email="other@gmail.com", name="other")
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="test", summary="test", content="test", author=cls.author,
        )
        cls.comment = Comment.objects.create(
            content="original", author=cls.author, article=cls.article,
        )
        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def test_get_edit_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_post_valid_edit(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, {"content": "updated comment"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "updated comment")

    def test_post_invalid_edit(self):
        self.client.force_login(self.author)
        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

    def test_edit_by_non_author(self):
        self.client.force_login(self.other_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestDeleteCommentView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User(email="tester@gmail.com", name="tester")
        cls.author.save()

        cls.other_user = User(email="other@gmail.com", name="other")
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="test", summary="test", content="test", author=cls.author,
        )

    def test_delete_comment(self):
        comment = Comment.objects.create(
            content="test", author=self.author, article=self.article,
        )
        self.client.force_login(self.author)
        url = reverse("delete_comment", args=[comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(pk=comment.id).exists())

    def test_delete_by_non_author(self):
        comment = Comment.objects.create(
            content="test", author=self.author, article=self.article,
        )
        self.client.force_login(self.other_user)
        url = reverse("delete_comment", args=[comment.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)
