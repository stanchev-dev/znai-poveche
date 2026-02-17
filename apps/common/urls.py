from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard-page'),
    path('mission/', views.mission, name='mission-page'),
    path('terms/', views.terms, name='terms-page'),
    path('privacy/', views.privacy, name='privacy-page'),
]
