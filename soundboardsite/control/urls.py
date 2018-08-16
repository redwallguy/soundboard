from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.boards, name='boards'),
    re_path(r'^boards/(?P<spec_board>\w{1,20})/$',
            views.clips_of_board, name='clips'),
    path('auth', views.auth, name="auth"),
    path('api',views.api, name='api'),
    
]
