from http import HTTPStatus

from django.test import Client, TestCase
from posts.models import Group, Post, User


class TestPostsURLs(TestCase):
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
        cls.index_url = '/'
        cls.group_list_url = f'/group/{cls.TEST_SLUG}/'
        cls.profile_url = f'/profile/{cls.post.author.username}/'
        cls.post_detail_url = f'/posts/{cls.post.id}/'
        cls.post_create_url = '/create/'
        cls.post_edit_url = f'/posts/{cls.post.id}/edit/'
        cls.unexisting_page = '/unexisting_page/'

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_exists_at_desired_location_to_guest_user(self):
        """Страница доступна любому пользователю"""
        url_names = [
            self.index_url,
            self.group_list_url,
            self.profile_url
        ]
        for address in url_names:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_to_authorized_user(self):
        """Страница доступна только авторизованному пользователю"""
        url = self.post_create_url
        response = self.guest_client.get(url)
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_exists_at_desired_location_to_author(self):
        """Страница доступна только автору"""
        url = self.post_edit_url
        response = self.guest_client.get(url)
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(url)
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.authorized_client.force_login(self.author)
        response = self.authorized_client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_of_unexisting_page_not_exists(self):
        """Запрос к несуществующей странице вернёт ошибку 404"""
        response = self.guest_client.get(self.unexisting_page)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
            self.post_create_url: 'posts/create_post.html',
            self.post_edit_url: 'posts/create_post.html',
        }
        self.authorized_client.force_login(self.author)
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_create_or_edit_url_redirect_anonymous(self):
        """URL перенаправляет анонимного пользователя на страницу логина."""
        page_urls = [
            self.post_create_url,
            self.post_edit_url
        ]
        for address in page_urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                redirect_address = f'/auth/login/?next={address}'
                self.assertRedirects(response, redirect_address)
