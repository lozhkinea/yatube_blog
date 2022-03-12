from django.test import Client, TestCase
from django.urls import reverse, reverse_lazy
from posts.models import Follow, Post, User


class TestFollow(TestCase):
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
        cls.url_follow_index = reverse_lazy(
            'posts:follow_index'
        )
        cls.url_follow = reverse_lazy(
            'posts:profile_follow',
            kwargs={'username': cls.author.username}
        )
        cls.url_unfollow = reverse_lazy(
            'posts:profile_unfollow',
            kwargs={'username': cls.author.username}
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='TestUser')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_anonymous_cant_subscribe(self):
        """"
        Анонимный пользователь не может подписываться на авторов.
        """
        count = Follow.objects.count()
        response = self.guest_client.get(self.url_follow)
        self.assertRedirects(response, f'/auth/login/?next={self.url_follow}')
        self.assertEqual(Follow.objects.count(), count)

    def test_authorized_user_can_subscribe_unsubscribe(self):
        """
        Авторизованный пользователь может подписываться на других
        пользователей и удалять их из подписок.
        """
        count = Follow.objects.count()
        self.authorized_client.get(self.url_follow)
        self.assertEqual(Follow.objects.count(), count + 1)
        self.authorized_client.get(self.url_unfollow)
        self.assertEqual(Follow.objects.count(), count)

    def test_new_post_appears_in_subscribers_feed(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        def posts_count(user):
            self.authorized_client.force_login(user)
            response = self.authorized_client.get(self.url_follow_index)
            return len(response.context['page_obj'])

        # создаем другого пользователя
        self.user1 = User.objects.create_user(username='TestUser1')
        # подписываем пользователя на автора
        self.authorized_client.get(self.url_follow, follow=True)
        count = posts_count(self.user)
        count1 = posts_count(self.user1)
        # создаем пост автора
        self.authorized_client.force_login(self.author)
        self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Новый пост'},
            follow=True
        )
        # проверяем ленту пользователя
        self.assertEqual(posts_count(self.user), count + 1)
        # проверяем ленту другого пользователя
        self.assertEqual(posts_count(self.user1), count1)
