# Generated by Django 4.2.6 on 2023-11-07 08:00

import core.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_song_playlist_songs'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='image',
            field=models.ImageField(null=True, upload_to=core.models.playlist_image_file_path),
        ),
    ]