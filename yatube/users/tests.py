from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from posts.models import User


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='User')

    def setUp(self):
        self.guest_client = Client()

    def test_signup_url_exists_at_desired_location(self):
        """Проверка доступности адреса /auth/signup/."""
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_signup_url_uses_correct_template(self):
        """Проверка шаблона для адреса /auth/signup/."""
        response = self.guest_client.get('/auth/signup/')
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_signup_view_uses_correct_template(self):
        """Проверка шаблона для users:signup."""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertTemplateUsed(response, 'users/signup.html')

    def test_signup_view_send_form_in_context(self):
        """Проверка форvы в контексте для users:signup."""
        response = self.guest_client.get(reverse('users:signup'))
        self.assertIsNotNone(response.context.get('form'))

    def test_create_user(self):
        """
        Валидная форма со страницы создания пользователя создает запись в БД.
        """
        form_data = {
            'username': 'TestUser',
            'email': 'testemail@test.tt',
            'password1': 'P@ssword12',
            'password2': 'P@ssword12',
        }
        users_count = User.objects.count()
        self.guest_client.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertEqual(User.objects.count(), users_count + 1)
