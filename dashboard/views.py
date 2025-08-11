from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, DepositTransaction, Wallet, AdAccount, AdminBM
from django.contrib import messages # Import messages

# Create your views here.

@login_required(login_url='auth')
def index(request):
    if request.user.is_staff:
        return redirect('review_deposit')  # Redirect staff to review deposits
    wallet = Wallet.objects.get(user=request.user)
    ad_accounts = AdAccount.objects.filter(user=request.user, status='active').order_by('-start_date')
    return render(request, 'index.html', {'wallet': wallet, 'ad_accounts': ad_accounts})       

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
            # Update user's wallet pending_deposits
            wallet = Wallet.objects.get(user=request.user)
            wallet.pending_deposits += 1
            wallet.save()

            messages.success(request, 'Deposit request submitted successfully!')
            return redirect('index') # Redirect to transactions page after successful submission
        except Exception as e:
            messages.error(request, f'Error submitting deposit request: {e}')
            return redirect('deposit') # Redirect back to deposit page on error
        
    wallet = Wallet.objects.get(user=request.user)
    return render(request, 'deposit.html', {'wallet': wallet})

@login_required(login_url='auth')
def deposit_transactions(request):
    if request.user.is_staff:
        transactions = DepositTransaction.objects.all().order_by('-created_at')
    else:
        transactions = DepositTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transactions.html', {'transactions': transactions})

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
            wallet.pending_deposits -= 1
            wallet.save()
        elif action == 'reject':
            transaction.status = 'rejected'
            messages.error(request, 'Deposit request rejected.')
            # Decrement pending_deposits even if rejected
            wallet = Wallet.objects.get(user=transaction.user)
            wallet.pending_deposits -= 1
            wallet.save()
        transaction.save()
        return redirect('review_deposit')

    return render(request, 'review_deposit_details.html', {'transaction': transaction})

@login_required(login_url='auth')
def request_ad_account(request):
    if request.method == 'POST':
        name = request.POST.get('accountName')
        acc_id = request.POST.get('accId') # Get acc_id from form
        bm_client_id = request.POST.get('bmId')
        bm_client_name = request.POST.get('bmClientName', '') # New field
        acc_link = request.POST.get('fbPageLink')
        start_date = request.POST.get('startDate')
        limit = request.POST.get('limit', 0.00) # New field

        # Validation
        if not name or not acc_id:
            messages.error(request, 'Account Name and Account ID are required.')
            return redirect('request_ad_account')

        # Check if an AdminBM object exists, if not create one
        mb_admin_reference = AdminBM.objects.first()
        if not mb_admin_reference:
            mb_admin_reference = AdminBM.objects.create(bm_id="DUMMY_BM_ID", bm_name="DUMMY_BM_NAME")

        balance = 0.00
        total_spent = 0.00

        AdAccount.objects.create(
            user=request.user,
            name=name,
            acc_id=acc_id,
            acc_link=acc_link,
            bm_client_id=bm_client_id,
            bm_client_name=bm_client_name,
            mb_admin_reference=mb_admin_reference,
            balance=balance,
            total_spent=total_spent,
            start_date=start_date,
            status='inactive',
            limit=limit
        )

        wallet = Wallet.objects.get(user=request.user)
        wallet.pending_accounts += 1
        wallet.save()
        messages.success(request, 'Ad account request submitted successfully!')
        return redirect('index')
    return render(request, 'request_ad_account.html')

@login_required(login_url='auth')
def ad_accounts(request):
    if request.user.is_staff:
        ad_accounts = AdAccount.objects.all().order_by('-start_date')
    else:
        ad_accounts = AdAccount.objects.filter(user=request.user).order_by('-start_date')
    return render(request, 'ad_accounts.html', {'ad_accounts': ad_accounts})

def logout_view(request):
    logout(request)
    return redirect('auth')

@login_required(login_url='auth')
def ad_account_details(request, ad_account_id):
    if not request.user.is_staff:
        return redirect('index')

    ad_account = get_object_or_404(AdAccount, id=ad_account_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'activate':
            ad_account.status = 'active'
            ad_account.save()
            wallet = Wallet.objects.get(user=ad_account.user)
            wallet.pending_accounts -= 1
            wallet.save()
            messages.success(request, 'Ad account has been activated.')
        elif action == 'deactivate':
            ad_account.status = 'inactive'
            ad_account.save()
            wallet = Wallet.objects.get(user=ad_account.user)
            wallet.pending_accounts += 1 # Increment if it was active and now inactive
            wallet.save()
            messages.warning(request, 'Ad account has been deactivated.')
        elif action == 'cancel':
            return redirect('ad_accounts')
        return redirect('ad_accounts')

    return render(request, 'ad_account_details.html', {'ad_account': ad_account})

@login_required(login_url='auth')
def review_ad_account(request):
    if not request.user.is_staff:
        return redirect('index')

    pending_ad_accounts = AdAccount.objects.filter(status='inactive').order_by('-start_date')
    return render(request, 'review_ad_account.html', {'ad_accounts': pending_ad_accounts})