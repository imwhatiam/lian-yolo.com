from django.urls import path
from .api_views import JSCode2SessionView, \
        CheckListView, CheckListSearchView
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

    path('api/activities/', views.activities, name='activities'),
    path('api/activities/<int:activity_id>/', views.activity, name='activity'),
    path('api/activities/<int:activity_id>/white_list/', views.activity_white_list, name='activity_white_list'),
    path('api/activities/<int:activity_id>/items/', views.activity_items, name='activity_items'),
    path('api/activities/<int:activity_id>/items/<str:item_id>/', views.activity_item, name='activity_item'),
]
