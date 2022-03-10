from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
import shutil
import tempfile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
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
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма со страницы создания поста создает запись в Post."""
        posts_count = Post.objects.count()
        form_data = {'text': self.post.text}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.author.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # при отправке поста с картинкой через форму PostForm 
        # создаётся запись в базе данных
        self.assertTrue(
            Post.objects.filter(
                image=self.post.image
            ).exists()
        )

    def test_edit_post(self):
        """Валидная форма со страницы редактирования поста изменяет запись в Post.
        """
        posts_count = Post.objects.count()
        post_text = self.post.text
        post_edited_text = post_text + '!!!'
        form_data = {'text': post_edited_text}
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        post_text_edited = Post.objects.get(id=self.post.id).text
        self.assertNotEqual(post_text_edited, post_text)

    def test_anonymous_cannot_create_post(self):
        """Аноноимный пользователь не может создать пост."""
        posts_count = Post.objects.count()
        form_data = {'text': self.post.text}
        address = reverse('posts:post_create')
        response = self.guest_client.post(
            address,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, f'/auth/login/?next={address}')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_anonymous_cannot_edit_post(self):
        """Аноноимный пользователь не может изменить пост."""
        posts_count = Post.objects.count()
        post_text = self.post.text
        form_data = {'text': post_text + '!!!'}
        address = reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        response = self.guest_client.post(
            address,
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, f'/auth/login/?next={address}')
        self.assertEqual(Post.objects.count(), posts_count)
        post_new_text = Post.objects.get(id=self.post.id).text
        self.assertEqual(post_new_text, post_text)

    def test_create_user(self):
        """
        При заполнении формы reverse('users:signup')
        создаётся новый пользователь.
        """
        users_count = User.objects.count()
        form_data = {
            'username': 'NewUser',
            'password1': 'NewPassword1',
            'password2': 'NewPassword1'
        }
        response = self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('posts:index')
        )
        self.assertEqual(User.objects.count(), users_count + 1)
