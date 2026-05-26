"""
Univote URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Root redirect → admin login
    path('', RedirectView.as_view(url='/admin-panel/login/', permanent=False)),

    path('django-admin/', admin.site.urls),  # Keep default Django admin hidden
    path('admin-panel/', include('accounts.urls')),
    path('admin-panel/', include('elections.urls')),
    path('admin-panel/', include('students.urls')),
    path('admin-panel/', include('analytics.urls')),
    path('admin-panel/', include('exports.urls')),
    path('admin-panel/', include('audit.urls')),
    path('vote/', include('voting.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

