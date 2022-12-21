from django.urls import path
from .views import get_listing, department_list, get_student_listing
from .wagtail_views import edit, index, create
app_name = "users"
urlpatterns = [
    path("list", get_listing, name="get_listing"),
    path("list/student", get_student_listing, name="get_student_listing"),
    path("department/list", department_list, name="department_list"),
    # path("", index, name="index"),
    # path("add/", create, name="add"),
    # path("<str:user_id>/", edit, name="edit"),
    
    # re_path(r'^create/$', post_create, name='post_create'),
    # re_path(r'^(?P<id>\d+)/edit_post/$', post_update, name='post_update'),
    # re_path(r'^(?P<id>\d+)/delete_post/$', post_delete, name='post_delete'),
    # re_path(r'^(\d+)/toggle/$', toggle_comment, name='toggle_comment'),
    # re_path(r'^(\d+)/deletecomment/$', delete_comment, name='delete_comment'),
    # re_path(r'^(?P<id>\d+)/edit_featuredpost/$', featuredpost_update, name='featuredpost_update'),
    # url(r'^captcha/', include('captcha.urls')),
]
