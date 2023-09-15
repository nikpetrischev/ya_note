from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class Tests(TestCase):

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.guest = User.objects.create(username='guest')
        cls.guest_client = Client()
        cls.guest_client.force_login(cls.guest)

        cls.note = Note.objects.create(
            title='Headline',
            text='Some text.',
            author=cls.author,
            slug='slug',
        )

        cls.list_url = reverse('notes:list')
        cls.create_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))

    def test_is_note_in_context(self):
        """
        Test if note is in context's object_list.
        Must be True for note's author and False otherwise.
        """
        test_cases = (
            (self.author_client, True),
            (self.guest_client, False),
        )
        for users_client, expected_outcome in test_cases:
            with self.subTest(users_client):
                response = users_client.get(self.list_url)
                object_list = response.context['object_list']
                statement = self.note in object_list
                self.assertEqual(statement, expected_outcome)

    def test_form_in_create_edit_pages(self):
        """Check if form is sent via context to /add/ and /edit/ pages."""
        for url in (self.create_url, self.edit_url):
            with self.subTest(url):
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
