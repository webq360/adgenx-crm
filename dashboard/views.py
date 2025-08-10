from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, DepositTransaction, Wallet # Import DepositTransaction and Wallet
from django.contrib import messages # Import messages

# Create your views here.

@login_required(login_url='auth')
def index(request):
    if request.user.is_staff:
        return redirect('review_deposit')
    wallet = Wallet.objects.get(user=request.user)
    return render(request, 'index.html', {'wallet': wallet})       

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
            # Update user's wallet pending_deposit
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.pending_deposit += 1
            wallet.save()

            messages.success(request, 'Deposit request submitted successfully!')
            return redirect('deposit_transactions') # Redirect to transactions page after successful submission
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
            wallet.pending_deposit -= 1
            wallet.save()
        elif action == 'reject':
            transaction.status = 'rejected'
            messages.error(request, 'Deposit request rejected.')
            # Decrement pending_deposit even if rejected
            wallet = Wallet.objects.get(user=transaction.user)
            wallet.pending_deposit -= 1
            wallet.save()
        transaction.save()
        return redirect('review_deposit')

    return render(request, 'review_deposit_details.html', {'transaction': transaction})

def logout_view(request):
    logout(request)
    return redirect('auth')