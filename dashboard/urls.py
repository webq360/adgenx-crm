from django.urls import path, include
from . import views

urlpatterns = [
    path('', include('authentication.urls')),
    path('', views.index, name='index'),
    path('ad_accounts/', views.ad_accounts, name='ad_accounts'),
    path('deposit/', views.deposit, name='deposit'),
    path('transactions/deposit/', views.deposit_transactions, name='deposit_transactions'),
    path('transactions/topup/', views.topup_transactions, name='topup_transactions'),
    path('request_ad_account/', views.request_ad_account, name='request_ad_account'),
    path('topup/', views.topup, name='topup'),
    path('request_bm_account/', views.request_bm_account, name='request_bm_account'),
    path('remove_bm_account_request/', views.remove_bm_account_request, name='remove_bm_account_request'),
    path('request_decrease_limit/', views.request_decrease_limit, name='request_decrease_limit'),
    path('account_settings/', views.account_settings, name='account_settings'),
]