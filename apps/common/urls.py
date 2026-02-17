from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard-page'),
    path('mission/', TemplateView.as_view(template_name='common/mission.html'), name='mission-page'),
    path('terms/', TemplateView.as_view(template_name='common/terms.html'), name='terms-page'),
    path('privacy/', TemplateView.as_view(template_name='common/privacy.html'), name='privacy-page'),
]
