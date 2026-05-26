from django.urls import path
from students import views

app_name = 'students'

urlpatterns = [
    path('students/', views.student_list, name='student_list'),
    path('students/create/', views.student_create, name='student_create'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('students/import/', views.student_import, name='student_import'),
    path('departments/', views.department_list, name='department_list'),
    path('programs/', views.program_list, name='program_list'),
    path('classes/', views.class_list, name='class_list'),
    path('organizations/', views.organization_list, name='organization_list'),
]
