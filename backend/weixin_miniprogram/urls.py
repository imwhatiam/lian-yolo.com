from django.urls import path
from .api_views import (
    JSCode2SessionView,
    ActivitiesView,
    ActivityView,
    ActivityCopyToMyView,
    ActivityWhiteListView,
    ActivityItemsView,
    ActivityItemsInitView,
    ActivityItemView
)

urlpatterns = [
    path('api/jscode2session/',
         JSCode2SessionView.as_view(),
         name='jscode2session-api-view'),

    path('api/activities/', ActivitiesView.as_view(), name='activities'),
    path('api/activities/<int:activity_id>/', ActivityView.as_view(), name='activity'),
    path('api/activities/<int:activity_id>/copy-to-my/', ActivityCopyToMyView.as_view(), name='activity-copy-to-my'),
    path('api/activities/<int:activity_id>/white_list/', ActivityWhiteListView.as_view(), name='activity_white_list'),
    path('api/activities/<int:activity_id>/items/', ActivityItemsView.as_view(), name='activity_items'),
    path('api/activities/<int:activity_id>/init-items/', ActivityItemsInitView.as_view(), name='activity_items_init'),
    path('api/activities/<int:activity_id>/items/<str:item_id>/', ActivityItemView.as_view(), name='activity_item'),
]
