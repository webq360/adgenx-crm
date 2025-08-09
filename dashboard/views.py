from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User

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
        payment_method = request.POST.get('payment_method')
        bdt_amount = request.POST.get('bdt_amount')
        tx_id = request.POST.get('tx_id')
        receipt = request.FILES.get('receipt')
        # Process the deposit
        print(payment_method, bdt_amount, tx_id, receipt)
        return redirect('index')
    return render(request, 'deposit.html')

def logout_view(request):
    logout(request)
    return redirect('auth')