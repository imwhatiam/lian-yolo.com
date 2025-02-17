from django.urls import path
from . import views, api_views

urlpatterns = [
    path('api/big-rise-volume/',
         api_views.BigRiseVolumeAPIView.as_view(),
         name='big-rise-volume-api-view'),

    path('api/trading-crowding/',
         api_views.TradingCrowdingAPIView.as_view(),
         name='wind-info-api-view'),

    path('api/wind-info/',
         api_views.WindInfoAPIView.as_view(),
         name='wind-info-api-view'),

    path('fupan/', views.fupan, name='stock_fupan'),
    path('import-industry-stock/',
         views.import_industry_stock,
         name='stock_import_industry_stock'),
]
