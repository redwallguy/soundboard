from django.urls import path, re_path
from . import boardviews
from . import apiviews
from . import authviews

urlpatterns = [
    path('', boardviews.boards, name='boards'),
    re_path(r'^boards/(?P<spec_board>\w{1,20})/$',
            boardviews.clips_of_board, name='clips'),
    path('auth', authviews.authcode, name="auth"),
    path('api',apiviews.api, name='api'),
    path('callmilton', apiviews.callmilton, name='callmilton'),
    path('login', authviews.login, name='login'),

]
