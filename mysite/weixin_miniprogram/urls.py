from django.urls import path
from .api_views import JSCode2SessionView, UserActivities, \
        CheckListView, CheckListSearchView
from .views import checklist_tree

urlpatterns = [
    path('checklist/', checklist_tree, name='checklist_tree'),

    path('api/jscode2session/',
         JSCode2SessionView.as_view(),
         name='jscode2session-api-view'),

    path('api/user-activities/',
         UserActivities.as_view(),
         name='user-activities-api-view'),

    path('api/check-list/',
         CheckListView.as_view(),
         name='checklist-api-view'),
    path('api/checklist/',
         CheckListView.as_view(),
         name='checklist-api-view'),

    path('api/checklist/search/',
         CheckListSearchView.as_view(),
         name='checklist-search-api-view'),
]
