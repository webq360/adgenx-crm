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
]