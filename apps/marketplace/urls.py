from django.urls import path

from . import views

urlpatterns = [
    path('marketplace/', views.listings_page, name='marketplace-page'),
    path('marketplace/my-listings/', views.my_listings_page, name='marketplace-my-listings-page'),
    path('marketplace/publish/', views.publish_listing_page, name='marketplace-publish-page'),
    path('marketplace/<int:listing_id>/edit/', views.edit_listing_page, name='marketplace-edit-page'),
    path('marketplace/<int:listing_id>/delete/', views.delete_listing_page, name='marketplace-delete-page'),
    path('marketplace/<int:listing_id>/', views.listing_detail_page, name='marketplace-detail-page'),
]
