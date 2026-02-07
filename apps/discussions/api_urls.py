from django.urls import path

from .api_views import (
    PostCommentListView,
    PostDetailView,
    PostListView,
    SubjectListView,
)

urlpatterns = [
    path("subjects/", SubjectListView.as_view(), name="api-subjects-list"),
    path("posts/", PostListView.as_view(), name="api-posts-list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="api-posts-detail"),
    path(
        "posts/<int:post_id>/comments/",
        PostCommentListView.as_view(),
        name="api-posts-comments",
    ),
]
