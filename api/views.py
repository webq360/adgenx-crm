from django.contrib.auth import authenticate
from django.db.models import Sum
from django.utils import timezone
from django.core.files.base import ContentFile
from datetime import timedelta, datetime
from decimal import Decimal, InvalidOperation
from io import BytesIO

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework import status

from PIL import Image

from dashboard.models import (
    User, Wallet, AdAccount, BMAccount, AdminBM,
    DepositTransaction, TopupHistory, PaymentMethod, ActivityLog
)
from dashboard.fb_api_reqs import get_ad_account_info, change_spend_cap
from dashboard.utils import log_activity


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not email or not password:
        return Response({'message': 'Email and password are required.'}, status=400)

    user = authenticate(request, username=email, password=password)
    if user is None:
        return Response({'message': 'Invalid email or password.'}, status=401)

    if not user.is_active:
        return Response({'message': 'Your account is not active. Please contact admin.'}, status=403)

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_staff': user.is_staff,
        }
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    first_name = request.data.get('first_name', '').strip()
    last_name  = request.data.get('last_name', '').strip()
    email      = request.data.get('email', '').strip()
    phone      = request.data.get('phone_number', '').strip()
    password   = request.data.get('password', '')
    password2  = request.data.get('password2', '')

    if not all([first_name, last_name, email, phone, password, password2]):
        return Response({'message': 'All fields are required.'}, status=400)

    if len(password) < 8:
        return Response({'message': 'Password must be at least 8 characters.'}, status=400)

    if password != password2:
        return Response({'message': 'Passwords do not match.'}, status=400)

    if User.objects.filter(email=email).exists():
        return Response({'message': 'User with this email already exists.'}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        phone_number=phone,
        is_active=False,
        is_verified=False,
    )
    Wallet.objects.create(user=user)

    return Response({'message': 'Registration successful! Wait for admin activation.'}, status=201)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    try:
        request.user.auth_token.delete()
    except Exception:
        pass
    return Response({'message': 'Logged out.'})


@api_view(['POST'])
@permission_classes([AllowAny])
def api_forgot_password(request):
    # Just return success — email sending handled separately
    return Response({'message': 'If an account exists, a reset link will be sent.'})


