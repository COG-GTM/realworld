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
            title="Article",
            summary="Sum",
            content="Body",
            author=cls.user,
        )

        cls.comment = Comment.objects.create(
            content="Original comment",
            author=cls.user,
            article=cls.article,
        )

        cls.url = reverse("edit_comment", args=[cls.comment.id])

    def test_edit_comment_get_displays_form(self):
        from .forms import CommentForm

        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertIn("comment", response.context)
        self.assertIsInstance(response.context["form"], CommentForm)
        self.assertEqual(response.context["comment"], self.comment)

    def test_edit_comment_post_with_valid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"content": "Updated comment text"})

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Updated comment text")

    def test_edit_comment_post_with_invalid_data(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url, {"content": ""})

        self.assertEqual(response.status_code, http.HTTPStatus.OK)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.content, "Original comment")

    def test_edit_comment_only_author_can_edit(self):
        self.client.force_login(self.other_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)


class TestDeleteCommentView(TestCase):
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
            title="Article",
            summary="Sum",
            content="Body",
            author=cls.user,
        )

    def test_delete_comment_removes_comment(self):
        comment = Comment.objects.create(
            content="Comment to delete",
            author=self.user,
            article=self.article,
        )

        self.client.force_login(self.user)

        comment_id = comment.id
        url = reverse("delete_comment", args=[comment_id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http.HTTPStatus.OK)

        self.assertFalse(Comment.objects.filter(pk=comment_id).exists())

    def test_delete_comment_only_author_can_delete(self):
        comment = Comment.objects.create(
            content="User's comment",
            author=self.user,
            article=self.article,
        )

        self.client.force_login(self.other_user)

        url = reverse("delete_comment", args=[comment.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, http.HTTPStatus.NOT_FOUND)

        self.assertTrue(Comment.objects.filter(pk=comment.id).exists())
