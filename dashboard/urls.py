from django.urls import path, include
from . import views
from . import test_context
from . import force_logout_view
from . import visual_test_view

urlpatterns = [
    path('', include('authentication.urls')),
    path('', views.landing, name='landing'),
    path('dashboard/', views.index, name='index'),
    path('test-permissions/', visual_test_view.visual_permission_test, name='visual_test'),  # BEAUTIFUL test page
    path('force-logout/', force_logout_view.force_logout, name='force_logout'),  # Force logout
    path('ad_accounts/', views.ad_accounts, name='ad_accounts'),
    path('ad_accounts/add/', views.add_ad_account_page, name='add_ad_account_page'),
    path('ad_accounts/fb_info/<int:ad_account_id>/', views.get_ad_account_fb_info, name='get_ad_account_fb_info'),
    path('add_ad_account/', views.add_ad_account, name='add_ad_account'),
    path('deposit/', views.deposit, name='deposit'),
    path('withdrawal/', views.withdrawal, name='withdrawal'),
    path('transactions/deposit/', views.deposit_transactions, name='deposit_transactions'),
    path('transactions/topup/', views.topup_transactions, name='topup_transactions'),
    path('transactions/withdrawal/', views.withdrawal_transactions, name='withdrawal_transactions'),
    path('request_ad_account/', views.request_ad_account, name='request_ad_account'),
    path('topup/', views.topup, name='topup'),
    path('request_bm_account/', views.request_bm_account, name='request_bm_account'),
    path('remove_bm_account_request/', views.remove_bm_account_request, name='remove_bm_account_request'),
    path('request_decrease_limit/', views.request_decrease_limit, name='request_decrease_limit'),
    path('edit_ad_account/', views.edit_ad_account, name='edit_ad_account'),
    path('delete_ad_account/', views.delete_ad_account, name='delete_ad_account'),
    path('account_settings/', views.account_settings, name='account_settings'),
]