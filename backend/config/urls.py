from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.views.static import serve
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST = BASE_DIR.parent / 'frontend' / 'dist'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('reconciliation.urls')),
    re_path(r'^assets/(?P<path>.*)$', serve, {'document_root': FRONTEND_DIST / 'assets'}),
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html'), name='home'),
]
