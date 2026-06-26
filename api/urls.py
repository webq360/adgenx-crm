from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('auth/api/login/',           views.api_login,            name='api_login'),
    path('auth/api/register/',        views.api_register,         name='api_register'),
    path('auth/api/logout/',          views.api_logout,           name='api_logout'),
    path('auth/api/forgot-password/', views.api_forgot_password,  name='api_forgot_password'),

    # Profile
    path('api/profile/',                      views.api_profile,         name='api_profile'),
    path('api/profile/change_password/',      views.api_change_password, name='api_change_password'),

    # Dashboard
    path('api/dashboard/',            views.api_dashboard,        name='api_dashboard'),

    # Ad Accounts
    path('api/ad-accounts/',                          views.api_ad_accounts,          name='api_ad_accounts'),
    path('api/ad-accounts/<int:ad_account_id>/fb_info/', views.api_ad_account_fb_info, name='api_ad_account_fb_info'),
    path('api/request-ad-account/',               views.api_request_ad_account,   name='api_request_ad_account'),

    # Topup
    path('api/topup/',                views.api_topup,            name='api_topup'),
    path('api/decrease-limit/',       views.api_decrease_limit,   name='api_decrease_limit'),
    path('api/topup-transactions/',   views.api_topup_transactions, name='api_topup_transactions'),

    # Deposit
    path('api/payment-methods/',      views.api_payment_methods,  name='api_payment_methods'),
    path('api/deposit/',              views.api_deposit,          name='api_deposit'),
    path('api/deposit-transactions/', views.api_deposit_transactions, name='api_deposit_transactions'),

    # BM
    path('api/request-bm/',           views.api_request_bm,      name='api_request_bm'),
    path('api/remove-bm/',            views.api_remove_bm,        name='api_remove_bm'),

    # Notifications
    path('api/notifications/',             views.api_notifications,           name='api_notifications'),
    path('api/notifications/read/',        views.api_mark_notifications_read, name='api_mark_notifications_read'),
    path('api/notifications/unread-count/', views.api_unread_count,           name='api_unread_count'),
    
    # CORS Test
    path('api/cors-test/', views.api_cors_test, name='api_cors_test'),
]
