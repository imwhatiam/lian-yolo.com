from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^lesson-(\d+)/$', views.lesson, name='react-naive-book-lesson'),
]
