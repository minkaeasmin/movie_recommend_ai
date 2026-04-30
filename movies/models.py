from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    title = models.CharField(max_length=255)
    year = models.IntegerField()
    description = models.TextField()
    genres = models.ManyToManyField(Genre, related_name='movies')
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True, help_text="Comma-separated list of cast members")
    poster_url = models.URLField(blank=True)
    imdb_rating = models.FloatField(default=0.0)
    runtime_minutes = models.IntegerField(default=0)
    language = models.CharField(max_length=50, default='English')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year', 'title']

    def __str__(self):
        return f"{self.title} ({self.year})"

    @property
    def avg_user_rating(self):
        ratings = self.ratings.all()
        if ratings:
            return round(sum(r.score for r in ratings) / len(ratings), 1)
        return None

    @property
    def rating_count(self):
        return self.ratings.count()

    @property
    def genre_list(self):
        return [g.name for g in self.genres.all()]

    @property
    def cast_list(self):
        return [c.strip() for c in self.cast.split(',') if c.strip()]


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} → {self.movie.title}: {self.score}/5"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlist')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='watchlisted_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie')

    def __str__(self):
        return f"{self.user.username} wants to watch {self.movie.title}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    favorite_genres = models.ManyToManyField(Genre, blank=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class UserMovie(models.Model):
    """A movie added privately by a user — only visible to them."""
    MOOD_CHOICES = [
        ('happy', '😄 Happy'),
        ('sad', '😢 Sad'),
        ('excited', '🤩 Excited'),
        ('scared', '😱 Scared'),
        ('romantic', '❤️ Romantic'),
        ('thoughtful', '🤔 Thoughtful'),
        ('chill', '😎 Chill'),
        ('any', '🎬 Any Mood'),
    ]
    WATCH_STATUS = [
        ('watched', '✅ Watched'),
        ('watching', '▶️ Watching'),
        ('plan_to_watch', '📋 Plan to Watch'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_movies')
    title = models.CharField(max_length=255)
    year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True)
    director = models.CharField(max_length=200, blank=True)
    cast = models.TextField(blank=True)
    genres = models.ManyToManyField(Genre, blank=True)
    my_rating = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    my_review = models.TextField(blank=True)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, default='any')
    is_favourite = models.BooleanField(default=False)
    watch_status = models.CharField(max_length=20, choices=WATCH_STATUS, default='watched')
    notes = models.TextField(blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username}'s movie: {self.title}"

    @property
    def genre_list(self):
        return [g.name for g in self.genres.all()]

    @property
    def cast_list(self):
        return [c.strip() for c in self.cast.split(',') if c.strip()]
