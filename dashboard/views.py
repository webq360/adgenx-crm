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
from functools import wraps

from .models import DepositTransaction, Wallet, AdAccount, BMAccount, TopupHistory, PaymentMethod, ActivityLog, WithdrawalRequest
from .fb_api_reqs import change_spend_cap, get_ad_account_info
from .utils import paginate_data, get_user_utils, get_processed_ad_accounts_data, log_activity
from .group_permissions import require_group_permission as require_permission  # Using Django Groups now

# Create your views here.

def landing(request):
    if request.user.is_authenticated:
        return redirect('index')
    from admin_dashboard.models import SiteSettings, FAQ, Testimonial
    settings = SiteSettings.get()
    faqs = FAQ.objects.filter(is_active=True).order_by('order')
    testimonials = Testimonial.objects.filter(is_active=True).order_by('order')
    return render(request, 'landing.html', {
        'settings': settings,
        'faqs': faqs,
        'testimonials': testimonials,
    })

@login_required(login_url='auth')
def index(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    
    # Use get_or_create to prevent DoesNotExist errors
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00, 'dollar_rate': 127.00}
    )

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
    withdrawal_qs = WithdrawalRequest.objects.filter(user=request.user, status__in=['approved', 'processed'])

    if start_date:
        deposit_qs = deposit_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
        withdrawal_qs = withdrawal_qs.filter(requested_at__gte=start_date, requested_at__lt=end_date)

    total_deposit = deposit_qs.aggregate(total=Sum('usd_amount'))['total'] or 0
    total_withdrawal = withdrawal_qs.aggregate(total=Sum('amount_usd'))['total'] or 0

    # Deposit summary by rate (group by exchange rate)
    from decimal import Decimal
    from collections import defaultdict
    
    deposits = deposit_qs.values('bdt_amount', 'usd_amount')
    rate_summary = defaultdict(lambda: {'bdt': Decimal('0'), 'usd': Decimal('0')})
    
    for deposit in deposits:
        bdt = Decimal(str(deposit['bdt_amount']))
        usd = Decimal(str(deposit['usd_amount']))
        if usd > 0:
            rate = round(bdt / usd, 2)
            rate_summary[rate]['bdt'] += bdt
            rate_summary[rate]['usd'] += usd
    
    # Convert to list and sort by rate
    deposit_by_rate = [
        {
            'rate': rate,
            'bdt_amount': float(data['bdt']),
            'usd_amount': float(data['usd'])
        }
        for rate, data in sorted(rate_summary.items(), reverse=True)
    ]

    ad_accounts_qs = AdAccount.objects.filter(user=request.user, status='active').order_by('-start_date')
    ad_accounts_data = get_processed_ad_accounts_data(ad_accounts_qs)

    utils = get_user_utils(request.user)
    return render(request, 'index.html', {
        'wallet': wallet,
        'ad_accounts': ad_accounts_data,
        'utils': utils,
        'total_deposit': total_deposit,
        'total_withdrawal': total_withdrawal,
        'deposit_by_rate': deposit_by_rate,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })


@login_required(login_url='auth')
@require_permission('can_manage_accounts')
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
    
    ad_accounts_paginated = paginate_data(request, ad_accounts_qs, 20)

    # Build lightweight account data (no FB API call here)
    ad_accounts_data = []
    for acc in ad_accounts_paginated.object_list:
        bm_accounts_list = []
        for bm in acc.bm_accounts.all():
            bm_accounts_list.append({
                'id': bm.id,
                'acc_name': bm.acc_name,
                'acc_id': bm.acc_id,
                'status': bm.status,
                'request_type': bm.request_type,
            })
        
        # Calculate total spent from TopupHistory
        topup_history = TopupHistory.objects.filter(ad_account=acc)
        total_spent = sum(t.amount for t in topup_history if t.type == 'increase')
        total_decreased = sum(t.amount for t in topup_history if t.type == 'decrease')
        
        # Update total_spent field in model
        acc.total_spent = total_spent
        
        # Calculate remaining balance
        remaining_balance = acc.monthly_budget - total_spent + total_decreased
        acc.remaining_balance = remaining_balance
        
        # Update limit (can be same as monthly_budget or set separately)
        if acc.limit == 0:
            acc.limit = acc.monthly_budget
        
        acc.save()
        
        ad_accounts_data.append({
            'id': acc.id,
            'name': acc.name,
            'acc_id': acc.acc_id,
            'acc_link': acc.acc_link,
            'start_date': str(acc.start_date),
            'monthly_budget': str(acc.monthly_budget),
            'total_spent': str(acc.total_spent),
            'remaining_balance': str(acc.remaining_balance),
            'limit': str(acc.limit),
            'status': acc.status,
            'has_admin_bm': bool(acc.admin_bm and acc.status == 'active'),
            'bm_accounts': bm_accounts_list,
        })

    return render(request, 'ad_accounts.html', {
        'ad_accounts': ad_accounts_paginated, 
        'ad_accounts_data': ad_accounts_data,
        'search_query': search_query
    })


