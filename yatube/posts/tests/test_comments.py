from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Post

User = get_user_model()


class PostsCommentsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TEST_COMMENT_TEXT = 'Тестовый комментарий'
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author
        )
        cls.url_add_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': cls.post.id}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_user_can_create_comment(self):
        """Комментировать посты может только авторизованный пользователь."""
        count = Comment.objects.count()
        form_data = {'text': self.TEST_COMMENT_TEXT}
        address = self.url_add_comment
        response = self.guest_client.post(
            address,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count)
        self.assertRedirects(response, f'/auth/login/?next={address}')

    def test_create_comment(self):
        """после успешной отправки комментарий появляется на странице поста."""
        count = Comment.objects.count()
        form_data = {'text': self.TEST_COMMENT_TEXT}
        response = self.authorized_client.post(
            self.url_add_comment,
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(
            response.context['comments'][0].text,
            self.TEST_COMMENT_TEXT
        )
