from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('movie/<int:pk>/', views.movie_detail, name='movie_detail'),
    path('movie/<int:pk>/rate/', views.rate_movie, name='rate_movie'),
    path('movie/<int:pk>/watchlist/', views.toggle_watchlist, name='toggle_watchlist'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('profile/', views.profile, name='profile'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # My Collection
    path('collection/', views.my_collection, name='my_collection'),
    path('collection/add/', views.add_user_movie, name='add_user_movie'),
    path('collection/edit/<int:pk>/', views.edit_user_movie, name='edit_user_movie'),
    path('collection/delete/<int:pk>/', views.delete_user_movie, name='delete_user_movie'),
    path('collection/favourite/<int:pk>/', views.toggle_favourite, name='toggle_favourite'),
]
