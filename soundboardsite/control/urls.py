from django.urls import path, re_path
from . import boardviews
from . import apiviews
from . import authviews
from django.contrib.auth import views as django_auth_views

urlpatterns = [
    path('', boardviews.boards, name='boards'),
    re_path(r'^boards/(?P<spec_board>\w{1,20})/$',
            boardviews.clips_of_board, name='clips'),
    path('auth', authviews.authcode, name="auth"),
    path('api',apiviews.api, name='api'),
    path('callmilton', apiviews.callmilton, name='callmilton'),
    path('login', django_auth_views.login, {"template_name": "control/registration/login.html"}, name='login'),
    path('logout', django_auth_views.logout, {"next_page": "boards"}, name='logout'),
    path('create_user', authviews.create_user, name='create_user'),
    path('change_password', django_auth_views.password_change,{"template_name": "control/registration/password_change_form.html"}, name='change_password'),
    path('password_change_done', django_auth_views.password_change_done, {"template_name": "control/registration/password_change_done.html"}, name='password_change_done'),
    path('app_login', authviews.app_login, name='app_login'),
    path('test_token', authviews.test_token, name='test_token'),
    path('discord', authviews.discord_view, name='discord'),

]
