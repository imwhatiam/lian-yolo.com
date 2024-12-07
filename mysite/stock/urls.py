from django.urls import path
from . import views

urlpatterns = [
    path('fupan/', views.fupan, name='stock_fupan'),
]
