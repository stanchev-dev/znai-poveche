from django.urls import path

from . import views

urlpatterns = [
    path('discussions/', views.discussions_page, name='discussions-page'),
    path('discussions/publish/', views.publish_post_page, name='discussions-publish-page'),
    path('subjects/<slug:slug>/', views.subjects_page, name='subjects-page'),
    path('posts/<int:post_id>/', views.post_detail_page, name='post-detail-page'),
]
