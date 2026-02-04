from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Web pages
    path('', include('apps.common.urls')),

    # API routes
    path('api/', include('apps.common.api_urls')),
    path('api/', include('apps.discussions.api_urls')),
    path('api/', include('apps.marketplace.api_urls')),
    path('api/', include('apps.moderation.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
