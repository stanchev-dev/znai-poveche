from django.db.models import Q
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination

from .models import Comment, Post, Subject
from .serializers import (
    CommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
    SubjectSerializer,
)


class PostPagination(PageNumberPagination):
    page_size = 10


class SubjectListView(ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class PostListView(ListAPIView):
    serializer_class = PostListSerializer
    pagination_class = PostPagination

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("subject", "author", "author__profile")
            .all()
        )
        subject_slug = self.request.query_params.get("subject")
        if subject_slug and subject_slug != "all":
            queryset = queryset.filter(subject__slug=subject_slug)

        search_text = self.request.query_params.get("q")
        if search_text:
            queryset = queryset.filter(
                Q(title__icontains=search_text) | Q(body__icontains=search_text)
            )

        sort = self.request.query_params.get("sort", "new")
        if sort == "top":
            queryset = queryset.order_by("-score", "-created_at")
        else:
            queryset = queryset.order_by("-created_at")

        return queryset


class PostDetailView(RetrieveAPIView):
    queryset = Post.objects.select_related(
        "subject",
        "author",
        "author__profile",
    )
    serializer_class = PostDetailSerializer


class PostCommentListView(ListAPIView):
    serializer_class = CommentSerializer

    def get_queryset(self):
        return (
            Comment.objects.select_related("author", "author__profile")
            .filter(post_id=self.kwargs["post_id"])
            .all()
        )
