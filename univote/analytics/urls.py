from django.urls import path
from analytics import views

app_name = 'analytics'

urlpatterns = [
    path('analytics/', views.analytics_dashboard, name='dashboard'),
    path('analytics/<int:pk>/data/', views.analytics_data, name='data'),
]
