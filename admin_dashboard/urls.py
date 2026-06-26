from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.admin_overview, name='admin_overview'),
    path('overview/', views.admin_overview, name='admin_overview_alt'),
    path('ad_accounts/', views.admin_ad_accounts, name='admin_ad_accounts'),
    path('wallet_balance_report/', views.wallet_balance_report, name='wallet_balance_report'),
    path('payment_methods/', views.payment_methods, name='payment_methods'),
    path('withdrawal_requests/', views.withdrawal_requests, name='withdrawal_requests'),
    path('review/deposit/', views.review_deposit, name='review_deposit'),
    path('review/deposit/<int:transaction_id>/', views.review_deposit_details, name='review_deposit_details'),
    path('review/ad_account/', views.review_ad_account, name='review_ad_account'),
    path('ad_accounts/<int:ad_account_id>/', views.ad_account_details, name='ad_account_details'),
    path('transfer_ad_account/', views.transfer_ad_account, name='transfer_ad_account'),
    path('review/bm_request/', views.review_bm_request, name='review_bm_request'),
    path('manage_user/', views.manage_user, name='manage_user'),
    path('roles/', views.manage_roles, name='manage_roles'),
    path('roles/<int:group_id>/edit/', views.edit_role, name='edit_role'),
    path('api/user/<int:user_id>/', views.user_api, name='user_api'),
    path('create_manual_client/', views.create_manual_client, name='create_manual_client'),
    path('edit_wallet_balance/', views.edit_wallet_balance, name='edit_wallet_balance'),
    path('delete_user/', views.delete_user, name='delete_user'),
    path('review/topup/', views.review_topup, name='review_topup'),
    path('delete_old_receipts/', views.delete_old_receipts, name='delete_old_receipts'),
    path('activity_log/', views.activity_log, name='activity_log'),
    path('appearance/', views.appearance, name='appearance'),
    path('admin_bm/', views.manage_admin_bm, name='manage_admin_bm'),
    path('admin_bm/add/', views.add_admin_bm, name='add_admin_bm'),
    path('admin_bm/<int:admin_bm_id>/edit/', views.edit_admin_bm, name='edit_admin_bm'),
    path('admin_bm/<int:admin_bm_id>/delete/', views.delete_admin_bm, name='delete_admin_bm'),
]