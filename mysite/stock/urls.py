from django.urls import path
from . import views, api_views

urlpatterns = [
    path('api/stock-industry-info/',
         api_views.StockIndustryInfoAPIView.as_view(),
         name='stock-industry-info-api-view'),

    path('api/big-rise-volume/',
         api_views.BigRiseVolumeAPIView.as_view(),
         name='big-rise-volume-api-view'),

    path('fupan/', views.fupan, name='stock_fupan'),
]
