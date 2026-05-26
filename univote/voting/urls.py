from django.urls import path
from voting import views

app_name = 'voting'

urlpatterns = [
    path('<slug:slug>/', views.credential_form, name='credential_form'),
    path('<slug:slug>/send-otp/', views.send_otp_view, name='send_otp'),
    path('<slug:slug>/verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('<slug:slug>/resend-otp/', views.resend_otp, name='resend_otp'),
    path('<slug:slug>/ballot/', views.ballot_view, name='ballot'),
    path('<slug:slug>/review/', views.review_view, name='review'),
    path('<slug:slug>/submit/', views.submit_view, name='submit'),
    path('<slug:slug>/receipt/<str:ballot_number>/', views.receipt_view, name='receipt'),
]
