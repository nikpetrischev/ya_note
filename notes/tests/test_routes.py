from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class Tests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Author')
        cls.guest = User.objects.create(username='Guest')
        cls.note = Note.objects.create(
            title='Headline',
            text='NoteText',
            slug='test',
            author=cls.author,
        )

    def test_pages_availability(self):
        """
        Check if main/login/logout/register pages are
        available to anonymous user.
        """
        urls = (
            'notes:home',
            'users:login',
            'users:logout',
            'users:signup',
        )
        for name in urls:
            with self.subTest(name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirects_for_anon(self):
        """
        Check if anon's get redirected from list of notes, note,
        add/edit/delete pages to login screen.
        """
        urls = (
            ('notes:list', None),
            ('notes:detail', (self.note.slug,)),
            ('notes:add', None),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:success', None),
        )
        login_url = settings.LOGIN_URL
        for name, args in urls:
            with self.subTest(name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                redirect_url = f'{login_url}?next={url}'
                self.assertRedirects(response, redirect_url)

    def test_create_edit_delete_note(self):
        """
        Check that author can access theirs notes,
        but other user cannot and recieves 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.guest, HTTPStatus.NOT_FOUND)
        )
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name, args in urls:
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=args)
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)
