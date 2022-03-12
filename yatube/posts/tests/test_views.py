import shutil
import tempfile

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse_lazy
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(
            username='author'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост' * 100,
            author=cls.author,
            group=cls.group,
            image=cls.uploaded
        )
        cls.index_url = reverse_lazy(
            'posts:index'
        )
        cls.group_list_url = reverse_lazy(
            'posts:group_list', kwargs={'slug': cls.group.slug}
        )
        cls.profile_url = reverse_lazy(
            'posts:profile', kwargs={'username': cls.author.username}
        )
        cls.post_detail_url = reverse_lazy(
            'posts:post_detail', kwargs={'post_id': cls.post.id}
        )
        cls.post_create_url = reverse_lazy(
            'posts:post_create'
        )
        cls.post_edit_url = reverse_lazy(
            'posts:post_edit', kwargs={'post_id': cls.post.id}
        )
        cls.urls_of_pages_with_posts = [
            cls.index_url,
            cls.group_list_url,
            cls.profile_url
        ]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template_by_guest_user(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            self.index_url: 'posts/index.html',
            self.group_list_url: 'posts/group_list.html',
            self.profile_url: 'posts/profile.html',
            self.post_detail_url: 'posts/post_detail.html',
            self.post_create_url: 'posts/create_post.html',
            self.post_edit_url: 'posts/create_post.html'
        }
        self.authorized_client.force_login(self.author)
        for url, template in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_posts_on_page_is_1(self):
        """На страницу передаётся ожидаемое количество объектов."""
        expected_count = 1
        for url in self.urls_of_pages_with_posts:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                posts_count = len(response.context['page_obj'])
                self.assertEqual(expected_count, posts_count)

    def test_pages_show_correct_context(self):
        """Шаблон страницы с постами сформирован с правильным контекстом."""
        for url in self.urls_of_pages_with_posts:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                first_post = response.context['page_obj'][0]
                post_text_0 = first_post.text
                post_author_0 = first_post.author
                post_group_0 = first_post.group
                post_image_0 = first_post.image
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_group_0, self.post.group)
                # при выводе поста с картинкой изображение передаётся
                # в словаре context
                self.assertEqual(post_image_0, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(self.group_list_url)
        expected = response.context['group']
        self.assertEqual(expected, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(self.profile_url)
        expected = response.context['author']
        self.assertEqual(expected, self.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(self.post_detail_url)
        post = response.context['post']
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.group, self.post.group)
        # при выводе поста с картинкой изображение передаётся
        # в словаре context
        self.assertEqual(post.image, self.post.image)

    def test_post_form_page_show_correct_context(self):
        """Шаблон страницы с формой сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        users_for_page = {
            self.post_create_url: self.user,
            self.post_edit_url: self.author,
        }
        for url, user in users_for_page.items():
            self.authorized_client.force_login(user)
            response = self.authorized_client.get(url)
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

    def test_post_with_group_appears_on_pages(self):
        """Пост с группой появляется на страницах сайта"""
        url_names = [
            self.index_url,
            self.group_list_url,
            self.profile_url
        ]
        for url in url_names:
            response = self.guest_client.get(url)
            first_post = response.context['page_obj'][0]
            self.assertEqual(first_post.group, self.group)

    def test_post_with_group_not_appears_on_pages_with_another_group(self):
        """Пост с группой не появляется на странице другой группы"""
        another_group = Group.objects.create(
            title='Тестовый заголовок другой группы',
            slug='test-another-slug',
            description='Тестовое описание другой группы'
        )
        another_group_list_url = reverse_lazy(
            'posts:group_list', kwargs={'slug': another_group.slug}
        )
        response = self.authorized_client.get(another_group_list_url)
        if len(response.context['page_obj']) > 0:
            first_post = response.context['page_obj'][0]
            self.assertNotEqual(first_post.group, self.group)
