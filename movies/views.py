from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Movie, Rating, Watchlist, Genre, UserProfile
from .ai_engine import (
    get_hybrid_recommendations,
    get_trending_movies,
    get_similar_movies,
    get_content_based_recommendations,
)


# ─────────────────────────────────────────────
# Home / Dashboard
# ─────────────────────────────────────────────

def home(request):
    trending = get_trending_movies(n=8)
    genres = Genre.objects.annotate(movie_count=Count('movies')).order_by('-movie_count')

    context = {
        'trending': trending,
        'genres': genres,
        'total_movies': Movie.objects.count(),
    }

    if request.user.is_authenticated:
        recommendations = get_hybrid_recommendations(request.user, n=8)
        watchlist_ids = set(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))
        rated_ids = set(Rating.objects.filter(user=request.user).values_list('movie_id', flat=True))
        context.update({
            'recommendations': recommendations,
            'watchlist_ids': watchlist_ids,
            'rated_ids': rated_ids,
            'user_rating_count': len(rated_ids),
        })

    return render(request, 'movies/home.html', context)


# ─────────────────────────────────────────────
# Movie Detail
# ─────────────────────────────────────────────

def movie_detail(request, pk):
    movie = get_object_or_404(Movie.objects.prefetch_related('genres'), pk=pk)
    similar = get_similar_movies(movie, n=6)

    user_rating = None
    in_watchlist = False

    if request.user.is_authenticated:
        try:
            user_rating = Rating.objects.get(user=request.user, movie=movie)
        except Rating.DoesNotExist:
            pass
        in_watchlist = Watchlist.objects.filter(user=request.user, movie=movie).exists()

    all_ratings = Rating.objects.filter(movie=movie).select_related('user').order_by('-created_at')[:10]

    context = {
        'movie': movie,
        'similar': similar,
        'user_rating': user_rating,
        'in_watchlist': in_watchlist,
        'all_ratings': all_ratings,
        'stars': range(1, 6),
    }
    return render(request, 'movies/movie_detail.html', context)


# ─────────────────────────────────────────────
# Browse / Search
# ─────────────────────────────────────────────

def browse(request):
    movies = Movie.objects.prefetch_related('genres').annotate(
        avg_score=Avg('ratings__score'),
        num_ratings=Count('ratings')
    )

    q = request.GET.get('q', '').strip()
    genre_id = request.GET.get('genre', '')
    sort = request.GET.get('sort', 'trending')

    if q:
        movies = movies.filter(
            Q(title__icontains=q) |
            Q(director__icontains=q) |
            Q(cast__icontains=q) |
            Q(description__icontains=q)
        )

    if genre_id:
        movies = movies.filter(genres__id=genre_id)

    sort_options = {
        'trending': ('-num_ratings', '-avg_score'),
        'rating': ('-avg_score',),
        'year': ('-year',),
        'title': ('title',),
    }
    movies = movies.order_by(*sort_options.get(sort, ('-num_ratings',)))

    genres = Genre.objects.annotate(movie_count=Count('movies')).order_by('name')

    watchlist_ids = set()
    if request.user.is_authenticated:
        watchlist_ids = set(Watchlist.objects.filter(user=request.user).values_list('movie_id', flat=True))

    context = {
        'movies': movies[:60],
        'genres': genres,
        'q': q,
        'selected_genre': genre_id,
        'sort': sort,
        'watchlist_ids': watchlist_ids,
    }
    return render(request, 'movies/browse.html', context)


# ─────────────────────────────────────────────
# Rating (AJAX)
# ─────────────────────────────────────────────

@login_required
@require_POST
def rate_movie(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    score = int(request.POST.get('score', 0))
    review = request.POST.get('review', '')

    if not 1 <= score <= 5:
        return JsonResponse({'error': 'Invalid score'}, status=400)

    rating, created = Rating.objects.update_or_create(
        user=request.user, movie=movie,
        defaults={'score': score, 'review': review}
    )

    return JsonResponse({
        'success': True,
        'score': score,
        'avg': movie.avg_user_rating,
        'count': movie.rating_count,
        'created': created,
    })


# ─────────────────────────────────────────────
# Watchlist toggle (AJAX)
# ─────────────────────────────────────────────

@login_required
@require_POST
def toggle_watchlist(request, pk):
    movie = get_object_or_404(Movie, pk=pk)
    wl, created = Watchlist.objects.get_or_create(user=request.user, movie=movie)

    if not created:
        wl.delete()
        return JsonResponse({'status': 'removed', 'message': f'Removed from watchlist'})

    return JsonResponse({'status': 'added', 'message': f'Added to watchlist'})


# ─────────────────────────────────────────────
# User Profile & Watchlist
# ─────────────────────────────────────────────

@login_required
def profile(request):
    ratings = Rating.objects.filter(user=request.user).select_related('movie').order_by('-created_at')
    watchlist = Watchlist.objects.filter(user=request.user).select_related('movie').order_by('-added_at')

    # Stats
    rated_count = ratings.count()
    avg_given = ratings.aggregate(a=Avg('score'))['a'] or 0
    fav_genre = None
    if rated_count:
        genre_counts = {}
        for r in ratings:
            for g in r.movie.genres.all():
                genre_counts[g.name] = genre_counts.get(g.name, 0) + 1
        if genre_counts:
            fav_genre = max(genre_counts, key=genre_counts.get)

    context = {
        'ratings': ratings,
        'watchlist': watchlist,
        'rated_count': rated_count,
        'avg_given': round(avg_given, 1),
        'fav_genre': fav_genre,
        'stars': range(1, 6),
    }
    return render(request, 'movies/profile.html', context)


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.username}! Start rating movies to get AI recommendations.')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'movies/auth.html', {'form': form, 'mode': 'register'})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(request.GET.get('next', 'home'))
    else:
        form = AuthenticationForm()
    return render(request, 'movies/auth.html', {'form': form, 'mode': 'login'})


