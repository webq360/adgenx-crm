from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify_email'),
    path('forget_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>/', views.password_reset, name='password_reset'),
]
