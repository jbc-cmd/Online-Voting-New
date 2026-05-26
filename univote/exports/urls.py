from django.urls import path
from exports import views

app_name = 'exports'

urlpatterns = [
    path('elections/<int:pk>/export/csv/', views.export_results_csv, name='results_csv'),
    path('elections/<int:pk>/export/excel/', views.export_results_excel, name='results_excel'),
    path('elections/<int:pk>/export/pdf/', views.export_results_pdf, name='results_pdf'),
    path('elections/<int:pk>/export/turnout/csv/', views.export_turnout_csv, name='turnout_csv'),
    path('export/verification-logs/csv/', views.export_verification_logs_csv, name='verification_csv'),
    path('export/audit-logs/csv/', views.export_audit_logs_csv, name='audit_csv'),
]
