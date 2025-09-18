from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta, datetime
import os

from dashboard.models import DepositTransaction, Wallet, AdAccount, BMAccount, AdminBM, User, TopupHistory
from dashboard.fb_api_reqs import get_ad_account_info, change_spend_cap
from dashboard.utils import paginate_data, get_user_utils


@login_required(login_url='auth')
def admin_overview(request):
    if not request.user.is_staff:
        return redirect('index')

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not start_date_str:
        start_date_str = timezone.now().strftime('%Y-%m-%d')

    start_date, end_date = None, None

    if start_date_str:
        try:
            start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
            if end_date_str:
                end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)
            else:
                end_date = start_date + timedelta(days=1)
        except (ValueError, TypeError):
            start_date, end_date = None, None

    # System-wide stats
    pending_deposits = DepositTransaction.objects.filter(status='pending').count()
    pending_accounts = AdAccount.objects.filter(status='inactive').count()
    active_accounts = AdAccount.objects.filter(status='active').count()

    # Filtered and aggregated data
    deposit_qs = DepositTransaction.objects.filter(status='approved')
    topup_qs = TopupHistory.objects.filter(status='approved', type='increase')

    if start_date:
        deposit_qs = deposit_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
        topup_qs = topup_qs.filter(date__gte=start_date, date__lt=end_date)

    total_bdt_deposit = deposit_qs.aggregate(total=Sum('bdt_amount'))['total'] or 0
    total_usd_deposit = deposit_qs.aggregate(total=Sum('usd_amount'))['total'] or 0
    total_topup_increase = topup_qs.aggregate(total=Sum('amount'))['total'] or 0

    one_month_ago = timezone.now() - timedelta(days=30)
    old_receipts_count = DepositTransaction.objects.filter(
        status__in=['approved', 'rejected'],
        created_at__lt=one_month_ago
    ).exclude(receipt='').count()

    utils = {
        'pending_deposits': pending_deposits,
        'pending_accounts': pending_accounts,
        'active_accounts': active_accounts,
    }

    context = {
        'utils': utils,
        'total_bdt_deposit': total_bdt_deposit,
        'total_usd_deposit': total_usd_deposit,
        'total_topup_increase': total_topup_increase,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'old_receipts_count': old_receipts_count,
    }

    return render(request, 'admin_overview.html', context)

@login_required(login_url='auth')
def review_deposit(request):
    if not request.user.is_staff:
        return redirect('index')

    search_query = request.GET.get('search', '')
    if search_query:
        pending_transactions_list = DepositTransaction.objects.filter(
            status='pending',
            user__email__icontains=search_query
        ).order_by('-created_at')
    else:
        pending_transactions_list = DepositTransaction.objects.filter(status='pending').order_by('-created_at')

    for transaction in pending_transactions_list:
        try:
            wallet = Wallet.objects.get(user=transaction.user)
            transaction.user_dollar_rate = wallet.dollar_rate
        except Wallet.DoesNotExist:
            transaction.user_dollar_rate = 'N/A'

    pending_transactions = paginate_data(request, pending_transactions_list, 10)

    return render(request, 'review_deposit.html', {
        'transactions': pending_transactions,
        'search_query': search_query
    })

