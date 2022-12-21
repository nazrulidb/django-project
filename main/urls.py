from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include, re_path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from django.views.generic import TemplateView

from wagtail.contrib.sitemaps.views import sitemap
from wagtail.images.views.serve import ServeView
from search import views as search_views
from students.views import StudentLogin, user_logout
from .views import cert, exam_result

urlpatterns = [
    path('django_admin/', admin.site.urls),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("student/login/", StudentLogin.as_view(), name="student_login"),
    path("student/logout/", user_logout, name="student_logout"),
    path("search/", search_views.search, name="search"),
    path("sitemap.xml", sitemap),
    # path('students/', include('students.urls')),
    path("users/", include("users.urls")),
    path("departments/", include("departments.urls")),
    path("batch_records/", include("custom_dashboard.urls")),
    path(
        "service_worker",
        (
            TemplateView.as_view(
                template_name="service_worker.js", content_type="application/javascript"
            )
        ),
        name="service_worker",
    ),
    # path('manifest', (
    #     TemplateView.as_view(
    #         template_name="manifest.json",
    #         content_type='application/json')), name='manifest'),
    re_path(
        r"^images/([^/]*)/(\d*)/([^/]*)/[^/]*$",
        ServeView.as_view(),
        name="wagtailimages_serve",
    ),
    path('cert', cert, name="cert"),
    path("exam_result/<int:id>/", exam_result, name="exam_result"),
]


if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    path("pages/", include(wagtail_urls)),
]
