from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO
import datetime
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from decimal import Decimal

from .models import DepositTransaction, Wallet, AdAccount, BMAccount, TopupHistory, PaymentMethod
from .fb_api_reqs import change_spend_cap, get_ad_account_info
from .utils import paginate_data, get_user_utils, get_processed_ad_accounts_data

# Create your views here.

@login_required(login_url='auth')
def index(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    wallet = Wallet.objects.get(user=request.user)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not start_date_str:
        start_date_str = timezone.now().strftime('%Y-%m-%d')

    start_date, end_date = None, None

    if start_date_str:
        try:
            start_date = timezone.make_aware(datetime.datetime.strptime(start_date_str, '%Y-%m-%d'))
            if end_date_str:
                end_date = timezone.make_aware(datetime.datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)
            else:
                end_date = start_date + timedelta(days=1)
        except (ValueError, TypeError):
            start_date, end_date = None, None

    # Filtered and aggregated data
    deposit_qs = DepositTransaction.objects.filter(user=request.user, status='approved')
    topup_qs = TopupHistory.objects.filter(ad_account__user=request.user, status='approved', type='increase')

    if start_date:
        deposit_qs = deposit_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
        topup_qs = topup_qs.filter(date__gte=start_date, date__lt=end_date)

    total_deposit = deposit_qs.aggregate(total=Sum('usd_amount'))['total'] or 0
    total_topup_increase = topup_qs.aggregate(total=Sum('amount'))['total'] or 0

    ad_accounts_qs = AdAccount.objects.filter(user=request.user, status='active').order_by('-start_date')[:5]
    ad_accounts_data = get_processed_ad_accounts_data(ad_accounts_qs)

    utils = get_user_utils(request.user)
    return render(request, 'index.html', {
        'wallet': wallet,
        'ad_accounts': ad_accounts_data,
        'utils': utils,
        'total_deposit': total_deposit,
        'total_topup_increase': total_topup_increase,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })


@login_required(login_url='auth')
def ad_accounts(request):    
    search_query = request.GET.get('search', '')
    if request.user.is_staff:
        ad_accounts_qs = AdAccount.objects.filter(
            name__icontains=search_query
        ).order_by('-start_date')
    else:
        ad_accounts_qs = AdAccount.objects.filter(
            user=request.user,
            name__icontains=search_query
        ).order_by('-start_date')
    
    ad_accounts_paginated = paginate_data(request, ad_accounts_qs, 5)
    ad_accounts_data = get_processed_ad_accounts_data(ad_accounts_paginated.object_list)

    return render(request, 'ad_accounts.html', {
        'ad_accounts': ad_accounts_paginated, 
        'ad_accounts_data': ad_accounts_data,
        'search_query': search_query
    })


@login_required(login_url='auth')
def deposit(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    
    wallet = Wallet.objects.get(user=request.user)
    utils = get_user_utils(request.user)
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        bdt_amount = request.POST.get('bdt_amount')
        tx_id = request.POST.get('tx_id')
        receipt = request.FILES.get('receipt')
        usd_amount = request.POST.get('usd_amount')

        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)

        if receipt:
            try:
                # Open the image
                img = Image.open(receipt)

                # Create a BytesIO object to hold the compressed image data
                img_io = BytesIO()

                # Resize and save the image with compression
                # Adjust width as needed, height will be proportional
                new_width = 800
                ratio = new_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save as JPEG with quality setting
                img.save(img_io, format='JPEG', quality=70)
                img_io.seek(0)

                # Create a new Django File object
                receipt = ContentFile(img_io.read(), name=receipt.name)

            except Exception as e:
                messages.error(request, f"Error processing image: {e}")
                return redirect('deposit')

        try:
            deposit_transaction = DepositTransaction.objects.create(
                user=request.user,
                method=payment_method.method_name,
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
            return redirect('deposit')
        
    return render(request, 'deposit.html', {'wallet': wallet, 'utils':utils, 'payment_methods': payment_methods})

@login_required(login_url='auth')
def deposit_transactions(request):
    trx_id = request.GET.get('trx_id')
    email = request.GET.get('email')
    
    if request.user.is_staff:
        transactions_list = DepositTransaction.objects.all().order_by('-created_at')
        if trx_id:
            transactions_list = transactions_list.filter(trx_id=trx_id)
        if email:
            transactions_list = transactions_list.filter(user__email__icontains=email)
        
        # Fetch wallet dollar rate for each user if staff
        for transaction in transactions_list:
            try:
                wallet = Wallet.objects.get(user=transaction.user)
                transaction.user_dollar_rate = wallet.dollar_rate
            except Wallet.DoesNotExist:
                transaction.user_dollar_rate = 'N/A' # Or handle as appropriate
    else:
        transactions_list = DepositTransaction.objects.filter(user=request.user).order_by('-created_at')
        if trx_id:
            transactions_list = transactions_list.filter(trx_id=trx_id)

    transactions = paginate_data(request, transactions_list, 10)
    return render(request, 'deposit_transactions.html', {'transactions': transactions, 'trx_id': trx_id, 'email': email})

@login_required(login_url='auth')
def topup_transactions(request):
    ad_acc_name = request.GET.get('ad_acc_name')
    if request.user.is_staff:
        if ad_acc_name:
            topups_list = TopupHistory.objects.filter(ad_account__name__icontains=ad_acc_name).order_by('-date')
        else:
            topups_list = TopupHistory.objects.all().order_by('-date')
    else:
        ad_acc_name = request.GET.get('ad_acc_name')
        if ad_acc_name:
            topups_list = TopupHistory.objects.filter(ad_account__name__icontains=ad_acc_name, ad_account__user=request.user).order_by('-date')
        else:
            topups_list = TopupHistory.objects.filter(ad_account__user=request.user).order_by('-date')
    topups = paginate_data(request, topups_list, 10)
    return render(request, 'topup_transactions.html', {'topups': topups, 'ad_acc_name': ad_acc_name})

@login_required(login_url='auth')
def request_ad_account(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    
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

        bm_account = BMAccount.objects.create(acc_id=bm_client_id, status='pending', request_type='add')

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


@login_required(login_url='auth')
def topup(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        amount = request.POST.get('amount')

        try:
            amount = float(amount)
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            wallet = get_object_or_404(Wallet, user=request.user)

            if wallet.balance > 0.01 and wallet.balance >= Decimal(amount):
                ad_account_limit = get_ad_account_info(ad_account.acc_id, ad_account.admin_bm.acc_id if ad_account.admin_bm else None).get('spend_cap', 0)
                    
                request = change_spend_cap(ad_account_limit + amount, ad_account.acc_id, ad_account.admin_bm.acc_id if ad_account.admin_bm else None)
                if not request:
                    return JsonResponse({'success': False, 'error': 'Topup failed.'})  
                wallet.balance -= Decimal(amount)
                wallet.save()
                TopupHistory.objects.create(
                    ad_account = ad_account,
                    amount = amount,
                    status = 'approved'
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Insufficient balance.'})
        except (ValueError, AdAccount.DoesNotExist, Wallet.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='auth')
def request_decrease_limit(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        amount = request.POST.get('amount')

        try:
            amount = float(amount)
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)

            TopupHistory.objects.create(
                ad_account=ad_account,
                amount=amount,
                type='decrease',
                status='pending'
            )
            return JsonResponse({'success': True})
        except (ValueError, AdAccount.DoesNotExist) as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='auth')
def request_bm_account(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        mb_name = request.POST.get('mb_name')
        mb_id = request.POST.get('mb_id')

        ad_account = get_object_or_404(AdAccount, id=ad_account_id)
        bm_account = BMAccount.objects.create(
            acc_id=mb_id, 
            acc_name= mb_name,
            request_type='add',
        )
        ad_account.bm_accounts.add(bm_account)

        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='auth')
def remove_bm_account_request(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        bm_account_id = request.POST.get('bm_account_id')

        try:
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            bm_account = get_object_or_404(BMAccount, id=bm_account_id)
            # Ensure the BM account is associated with the ad account and user
            if bm_account in ad_account.bm_accounts.all():
                bm_account.request_type = 'remove'
                bm_account.status = 'pending'
                bm_account.save()
                messages.success(request, 'Remove BM Account request submitted successfully!')
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'BM account not associated with this Ad Account.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})