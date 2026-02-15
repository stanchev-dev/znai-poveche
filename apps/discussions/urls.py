from django.urls import path

from . import views

urlpatterns = [
    path('subjects/<slug:slug>/', views.subjects_page, name='subjects-page'),
    path('posts/<int:post_id>/', views.post_detail_page, name='post-detail-page'),
]
