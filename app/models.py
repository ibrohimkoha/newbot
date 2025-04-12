from django.db import models

class Anime(models.Model):
    name = models.CharField(max_length=100)
    genre = models.CharField(max_length=100)
    count_episode = models.IntegerField()
    unique_id = models.PositiveIntegerField()
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.unique_id
    
    class Meta:
        db_table = 'animes'

class AnimeLanguage(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='translations')
    language = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'languages_for_anime'

    def __str__(self):
        return f"{self.anime.unique_id} ({self.language})"

class Episode(models.Model):
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='episodes')
    episode_number = models.IntegerField()
    video_id = models.CharField(max_length=255)  # Telegram video file ID yoki tashqi link
    language = models.ForeignKey(AnimeLanguage, on_delete=models.CASCADE)  # Masalan: 'en', 'uz', 'ru'

    class Meta:
        db_table = 'episodes_for_language'

    def __str__(self):
        return f"{self.anime.unique_id} - Episode {self.episode_number} ({self.language})"

class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True)  # Telegram user ID
    username = models.CharField(max_length=100, blank=True, null=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_for_anime'

    def __str__(self):
        return f"User {self.telegram_id}"

class Channel(models.Model):
    channel_id = models.BigIntegerField(unique=True)  # Telegram kanal ID
    name = models.CharField(max_length=255)  # Kanal nomi
    username = models.CharField(max_length=100, blank=True, null=True)  # @username shaklida
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'channels'
    
    def __str__(self):
        return f"Channel {self.name} (@{self.username})"

class Post(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    anime = models.ForeignKey(Anime, on_delete=models.CASCADE, related_name='posts')
    message_id = models.BigIntegerField(unique=True)  # Telegramdagi post ID
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'posts'
    
    def __str__(self):
        return f"Post {self.message_id} in {self.channel.name}"
