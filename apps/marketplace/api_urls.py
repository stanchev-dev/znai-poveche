from django.urls import path

from .api_views import (
    ListingContactAPIView,
    ListingDetailAPIView,
    ListingListCreateAPIView,
)

urlpatterns = [
    path(
        "listings/",
        ListingListCreateAPIView.as_view(),
        name="listing-list-create",
    ),
    path(
        "listings/<int:pk>/",
        ListingDetailAPIView.as_view(),
        name="listing-detail",
    ),
    path(
        "listings/<int:pk>/contact/",
        ListingContactAPIView.as_view(),
        name="listing-contact",
    ),
]