# ─── PROFILE ──────────────────────────────────────────────────────────────────

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated])
def api_profile(request):
    user = request.user

    if request.method == 'GET':
        wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0, 'dollar_rate': 127})
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number,
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_staff': user.is_staff,
            'wallet': {
                'balance': str(wallet.balance),
                'dollar_rate': str(wallet.dollar_rate),
            }
        })

    # PATCH — update profile
    user.first_name = request.data.get('first_name', user.first_name).strip()
    user.last_name  = request.data.get('last_name', user.last_name).strip()
    user.phone_number = request.data.get('phone_number', user.phone_number).strip()
    user.save()
    return Response({'message': 'Profile updated.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_change_password(request):
    old_password = request.data.get('old_password', '')
    new_password = request.data.get('new_password', '')

    if not old_password or not new_password:
        return Response({'message': 'Both fields are required.'}, status=400)

    if len(new_password) < 8:
        return Response({'message': 'New password must be at least 8 characters.'}, status=400)

    if not request.user.check_password(old_password):
        return Response({'message': 'Current password is incorrect.'}, status=400)

    request.user.set_password(new_password)
    request.user.save()
    # Re-generate token after password change
    Token.objects.filter(user=request.user).delete()
    token = Token.objects.create(user=request.user)
    return Response({'message': 'Password changed.', 'token': token.key})


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    user = request.user
    wallet, _ = Wallet.objects.get_or_create(user=user, defaults={'balance': 0, 'dollar_rate': 127})

    start_date_str = request.GET.get('start_date')
    end_date_str   = request.GET.get('end_date')

    if not start_date_str:
        start_date_str = timezone.now().strftime('%Y-%m-%d')

    start_date = end_date = None
    try:
        start_date = timezone.make_aware(datetime.strptime(start_date_str, '%Y-%m-%d'))
        if end_date_str:
            end_date = timezone.make_aware(datetime.strptime(end_date_str, '%Y-%m-%d')) + timedelta(days=1)
        else:
            end_date = start_date + timedelta(days=1)
    except (ValueError, TypeError):
        pass

    deposit_qs = DepositTransaction.objects.filter(user=user, status='approved')
    topup_qs   = TopupHistory.objects.filter(ad_account__user=user, status='approved', type='increase')

    if start_date:
        deposit_qs = deposit_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
        topup_qs   = topup_qs.filter(date__gte=start_date, date__lt=end_date)

    total_deposit = deposit_qs.aggregate(total=Sum('usd_amount'))['total'] or 0
    total_topup   = topup_qs.aggregate(total=Sum('amount'))['total'] or 0

    active_accounts = AdAccount.objects.filter(user=user, status='active').order_by('-start_date')[:10]
    accounts_data = []
    for acc in active_accounts:
        bms = [{'id': b.id, 'acc_name': b.acc_name, 'acc_id': b.acc_id, 'status': b.status} for b in acc.bm_accounts.all()]
        accounts_data.append({
            'id': acc.id,
            'name': acc.name,
            'acc_id': acc.acc_id,
            'acc_link': acc.acc_link,
            'start_date': str(acc.start_date),
            'monthly_budget': str(acc.monthly_budget),
            'status': acc.status,
            'has_admin_bm': bool(acc.admin_bm and acc.status == 'active'),
            'bm_accounts': bms,
        })

    return Response({
        'wallet': {'balance': str(wallet.balance), 'dollar_rate': str(wallet.dollar_rate)},
        'total_deposit': str(total_deposit),
        'total_topup_increase': str(total_topup),
        'ad_accounts': accounts_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
    })


# ─── AD ACCOUNTS ──────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_ad_accounts(request):
    user = request.user
    search = request.GET.get('search', '')

    qs = AdAccount.objects.filter(user=user)
    if search:
        qs = qs.filter(name__icontains=search)
    qs = qs.order_by('-start_date')

    # Simple pagination
    page = int(request.GET.get('page', 1))
    per_page = 20
    start = (page - 1) * per_page
    end   = start + per_page
    total = qs.count()
    items = qs[start:end]

    results = []
    for acc in items:
        bms = [{'id': b.id, 'acc_name': b.acc_name, 'acc_id': b.acc_id, 'status': b.status, 'request_type': b.request_type}
               for b in acc.bm_accounts.all()]
        results.append({
            'id': acc.id,
            'name': acc.name,
            'acc_id': acc.acc_id,
            'acc_link': acc.acc_link,
            'start_date': str(acc.start_date),
            'monthly_budget': str(acc.monthly_budget),
            'status': acc.status,
            'has_admin_bm': bool(acc.admin_bm and acc.status == 'active'),
            'bm_accounts': bms,
        })

    return Response({
        'count': total,
        'next': f'?page={page+1}' if end < total else None,
        'previous': f'?page={page-1}' if page > 1 else None,
        'results': results,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_ad_account_fb_info(request, ad_account_id):
    try:
        acc = AdAccount.objects.get(id=ad_account_id, user=request.user)
    except AdAccount.DoesNotExist:
        return Response({'success': False}, status=404)

    if acc.admin_bm and acc.status == 'active':
        try:
            info = get_ad_account_info(acc.acc_id, acc.admin_bm.acc_id)
            if info:
                return Response({
                    'success': True,
                    'balance': info.get('balance', 'N/A'),
                    'total_spent': info.get('amount_spent', 'N/A'),
                    'limit': info.get('spend_cap', 'N/A'),
                })
        except Exception:
            pass

    return Response({'success': True, 'balance': 'N/A', 'total_spent': 'N/A', 'limit': 'N/A'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_request_ad_account(request):
    name           = request.data.get('accountName', '').strip()
    bm_client_id   = request.data.get('bmId', '').strip()
    acc_link       = request.data.get('fbPageLink', '').strip()
    start_date     = request.data.get('startDate', '').strip()
    monthly_budget = request.data.get('monthly_budget', 0)

    if not all([name, bm_client_id, acc_link, start_date]):
        return Response({'message': 'All fields are required.'}, status=400)

    bm = BMAccount.objects.create(acc_id=bm_client_id, acc_name=bm_client_id, status='pending', request_type='add')
    acc = AdAccount.objects.create(
        user=request.user,
        name=name,
        acc_id='',
        acc_link=acc_link,
        start_date=start_date,
        status='inactive',
        monthly_budget=monthly_budget or 0,
    )
    acc.bm_accounts.add(bm)
    
    # Send notifications
    from dashboard.notification_handler import notify_ad_account_requested
    notify_ad_account_requested(acc)

    return Response({'message': 'Ad account request submitted successfully!'})


# ─── TOPUP ────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_topup(request):
    from django.db import transaction as db_transaction
    from django.db.models import F

    ad_account_id = request.data.get('ad_account_id')
    amount_raw    = request.data.get('amount')

    try:
        amount = Decimal(str(amount_raw))
        if amount <= 0:
            return Response({'success': False, 'error': 'Amount must be positive.'})
    except (InvalidOperation, TypeError):
        return Response({'success': False, 'error': 'Invalid amount.'})

    try:
        acc = AdAccount.objects.get(id=ad_account_id, user=request.user)
    except AdAccount.DoesNotExist:
        return Response({'success': False, 'error': 'Ad account not found.'})

    with db_transaction.atomic():
        wallet = Wallet.objects.select_for_update().get(user=request.user)
        if wallet.balance < amount:
            return Response({'success': False, 'error': 'Insufficient balance.'})

        admin_bm_id = acc.admin_bm.acc_id if acc.admin_bm else None
        try:
            ad_info = get_ad_account_info(acc.acc_id, admin_bm_id)
            if not ad_info:
                return Response({'success': False, 'error': 'Failed to fetch ad account info.'})

            current_cap = float(ad_info.get('spend_cap', 0))
            result = change_spend_cap(current_cap + float(amount), acc.acc_id, admin_bm_id)
            if not result:
                return Response({'success': False, 'error': 'Failed to update spend cap.'})
        except Exception as e:
            return Response({'success': False, 'error': str(e)})

        old_balance = wallet.balance
        wallet.balance = F('balance') - amount
        wallet.save()
        wallet.refresh_from_db()

        TopupHistory.objects.create(ad_account=acc, amount=amount, status='approved', type='increase')

        log_activity(
            performed_by=request.user,
            activity_type='topup_increase',
            description=f"Top-up ${amount} to {acc.name}. Wallet: ${old_balance} → ${wallet.balance}",
            target_user=request.user,
            old_value={'wallet_balance': str(old_balance)},
            new_value={'wallet_balance': str(wallet.balance), 'topup_amount': str(amount)},
            request=request,
        )

    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_decrease_limit(request):
    ad_account_id = request.data.get('ad_account_id')
    amount_raw    = request.data.get('amount')

    try:
        amount = float(amount_raw)
        if amount <= 0:
            return Response({'success': False, 'error': 'Amount must be positive.'})
    except (TypeError, ValueError):
        return Response({'success': False, 'error': 'Invalid amount.'})

    try:
        acc = AdAccount.objects.get(id=ad_account_id, user=request.user)
    except AdAccount.DoesNotExist:
        return Response({'success': False, 'error': 'Ad account not found.'})

    TopupHistory.objects.create(ad_account=acc, amount=amount, type='decrease', status='pending')
    
    # Send notifications
    from dashboard.notification_handler import notify_topup_requested
    notify_topup_requested(TopupHistory.objects.filter(ad_account=acc, type='decrease', status='pending').last())
    
    return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_topup_transactions(request):
    ad_acc_name = request.GET.get('ad_acc_name', '')
    page = int(request.GET.get('page', 1))
    per_page = 15

    qs = TopupHistory.objects.filter(ad_account__user=request.user).order_by('-date')
    if ad_acc_name:
        qs = qs.filter(ad_account__name__icontains=ad_acc_name)

    start = (page - 1) * per_page
    end   = start + per_page
    total = qs.count()
    items = qs[start:end]

    results = [{
        'id': t.id,
        'ad_account_name': t.ad_account.name if t.ad_account else '',
        'amount': str(t.amount),
        'type': t.type,
        'status': t.status,
        'date': str(t.date),
    } for t in items]

    return Response({
        'count': total,
        'next': f'?page={page+1}' if end < total else None,
        'previous': f'?page={page-1}' if page > 1 else None,
        'results': results,
    })


# ─── DEPOSIT ──────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_payment_methods(request):
    methods = PaymentMethod.objects.filter(is_active=True)
    data = [{
        'id': m.id,
        'method_name': m.method_name,
        'method_type': m.method_type,
        'method_logo': request.build_absolute_uri(m.method_logo.url) if m.method_logo else None,
        'account_name': m.account_name,
        'account_number': m.account_number,
        'district': m.district,
        'branch_name': m.branch_name,
    } for m in methods]
    return Response({'methods': data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_deposit(request):
    payment_method_id = request.data.get('payment_method_id')
    bdt_amount_raw    = request.data.get('bdt_amount')
    usd_amount_raw    = request.data.get('usd_amount')
    tx_id             = request.data.get('tx_id', '').strip()
    receipt           = request.FILES.get('receipt')

    try:
        bdt_amount = Decimal(str(bdt_amount_raw))
        usd_amount = Decimal(str(usd_amount_raw))
        if bdt_amount <= 0 or usd_amount <= 0:
            return Response({'message': 'Amount must be positive.'}, status=400)
    except (InvalidOperation, TypeError):
        return Response({'message': 'Invalid amount.'}, status=400)

    if not tx_id:
        return Response({'message': 'Transaction ID is required.'}, status=400)

    try:
        method = PaymentMethod.objects.get(id=payment_method_id, is_active=True)
    except PaymentMethod.DoesNotExist:
        return Response({'message': 'Invalid payment method.'}, status=400)

    # Compress image if provided
    compressed_receipt = None
    if receipt:
        try:
            img = Image.open(receipt)
            img_io = BytesIO()
            img = img.resize(
                (800, int(img.height * 800 / img.width)),
                Image.Resampling.LANCZOS
            )
            img.save(img_io, format='JPEG', quality=70)
            img_io.seek(0)
            compressed_receipt = ContentFile(img_io.read(), name=receipt.name)
        except Exception:
            compressed_receipt = receipt

    deposit = DepositTransaction.objects.create(
        user=request.user,
        method=method.method_name,
        trx_id=tx_id,
        vendor_trx_id=tx_id,
        receipt=compressed_receipt,
        bdt_amount=bdt_amount,
        usd_amount=usd_amount,
        status='pending',
    )
    
    # Send notifications
    from dashboard.notification_handler import notify_deposit_submitted
    notify_deposit_submitted(deposit)

    return Response({'message': 'Deposit request submitted successfully!'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_deposit_transactions(request):
    trx_id = request.GET.get('trx_id', '')
    page   = int(request.GET.get('page', 1))
    per_page = 15

    qs = DepositTransaction.objects.filter(user=request.user).order_by('-created_at')
    if trx_id:
        qs = qs.filter(trx_id__icontains=trx_id)

    start = (page - 1) * per_page
    end   = start + per_page
    total = qs.count()
    items = qs[start:end]

    results = [{
        'id': t.id,
        'method': t.method,
        'trx_id': t.trx_id,
        'bdt_amount': str(t.bdt_amount),
        'usd_amount': str(t.usd_amount),
        'status': t.status,
        'created_at': t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else '',
        'receipt': request.build_absolute_uri(t.receipt.url) if t.receipt else None,
    } for t in items]

    return Response({
        'count': total,
        'next': f'?page={page+1}' if end < total else None,
        'previous': f'?page={page-1}' if page > 1 else None,
        'results': results,
    })


# ─── BM ACCOUNT ───────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_request_bm(request):
    ad_account_id = request.data.get('ad_account_id')
    mb_name       = request.data.get('mb_name', '').strip()
    mb_id         = request.data.get('mb_id', '').strip()

    if not mb_name or not mb_id:
        return Response({'success': False, 'error': 'BM name and ID are required.'})

    try:
        acc = AdAccount.objects.get(id=ad_account_id, user=request.user)
    except AdAccount.DoesNotExist:
        return Response({'success': False, 'error': 'Ad account not found.'})

    bm = BMAccount.objects.create(acc_id=mb_id, acc_name=mb_name, request_type='add')
    acc.bm_accounts.add(bm)
    
    # Send notifications
    from dashboard.notification_handler import notify_bm_requested
    notify_bm_requested(bm, acc)
    
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_remove_bm(request):
    ad_account_id = request.data.get('ad_account_id')
    bm_account_id = request.data.get('bm_account_id')

    try:
        acc = AdAccount.objects.get(id=ad_account_id, user=request.user)
        bm  = BMAccount.objects.get(id=bm_account_id)
    except (AdAccount.DoesNotExist, BMAccount.DoesNotExist):
        return Response({'success': False, 'error': 'Not found.'})

    if bm in acc.bm_accounts.all():
        bm.request_type = 'remove'
        bm.status = 'pending'
        bm.save()
        return Response({'success': True})

    return Response({'success': False, 'error': 'BM not linked to this account.'})


# ─── NOTIFICATIONS ────────────────────────────────────────────────────────────

def create_notification(user, notification_type, title, message):
    """Helper to create a notification for a user"""
    from dashboard.models import Notification
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_notifications(request):
    from dashboard.models import Notification
    page = int(request.GET.get('page', 1))
    per_page = 20

    qs = Notification.objects.filter(user=request.user)
    unread_count = qs.filter(is_read=False).count()

    start = (page - 1) * per_page
    end   = start + per_page
    total = qs.count()
    items = qs[start:end]

    results = [{
        'id': n.id,
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M'),
    } for n in items]

    return Response({
        'count': total,
        'unread_count': unread_count,
        'next': f'?page={page+1}' if end < total else None,
        'results': results,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_mark_notifications_read(request):
    from dashboard.models import Notification
    notif_id = request.data.get('id')  # single id, or None = mark all read
    if notif_id:
        Notification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
    else:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return Response({'success': True})


@api_view(['GET'])
@permission_classes([AllowAny])
def api_unread_count(request):
    from dashboard.models import Notification
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return Response({'unread_count': count})


# ─── CORS TEST ────────────────────────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def api_cors_test(request):
    """Test endpoint to verify CORS is working"""
    return Response({
        'success': True,
        'message': 'CORS is working!',
        'method': request.method,
        'origin': request.META.get('HTTP_ORIGIN', 'No origin header'),
        'timestamp': timezone.now().isoformat(),
    })
