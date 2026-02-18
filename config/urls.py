from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from letters import views as letter_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("media/<path:file_path>", letter_views.media_file, name="media_file"),
    path("", include("letters.urls")),
]

if settings.DEBUG or settings.SERVE_MEDIA_FILES:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
