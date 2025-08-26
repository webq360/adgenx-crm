from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dashboard.models import DepositTransaction, Wallet, AdAccount, BMAccount, AdminBM
from django.contrib import messages

@login_required(login_url='auth')
def review_deposit(request):
    if not request.user.is_staff:
        return redirect('index')
    pending_transactions = DepositTransaction.objects.filter(status='pending').order_by('-created_at')
    return render(request, 'review_deposit.html', {'transactions': pending_transactions})

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

from dashboard.fb_api_reqs import get_ad_account_info

@login_required(login_url='auth')
def ad_account_details(request, ad_account_id):
    if not request.user.is_staff:
        return redirect('index')

    ad_account = get_object_or_404(AdAccount, id=ad_account_id)
    admin_bms = AdminBM.objects.all()

    if ad_account.status == 'active':
        ad_info = get_ad_account_info(ad_account.acc_id, ad_account.admin_bm.id if ad_account.admin_bm else None)
        ad_account.balance = ad_info.get('balance', 0)
        ad_account.total_spent = ad_info.get('amount_spent', 0)
        spend_cap_str = ad_info.get('spend_cap', '0')
        try:
            ad_account.limit = float(spend_cap_str) / 100
        except (ValueError, TypeError):
            ad_account.limit = 0
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

        return redirect('admin_dashboard:ad_account_details', ad_account_id=ad_account.id)

    return render(request, 'ad_account_details.html', {'ad_account': ad_account, 'admin_bms': admin_bms})

@login_required(login_url='auth')
def review_ad_account(request):
    if not request.user.is_staff:
        return redirect('index')

    pending_ad_accounts = AdAccount.objects.filter(status='inactive').order_by('-start_date')

    return render(request, 'review_ad_account.html', {'ad_accounts': pending_ad_accounts})



@login_required(login_url='auth')
def review_bm_request(request):
    if not request.user.is_staff:
        return redirect('index')

    pending_bm_accounts = BMAccount.objects.filter(status='pending')
    ad_accounts = AdAccount.objects.filter(bm_accounts__in=pending_bm_accounts, status='active').distinct()

    return render(request, 'review_bm_request.html', {'ad_accounts': ad_accounts})

@login_required(login_url='auth')
def all_ad_accounts(request):
    if not request.user.is_staff:
        return redirect('index')

    raw_ad_accounts = AdAccount.objects.all().order_by('-start_date')
    ad_accounts = []
    for acc in raw_ad_accounts:
        if acc.status != 'active':
            acc.balance = 'N/A'
            acc.limit = 'N/A'
            acc.total_spent = 'N/A'
               
        else:
            ad_info = get_ad_account_info(acc.acc_id, acc.admin_bm.id if acc.admin_bm else None)
            if ad_info:
                acc.balance = ad_info.get('balance', 0)
                acc.total_spent = ad_info.get('amount_spent', 0)
                spend_cap_str = ad_info.get('spend_cap', '0')
                try:
                    acc.limit = float(spend_cap_str) / 100
                except (ValueError, TypeError):
                    acc.limit = 0
        ad_accounts.append(acc)
    return render(request, 'all_ad_accounts.html', {'ad_accounts': ad_accounts})