def logout_view(request):
    logout(request)
    return redirect('home')


# ─────────────────────────────────────────────
# AI Recommendations page
# ─────────────────────────────────────────────

@login_required
def recommendations(request):
    hybrid = get_hybrid_recommendations(request.user, n=16)
    content = get_content_based_recommendations(request.user, n=8)

    rated_count = Rating.objects.filter(user=request.user).count()

    context = {
        'hybrid': hybrid,
        'content_based': content,
        'rated_count': rated_count,
        'needs_more_ratings': rated_count < 3,
    }
    return render(request, 'movies/recommendations.html', context)


# ─────────────────────────────────────────────
# User Movie Collection (add/edit/delete)
# ─────────────────────────────────────────────

from .models import UserMovie

@login_required
def my_collection(request):
    movies = UserMovie.objects.filter(user=request.user).prefetch_related('genres')

    # filters
    status = request.GET.get('status', '')
    mood = request.GET.get('mood', '')
    fav = request.GET.get('fav', '')
    q = request.GET.get('q', '').strip()

    if status:
        movies = movies.filter(watch_status=status)
    if mood:
        movies = movies.filter(mood=mood)
    if fav:
        movies = movies.filter(is_favourite=True)
    if q:
        movies = movies.filter(title__icontains=q)

    genres = Genre.objects.all()
    stats = {
        'total': UserMovie.objects.filter(user=request.user).count(),
        'watched': UserMovie.objects.filter(user=request.user, watch_status='watched').count(),
        'watching': UserMovie.objects.filter(user=request.user, watch_status='watching').count(),
        'plan': UserMovie.objects.filter(user=request.user, watch_status='plan_to_watch').count(),
        'favourites': UserMovie.objects.filter(user=request.user, is_favourite=True).count(),
    }

    return render(request, 'movies/my_collection.html', {
        'movies': movies,
        'genres': genres,
        'stats': stats,
        'status': status,
        'mood': mood,
        'q': q,
        'mood_choices': UserMovie.MOOD_CHOICES,
        'status_choices': UserMovie.WATCH_STATUS,
    })


@login_required
def add_user_movie(request):
    genres = Genre.objects.all()
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        if not title:
            return render(request, 'movies/add_movie.html', {
                'genres': genres,
                'error': 'Title is required.',
                'mood_choices': UserMovie.MOOD_CHOICES,
                'status_choices': UserMovie.WATCH_STATUS,
                'post': request.POST,
            })

        movie = UserMovie.objects.create(
            user=request.user,
            title=title,
            year=request.POST.get('year') or None,
            description=request.POST.get('description', ''),
            director=request.POST.get('director', ''),
            cast=request.POST.get('cast', ''),
            my_rating=request.POST.get('my_rating') or None,
            my_review=request.POST.get('my_review', ''),
            mood=request.POST.get('mood', 'any'),
            is_favourite=bool(request.POST.get('is_favourite')),
            watch_status=request.POST.get('watch_status', 'watched'),
            notes=request.POST.get('notes', ''),
        )
        genre_ids = request.POST.getlist('genres')
        if genre_ids:
            movie.genres.set(genre_ids)

        messages.success(request, f'"{title}" added to your collection!')
        return redirect('my_collection')

    return render(request, 'movies/add_movie.html', {
        'genres': genres,
        'mood_choices': UserMovie.MOOD_CHOICES,
        'status_choices': UserMovie.WATCH_STATUS,
    })


@login_required
def edit_user_movie(request, pk):
    movie = get_object_or_404(UserMovie, pk=pk, user=request.user)
    genres = Genre.objects.all()

    if request.method == 'POST':
        movie.title = request.POST.get('title', movie.title).strip()
        movie.year = request.POST.get('year') or None
        movie.description = request.POST.get('description', '')
        movie.director = request.POST.get('director', '')
        movie.cast = request.POST.get('cast', '')
        movie.my_rating = request.POST.get('my_rating') or None
        movie.my_review = request.POST.get('my_review', '')
        movie.mood = request.POST.get('mood', 'any')
        movie.is_favourite = bool(request.POST.get('is_favourite'))
        movie.watch_status = request.POST.get('watch_status', 'watched')
        movie.notes = request.POST.get('notes', '')
        movie.save()
        genre_ids = request.POST.getlist('genres')
        movie.genres.set(genre_ids)
        messages.success(request, f'"{movie.title}" updated!')
        return redirect('my_collection')

    return render(request, 'movies/add_movie.html', {
        'movie': movie,
        'genres': genres,
        'mood_choices': UserMovie.MOOD_CHOICES,
        'status_choices': UserMovie.WATCH_STATUS,
        'editing': True,
    })


@login_required
@require_POST
def delete_user_movie(request, pk):
    movie = get_object_or_404(UserMovie, pk=pk, user=request.user)
    title = movie.title
    movie.delete()
    return JsonResponse({'success': True, 'message': f'"{title}" removed from collection'})


@login_required
@require_POST
def toggle_favourite(request, pk):
    movie = get_object_or_404(UserMovie, pk=pk, user=request.user)
    movie.is_favourite = not movie.is_favourite
    movie.save()
    return JsonResponse({'success': True, 'is_favourite': movie.is_favourite})
