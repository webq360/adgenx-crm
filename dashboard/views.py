from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, DepositTransaction, Wallet, AdAccount, BMAccount
from django.contrib import messages
from django.http import JsonResponse
import json

from .fb_api_reqs import change_spend_cap, get_ad_account_info

# Create your views here.

def get_utils(user):
    pending_deposits = DepositTransaction.objects.filter(user=user, status='pending').count()
    pending_accounts = AdAccount.objects.filter(user=user, status='inactive').count()
    return {
        'pending_deposits': pending_deposits,
        'pending_accounts': pending_accounts
    }

@login_required(login_url='auth')
def index(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:review_deposit')  # Redirect staff to review deposits
    wallet = Wallet.objects.get(user=request.user)
    ad_accounts_qs = AdAccount.objects.filter(user=request.user, status='active').order_by('-start_date')
    
    ad_accounts = []
    for acc in ad_accounts_qs:
        ad_info = get_ad_account_info(acc.acc_id)
        acc.balance = ad_info.get('balance', 0)
        spend_cap_str = ad_info.get('spend_cap', '0')
        try:
            acc.limit = float(spend_cap_str) / 100
        except (ValueError, TypeError):
            acc.limit = 0
        acc.total_spent = ad_info.get('amount_spent', 0)
        print(acc.limit)
        ad_accounts.append(acc)

    utils = get_utils(request.user)
    return render(request, 'index.html', {'wallet': wallet, 'ad_accounts': ad_accounts, 'utils': utils})       

def auth(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('index')
        elif action == 'register':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')

            if password == password2:
                if User.objects.filter(email=email).exists():
                    # Handle existing user
                    pass
                else:
                    user = User.objects.create_user(
                        username=email, 
                        email=email, 
                        password=password, 
                        first_name=first_name, 
                        last_name=last_name
                    )
                    login(request, user)
                    Wallet.objects.create(user=user)
                    return redirect('index')
    return render(request, 'auth.html')

@login_required(login_url='auth')
def deposit(request):
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method').capitalize()
        bdt_amount = request.POST.get('bdt_amount')
        tx_id = request.POST.get('tx_id')
        receipt = request.FILES.get('receipt')
        usd_amount = request.POST.get('usd_amount')

        try:
            deposit_transaction = DepositTransaction.objects.create(
                user=request.user,
                method=payment_method,
                trx_id=tx_id,
                vendor_trx_id=tx_id, # Assuming vendor_trx_id is same as trx_id for now
                receipt=receipt,
                bdt_amount=bdt_amount,
                usd_amount=usd_amount,
                status='pending'
            )

            messages.success(request, 'Deposit request submitted successfully!')
            return redirect('index') # Redirect to transactions page after successful submission
        except Exception as e:
            messages.error(request, f'Error submitting deposit request: {e}')
            return redirect('deposit') # Redirect back to deposit page on error
        
    return render(request, 'deposit.html')

@login_required(login_url='auth')
def deposit_transactions(request):
    if request.user.is_staff:
        transactions = DepositTransaction.objects.all().order_by('-created_at')
    else:
        transactions = DepositTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transactions.html', {'transactions': transactions})

@login_required(login_url='auth')
def request_ad_account(request):
    if request.method == 'POST':
        name = request.POST.get('accountName')
        bm_client_id = request.POST.get('bmId')
        acc_link = request.POST.get('fbPageLink')
        start_date = request.POST.get('startDate')
        monthly_budget = request.POST.get('monthly_budget', 0.00)

        # Validation
        if not name or not bm_client_id or not acc_link or not start_date or not monthly_budget:
            messages.error(request, 'All fields are required.')
            return redirect('request_ad_account')

        bm_account, created = BMAccount.objects.get_or_create(acc_id=bm_client_id)

        

        ad_account = AdAccount.objects.create(
            user=request.user,
            name=name,
            acc_id="",  # Set acc_id to empty string
            acc_link=acc_link,
            start_date=start_date,
            status='inactive',
            monthly_budget=monthly_budget
        )
        ad_account.bm_accounts.add(bm_account)

        messages.success(request, 'Ad account request submitted successfully!')
        return redirect('index')
    return render(request, 'request_ad_account.html')



def logout_view(request):
    logout(request)
    return redirect('auth')

from decimal import Decimal

@login_required(login_url='auth')
def topup(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        amount = request.POST.get('amount')

        try:
            amount = float(amount)
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            wallet = get_object_or_404(Wallet, user=request.user)

            if wallet.balance >= Decimal(amount):
                spend_cap_str = get_ad_account_info(ad_account.acc_id).get('spend_cap', '0')
                try:
                    ad_account_limit = float(spend_cap_str) / 100
                except (ValueError, TypeError):
                    ad_account_limit = 0
                    
                request = change_spend_cap(ad_account_limit + amount, ad_account.acc_id)
                if not request:
                    return JsonResponse({'success': False, 'error': 'Failed to update spend cap.'})  
                wallet.balance -= Decimal(amount)
                wallet.save()
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient balance.'})
        except (ValueError, AdAccount.DoesNotExist, Wallet.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='auth')
def request_bm_account(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        mb_name = request.POST.get('mb_name')
        mb_id = request.POST.get('mb_id')

        ad_account = get_object_or_404(AdAccount, id=ad_account_id)
        bm_account, created = BMAccount.objects.get_or_create(
            acc_id=mb_id, 
            defaults={'acc_name': mb_name}
        )
        ad_account.bm_accounts.add(bm_account)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
