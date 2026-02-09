from django.urls import path

from .api_views import (
    CommentVoteAPIView,
    LeaderboardAPIView,
    PostCommentListView,
    PostDetailView,
    PostListView,
    PostVoteAPIView,
    SubjectListView,
)

urlpatterns = [
    path("subjects/", SubjectListView.as_view(), name="api-subjects-list"),
    path("posts/", PostListView.as_view(), name="api-posts-list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="api-posts-detail"),
    path(
        "posts/<int:pk>/vote/",
        PostVoteAPIView.as_view(),
        name="api-posts-vote",
    ),
    path(
        "posts/<int:post_id>/comments/",
        PostCommentListView.as_view(),
        name="api-posts-comments",
    ),
    path(
        "comments/<int:pk>/vote/",
        CommentVoteAPIView.as_view(),
        name="api-comments-vote",
    ),
    path("leaderboard/", LeaderboardAPIView.as_view(), name="leaderboard"),
]
