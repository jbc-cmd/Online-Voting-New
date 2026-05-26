from django.urls import path
from audit import views

app_name = 'audit'

urlpatterns = [
    path('audit-logs/', views.audit_log_list, name='audit_logs'),
    path('verification-logs/', views.verification_log_list, name='verification_logs'),
    path('evaluation/', views.system_evaluation, name='system_evaluation'),
]
