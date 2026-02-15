from django.urls import path

from . import views

urlpatterns = [
    path('marketplace/', views.listings_page, name='marketplace-page'),
    path('marketplace/<int:listing_id>/', views.listing_detail_page, name='marketplace-detail-page'),
]
