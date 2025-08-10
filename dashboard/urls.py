from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', views.auth, name='auth'),
    path('logout/', views.logout_view, name='logout'),
    path('deposit/', views.deposit, name='deposit'),
    path('transactions/deposit/', views.deposit_transactions, name='deposit_transactions'),
    path('review/deposit/', views.review_deposit, name='review_deposit'),
    path('review/deposit/<int:transaction_id>/', views.review_deposit_details, name='review_deposit_details'),
    path('review/ad_account/', views.review_ad_account, name='review_ad_account'),
    path('request_ad_account/', views.request_ad_account, name='request_ad_account'),
    path('ad_accounts/', views.ad_accounts, name='ad_accounts'),
    path('ad_accounts/<int:ad_account_id>/', views.ad_account_details, name='ad_account_details'),
]