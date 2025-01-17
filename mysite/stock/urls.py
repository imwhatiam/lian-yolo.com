from django.urls import path
from . import views, api_views

urlpatterns = [
    path('api/stock-industry-info/',
         api_views.StockIndustryInfoAPIView.as_view(),
         name='stock-industry-info-api-view'),

    path('fupan/', views.fupan, name='stock_fupan'),
]
