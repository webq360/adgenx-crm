from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('review/deposit/', views.review_deposit, name='review_deposit'),
    path('review/deposit/<int:transaction_id>/', views.review_deposit_details, name='review_deposit_details'),
    path('review/ad_account/', views.review_ad_account, name='review_ad_account'),
    path('ad_accounts/<int:ad_account_id>/', views.ad_account_details, name='ad_account_details'),
]