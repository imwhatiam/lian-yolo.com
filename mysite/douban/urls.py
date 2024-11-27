from django.urls import path
from . import views

urlpatterns = [
    path('zufang/', views.zufang, name='douban_zufang'),
    path('jiaoyou/', views.jiaoyou, name='douban_jiaoyou'),
]
