from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse_lazy

from ..models import Group, Post
from ..views import POSTS_PER_PAGE

User = get_user_model()


class TestPaginatorView(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.POSTS_COUNT = 13
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        post_list = [
            Post(
                text='Тестовый текст',
                author=cls.author,
                group=cls.group
            )
        ] * cls.POSTS_COUNT
        cls.posts = Post.objects.bulk_create(post_list)
        cls.urls = {
            reverse_lazy(
                'posts:index'
            ),
            reverse_lazy(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ),
            reverse_lazy(
                'posts:profile', kwargs={'username': cls.author.username}
            ),
        }
        cls.client = Client()

    def test_first_page_contains_ten_records(self):
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(
                    len(response.context['page_obj']),
                    POSTS_PER_PAGE
                )

    def test_second_page_contains_three_records(self):
        for url in self.urls:
            with self.subTest(url=url):
                response = self.client.get(url + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.POSTS_COUNT - POSTS_PER_PAGE
                )
