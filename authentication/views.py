from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings

from dashboard.models import User
from dashboard.models import Wallet
from .tokens import account_activation_token

def auth_view(request):
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'login':
            email = request.POST.get('email')
            password = request.POST.get('password')

            if not email or not password:
                messages.error(request, 'Please provide both email and password.')
                return redirect('auth')

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                return redirect('index')
            else:
                messages.error(request, 'Invalid email or password.')
                return redirect('auth')

        elif action == 'register':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            phone_number = request.POST.get('phone_number')
            password = request.POST.get('password')
            password2 = request.POST.get('password2')

            if not all([first_name, last_name, email, phone_number, password, password2]):
                messages.error(request, 'Please fill in all fields.')
                return redirect('auth')
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return redirect('auth')

            if password != password2:
                messages.error(request, 'Passwords do not match.')
                return redirect('auth')

            if User.objects.filter(email=email).exists():
                messages.error(request, 'User with this email already exists.')
                return redirect('auth')
            
            user = User.objects.create_user(
                username=email, 
                email=email, 
                password=password, 
                first_name=first_name, 
                last_name=last_name,
                phone_number=phone_number,
                is_active=False,
                is_verified=False
            )
            Wallet.objects.create(user=user)

            # Send verification email
            current_site = request.get_host()
            mail_subject = 'Activate your CRM account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = email
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [to_email],
                fail_silently=False,
            )

            messages.success(request, 'Registration successful! Please confirm your email address to complete the registration.')
            return redirect('auth')

    return render(request, 'auth.html')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Your account has been successfully activated. You can now log in.')
        return redirect('auth')
    else:
        messages.error(request, 'Activation link is invalid!')
        return redirect('auth')

def logout_view(request):
    logout(request)
    return redirect('auth')