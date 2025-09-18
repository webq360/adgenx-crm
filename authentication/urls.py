from django.urls import path
from . import views

urlpatterns = [
    path('auth/', views.auth_view, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('forget_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<uidb64>/<token>/', views.password_reset, name='password_reset'),
]
