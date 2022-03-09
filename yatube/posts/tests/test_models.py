from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import CHARS_IN_POST_STR, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
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
        cls.post = Post.objects.create(
            text='Тестовый пост ' * 100,
            author=cls.author,
            group=cls.group
        )

    def test_object_name_is_truncated_text_fild(self):
        """
        В поле __str__ объекта post записано усеченное значение поля post.text.
        """
        post = self.post
        expected_object_name = post.text[:CHARS_IN_POST_STR]
        self.assertEqual(expected_object_name, str(post))

    def test_object_name_is_title_fild(self):
        """
        В поле __str__  объекта group записано значение поля group.title.
        """
        group = PostModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = self.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected
                )
