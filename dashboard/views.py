from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, DepositTransaction # Import DepositTransaction
from django.contrib import messages # Import messages

# Create your views here.

@login_required(login_url='auth')
def index(request):
    return render(request, 'index.html')

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
            return redirect('/') # Redirect to transactions page after successful submission
        except Exception as e:
            messages.error(request, f'Error submitting deposit request: {e}')
            return redirect('deposit') # Redirect back to deposit page on error
    return render(request, 'deposit.html')

@login_required(login_url='auth')
def deposit_transactions(request):
    transactions = DepositTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'transactions.html', {'transactions': transactions})

def logout_view(request):
    logout(request)
    return redirect('auth')