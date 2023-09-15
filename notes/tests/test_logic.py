from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from pytils.translit import slugify

from notes.forms import WARNING
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

        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))

    def test_author_can_edit_note(self):
        """User can edit theirs notes."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.SUCCESS_REDIRECT)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.UPD_NOTE_TEXT)

    def test_author_can_delete_note(self):
        """User can delete theirs notes."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.SUCCESS_REDIRECT)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_guest_cant_edit_others_note(self):
        """User cannot edit others' notes."""
        response = self.guest_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)

    def test_guest_cant_delete_others_note(self):
        """User cannot delete others' notes."""
        response = self.guest_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_slug_is_unique(self):
        """Slug field is unique through db."""
        response = self.author_client.post(self.add_url, data=self.form_data)
        self.assertFormError(
            response,
            'form',
            'slug',
            errors=(self.note.slug + WARNING),)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestCreateNote(TestCase):
    SUCCESS_REDIRECT = reverse('notes:success')

    @classmethod
    def setUpTestData(cls) -> None:
        cls.author = User.objects.create(username='Author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.anon_client = Client()

        cls.form_data = {
            'title': 'Headline',
            'text': 'Some text.',
            'slug': 'note',
        }

        cls.add_url = reverse('notes:add')

    def test_authorized_user_can_create_note(self):
        """
        Check if authorized user can create note
        and it's created correctly.
        """
        response = self.author_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.SUCCESS_REDIRECT)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.form_data['title'])
        self.assertEqual(new_note.text, self.form_data['text'])
        self.assertEqual(new_note.slug, self.form_data['slug'])
        self.assertEqual(new_note.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """
        Check if unauthorized user instead of creating note
        gets redirected.
        """
        response = self.anon_client.post(self.add_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_empty_slug_field(self):
        """
        Test if in plase of empty slug field transliterated title is placed.
        """
        self.form_data.pop('slug')
        self.author_client.post(self.add_url, data=self.form_data)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)