@login_required(login_url='auth')
def get_ad_account_fb_info(request, ad_account_id):
    """Returns live FB balance/spent/limit for a single ad account via AJAX."""
    try:
        if request.user.is_staff:
            ad_account = get_object_or_404(AdAccount, id=ad_account_id)
        else:
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)

        if ad_account.admin_bm and ad_account.status == 'active':
            ad_info = get_ad_account_info(ad_account.acc_id, ad_account.admin_bm.acc_id)
            if ad_info:
                return JsonResponse({
                    'success': True,
                    'balance': ad_info.get('balance', 'N/A'),
                    'total_spent': ad_info.get('amount_spent', 'N/A'),
                    'limit': ad_info.get('spend_cap', 'N/A'),
                })
        return JsonResponse({'success': True, 'balance': 'N/A', 'total_spent': 'N/A', 'limit': 'N/A'})
    except Exception as e:
        return JsonResponse({'success': False, 'balance': 'N/A', 'total_spent': 'N/A', 'limit': 'N/A'})


@login_required(login_url='auth')
@require_permission('can_manage_payments')
def withdrawal(request):
    """Handle withdrawal requests from users"""
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00, 'dollar_rate': 127.00}
    )
    utils = get_user_utils(request.user)
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        amount_usd = request.POST.get('amount_usd')
        account_details = request.POST.get('account_details', '').strip()

        # Input validation
        try:
            from decimal import Decimal, InvalidOperation
            amount_usd = Decimal(str(amount_usd))
            
            if amount_usd <= 0:
                messages.error(request, 'Amount must be positive.')
                return redirect('withdrawal')
            
            if amount_usd > wallet.balance:
                messages.error(request, f'Insufficient balance. Your current balance is ${wallet.balance}')
                return redirect('withdrawal')
            
            if amount_usd > 999999999:
                messages.error(request, 'Amount too large.')
                return redirect('withdrawal')
                
            if not account_details:
                messages.error(request, 'Please provide account details for withdrawal.')
                return redirect('withdrawal')
        except (ValueError, InvalidOperation, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect('withdrawal')

        payment_method = get_object_or_404(PaymentMethod, id=payment_method_id)
        
        # Calculate BDT amount
        amount_bdt = amount_usd * wallet.dollar_rate

        try:
            withdrawal_request = WithdrawalRequest.objects.create(
                user=request.user,
                amount_usd=amount_usd,
                amount_bdt=amount_bdt,
                payment_method=payment_method.method_name,
                account_details=account_details,
                status='pending'
            )

            # Send notifications to user and admins
            from dashboard.notification_handler import notify_withdrawal_requested
            notify_withdrawal_requested(withdrawal_request)

            messages.success(request, 'Withdrawal request submitted successfully! Awaiting admin approval.')
            return redirect('withdrawal_transactions')
        except Exception as e:
            messages.error(request, f'Error submitting withdrawal request: {e}')
            return redirect('withdrawal')
        
    return render(request, 'withdrawal.html', {
        'wallet': wallet,
        'utils': utils,
        'payment_methods': payment_methods
    })


@login_required(login_url='auth')
@require_permission('can_manage_payments')
def deposit(request):
    if request.user.is_staff:
        return redirect('admin_dashboard:admin_overview')
    
    wallet, created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00, 'dollar_rate': 127.00}
    )
    utils = get_user_utils(request.user)
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    if request.method == 'POST':
        payment_method_id = request.POST.get('payment_method')
        bdt_amount = request.POST.get('bdt_amount')
        tx_id = request.POST.get('tx_id')
        receipt = request.FILES.get('receipt')
        usd_amount = request.POST.get('usd_amount')

        # Input validation
        try:
            from decimal import Decimal, InvalidOperation
            bdt_amount = Decimal(str(bdt_amount))
            usd_amount = Decimal(str(usd_amount))
            
            if bdt_amount <= 0 or usd_amount <= 0:
                messages.error(request, 'Amount must be positive.')
                return redirect('deposit')
            
            if bdt_amount > 999999999 or usd_amount > 999999999:
                messages.error(request, 'Amount too large.')
                return redirect('deposit')
        except (ValueError, InvalidOperation, TypeError):
            messages.error(request, 'Invalid amount entered.')
            return redirect('deposit')

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

            # Send notifications to user and admins
            from dashboard.notification_handler import notify_deposit_submitted
            notify_deposit_submitted(deposit_transaction)

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
def withdrawal_transactions(request):
    if request.user.is_staff:
        withdrawals_list = WithdrawalRequest.objects.all().order_by('-requested_at')
    else:
        withdrawals_list = WithdrawalRequest.objects.filter(user=request.user).order_by('-requested_at')
    
    withdrawals = paginate_data(request, withdrawals_list, 10)
    return render(request, 'withdrawal_transactions.html', {'withdrawals': withdrawals})

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
            from decimal import Decimal, InvalidOperation
            from django.db import transaction
            from django.db.models import F
            
            amount = Decimal(str(amount))
            
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be positive.'})
            
            ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            
            # Atomic transaction to prevent race conditions
            with transaction.atomic():
                wallet = Wallet.objects.select_for_update().get(user=request.user)
                old_balance = wallet.balance
                
                if wallet.balance >= amount:
                    admin_bm_id = ad_account.admin_bm.acc_id if ad_account.admin_bm else None
                    ad_info = get_ad_account_info(ad_account.acc_id, admin_bm_id)
                    
                    if not ad_info:
                        return JsonResponse({'success': False, 'error': 'Failed to fetch account info.'})
                    
                    ad_account_limit = float(ad_info.get('spend_cap', 0))
                    
                    api_result = change_spend_cap(ad_account_limit + float(amount), ad_account.acc_id, admin_bm_id)
                    
                    if not api_result:
                        return JsonResponse({'success': False, 'error': 'Topup failed.'})
                    
                    wallet.balance = F('balance') - amount
                    wallet.save()
                    wallet.refresh_from_db()
                    new_balance = wallet.balance
                    
                    # Update ad account balances
                    ad_account.total_spent = F('total_spent') + amount
                    ad_account.remaining_balance = F('remaining_balance') - amount
                    ad_account.save()
                    ad_account.refresh_from_db()
                    
                    TopupHistory.objects.create(
                        ad_account=ad_account,
                        amount=amount,
                        status='approved'
                    )
                    
                    # Log activity with detailed wallet balance tracking
                    user_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
                    log_activity(
                        performed_by=request.user,
                        activity_type='topup_increase',
                        description=f"[USER: {user_info}] Top-up ${amount} to {ad_account.name} ({ad_account.acc_id}). Wallet before: ${old_balance}, Wallet after: ${new_balance}, Remaining balance: ${new_balance}",
                        target_user=request.user,
                        old_value={
                            'wallet_balance_before_topup': str(old_balance),
                            'ad_account': ad_account.name,
                            'ad_account_id': ad_account.acc_id,
                            'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                        },
                        new_value={
                            'wallet_balance_after_topup': str(new_balance),
                            'topup_amount': str(amount),
                            'remaining_balance': str(new_balance),
                            'ad_account': ad_account.name
                        },
                        request=request
                    )
                    
                    return JsonResponse({'success': True})
                else:
                    return JsonResponse({'success': False, 'error': 'Insufficient balance.'})
                    
        except (ValueError, InvalidOperation, AdAccount.DoesNotExist, Wallet.DoesNotExist) as e:
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

@login_required(login_url='auth')
def account_settings(request):
    return render(request, 'account_settings.html')

@login_required(login_url='auth')
def edit_ad_account(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')
        account_name = request.POST.get('account_name')
        account_link = request.POST.get('account_link')
        monthly_budget = request.POST.get('monthly_budget')
        limit = request.POST.get('limit')

        try:
            from decimal import Decimal, InvalidOperation
            
            if request.user.is_staff:
                ad_account = get_object_or_404(AdAccount, id=ad_account_id)
            else:
                ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            
            ad_account.name = account_name
            ad_account.acc_link = account_link
            
            # Update monthly budget if provided
            if monthly_budget:
                try:
                    monthly_budget_decimal = Decimal(str(monthly_budget))
                    if monthly_budget_decimal >= 0:
                        ad_account.monthly_budget = monthly_budget_decimal
                except InvalidOperation:
                    pass
            
            # Update limit if provided
            if limit:
                try:
                    limit_decimal = Decimal(str(limit))
                    if limit_decimal >= 0:
                        ad_account.limit = limit_decimal
                except InvalidOperation:
                    pass
            
            ad_account.save()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required(login_url='auth')
def delete_ad_account(request):
    if request.method == 'POST':
        ad_account_id = request.POST.get('ad_account_id')

        try:
            if request.user.is_staff:
                ad_account = get_object_or_404(AdAccount, id=ad_account_id)
            else:
                ad_account = get_object_or_404(AdAccount, id=ad_account_id, user=request.user)
            
            ad_account.delete()
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required(login_url='auth')
@login_required(login_url='auth')
def add_ad_account_page(request):
    """Render page to add new ad account"""
    if request.method == 'POST':
        account_name = request.POST.get('account_name', '').strip()
        account_id = request.POST.get('account_id', '').strip()
        account_link = request.POST.get('account_link', '').strip()
        monthly_budget = request.POST.get('monthly_budget', '0')
        limit = request.POST.get('limit', '0')
        status = request.POST.get('status', 'inactive')
        bm_accounts = request.POST.getlist('bm_accounts')

        try:
            # Validation
            if not account_name or not account_id or not account_link:
                messages.error(request, 'All required fields must be filled.')
                return redirect('add_ad_account_page')
            
            from decimal import Decimal, InvalidOperation
            try:
                monthly_budget = Decimal(str(monthly_budget)) if monthly_budget else Decimal('0')
                limit = Decimal(str(limit)) if limit else monthly_budget
                
                if monthly_budget < 0:
                    messages.error(request, 'Monthly budget cannot be negative.')
                    return redirect('add_ad_account_page')
                if limit < 0:
                    messages.error(request, 'Limit cannot be negative.')
                    return redirect('add_ad_account_page')
            except InvalidOperation:
                messages.error(request, 'Invalid budget or limit amount.')
                return redirect('add_ad_account_page')
            
            # Check if account already exists
            if AdAccount.objects.filter(user=request.user, acc_id=account_id).exists():
                messages.error(request, 'This ad account already exists.')
                return redirect('add_ad_account_page')
            
            # Create new ad account
            ad_account = AdAccount.objects.create(
                user=request.user,
                name=account_name,
                acc_id=account_id,
                acc_link=account_link,
                status=status,
                monthly_budget=monthly_budget,
                limit=limit,
                remaining_balance=monthly_budget,
                total_spent=Decimal('0'),
                start_date=timezone.now().date()
            )
            
            # Add BM accounts if selected
            if bm_accounts:
                for bm_id in bm_accounts:
                    try:
                        bm = BMAccount.objects.get(id=bm_id)
                        ad_account.bm_accounts.add(bm)
                    except BMAccount.DoesNotExist:
                        pass
            
            log_activity(
                performed_by=request.user,
                activity_type='ad_account_created',
                description=f"Created new ad account: {account_name} ({account_id}) - Status: {status}",
                target_user=request.user,
                old_value=None,
                new_value={'account_id': ad_account.id, 'account_name': account_name},
                request=request
            )
            
            messages.success(request, 'Ad account created successfully!')
            return redirect('ad_accounts')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('add_ad_account_page')
    
    # GET request - prepare context
    available_bms = BMAccount.objects.all()
    return render(request, 'add_ad_account.html', {
        'available_bms': available_bms
    })


def add_ad_account(request):
    """AJAX endpoint for adding ad account via modal"""
    if request.method == 'POST':
        account_name = request.POST.get('account_name', '').strip()
        account_id = request.POST.get('account_id', '').strip()
        account_link = request.POST.get('account_link', '').strip()
        monthly_budget = request.POST.get('monthly_budget', '0')

        try:
            # Validation
            if not account_name or not account_id or not account_link:
                return JsonResponse({'success': False, 'error': 'All required fields must be filled.'})
            
            from decimal import Decimal, InvalidOperation
            try:
                monthly_budget = Decimal(str(monthly_budget)) if monthly_budget else Decimal('0')
                if monthly_budget < 0:
                    return JsonResponse({'success': False, 'error': 'Monthly budget cannot be negative.'})
            except InvalidOperation:
                return JsonResponse({'success': False, 'error': 'Invalid budget amount.'})
            
            # Check if account already exists
            if AdAccount.objects.filter(user=request.user, acc_id=account_id).exists():
                return JsonResponse({'success': False, 'error': 'This ad account already exists.'})
            
            # Create new ad account
            ad_account = AdAccount.objects.create(
                user=request.user,
                name=account_name,
                acc_id=account_id,
                acc_link=account_link,
                status='inactive',
                monthly_budget=monthly_budget,
                start_date=timezone.now().date()
            )
            
            log_activity(
                performed_by=request.user,
                activity_type='ad_account_created',
                description=f"Created new ad account: {account_name} ({account_id}) via modal",
                target_user=request.user,
                old_value=None,
                new_value={'account_id': ad_account.id, 'account_name': account_name},
                request=request
            )
            
            return JsonResponse({'success': True, 'message': 'Ad account created successfully!'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})
