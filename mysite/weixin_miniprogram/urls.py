from django.urls import path
from .api_views import JSCode2SessionView, UserActivities, CheckListView

urlpatterns = [
    path('api/jscode2session/',
         JSCode2SessionView.as_view(),
         name='jscode2session-api-view'),

    path('api/user-activities/',
         UserActivities.as_view(),
         name='user-activities-api-view'),

    path('api/check-list/',
         CheckListView.as_view(),
         name='check-list-api-view'),
]
