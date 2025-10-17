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

    path('api/activities/', views.create_activity, name='create_activity'),
    path('api/activities/<int:id>/', views.get_activity_detail, name='get_activity_detail'),
    path('api/activities/<int:id>/white_list/add/', views.add_white_list, name='add_white_list'),
    path('api/activities/<int:id>/white_list/remove/', views.remove_white_list, name='remove_white_list'),
    path('api/activities/<int:id>/items/update/', views.update_activity_item, name='update_activity_item'),
    path('api/activities/<int:id>/items/add/', views.add_activity_item, name='add_activity_item'),
]
