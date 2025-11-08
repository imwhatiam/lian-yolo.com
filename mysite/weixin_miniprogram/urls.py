from django.urls import path
from .api_views import (
    JSCode2SessionView,
    CheckListView,
    CheckListSearchView,
    ActivitiesView,
    ActivityView,
    ActivityWhiteListView,
    ActivityItemsView,
    ActivityItemsInitView,
    ActivityItemView
)
from . import views

urlpatterns = [
    path('checklist/', views.checklist_tree, name='checklist_tree'),

    path('api/jscode2session/',
         JSCode2SessionView.as_view(),
         name='jscode2session-api-view'),

    path('api/check-list/',
         CheckListView.as_view(),
         name='checklist-api-view'),
    path('api/checklist/',
         CheckListView.as_view(),
         name='checklist-api-view'),

    path('api/checklist/search/',
         CheckListSearchView.as_view(),
         name='checklist-search-api-view'),

    # 使用新的 APIView 类
    path('api/activities/', ActivitiesView.as_view(), name='activities'),
    path('api/activities/<int:activity_id>/', ActivityView.as_view(), name='activity'),
    path('api/activities/<int:activity_id>/white_list/', ActivityWhiteListView.as_view(), name='activity_white_list'),
    path('api/activities/<int:activity_id>/items/', ActivityItemsView.as_view(), name='activity_items'),
    path('api/activities/<int:activity_id>/init-items/', ActivityItemsInitView.as_view(), name='activity_items_init'),
    path('api/activities/<int:activity_id>/items/<str:item_id>/', ActivityItemView.as_view(), name='activity_item'),
]
