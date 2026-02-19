from django.urls import path

from . import views

urlpatterns = [
    path('discussions/', views.discussions_page, name='discussions-page'),
    path('discussions/publish/', views.publish_post_page, name='discussions-publish-page'),
    path('discussions/my-discussions/', views.my_discussions_page, name='my-discussions-page'),
    path('discussions/my-discussions/<int:post_id>/edit/', views.edit_my_discussion_page, name='my-discussions-edit-page'),
    path('discussions/my-discussions/<int:post_id>/delete/', views.delete_my_discussion_page, name='my-discussions-delete-page'),
    path('subjects/<slug:slug>/', views.subjects_page, name='subjects-page'),
    path('posts/<int:post_id>/', views.post_detail_page, name='post-detail-page'),
]