@login_required(login_url='auth')
def review_deposit_details(request, transaction_id):
    if not request.user.is_staff:
        return redirect('index') # Or some other appropriate redirect/error
    transaction = get_object_or_404(DepositTransaction, id=transaction_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            transaction.status = 'approved'
            messages.success(request, 'Deposit request approved successfully!')
            # Update user's wallet balance
            wallet = Wallet.objects.get(user=transaction.user)
            wallet.balance += transaction.usd_amount
            wallet.save()
        elif action == 'reject':
            transaction.status = 'rejected'
            messages.error(request, 'Deposit request rejected.')
        transaction.save()
        return redirect('admin_dashboard:review_deposit')

    return render(request, 'review_deposit_details.html', {'transaction': transaction})

@login_required(login_url='auth')
def ad_account_details(request, ad_account_id):
    if not request.user.is_staff:
        return redirect('index')

    ad_account = get_object_or_404(AdAccount, id=ad_account_id)
    admin_bms = AdminBM.objects.all()

    if ad_account.status == 'active':
        ad_info = get_ad_account_info(ad_account.acc_id, ad_account.admin_bm.acc_id if ad_account.admin_bm else None)
        ad_account.balance = ad_info.get('balance', 0)
        ad_account.total_spent = ad_info.get('amount_spent', 0)
        ad_account.limit = ad_info.get('spend_cap', 0)
    else:
        ad_account.balance = 'N/A'
        ad_account.limit = 'N/A'
        ad_account.total_spent = 'N/A'

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            ad_account.name = request.POST.get('name')
            ad_account.acc_id = request.POST.get('acc_id')
            admin_bm_id = request.POST.get('admin_bm')
            if admin_bm_id:
                admin_bm = get_object_or_404(AdminBM, id=admin_bm_id)
                ad_account.admin_bm = admin_bm
            ad_account.save()

            messages.success(request, 'Ad account details have been updated.')

        elif action == 'add_bm':
            bm_acc_name = request.POST.get('bm_acc_name')
            bm_acc_id = request.POST.get('bm_acc_id')
            if bm_acc_name and bm_acc_id:
                bm_account, created = BMAccount.objects.get_or_create(acc_id=bm_acc_id, defaults={'acc_name': bm_acc_name, 'request_type': 'add'})
                ad_account.bm_accounts.add(bm_account)
                messages.success(request, 'BM account has been added.')

        elif action.startswith('approve_bm_'):
            bm_account_id = action.split('_')[-1]
            bm_account = get_object_or_404(BMAccount, id=bm_account_id)

            if bm_account.request_type == 'add':
                bm_account.acc_name = request.POST.get(f'bm_acc_name_{bm_account.id}')
                bm_account.acc_id = request.POST.get(f'bm_acc_id_{bm_account.id}')
                bm_account.request_type = 'N/A'

            bm_account.status = 'approved'
            bm_account.save()
            messages.success(request, 'BM account has been approved.')

        elif action.startswith('remove_bm_'):
            bm_account_id = action.split('_')[-1]
            bm_account = get_object_or_404(BMAccount, id=bm_account_id)
            ad_account.bm_accounts.remove(bm_account)
            bm_account.delete()
            messages.success(request, 'BM account has been removed.')

        elif action == 'activate':
            ad_account.status = 'active'
            ad_account.save()
            for bm_account in ad_account.bm_accounts.all():
                bm_account.status = 'approved'
                bm_account.save()
            messages.success(request, 'Ad account has been activated.')

        elif action == 'deactivate':
            ad_account.status = 'inactive'
            ad_account.save()
            messages.warning(request, 'Ad account has been deactivated.')
        
        elif action == 'delete':
            ad_account.delete()
            messages.success(request, 'Ad account has been deleted.')
            return redirect('ad_accounts')

        return redirect('admin_dashboard:ad_account_details', ad_account_id=ad_account.id)

    return render(request, 'ad_account_details.html', {'ad_account': ad_account, 'admin_bms': admin_bms})

@login_required(login_url='auth')
def review_ad_account(request):
    if not request.user.is_staff:
        return redirect('index')

    search_query = request.GET.get('search', '')
    if search_query:
        pending_ad_accounts_list = AdAccount.objects.filter(
            status='inactive',
            name__icontains=search_query
        ).order_by('-start_date')
    else:
        pending_ad_accounts_list = AdAccount.objects.filter(status='inactive').order_by('-start_date')

    pending_ad_accounts = paginate_data(request, pending_ad_accounts_list, 5)

    return render(request, 'review_ad_account.html', {
        'ad_accounts': pending_ad_accounts,
        'search_query': search_query
    })



@login_required(login_url='auth')
def review_bm_request(request):
    if not request.user.is_staff:
        return redirect('index')

    search_query = request.GET.get('search', '')
    pending_bm_accounts = BMAccount.objects.filter(status='pending')
    ad_accounts_list = AdAccount.objects.filter(bm_accounts__in=pending_bm_accounts, status='active').distinct()

    if search_query:
        ad_accounts_list = ad_accounts_list.filter(name__icontains=search_query)

    ad_accounts = paginate_data(request, ad_accounts_list, 10)

    return render(request, 'review_bm_request.html', {
        'ad_accounts': ad_accounts,
        'search_query': search_query
    })


@login_required(login_url='auth')
def manage_user(request):
    if not request.user.is_staff:
        return redirect('index')

    user_to_manage = None
    wallet = None
    ad_accounts =None
    utils = None
    username = request.GET.get('username')
    if username:
        try:
            user_to_manage = User.objects.get(username=username, is_staff=False)
            wallet = Wallet.objects.get(user=user_to_manage)
            ad_accounts = AdAccount.objects.filter(user=user_to_manage)
            utils = get_user_utils(user_to_manage)
        except User.DoesNotExist:
            messages.error(request, f"Normal user with username '{username}' not found.")
        except Wallet.DoesNotExist:
            pass

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user_to_manage = get_object_or_404(User, id=user_id)
        
        is_active = request.POST.get('is_active') == 'on'
        dollar_rate = request.POST.get('dollar_rate')

        user_to_manage.is_active = is_active
        user_to_manage.save()

        if dollar_rate:
            try:
                wallet = Wallet.objects.get(user=user_to_manage)
                wallet.dollar_rate = dollar_rate
                wallet.save()
            except Wallet.DoesNotExist:
                pass

        messages.success(request, 'User details updated successfully.')
        return redirect(f'/admin_dashboard/manage_user/')
    
    all_users_list = User.objects.filter(is_staff=False)
    all_users = paginate_data(request, all_users_list, 10)
    return render(request, 'manage_user.html', {'user_to_manage': user_to_manage, 'wallet': wallet, 'ad_accounts':ad_accounts, 'all_users': all_users, 'utils': utils})

@login_required(login_url='auth')
def review_topup(request):
    if not request.user.is_staff:
        return redirect('index')

    if request.method == 'POST':
        topup_id = request.POST.get('topup_id')
        action = request.POST.get('action')
        topup = get_object_or_404(TopupHistory, id=topup_id)

        if action == 'approve':
            ad_account_info = get_ad_account_info(topup.ad_account.acc_id, topup.ad_account.admin_bm.acc_id)
            
            balance = float(ad_account_info.get('balance', 0))
            spend_cap = float(ad_account_info.get('spend_cap', 0))
            topup_amount = float(topup.amount)

            if topup.type == 'decrease' and topup_amount < balance:
                new_spend_cap = spend_cap - topup_amount
                
                if new_spend_cap >= 0:
                    res = change_spend_cap(new_spend_cap, topup.ad_account.acc_id, topup.ad_account.admin_bm.acc_id)

                    if res:
                        user = topup.ad_account.user
                        wallet = Wallet.objects.get(user=user)
                        wallet.balance += topup.amount
                        wallet.save()
                        
                        topup.status = 'approved'
                        topup.save()
                        messages.success(request, "Top-up approved and spend cap updated.")
                    else:
                        messages.error(request, "Failed to update spend cap via API.")
                else:
                    messages.error(request, "Decrease amount is larger than the current spend cap.")
            else:
                messages.info(request, "Top-up request could not be processed.")

        elif action == 'delete':
            topup.delete()

        return redirect('admin_dashboard:review_topup')

    search_query = request.GET.get('search', '')
    if search_query:
        pending_topups_list = TopupHistory.objects.filter(
            status='pending',
            ad_account__name__icontains=search_query
        ).order_by('-date')
    else:
        pending_topups_list = TopupHistory.objects.filter(status='pending').order_by('-date')

    pending_topups = paginate_data(request, pending_topups_list, 10)
    return render(request, 'review_topup.html', {
        'topups': pending_topups,
        'search_query': search_query
    })

@login_required(login_url='auth')
def delete_old_receipts(request):
    if not request.user.is_staff:
        return redirect('index')

    if request.method == 'POST':
        one_month_ago = timezone.now() - timedelta(days=30)
        transactions_to_delete = DepositTransaction.objects.filter(
            status__in=['approved', 'rejected'],
            created_at__lt=one_month_ago
        ).exclude(receipt='')
        
        deleted_count = 0
        for transaction in transactions_to_delete:
            if transaction.receipt:
                if os.path.exists(transaction.receipt.path):
                    os.remove(transaction.receipt.path)
                    transaction.receipt = ''
                    transaction.save()
                    deleted_count += 1

        if deleted_count > 0:
            messages.success(request, f'Successfully deleted {deleted_count} old receipt images.')
        else:
            messages.info(request, 'No old receipt images to delete.')

        return redirect('admin_dashboard:admin_overview')

    return redirect('admin_dashboard:admin_overview')