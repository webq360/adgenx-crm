from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from dashboard.models import DepositTransaction, Wallet, AdAccount, BMAccount
from django.contrib import messages

@login_required(login_url='auth')
def review_deposit(request):
    if not request.user.is_staff:
        return redirect('index') # Or some other appropriate redirect/error
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

@login_required(login_url='auth')
def ad_account_details(request, ad_account_id):
    if not request.user.is_staff:
        return redirect('index')

    ad_account = get_object_or_404(AdAccount, id=ad_account_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save':
            ad_account.name = request.POST.get('name')
            ad_account.acc_id = request.POST.get('acc_id')
            ad_account.acc_link = request.POST.get('acc_link')
            ad_account.monthly_budget = request.POST.get('monthly_budget')
            ad_account.balance = request.POST.get('balance')
            ad_account.total_spent = request.POST.get('total_spent')
            ad_account.limit = request.POST.get('limit')
            ad_account.save()

            for bm_account in ad_account.bm_accounts.all():
                bm_account.acc_name = request.POST.get(f'bm_acc_name_{bm_account.id}')
                bm_account.acc_id = request.POST.get(f'bm_acc_id_{bm_account.id}')
                bm_account.save()

            messages.success(request, 'Ad account details have been updated.')

        elif action == 'add_bm':
            bm_acc_name = request.POST.get('bm_acc_name')
            bm_acc_id = request.POST.get('bm_acc_id')
            if bm_acc_name and bm_acc_id:
                bm_account, created = BMAccount.objects.get_or_create(acc_id=bm_acc_id, defaults={'acc_name': bm_acc_name})
                ad_account.bm_accounts.add(bm_account)
                messages.success(request, 'BM account has been added.')

        elif action.startswith('remove_bm_'):
            bm_account_id = action.split('_')[-1]
            bm_account = get_object_or_404(BMAccount, id=bm_account_id)
            ad_account.bm_accounts.remove(bm_account)
            messages.success(request, 'BM account has been removed.')

        elif action == 'activate':
            ad_account.status = 'active'
            ad_account.save()
            messages.success(request, 'Ad account has been activated.')

        elif action == 'deactivate':
            ad_account.status = 'inactive'
            ad_account.save()
            messages.warning(request, 'Ad account has been deactivated.')

        return redirect('admin_dashboard:ad_account_details', ad_account_id=ad_account.id)

    return render(request, 'ad_account_details.html', {'ad_account': ad_account})

@login_required(login_url='auth')
def review_ad_account(request):
    if not request.user.is_staff:
        return redirect('index')

    pending_ad_accounts = AdAccount.objects.filter(status='inactive').order_by('-start_date')
    return render(request, 'review_ad_account.html', {'ad_accounts': pending_ad_accounts})