"""
AI Recommendation Engine
========================
Implements two recommendation strategies:
  1. Content-Based Filtering  — recommends movies similar to ones you liked
  2. Collaborative Filtering  — recommends movies liked by similar users
  3. Hybrid                   — blends both for best results
"""

import math
from collections import defaultdict
from movies.models import Movie, Rating, Genre


# ─────────────────────────────────────────────
# Utility: cosine similarity
# ─────────────────────────────────────────────

def cosine_similarity(vec_a: dict, vec_b: dict) -> float:
    """Compute cosine similarity between two sparse vectors (dicts)."""
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in vec_a)
    norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ─────────────────────────────────────────────
# 1. Content-Based Filtering
# ─────────────────────────────────────────────

def build_movie_feature_vector(movie: Movie) -> dict:
    """Build a feature vector for a movie from genres, director, cast."""
    vector = {}

    # Genre features (weight: 3)
    for genre in movie.genres.all():
        vector[f"genre_{genre.name.lower().replace(' ', '_')}"] = 3.0

    # Director feature (weight: 2)
    if movie.director:
        key = f"director_{movie.director.lower().replace(' ', '_')}"
        vector[key] = 2.0

    # Cast features (weight: 1)
    for actor in movie.cast_list[:5]:  # top 5 cast members
        key = f"actor_{actor.lower().replace(' ', '_')}"
        vector[key] = 1.0

    # Decade feature
    decade = (movie.year // 10) * 10
    vector[f"decade_{decade}"] = 1.0

    return vector


def get_content_based_recommendations(user, n=10, exclude_seen=True):
    """
    Recommend movies based on what the user has highly rated.
    Returns list of (movie, score, reason) tuples.
    """
    # Get user's highly-rated movies (≥ 4 stars)
    liked_ratings = Rating.objects.filter(user=user, score__gte=4).select_related('movie')
    if not liked_ratings.exists():
        return []

    # Build user taste profile (average of liked movie vectors)
    user_profile = defaultdict(float)
    for rating in liked_ratings:
        vec = build_movie_feature_vector(rating.movie)
        weight = rating.score / 5.0
        for k, v in vec.items():
            user_profile[k] += v * weight

    # Normalize profile
    total = sum(user_profile.values()) or 1
    user_profile = {k: v / total for k, v in user_profile.items()}

    # Movies to exclude
    seen_ids = set()
    if exclude_seen:
        seen_ids = set(Rating.objects.filter(user=user).values_list('movie_id', flat=True))

    # Score all candidate movies
    results = []
    for movie in Movie.objects.prefetch_related('genres').exclude(id__in=seen_ids):
        movie_vec = build_movie_feature_vector(movie)
        score = cosine_similarity(dict(user_profile), movie_vec)
        if score > 0:
            # Build human-readable reason
            top_genres = [movie.genres.first().name] if movie.genres.exists() else []
            reason = f"Matches your taste in {', '.join(top_genres) or 'similar films'}"
            results.append((movie, round(score * 100, 1), reason))

    results.sort(key=lambda x: -x[1])
    return results[:n]


# ─────────────────────────────────────────────
# 2. Collaborative Filtering (User-Based)
# ─────────────────────────────────────────────

def build_user_rating_vector(user) -> dict:
    """Build a rating vector {movie_id: score} for a user."""
    return {r.movie_id: r.score for r in Rating.objects.filter(user=user)}


def get_collaborative_recommendations(user, n=10, exclude_seen=True):
    """
    Recommend movies using user-based collaborative filtering.
    Returns list of (movie, predicted_score, reason) tuples.
    """
    from django.contrib.auth.models import User as DjangoUser

    user_vec = build_user_rating_vector(user)
    if not user_vec:
        return []

    seen_ids = set(user_vec.keys())

    # Find similar users
    other_users = DjangoUser.objects.exclude(id=user.id).filter(ratings__isnull=False).distinct()
    similarities = []

    for other in other_users:
        other_vec = build_user_rating_vector(other)
        sim = cosine_similarity(user_vec, other_vec)
        if sim > 0.1:  # only consider reasonably similar users
            similarities.append((other, sim, other_vec))

    if not similarities:
        return []

    similarities.sort(key=lambda x: -x[1])
    top_neighbors = similarities[:20]  # top 20 similar users

    # Predict ratings for unseen movies
    candidate_scores = defaultdict(list)
    for neighbor, sim, neighbor_vec in top_neighbors:
        for movie_id, score in neighbor_vec.items():
            if movie_id not in seen_ids:
                candidate_scores[movie_id].append((sim, score))

    # Weighted average prediction
    predictions = []
    for movie_id, sim_scores in candidate_scores.items():
        total_sim = sum(s for s, _ in sim_scores)
        if total_sim == 0:
            continue
        predicted = sum(s * r for s, r in sim_scores) / total_sim
        predictions.append((movie_id, predicted))

    predictions.sort(key=lambda x: -x[1])

    # Fetch top movies
    top_movie_ids = [mid for mid, _ in predictions[:n]]
    movies_by_id = {m.id: m for m in Movie.objects.filter(id__in=top_movie_ids).prefetch_related('genres')}

    results = []
    for movie_id, score in predictions[:n]:
        if movie_id in movies_by_id:
            movie = movies_by_id[movie_id]
            reason = "Loved by users with similar taste to you"
            results.append((movie, round(score * 20, 1), reason))  # scale to 0-100

    return results


# ─────────────────────────────────────────────
# 3. Hybrid Recommender
# ─────────────────────────────────────────────

def get_hybrid_recommendations(user, n=12):
    """
    Blend content-based and collaborative recommendations.
    Returns list of (movie, score, reason, method) dicts.
    """
    content_recs = {m.id: (m, s, r) for m, s, r in get_content_based_recommendations(user, n=20)}
    collab_recs = {m.id: (m, s, r) for m, s, r in get_collaborative_recommendations(user, n=20)}

    all_ids = set(content_recs) | set(collab_recs)
    blended = []

    for mid in all_ids:
        c_score = content_recs[mid][1] if mid in content_recs else 0
        cf_score = collab_recs[mid][1] if mid in collab_recs else 0

        # Weighted blend: 40% content, 60% collaborative
        hybrid_score = 0.4 * c_score + 0.6 * cf_score

        if mid in content_recs:
            movie, _, reason = content_recs[mid]
        else:
            movie, _, reason = collab_recs[mid]

        method = "Hybrid AI"
        if mid in content_recs and mid in collab_recs:
            reason = "Perfect match: fits your taste & loved by similar users"
        elif mid in collab_recs:
            reason = "Highly rated by users who think like you"

        blended.append({
            'movie': movie,
            'score': round(hybrid_score, 1),
            'reason': reason,
            'method': method,
        })

    blended.sort(key=lambda x: -x['score'])
    return blended[:n]


# ─────────────────────────────────────────────
# 4. Trending / Popular (cold start fallback)
# ─────────────────────────────────────────────

def get_trending_movies(n=12):
    """Return trending movies based on rating count and average score."""
    from django.db.models import Avg, Count
    return (
        Movie.objects
        .annotate(avg_score=Avg('ratings__score'), num_ratings=Count('ratings'))
        .filter(num_ratings__gte=1)
        .order_by('-avg_score', '-num_ratings')[:n]
    )


def get_similar_movies(movie: Movie, n=6):
    """Find movies similar to a given movie using content-based approach."""
    target_vec = build_movie_feature_vector(movie)
    results = []
    for other in Movie.objects.exclude(id=movie.id).prefetch_related('genres'):
        other_vec = build_movie_feature_vector(other)
        score = cosine_similarity(target_vec, other_vec)
        if score > 0:
            results.append((other, score))
    results.sort(key=lambda x: -x[1])
    return [m for m, _ in results[:n]]
