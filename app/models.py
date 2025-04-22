from django.db import models
from django.utils import timezone
import bcrypt

from hash_functions import hash_password


class AnimeType(models.TextChoices):
    TV = 'TV', 'TV'
    MOVIE = 'Movie', 'Movie'
    OVA = 'OVA', 'OVA'
    ONA = 'ONA', 'ONA'
    SPECIAL = 'Special', 'Special'

class AnimeStatus(models.TextChoices):
    AIRING = 'Airing', 'Airing'
    FINISHED = 'Finished', 'Finished'
    UPCOMING = 'Upcoming', 'Upcoming'

class Anime(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    original_title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    genre = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    type = models.CharField(
        max_length=10,
        choices=AnimeType.choices,
        default=AnimeType.TV
    )
    status = models.CharField(
        max_length=10,
        choices=AnimeStatus.choices,
        default=AnimeStatus.UPCOMING
    )
    release_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    studio = models.CharField(max_length=100, blank=True, null=True)
    rating = models.CharField(max_length=20, blank=True, null=True)
    score = models.PositiveIntegerField(blank=True, null=True)
    count_episode = models.PositiveIntegerField(blank=True, null=True)
    unique_id = models.PositiveIntegerField(unique=True, db_index=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'animes'
        constraints = [
            models.UniqueConstraint(fields=['unique_id'], name='uq_anime_unique_id')
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.unique_id})"

class AnimeLanguage(models.Model):
    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name='translations'
    )
    language = models.CharField(max_length=10)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'anime_languages'
        constraints = [
            models.UniqueConstraint(
                fields=['anime', 'language'],
                name='uq_language_per_anime'
            )
        ]

    def __str__(self):
        return f"{self.anime.title} [{self.language}]"

class Episode(models.Model):
    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name='episodes'
    )
    language = models.ForeignKey(
        AnimeLanguage,
        on_delete=models.CASCADE,
        related_name='episodes'
    )
    episode_number = models.PositiveIntegerField()
    video_id = models.CharField(max_length=255)

    class Meta:
        db_table = 'episodes'
        constraints = [
            models.UniqueConstraint(
                fields=['anime', 'language', 'episode_number'],
                name='uq_episode_lang_number'
            )
        ]
        ordering = ['episode_number']

    def __str__(self):
        return f"{self.anime.title} Ep{self.episode_number} [{self.language.language}]"

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'users'
        constraints = [
            models.UniqueConstraint(
                fields=['telegram_id'],
                name='uq_user_telegram_id'
            )
        ]

    def __str__(self):
        return f"User {self.telegram_id}"

class Channel(models.Model):
    channel_id = models.BigIntegerField(unique=True)
    name = models.CharField(max_length=255)
    username = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'channels'
        constraints = [
            models.UniqueConstraint(
                fields=['channel_id'],
                name='uq_channel_channel_id'
            )
        ]

    def __str__(self):
        return self.name

class Post(models.Model):
    channel = models.ForeignKey(
        Channel,
        on_delete=models.SET_NULL,
        related_name='posts',
        null=True
    )
    anime = models.ForeignKey(
        Anime,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    message_id = models.BigIntegerField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'posts'
        constraints = [
            models.UniqueConstraint(
                fields=['message_id'],
                name='uq_post_message_id'
            )
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Post {self.message_id}"


class Admin(models.Model):
    telegram_id = models.BigIntegerField(unique=True)
    full_name = models.CharField(max_length=255)
    is_super_admin = models.BooleanField(default=False)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admins'
        constraints = [
            models.UniqueConstraint(
                fields=['telegram_id'],
                name='uq_admin_telegram_id'
            )
        ]

    def __str__(self):
        return f"Admin {self.telegram_id}"

    def save(self, *args, **kwargs):
        if not self.password.startswith('$2b$'):  # already hashed password
            self.password = hash_password(self.password)  # Hash the password
        super().save(*args, **kwargs)

class RequiredChannel(models.Model):
    channel_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'required_channels'
        constraints = [
            models.UniqueConstraint(
                fields=['channel_id'],
                name='uq_required_channel_id'
            )
        ]

    def __str__(self):
        return self.name

