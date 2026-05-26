from django.urls import path
from elections import views

app_name = 'elections'

urlpatterns = [
    path('elections/', views.election_list, name='election_list'),
    path('elections/create/', views.election_create, name='election_create'),
    path('elections/<int:pk>/edit/', views.election_edit, name='election_edit'),
    path('elections/<int:pk>/delete/', views.election_delete, name='election_delete'),
    path('elections/<int:pk>/toggle/', views.election_toggle, name='election_toggle'),
    path('elections/<int:pk>/positions/', views.manage_positions, name='manage_positions'),
    path('elections/<int:pk>/candidates/', views.manage_candidates, name='manage_candidates'),
    path('elections/<int:pk>/results/', views.election_results, name='election_results'),
]
