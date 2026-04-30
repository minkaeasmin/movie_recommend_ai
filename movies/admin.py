from django.contrib import admin
from .models import Movie, Genre, Rating, Watchlist, UserProfile


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name']


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['title', 'year', 'director', 'imdb_rating', 'rating_count']
    list_filter = ['genres', 'year']
    search_fields = ['title', 'director', 'cast']
    filter_horizontal = ['genres']


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'score', 'created_at']
    list_filter = ['score']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'movie', 'added_at']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
    filter_horizontal = ['favorite_genres']

from .models import UserMovie

@admin.register(UserMovie)
class UserMovieAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'year', 'my_rating', 'watch_status', 'is_favourite', 'added_at']
    list_filter = ['watch_status', 'is_favourite', 'mood']
    search_fields = ['title', 'user__username']
