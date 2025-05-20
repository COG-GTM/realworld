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

        cls.comment = Comment.objects.create(
            article=cls.article,
            author=cls.author,
            content="original comment"
        )

        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def test_edit_comment_get(self):
        self.client.force_login(self.author)
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIsNotNone(response.context["form"])
        self.assertEqual(response.context["comment"], self.comment)

    def test_edit_comment_post(self):
        self.client.force_login(self.author)
        
        response = self.client.post(self.url, {"content": "updated comment"})
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        
        comment = Comment.objects.get(pk=self.comment.id)
        self.assertEqual(comment.content, "updated comment")


class TestDeleteCommentView(TestCase):

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

        cls.comment = Comment.objects.create(
            article=cls.article,
            author=cls.author,
            content="test comment"
        )

        cls.url = reverse("delete_comment", args=[cls.comment.id])

    def test_delete_comment(self):
        self.client.force_login(self.author)
        
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        
        self.assertFalse(Comment.objects.filter(pk=self.comment.id).exists())
