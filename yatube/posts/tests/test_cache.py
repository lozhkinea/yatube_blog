from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse_lazy

from ..models import Post

User = get_user_model()


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост' * 100,
            author=cls.author,
        )
        cls.index_url = reverse_lazy('posts:index')

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_index_cache(self):
        """"
        При удалении записи из базы, она остаётся в response.content главной
        страницы до тех пор, пока кэш не будет очищен принудительно.
        """
        response = self.guest_client.get(self.index_url)
        content = response.content
        self.post.delete()
        response = self.guest_client.get(self.index_url)
        self.assertEqual(response.content, content)
        cache.clear()
        response = self.guest_client.get(self.index_url)
        self.assertNotEqual(response.content, content)
