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

    def test_add_comment_invalid_form(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        
        self.assertFalse(Comment.objects.exists())
        self.assertTrue(response.context["form"].errors)


class TestEditCommentView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.save()

        cls.other_user = User(
            email="other@gmail.com",
            name="other",
        )
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.comment = Comment.objects.create(
            content="original content",
            author=cls.author,
            article=cls.article,
        )

        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def test_edit_comment_get(self):
        self.client.force_login(self.author)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertContains(response, "original content")
        self.assertEqual(response.context["comment"], self.comment)

    def test_edit_comment_post_valid(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": "updated content"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "updated content")

    def test_edit_comment_post_invalid(self):
        self.client.force_login(self.author)

        response = self.client.post(self.url, {"content": ""})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "original content")
        self.assertTrue(response.context["form"].errors)

    def test_edit_comment_unauthorized_user(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        response = self.client.post(self.url, {"content": "hacked content"})
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "original content")


class TestDeleteCommentView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User(
            email="tester@gmail.com",
            name="tester",
        )
        cls.author.save()

        cls.other_user = User(
            email="other@gmail.com",
            name="other",
        )
        cls.other_user.save()

        cls.article = Article.objects.create(
            title="test",
            summary="test",
            content="test",
            author=cls.author,
        )

        cls.comment = Comment.objects.create(
            content="test content",
            author=cls.author,
            article=cls.article,
        )

        cls.url = reverse("delete_comment", args=[cls.comment.id])

    def test_delete_comment(self):
        self.client.force_login(self.author)

        self.assertTrue(Comment.objects.filter(pk=self.comment.id).exists())

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertFalse(Comment.objects.filter(pk=self.comment.id).exists())

    def test_delete_comment_unauthorized_user(self):
        self.client.force_login(self.other_user)

        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        self.assertTrue(Comment.objects.filter(pk=self.comment.id).exists())
