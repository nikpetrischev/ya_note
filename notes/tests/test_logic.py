from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestNoteEditAndDelete(TestCase):
    NOTE_TEXT = 'Note'
    UPD_NOTE_TEXT = 'Updated note'
    SUCCESS_REDIRECT = reverse('notes:success')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.note = Note.objects.create(
            title='Headline',
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug='test',
        )
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.UPD_NOTE_TEXT,
            'slug': cls.note.slug,
        }

        cls.guest = User.objects.create(username='Guest')
        cls.guest_client = Client()
        cls.guest_client.force_login(cls.guest)

        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.SUCCESS_REDIRECT)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.UPD_NOTE_TEXT)

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.SUCCESS_REDIRECT)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_guest_cant_edit_others_note(self):
        response = self.guest_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_guest_cant_delete_others_note(self):
        response = self.guest_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
