"""
Tests for the songs API.
"""
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Song,
    Playlist,
)

from playlist.serializers import SongSerializer

SONGS_URL = reverse('playlist:song-list')


def detail_url(song_id):
    """Create and return song detail URL"""
    return reverse("playlist:song-detail", args=[song_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicSongsApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving songs."""
        res = self.client.get(SONGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateSongsApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_songs(self):
        """Test retrieving a list of songs."""
        Song.objects.create(user=self.user, name="Breed", artist="Nirvana")
        Song.objects.create(user=self.user, name="Polly", artist="Nirvana")

        res = self.client.get(SONGS_URL)

        songs = Song.objects.all().order_by('-name')
        serializer = SongSerializer(songs, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_songs_limited_to_user(self):
        """Test list of songs is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Song.objects.create(user=user2, name="Drain you", artist="Nirvana")
        song = Song.objects.create(user=self.user, name="Love Buzz",
                                   artist="Nirvana")

        res = self.client.get(SONGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], song.name)
        self.assertEqual(res.data[0]['artist'], song.artist)
        self.assertEqual(res.data[0]['id'], song.id)

    def test_update_song(self):
        """Test updating song"""
        song = Song.objects.create(user=self.user, name="Beat it",
                                   artist="Jackson")

        payload = {"name": "CoolName"}
        url = detail_url(song.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        song.refresh_from_db()
        self.assertEqual(song.name, payload["name"])

    def test_delete_song(self):
        """Test deleting song"""
        song = Song.objects.create(user=self.user, name="Shame",
                                   artist="Jackson")

        url = detail_url(song.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        songs = Song.objects.filter(user=self.user)
        self.assertFalse(songs.exists())

    def test_filter_songs_assigned_to_playlists(self):
        """test listing songs by those assigned to playlists."""
        song1 = Song.objects.create(user=self.user, name="Back in Black")
        song2 = Song.objects.create(user=self.user, name="TNT")
        playlist = Playlist.objects.create(
            title="ACDC pack",
            time_minutes=6,
            general_genre="Rock'n'Roll",
            user=self.user,
        )
        playlist.songs.add(song1)

        res = self.client.get(SONGS_URL, {"assigned_only": 1})

        s1 = SongSerializer(song1)
        s2 = SongSerializer(song2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_songs_unique(self):
        """Test filtered songs return a unique list"""
        song = Song.objects.create(user=self.user, name="Sunday")
        Song.objects.create(user=self.user, name="April")
        playlist1 = Playlist.objects.create(
            title="Days' songs",
            time_minutes=4,
            general_genre="Different",
            user=self.user,
        )
        playlist2 = Playlist.objects.create(
            title="Funny songs",
            time_minutes=20,
            general_genre="Different",
            user=self.user,
        )
        playlist1.songs.add(song)
        playlist2.songs.add(song)

        res = self.client.get(SONGS_URL, {"assigned_only": 1})

        self.assertEqual(len(res.data), 1)
