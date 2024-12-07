from django.urls import path
from . import views, api_views

urlpatterns = [
    path('api/basic-info/',
         api_views.StockBasicInfoAPIView.as_view(),
         name='stock-basic-info-api-view'),

    path('fupan/', views.fupan, name='stock_fupan'),
]
