from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('deposit/', views.deposit, name='deposit'),
    path('transactions/deposit/', views.deposit_transactions, name='deposit_transactions'),
    path('request_ad_account/', views.request_ad_account, name='request_ad_account'),
    path('ad_accounts/', views.ad_accounts, name='ad_accounts'),
]