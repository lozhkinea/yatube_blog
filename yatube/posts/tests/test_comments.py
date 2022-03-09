from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_SLUG = 'test-slug'
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.TEST_SLUG,
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост' * 100,
            author=cls.author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий ' * 100,
            author=cls.author,
            post=cls.post
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_anonymous_cannot_create_post(self):
        """Комментировать посты может только авторизованный пользователь."""
        count = Post.objects.count()
        form_data = {'text': self.comment.text}
        address = reverse(
            'posts:add_comment',
            kwargs={'post_id': self.comment.post.id}
        )
        response = self.guest_client.post(
            address,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, f'/auth/login/?next={address}')
        self.assertEqual(Comment.objects.count(), count)

    def test_create_comment(self):
        """после успешной отправки комментарий появляется на странице поста."""
        count = Comment.objects.count()
        form_data = {'text': self.comment.text}
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': self.comment.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': self.comment.post.id}
            )
        )
        self.assertEqual(Comment.objects.count(), count + 1)
        self.assertTrue(
            Comment.objects.filter(text=self.comment.text).exists()
        )
