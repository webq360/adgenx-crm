from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Sum, Q, F
from django.db import models
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
import os

from dashboard.models import DepositTransaction, Wallet, AdAccount, BMAccount, AdminBM, User, TopupHistory, ActivityLog
from dashboard.fb_api_reqs import get_ad_account_info, change_spend_cap
from dashboard.utils import paginate_data, get_user_utils, log_activity
from dashboard.group_permissions import require_group_permission as require_permission, GroupPermissionManager


def clear_user_sessions(user):
    """Clear all sessions for a user - no longer needed with Groups but kept for compatibility"""
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        try:
            session_data = session.get_decoded()
            if str(user.pk) == str(session_data.get('_auth_user_id')):
                session.delete()
        except:
            continue


@login_required(login_url='auth')
@require_permission('can_review_deposits')
def admin_overview(request):

    from decimal import Decimal
    from django.db.models import Count, Avg
    from dashboard.models import BusinessExpense

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    include_manual = request.GET.get('include_manual', 'all')

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
    
    # Count pending BM requests (add and remove)
    pending_bm_requests = BMAccount.objects.filter(status='pending').count()
    
    # Count pending withdrawal requests
    from dashboard.models import WithdrawalRequest
    pending_withdrawals = WithdrawalRequest.objects.filter(status='pending').count()

    # Build user queryset based on filter
    user_qs = User.objects.filter(is_staff=False)
    if include_manual == 'yes':
        user_qs = user_qs.filter(is_manual_client=True, include_in_profit_reports=True)
    elif include_manual == 'no':
        user_qs = user_qs.filter(is_manual_client=False, include_in_profit_reports=True)
    else:
        user_qs = user_qs.filter(include_in_profit_reports=True)

    # Filtered and aggregated data
    deposit_qs = DepositTransaction.objects.filter(status='approved', user__in=user_qs)
    topup_qs = TopupHistory.objects.filter(status='approved', type='increase', ad_account__user__in=user_qs)

    if start_date:
        deposit_qs = deposit_qs.filter(created_at__gte=start_date, created_at__lt=end_date)
        topup_qs = topup_qs.filter(date__gte=start_date, date__lt=end_date)

    total_bdt_deposit = deposit_qs.aggregate(total=Sum('bdt_amount'))['total'] or 0
    total_usd_deposit = deposit_qs.aggregate(total=Sum('usd_amount'))['total'] or Decimal('0')
    total_topup_increase = topup_qs.aggregate(total=Sum('amount'))['total'] or Decimal('0')

    # Deposit summary by rate (group by exchange rate)
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

    # Calculate profit metrics
    total_revenue = total_usd_deposit + total_topup_increase
    
    # Calculate expenses
    expense_qs = BusinessExpense.objects.all()
    if start_date:
        expense_qs = expense_qs.filter(date__gte=start_date, date__lt=end_date)
    
    total_expenses = expense_qs.aggregate(total=Sum('amount_usd'))['total'] or Decimal('0')
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Expenses by category
    expenses_by_category = expense_qs.values('category').annotate(
        total=Sum('amount_usd'),
        count=Count('id')
    ).order_by('-total')
    
    category_dict = dict(BusinessExpense.CATEGORY_CHOICES)
    for item in expenses_by_category:
        item['category_display'] = category_dict.get(item['category'], item['category'])

    # Handle expense CRUD operations
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                category = request.POST.get('category')
                description = request.POST.get('description', '').strip()
                amount_usd = Decimal(request.POST.get('amount_usd', 0))
                date = request.POST.get('date')
                notes = request.POST.get('notes', '').strip()
                receipt = request.FILES.get('receipt')
                
                expense = BusinessExpense.objects.create(
                    category=category,
                    description=description,
                    amount_usd=amount_usd,
                    date=date,
                    notes=notes,
                    receipt=receipt,
                    added_by=request.user
                )
                
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_added',
                    description=f"Added business expense: {category} - ${amount_usd}",
                    target_user=None,
                    old_value=None,
                    new_value={'category': category, 'amount': str(amount_usd), 'description': description},
                    request=request
                )
                
                messages.success(request, f'Expense added successfully: ${amount_usd}')
            except Exception as e:
                messages.error(request, f'Error adding expense: {str(e)}')
        
        elif action == 'delete':
            try:
                expense_id = request.POST.get('expense_id')
                expense = get_object_or_404(BusinessExpense, id=expense_id)
                
                amount = expense.amount_usd
                category = expense.get_category_display()
                
                expense.delete()
                
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_removed',
                    description=f"Deleted business expense: {category} - ${amount}",
                    target_user=None,
                    old_value={'amount': str(amount), 'category': category},
                    new_value=None,
                    request=request
                )
                
                messages.success(request, f'Expense deleted: {category} - ${amount}')
            except Exception as e:
                messages.error(request, f'Error deleting expense: {str(e)}')
        
        elif action == 'edit':
            try:
                expense_id = request.POST.get('expense_id')
                expense = get_object_or_404(BusinessExpense, id=expense_id)
                
                old_category = expense.get_category_display()
                old_amount = expense.amount_usd
                
                expense.category = request.POST.get('category')
                expense.description = request.POST.get('description', '').strip()
                expense.amount_usd = Decimal(request.POST.get('amount_usd', 0))
                expense.date = request.POST.get('date')
                expense.notes = request.POST.get('notes', '').strip()
                expense.save()
                
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_edited',
                    description=f"Edited business expense: {old_category} (${old_amount}) → {expense.get_category_display()} (${expense.amount_usd})",
                    target_user=None,
                    old_value={'category': old_category, 'amount': str(old_amount)},
                    new_value={'category': expense.get_category_display(), 'amount': str(expense.amount_usd)},
                    request=request
                )
                
                messages.success(request, f'Expense updated successfully')
            except Exception as e:
                messages.error(request, f'Error editing expense: {str(e)}')
        
        return redirect('admin_dashboard:admin_overview')

    # Recent expenses for display - with pagination
    all_expenses_list = expense_qs.order_by('-date')
    all_expenses = paginate_data(request, all_expenses_list, 10)

    one_month_ago = timezone.now() - timedelta(days=30)
    old_receipts_count = DepositTransaction.objects.filter(
        status__in=['approved', 'rejected'],
        created_at__lt=one_month_ago
    ).exclude(receipt='').count()

    # Calculate total user wallet balances
    total_user_wallet_balance = Wallet.objects.filter(
        user__is_staff=False
    ).aggregate(total=Sum('balance'))['total'] or Decimal('0')
    
    # Remaining balance is the same as current balance
    total_user_wallet_remaining_balance = total_user_wallet_balance

    # Get recent withdrawal requests
    from dashboard.models import WithdrawalRequest
    recent_withdrawal_requests_list = WithdrawalRequest.objects.filter(
        status='pending'
    ).select_related('user').order_by('-requested_at')[:10]
    
    utils = {
        'pending_deposits': pending_deposits,
        'pending_accounts': pending_accounts,
        'active_accounts': active_accounts,
        'pending_bm_requests': pending_bm_requests,
        'pending_withdrawals': pending_withdrawals,
    }

    context = {
        'utils': utils,
        'total_bdt_deposit': total_bdt_deposit,
        'total_usd_deposit': total_usd_deposit,
        'total_topup_increase': total_topup_increase,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'old_receipts_count': old_receipts_count,
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'profit_margin': profit_margin,
        'total_deposits': total_usd_deposit,
        'total_topups': total_topup_increase,
        'user_count': user_qs.count(),
        'expense_count': expense_qs.count(),
        'expenses_by_category': expenses_by_category,
        'expenses': all_expenses,
        'include_manual': include_manual,
        'today': timezone.now().strftime('%Y-%m-%d'),
        'total_user_wallet_balance': total_user_wallet_balance,
        'total_user_wallet_remaining_balance': total_user_wallet_remaining_balance,
        'recent_withdrawal_requests': recent_withdrawal_requests_list,
        'deposit_by_rate': deposit_by_rate,
    }

    return render(request, 'admin_overview.html', context)

@login_required(login_url='auth')
@require_permission('can_review_deposits')
def review_deposit(request):

    search_query = request.GET.get('search', '')
    if search_query:
        pending_transactions_list = DepositTransaction.objects.filter(
            status='pending',
            user__email__icontains=search_query
        ).select_related('user', 'user__wallet').order_by('-created_at')
    else:
        pending_transactions_list = DepositTransaction.objects.filter(
            status='pending'
        ).select_related('user', 'user__wallet').order_by('-created_at')

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
@require_permission('can_review_deposits')
def review_deposit_details(request, transaction_id):
    transaction = get_object_or_404(DepositTransaction, id=transaction_id)
    
    # Get user's wallet balance
    try:
        wallet = Wallet.objects.get(user=transaction.user)
        current_balance = wallet.balance
        dollar_rate = wallet.dollar_rate
    except Wallet.DoesNotExist:
        current_balance = 0
        dollar_rate = 127.00

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            old_balance = wallet.balance
            transaction.status = 'approved'
            messages.success(request, 'Deposit request approved successfully!')
            wallet.balance += transaction.usd_amount
            wallet.save()

            admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
            log_activity(
                performed_by=request.user,
                activity_type='deposit_approved',
                description=f"[ADMIN: {admin_info}] Approved deposit of ${transaction.usd_amount} (৳{transaction.bdt_amount}) for {transaction.user.username}. Wallet: ${old_balance} → ${wallet.balance}",
                target_user=transaction.user,
                old_value={'balance': str(old_balance), 'transaction_id': transaction.id},
                new_value={'balance': str(wallet.balance), 'deposit_amount': str(transaction.usd_amount)},
                request=request
            )
            # Notify user
            from dashboard.models import Notification
            from dashboard.notification_handler import notify_deposit_approved
            Notification.objects.create(
                user=transaction.user,
                notification_type='deposit_approved',
                title='Deposit Approved ✓',
                message=f'Your deposit of ${transaction.usd_amount} (৳{transaction.bdt_amount}) via {transaction.method} has been approved. Wallet balance updated to ${wallet.balance}.',
            )
            # Send email
            notify_deposit_approved(transaction)

        elif action == 'reject':
            transaction.status = 'rejected'
            messages.error(request, 'Deposit request rejected.')

            admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
            log_activity(
                performed_by=request.user,
                activity_type='deposit_rejected',
                description=f"[ADMIN: {admin_info}] Rejected deposit of ${transaction.usd_amount} (৳{transaction.bdt_amount}) for {transaction.user.username}",
                target_user=transaction.user,
                old_value={'transaction_id': transaction.id, 'status': 'pending'},
                new_value={'transaction_id': transaction.id, 'status': 'rejected'},
                request=request
            )
            # Notify user
            from dashboard.models import Notification
            from dashboard.notification_handler import notify_deposit_rejected
            Notification.objects.create(
                user=transaction.user,
                notification_type='deposit_rejected',
                title='Deposit Rejected ✗',
                message=f'Your deposit of ${transaction.usd_amount} (৳{transaction.bdt_amount}) via {transaction.method} has been rejected. Please contact support for details.',
            )
            # Send email
            notify_deposit_rejected(transaction)
            
        transaction.save()
        return redirect('admin_dashboard:review_deposit')

    return render(request, 'review_deposit_details.html', {
        'transaction': transaction,
        'current_balance': current_balance,
        'dollar_rate': dollar_rate
    })

@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def ad_account_details(request, ad_account_id):

    ad_account = get_object_or_404(AdAccount, id=ad_account_id)
    admin_bms = AdminBM.objects.all()

    if ad_account.status == 'active' and ad_account.admin_bm:
        ad_info = get_ad_account_info(ad_account.acc_id, ad_account.admin_bm.acc_id)
        if isinstance(ad_info, dict):
            ad_account.balance = ad_info.get('balance', 0)
            ad_account.total_spent = ad_info.get('amount_spent', 0)
            ad_account.limit = ad_info.get('spend_cap', 0)
        else:
            ad_account.balance = 'N/A'
            ad_account.limit = 'N/A'
            ad_account.total_spent = 'N/A'
            messages.warning(request, 'Unable to fetch ad account stats right now. Please try again later.')
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
            from dashboard.models import Notification
            Notification.objects.create(
                user=ad_account.user,
                notification_type='ad_account_activated',
                title='Ad Account Activated ✓',
                message=f'Your ad account "{ad_account.name}" has been activated. You can now top up and run ads.',
            )

        elif action == 'deactivate':
            ad_account.status = 'inactive'
            ad_account.save()
            messages.warning(request, 'Ad account has been deactivated.')
            from dashboard.models import Notification
            Notification.objects.create(
                user=ad_account.user,
                notification_type='ad_account_deactivated',
                title='Ad Account Deactivated',
                message=f'Your ad account "{ad_account.name}" has been deactivated. Please contact support for more info.',
            )
        
        elif action == 'delete':
            ad_account.delete()
            messages.success(request, 'Ad account has been deleted.')
            return redirect('ad_accounts')

        return redirect('admin_dashboard:ad_account_details', ad_account_id=ad_account.id)

    return render(request, 'ad_account_details.html', {'ad_account': ad_account, 'admin_bms': admin_bms})

@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def review_ad_account(request):

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
@require_permission('can_manage_accounts')
def review_bm_request(request):

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
@require_permission('can_manage_users')
def manage_user(request):

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        user_to_manage = get_object_or_404(User.objects.prefetch_related('groups'), id=user_id, is_staff=False)
        
        if action == 'edit_user':
            # Update user details
            user_to_manage.first_name = request.POST.get('first_name', '').strip()
            user_to_manage.last_name = request.POST.get('last_name', '').strip()
            user_to_manage.email = request.POST.get('email', '').strip()
            user_to_manage.phone_number = request.POST.get('phone_number', '').strip()
            
            old_active_status = user_to_manage.is_active
            is_active = request.POST.get('is_active') == 'on'
            user_to_manage.is_active = is_active
            
            old_verified = user_to_manage.is_verified
            is_verified = request.POST.get('is_verified') == 'on'
            user_to_manage.is_verified = is_verified
            
            # Handle group (role) assignment - USING DJANGO GROUPS
            group_id = request.POST.get('group')
            group_changed = False
            if group_id:
                old_groups = list(user_to_manage.groups.all())
                try:
                    new_group = Group.objects.get(id=group_id)
                    # Clear existing groups and add new one
                    user_to_manage.groups.clear()
                    user_to_manage.groups.add(new_group)
                    group_changed = True
                    
                    old_group_names = ', '.join([g.name for g in old_groups]) if old_groups else "No group"
                    admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
                    log_activity(
                        performed_by=request.user,
                        activity_type='role_change',
                        description=f"[ADMIN: {admin_info}] Changed group for {user_to_manage.username}: {old_group_names} → {new_group.name}",
                        target_user=user_to_manage,
                        old_value={'group': old_group_names},
                        new_value={'group': new_group.name},
                        request=request
                    )
                except Group.DoesNotExist:
                    pass
            else:
                # Remove all groups
                old_groups = list(user_to_manage.groups.all())
                if old_groups:
                    user_to_manage.groups.clear()
                    group_changed = True
                    old_group_names = ', '.join([g.name for g in old_groups])
                    admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
                    log_activity(
                        performed_by=request.user,
                        activity_type='role_change',
                        description=f"[ADMIN: {admin_info}] Removed groups from {user_to_manage.username}: {old_group_names}",
                        target_user=user_to_manage,
                        old_value={'group': old_group_names},
                        new_value={'group': 'No group'},
                        request=request
                    )
            
            user_to_manage.save()
            
            # Clear user's sessions if group changed (force re-login to apply new permissions)
            if group_changed:
                clear_user_sessions(user_to_manage)
                messages.success(request, f'User updated successfully! {user_to_manage.username} needs to log in again for permissions to take effect.')
            else:
                messages.success(request, 'User updated successfully!')
            
            # Update dollar rate
            dollar_rate = request.POST.get('dollar_rate')
            if dollar_rate:
                try:
                    wallet = Wallet.objects.get(user=user_to_manage)
                    old_rate = wallet.dollar_rate
                    new_rate = float(dollar_rate)
                    
                    if old_rate != new_rate:
                        wallet.dollar_rate = new_rate
                        wallet.save()
                        
                        admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
                        log_activity(
                            performed_by=request.user,
                            activity_type='rate_change',
                            description=f"[ADMIN: {admin_info}] Changed dollar rate for {user_to_manage.username}: ৳{old_rate} → ৳{new_rate}",
                            target_user=user_to_manage,
                            old_value={'dollar_rate': str(old_rate)},
                            new_value={'dollar_rate': str(new_rate)},
                            request=request
                        )
                except Wallet.DoesNotExist:
                    pass
            
            # Log activation/deactivation
            if old_active_status != is_active:
                log_activity(
                    performed_by=request.user,
                    activity_type='user_activated' if is_active else 'user_deactivated',
                    description=f"{'Activated' if is_active else 'Deactivated'} user {user_to_manage.username}",
                    target_user=user_to_manage,
                    old_value={'is_active': old_active_status},
                    new_value={'is_active': is_active},
                    request=request
                )
            
            return redirect('admin_dashboard:manage_user')
        
        elif action == 'toggle_ban':
            # Ban/Unban user
            is_active = request.POST.get('is_active') == 'true'
            old_status = user_to_manage.is_active
            user_to_manage.is_active = is_active
            user_to_manage.save()
            
            admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
            log_activity(
                performed_by=request.user,
                activity_type='user_activated' if is_active else 'user_deactivated',
                description=f"[ADMIN: {admin_info}] {'Unbanned' if is_active else 'Banned'} user {user_to_manage.username}",
                target_user=user_to_manage,
                old_value={'is_active': old_status},
                new_value={'is_active': is_active},
                request=request
            )
            
            messages.success(request, f"User {'unbanned' if is_active else 'banned'} successfully!")
            return redirect('admin_dashboard:manage_user')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    all_users_list = User.objects.filter(is_staff=False).prefetch_related('groups', 'wallet').order_by('-id')
    
    if search_query:
        all_users_list = all_users_list.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    
    # Add spending info to each user
    from decimal import Decimal
    for user in all_users_list:
        # Calculate total spent (top-ups)
        total_spent = TopupHistory.objects.filter(
            ad_account__user=user,
            status='approved',
            type='increase'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Calculate total received (deposits)
        total_received = DepositTransaction.objects.filter(
            user=user,
            status='approved'
        ).aggregate(total=Sum('usd_amount'))['total'] or Decimal('0')
        
        user.total_spent = total_spent
        user.total_received = total_received
        user.group_name = user.groups.first().name if user.groups.exists() else 'No Role'
    
    all_users = paginate_data(request, all_users_list, 15)
    return render(request, 'manage_user.html', {'all_users': all_users})

@login_required(login_url='auth')
@require_permission('can_manage_users')
def manage_roles(request):
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(User)
    available_permissions = GroupPermissionManager.PERMISSIONS

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_role':
            role_name = request.POST.get('group_name', '').strip()
            selected_permissions = request.POST.getlist('permissions')

            if not role_name:
                messages.error(request, 'Role name is required.')
            else:
                group, created = Group.objects.get_or_create(name=role_name)
                group.permissions.clear()

                for permission_codename in selected_permissions:
                    permission, _ = Permission.objects.get_or_create(
                        codename=permission_codename,
                        content_type=content_type,
                        defaults={'name': GroupPermissionManager.PERMISSIONS.get(permission_codename, permission_codename)}
                    )
                    group.permissions.add(permission)

                messages.success(request, f"Role '{role_name}' saved successfully.")
                return redirect('admin_dashboard:manage_roles')

        elif action == 'delete_role':
            group_id = request.POST.get('group_id')
            group = Group.objects.filter(id=group_id).first()
            if group:
                group.delete()
                messages.success(request, f"Role '{group.name}' deleted successfully.")
            else:
                messages.error(request, 'Role not found.')
            return redirect('admin_dashboard:manage_roles')

    roles = Group.objects.prefetch_related('permissions').all()
    return render(request, 'manage_roles.html', {
        'roles': roles,
        'available_permissions': available_permissions,
    })

@login_required(login_url='auth')
@require_permission('can_manage_users')
def edit_role(request, group_id):
    from django.contrib.contenttypes.models import ContentType

    content_type = ContentType.objects.get_for_model(User)
    group = get_object_or_404(Group, id=group_id)
    available_permissions = GroupPermissionManager.PERMISSIONS
    current_permissions = [perm.codename for perm in group.permissions.all()]

    if request.method == 'POST':
        new_name = request.POST.get('group_name', '').strip()
        selected_permissions = request.POST.getlist('permissions')

        if not new_name:
            messages.error(request, 'Role name is required.')
        elif Group.objects.filter(name=new_name).exclude(id=group.id).exists():
            messages.error(request, 'Another role with that name already exists.')
        else:
            group.name = new_name
            group.save()
            group.permissions.clear()

            for permission_codename in selected_permissions:
                permission, _ = Permission.objects.get_or_create(
                    codename=permission_codename,
                    content_type=content_type,
                    defaults={'name': GroupPermissionManager.PERMISSIONS.get(permission_codename, permission_codename)}
                )
                group.permissions.add(permission)

            messages.success(request, f"Role '{new_name}' updated successfully.")
            return redirect('admin_dashboard:manage_roles')

        current_permissions = selected_permissions

    return render(request, 'edit_role.html', {
        'group': group,
        'available_permissions': available_permissions,
        'current_permissions': current_permissions,
    })

@login_required(login_url='auth')
@require_permission('can_manage_users')
def user_api(request, user_id):
    """API endpoint for user details (for modals)"""
    
    try:
        user = User.objects.get(id=user_id, is_staff=False)
        
        # Try to get wallet, create if doesn't exist
        try:
            wallet = user.wallet
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=user)
        
        # Get user statistics
        pending_deposits = DepositTransaction.objects.filter(user=user, status='pending').count()
        pending_accounts = AdAccount.objects.filter(user=user, status='inactive').count()
        active_accounts = AdAccount.objects.filter(user=user, status='active').count()
        
        # Calculate total deposits
        total_approved_deposit = DepositTransaction.objects.filter(
            user=user, 
            status='approved'
        ).aggregate(total=Sum('usd_amount'))['total'] or 0
        
        # Calculate total spent (top-ups to ad accounts)
        total_spent = TopupHistory.objects.filter(
            ad_account__user=user,
            status='approved',
            type='increase'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Current balance
        current_balance = wallet.balance
        
        # Total received = deposits
        total_received = total_approved_deposit
        
        # Remaining = Current balance (what's left in wallet)
        remaining_balance = current_balance
        
        # Get available groups and current user's group
        from django.contrib.auth.models import Group
        available_groups = Group.objects.all().values('id', 'name')
        user_group_id = user.groups.first().id if user.groups.exists() else None

        # Get user's ad accounts
        ad_accounts = AdAccount.objects.filter(user=user).values('id', 'name', 'status')
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone_number': user.phone_number or '',
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_manual_client': user.is_manual_client,
            'wallet_balance': str(current_balance),
            'dollar_rate': str(wallet.dollar_rate),
            'total_received': str(total_received),
            'total_spent': str(total_spent),
            'remaining_balance': str(remaining_balance),
            'available_groups': list(available_groups),
            'group_id': user_group_id,
            'ad_accounts': list(ad_accounts),
            'stats': {
                'pending_deposits': pending_deposits,
                'pending_accounts': pending_accounts,
                'active_accounts': active_accounts,
                'total_approved_deposit': str(total_approved_deposit),
                'total_spent': str(total_spent),
                'remaining_balance': str(remaining_balance),
            }
        }
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'User not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required(login_url='auth')
@require_permission('can_review_deposits')
def review_topup(request):

    if request.method == 'POST':
        topup_id = request.POST.get('topup_id')
        action = request.POST.get('action')
        topup = get_object_or_404(TopupHistory, id=topup_id)

        if action == 'approve':
            if not topup.ad_account:
                messages.error(request, "Ad account associated with this top-up has been deleted.")
                return redirect('admin_dashboard:review_topup')
            
            if not topup.ad_account.admin_bm:
                messages.error(request, "Admin BM account associated with this top-up has been removed.")
                return redirect('admin_dashboard:review_topup')
            
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
                        old_wallet_balance = wallet.balance
                        wallet.balance += topup.amount
                        new_wallet_balance = wallet.balance
                        wallet.save()
                        
                        # Update ad account balances
                        ad_account = topup.ad_account
                        ad_account.total_spent = F('total_spent') - topup.amount
                        ad_account.remaining_balance = F('remaining_balance') + topup.amount
                        ad_account.save()
                        ad_account.refresh_from_db()
                        
                        topup.status = 'approved'
                        topup.save()
                        
                        # Log activity with wallet balance details
                        admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
                        log_activity(
                            performed_by=request.user,
                            activity_type='topup_decrease',
                            description=f"[ADMIN: {admin_info}] Approved top-up decrease ${topup_amount} for {topup.ad_account.name}. Wallet: ${old_wallet_balance} → ${new_wallet_balance}",
                            target_user=user,
                            old_value={
                                'wallet_balance': str(old_wallet_balance),
                                'ad_account': topup.ad_account.name,
                                'approved_by': admin_info
                            },
                            new_value={
                                'wallet_balance': str(new_wallet_balance),
                                'returned_amount': str(topup_amount),
                                'remaining_balance': str(new_wallet_balance)
                            },
                            request=request
                        )
                        
                        # Send notifications
                        from dashboard.notification_handler import notify_topup_approved
                        notify_topup_approved(topup)
                        
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
    # Staff only - keep this check
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


@login_required(login_url='auth')
def activity_log(request):
    """View all activity logs - Staff only"""
    if request.user.is_staff:
        # Admin can see all logs
        logs = ActivityLog.objects.select_related('performed_by', 'target_user').all()
        
        # Filters for admin
        activity_type = request.GET.get('activity_type', '')
        user_filter = request.GET.get('user', '')
        
        if activity_type:
            logs = logs.filter(activity_type=activity_type)
        
        if user_filter:
            logs = logs.filter(
                models.Q(performed_by__username__icontains=user_filter) |
                models.Q(target_user__username__icontains=user_filter)
            )
    else:
        # Normal user can only see their own activities
        logs = ActivityLog.objects.select_related('performed_by', 'target_user').filter(
            models.Q(performed_by=request.user) | models.Q(target_user=request.user)
        )
        
        activity_type = request.GET.get('activity_type', '')
        user_filter = ''
        
        if activity_type:
            logs = logs.filter(activity_type=activity_type)
    
    # Date filters (both admin and user)
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if date_from:
        try:
            date_from_obj = timezone.make_aware(datetime.strptime(date_from, '%Y-%m-%d'))
            logs = logs.filter(timestamp__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = timezone.make_aware(datetime.strptime(date_to, '%Y-%m-%d')) + timedelta(days=1)
            logs = logs.filter(timestamp__lt=date_to_obj)
        except ValueError:
            pass
    
    # Paginate
    logs_paginated = paginate_data(request, logs, 50)
    
    # Get activity types for filter dropdown
    activity_types = ActivityLog.ACTIVITY_TYPES
    
    context = {
        'logs': logs_paginated,
        'activity_types': activity_types,
        'activity_type': activity_type,
        'user_filter': user_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'activity_log.html', context)


@login_required(login_url='auth')
@require_permission('can_manage_users')
def create_manual_client(request):
    """Create a manual client with custom settings"""
    
    if request.method == 'POST':
        try:
            # Extract form data
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            email = request.POST.get('email', '').strip()
            phone_number = request.POST.get('phone_number', '').strip()
            password = request.POST.get('password', '')
            
            # Wallet configuration
            usd_balance = float(request.POST.get('usd_balance', 0))
            bdt_balance = float(request.POST.get('bdt_balance', 0))
            dollar_rate = float(request.POST.get('dollar_rate', 127.00))
            
            # Additional settings
            notes = request.POST.get('notes', '').strip()
            is_active = request.POST.get('is_active') == 'on'
            is_verified = request.POST.get('is_verified') == 'on'
            include_in_profit_reports = request.POST.get('include_in_profit_reports') == 'on'
            
            # Validation
            if not first_name or not last_name or not email or not password:
                messages.error(request, 'Please fill in all required fields.')
                return render(request, 'create_manual_client.html')
            
            if len(password) < 8:
                messages.error(request, 'Password must be at least 8 characters long.')
                return render(request, 'create_manual_client.html')
            
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, f'A user with email {email} already exists.')
                return render(request, 'create_manual_client.html')
            
            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                phone_number=phone_number,
                is_active=is_active,
                is_verified=is_verified,
                is_manual_client=True,
                notes=notes,
                include_in_profit_reports=include_in_profit_reports,
                created_by=request.user
            )
            
            # Calculate total USD balance (USD balance + converted BDT balance)
            total_usd_balance = usd_balance + (bdt_balance / dollar_rate if dollar_rate > 0 else 0)
            
            # Create wallet
            wallet = Wallet.objects.create(
                user=user,
                balance=total_usd_balance,
                dollar_rate=dollar_rate
            )
            
            # Log activity
            log_activity(
                performed_by=request.user,
                activity_type='user_created',
                description=f"Created manual client {user.username} ({user.first_name} {user.last_name}) with ${total_usd_balance} balance",
                target_user=user,
                old_value=None,
                new_value={
                    'username': user.username,
                    'email': user.email,
                    'balance': str(total_usd_balance),
                    'dollar_rate': str(dollar_rate),
                    'is_manual_client': True
                },
                request=request
            )
            
            messages.success(request, f'Manual client {user.first_name} {user.last_name} created successfully!')
            return redirect('admin_dashboard:manage_user')
            
        except ValueError as e:
            messages.error(request, f'Invalid number format: {str(e)}')
            return render(request, 'create_manual_client.html')
        except Exception as e:
            messages.error(request, f'Error creating client: {str(e)}')
            return render(request, 'create_manual_client.html')
    
    return render(request, 'create_manual_client.html')



@login_required(login_url='auth')
@require_permission('can_review_deposits')
def edit_wallet_balance(request):
    """Manually edit user's wallet balance"""
    
    if request.method == 'POST':
        try:
            from decimal import Decimal
            
            user_id = request.POST.get('user_id')
            new_balance = request.POST.get('new_balance')
            admin_reason = request.POST.get('admin_reason', '').strip()
            
            user = get_object_or_404(User, id=user_id)
            wallet = get_object_or_404(Wallet, user=user)
            
            old_balance = wallet.balance
            new_balance_decimal = Decimal(new_balance)
            
            if new_balance_decimal < 0:
                messages.error(request, 'Balance cannot be negative.')
                return redirect(f'/admin_dashboard/manage_user/?username={user.username}')
            
            # Update wallet balance
            wallet.balance = new_balance_decimal
            wallet.save()
            
            # Log activity with admin details
            admin_info = f"{request.user.first_name} {request.user.last_name} ({request.user.username})"
            log_activity(
                performed_by=request.user,
                activity_type='wallet_edit',
                description=f"[ADMIN: {admin_info}] Manually edited wallet balance for {user.username} ({user.first_name} {user.last_name}): ${old_balance} → ${new_balance_decimal}. Reason: {admin_reason or 'No reason provided'}",
                target_user=user,
                old_value={
                    'balance': str(old_balance),
                    'edited_by': admin_info,
                    'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                new_value={
                    'balance': str(new_balance_decimal),
                    'reason': admin_reason or 'No reason provided',
                    'edited_by': admin_info
                },
                request=request
            )
            
            messages.success(request, f'Wallet balance updated successfully! Old: ${old_balance} → New: ${new_balance_decimal}')
            return redirect(f'/admin_dashboard/manage_user/?username={user.username}')
            
        except ValueError:
            messages.error(request, 'Invalid balance amount.')
            return redirect(f'/admin_dashboard/manage_user/?username={user.username}')
        except Exception as e:
            messages.error(request, f'Error editing wallet balance: {str(e)}')
            return redirect(f'/admin_dashboard/manage_user/?username={user.username}')
    
    return redirect('admin_dashboard:manage_user')



@login_required(login_url='auth')
@require_permission('can_manage_payments')
def payment_methods(request):
    """Manage payment methods"""
    
    from dashboard.models import PaymentMethod
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                method_type = request.POST.get('method_type', 'bank')
                method_name = request.POST.get('method_name', '').strip()
                account_name = request.POST.get('account_name', '').strip()
                account_number = request.POST.get('account_number', '').strip()
                district = request.POST.get('district', '').strip()
                branch_name = request.POST.get('branch_name', '').strip()
                is_active = request.POST.get('is_active') == 'on'
                method_logo = request.FILES.get('method_logo')

                if not method_name:
                    messages.error(request, 'Method name is required.')
                    return redirect('admin_dashboard:payment_methods')

                PaymentMethod.objects.create(
                    method_type=method_type,
                    method_name=method_name,
                    account_name=account_name,
                    account_number=account_number,
                    district=district if method_type == 'bank' else '',
                    branch_name=branch_name if method_type == 'bank' else '',
                    is_active=is_active,
                    method_logo=method_logo,
                )
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_added',
                    description=f"Added {method_type} payment method: {method_name}",
                    target_user=None, old_value=None,
                    new_value={'method_name': method_name, 'method_type': method_type},
                    request=request,
                )
                messages.success(request, f'Payment method "{method_name}" added successfully!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')

        elif action == 'edit':
            try:
                method_id = request.POST.get('method_id')
                pm = get_object_or_404(PaymentMethod, id=method_id)
                method_type = request.POST.get('method_type', pm.method_type)
                pm.method_type = method_type
                pm.method_name = request.POST.get('method_name', '').strip()
                pm.account_name = request.POST.get('account_name', '').strip()
                pm.account_number = request.POST.get('account_number', '').strip()
                pm.district = request.POST.get('district', '').strip() if method_type == 'bank' else ''
                pm.branch_name = request.POST.get('branch_name', '').strip() if method_type == 'bank' else ''
                pm.is_active = request.POST.get('is_active') == 'on'
                if request.FILES.get('method_logo'):
                    pm.method_logo = request.FILES.get('method_logo')
                pm.save()
                messages.success(request, f'"{pm.method_name}" updated successfully!')
            except Exception as e:
                messages.error(request, f'Error: {str(e)}')
        
        elif action == 'toggle':
            try:
                method_id = request.POST.get('method_id')
                payment_method = get_object_or_404(PaymentMethod, id=method_id)
                
                payment_method.is_active = not payment_method.is_active
                payment_method.save()
                
                status = 'activated' if payment_method.is_active else 'deactivated'
                messages.success(request, f'Payment method "{payment_method.method_name}" {status}!')
            except Exception as e:
                messages.error(request, f'Error toggling payment method: {str(e)}')
        
        elif action == 'delete':
            try:
                method_id = request.POST.get('method_id')
                payment_method = get_object_or_404(PaymentMethod, id=method_id)
                
                method_name = payment_method.method_name
                payment_method.delete()
                
                # Log activity
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_removed',
                    description=f"Deleted payment method: {method_name}",
                    target_user=None,
                    old_value={'method_name': method_name},
                    new_value=None,
                    request=request
                )
                
                messages.success(request, f'Payment method "{method_name}" deleted successfully!')
            except Exception as e:
                messages.error(request, f'Error deleting payment method: {str(e)}')
        
        return redirect('admin_dashboard:payment_methods')
    
    payment_methods_list = PaymentMethod.objects.all().order_by('-is_active', 'method_name')

    return render(request, 'payment_methods.html', {
        'payment_methods': payment_methods_list,
        'bank_methods': payment_methods_list.filter(method_type='bank'),
        'mobile_methods': payment_methods_list.filter(method_type='mobile_wallet'),
        'bank_count': payment_methods_list.filter(method_type='bank').count(),
        'mobile_count': payment_methods_list.filter(method_type='mobile_wallet').count(),
        'active_count': payment_methods_list.filter(is_active=True).count(),
    })



@login_required(login_url='auth')
@require_permission('can_manage_users')
def delete_user(request):
    """Delete a user and all associated data"""
    
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            confirm_email = request.POST.get('confirm_email', '').strip()
            
            user_to_delete = get_object_or_404(User, id=user_id, is_staff=False)
            
            # Verify email confirmation
            if confirm_email != user_to_delete.email:
                messages.error(request, 'Email confirmation does not match. User not deleted.')
                return redirect(f'/admin_dashboard/manage_user/?username={user_to_delete.username}')
            
            # Store info for logging
            username = user_to_delete.username
            email = user_to_delete.email
            
            # Log activity before deletion
            log_activity(
                performed_by=request.user,
                activity_type='user_deleted',
                description=f"Deleted user {username} ({email})",
                target_user=None,  # User will be deleted
                old_value={
                    'username': username,
                    'email': email,
                    'is_manual_client': user_to_delete.is_manual_client
                },
                new_value=None,
                request=request
            )
            
            # Delete user (cascades to wallet, ad accounts, etc.)
            user_to_delete.delete()
            
            messages.success(request, f'User {username} ({email}) and all associated data deleted successfully!')
            return redirect('admin_dashboard:manage_user')
            
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')
            return redirect('admin_dashboard:manage_user')
    
    return redirect('admin_dashboard:manage_user')



@login_required(login_url='auth')
@require_permission('can_review_deposits')
def withdrawal_requests(request):
    """Manage withdrawal requests"""
    
    from dashboard.models import WithdrawalRequest
    
    # Handle processing withdrawal requests
    if request.method == 'POST':
        try:
            withdrawal_id = request.POST.get('withdrawal_id')
            action = request.POST.get('action')
            admin_notes = request.POST.get('admin_notes', '').strip()
            
            withdrawal = get_object_or_404(WithdrawalRequest, id=withdrawal_id)
            old_status = withdrawal.status
            
            if action in ['approved', 'rejected', 'processed']:
                withdrawal.status = action
                withdrawal.reviewed_by = request.user
                withdrawal.reviewed_at = timezone.now()
                withdrawal.admin_notes = admin_notes
                withdrawal.save()
                
                # Log activity
                log_activity(
                    performed_by=request.user,
                    activity_type='payment_method_added',  # Reusing existing type
                    description=f"{'Approved' if action == 'approved' else 'Rejected' if action == 'rejected' else 'Processed'} withdrawal request of ${withdrawal.amount_usd} for {withdrawal.user.username}",
                    target_user=withdrawal.user,
                    old_value={'status': old_status, 'withdrawal_id': withdrawal_id},
                    new_value={'status': action, 'admin_notes': admin_notes},
                    request=request
                )
                
                messages.success(request, f'Withdrawal request {action}!')
            
        except Exception as e:
            messages.error(request, f'Error processing withdrawal: {str(e)}')
        
        return redirect('admin_dashboard:withdrawal_requests')
    
    # Get filter parameter
    status_filter = request.GET.get('status', 'pending')
    
    # Build queryset
    if status_filter == 'all':
        withdrawals_list = WithdrawalRequest.objects.all()
    else:
        withdrawals_list = WithdrawalRequest.objects.filter(status=status_filter)
    
    withdrawals_list = withdrawals_list.select_related('user', 'reviewed_by').order_by('-requested_at')
    
    # Get counts for tabs
    pending_count = WithdrawalRequest.objects.filter(status='pending').count()
    approved_count = WithdrawalRequest.objects.filter(status='approved').count()
    rejected_count = WithdrawalRequest.objects.filter(status='rejected').count()
    total_count = WithdrawalRequest.objects.count()
    
    # Paginate
    withdrawals = paginate_data(request, withdrawals_list, 20)
    
    context = {
        'withdrawals': withdrawals,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_count': total_count,
    }
    
    return render(request, 'withdrawal_requests.html', context)



@login_required(login_url='auth')
@require_permission('can_review_deposits')
def wallet_balance_report(request):
    """Total wallet balance report for all users"""
    
    from decimal import Decimal
    from django.db.models import Count, Avg
    
    # Get filter parameters
    user_type = request.GET.get('user_type', 'all')
    balance_filter = request.GET.get('balance_filter', 'all')
    sort_by = request.GET.get('sort_by', 'balance_desc')
    
    # Base queryset
    wallets_qs = Wallet.objects.select_related('user').filter(user__is_staff=False)
    
    # User type filter
    if user_type == 'manual':
        wallets_qs = wallets_qs.filter(user__is_manual_client=True)
    elif user_type == 'regular':
        wallets_qs = wallets_qs.filter(user__is_manual_client=False)
    
    # Balance filter
    if balance_filter == 'positive':
        wallets_qs = wallets_qs.filter(balance__gt=0)
    elif balance_filter == 'zero':
        wallets_qs = wallets_qs.filter(balance=0)
    elif balance_filter == 'negative':
        wallets_qs = wallets_qs.filter(balance__lt=0)
    
    # Sorting
    if sort_by == 'balance_desc':
        wallets_qs = wallets_qs.order_by('-balance')
    elif sort_by == 'balance_asc':
        wallets_qs = wallets_qs.order_by('balance')
    elif sort_by == 'name':
        wallets_qs = wallets_qs.order_by('user__first_name', 'user__last_name')
    elif sort_by == 'recent':
        wallets_qs = wallets_qs.order_by('-user__date_joined')
    
    # Calculate totals
    total_balance_usd = wallets_qs.aggregate(total=Sum('balance'))['total'] or Decimal('0')
    avg_dollar_rate = wallets_qs.aggregate(avg=Avg('dollar_rate'))['avg'] or Decimal('127.00')
    total_users = wallets_qs.count()
    
    # Add computed fields
    wallets_list = []
    total_balance_bdt = Decimal('0')
    total_active_accounts = 0
    
    for wallet in wallets_qs:
        wallet.balance_bdt = wallet.balance * wallet.dollar_rate
        wallet.active_accounts = AdAccount.objects.filter(user=wallet.user, status='active').count()
        total_balance_bdt += wallet.balance_bdt
        total_active_accounts += wallet.active_accounts
        wallets_list.append(wallet)
    
    # Paginate
    wallets = paginate_data(request, wallets_list, 50)
    
    context = {
        'wallets': wallets,
        'total_users': total_users,
        'total_balance_usd': total_balance_usd,
        'total_balance_bdt': total_balance_bdt,
        'avg_dollar_rate': avg_dollar_rate,
        'total_active_accounts': total_active_accounts,
        'user_type': user_type,
        'balance_filter': balance_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'wallet_balance_report.html', context)



@login_required(login_url='auth')
@require_permission('can_manage_users')
def transfer_ad_account(request):
    """Transfer ad account to another user"""
    
    if request.method == 'POST':
        try:
            ad_account_id = request.POST.get('ad_account_id')
            new_user_id = request.POST.get('new_user_id')
            
            ad_account = get_object_or_404(AdAccount, id=ad_account_id)
            new_user = get_object_or_404(User, id=new_user_id, is_staff=False)
            
            old_user = ad_account.user
            
            # Transfer account
            ad_account.user = new_user
            ad_account.save()
            
            # Log activity
            log_activity(
                performed_by=request.user,
                activity_type='ad_account_activated',
                description=f"Transferred ad account '{ad_account.name}' from {old_user.username} to {new_user.username}",
                target_user=new_user,
                old_value={'user': old_user.username, 'ad_account': ad_account.name},
                new_value={'user': new_user.username, 'ad_account': ad_account.name},
                request=request
            )
            
            messages.success(request, f'Ad account "{ad_account.name}" transferred from {old_user.username} to {new_user.username}!')
            return redirect('admin_dashboard:ad_account_details', ad_account_id=ad_account.id)
            
        except Exception as e:
            messages.error(request, f'Error transferring account: {str(e)}')
            return redirect('admin_dashboard:review_ad_account')
    
    return redirect('admin_dashboard:review_ad_account')


# ── Appearance Views ──

@login_required(login_url='auth')
@require_permission('can_edit_settings')
def appearance(request):

    from .models import SiteSettings, FAQ, Testimonial

    settings = SiteSettings.get()
    faqs = FAQ.objects.all()
    testimonials = Testimonial.objects.all()

    if request.method == 'POST':
        section = request.POST.get('section')

        if section == 'site_settings':
            settings.hero_title_line1 = request.POST.get('hero_title_line1', '').strip()
            settings.hero_title_line2 = request.POST.get('hero_title_line2', '').strip()
            settings.hero_subtitle = request.POST.get('hero_subtitle', '').strip()
            settings.hero_badge_text = request.POST.get('hero_badge_text', '').strip()
            settings.stat_users = request.POST.get('stat_users', '').strip()
            settings.stat_ad_spend = request.POST.get('stat_ad_spend', '').strip()
            settings.about_title = request.POST.get('about_title', '').strip()
            settings.about_body1 = request.POST.get('about_body1', '').strip()
            settings.about_body2 = request.POST.get('about_body2', '').strip()
            settings.about_founded_year = request.POST.get('about_founded_year', '').strip()
            settings.about_stat_clients = request.POST.get('about_stat_clients', '').strip()
            settings.about_stat_spend = request.POST.get('about_stat_spend', '').strip()
            settings.about_stat_uptime = request.POST.get('about_stat_uptime', '').strip()
            settings.whatsapp_number = request.POST.get('whatsapp_number', '').strip()
            settings.email_support = request.POST.get('email_support', '').strip()
            settings.facebook_url = request.POST.get('facebook_url', '').strip()
            settings.telegram_url = request.POST.get('telegram_url', '').strip()
            settings.tiktok_url = request.POST.get('tiktok_url', '').strip()
            settings.instagram_url = request.POST.get('instagram_url', '').strip()
            settings.footer_tagline = request.POST.get('footer_tagline', '').strip()
            
            # Handle logo upload
            if 'logo' in request.FILES:
                settings.logo = request.FILES['logo']
            
            settings.save()
            messages.success(request, 'Site settings updated successfully.')

        elif section == 'add_faq':
            FAQ.objects.create(
                question=request.POST.get('question', '').strip(),
                answer=request.POST.get('answer', '').strip(),
                order=request.POST.get('order', 0),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, 'FAQ added successfully.')

        elif section == 'edit_faq':
            faq = get_object_or_404(FAQ, id=request.POST.get('faq_id'))
            faq.question = request.POST.get('question', '').strip()
            faq.answer = request.POST.get('answer', '').strip()
            faq.order = request.POST.get('order', 0)
            faq.is_active = request.POST.get('is_active') == 'on'
            faq.save()
            messages.success(request, 'FAQ updated successfully.')

        elif section == 'delete_faq':
            FAQ.objects.filter(id=request.POST.get('faq_id')).delete()
            messages.success(request, 'FAQ deleted.')

        elif section == 'add_testimonial':
            Testimonial.objects.create(
                name=request.POST.get('name', '').strip(),
                role=request.POST.get('role', '').strip(),
                avatar_initials=request.POST.get('avatar_initials', '').strip(),
                avatar_color=request.POST.get('avatar_color', '#4f46e5').strip(),
                rating=request.POST.get('rating', 5),
                content=request.POST.get('content', '').strip(),
                order=request.POST.get('order', 0),
                is_active=request.POST.get('is_active') == 'on',
            )
            messages.success(request, 'Testimonial added successfully.')

        elif section == 'edit_testimonial':
            t = get_object_or_404(Testimonial, id=request.POST.get('testimonial_id'))
            t.name = request.POST.get('name', '').strip()
            t.role = request.POST.get('role', '').strip()
            t.avatar_initials = request.POST.get('avatar_initials', '').strip()
            t.avatar_color = request.POST.get('avatar_color', '#4f46e5').strip()
            t.rating = request.POST.get('rating', 5)
            t.content = request.POST.get('content', '').strip()
            t.order = request.POST.get('order', 0)
            t.is_active = request.POST.get('is_active') == 'on'
            t.save()
            messages.success(request, 'Testimonial updated successfully.')

        elif section == 'delete_testimonial':
            Testimonial.objects.filter(id=request.POST.get('testimonial_id')).delete()
            messages.success(request, 'Testimonial deleted.')

        return redirect('admin_dashboard:appearance')

    return render(request, 'appearance.html', {
        'settings': settings,
        'faqs': faqs,
        'testimonials': testimonials,
    })



@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def manage_admin_bm(request):
    """List and manage Admin BM accounts and BM Accounts"""
    
    tab = request.GET.get('tab', 'admin_bm')  # Default to admin_bm tab
    search_query = request.GET.get('search', '')
    
    admin_bms = None
    bm_accounts = None
    
    if tab == 'admin_bm':
        if search_query:
            admin_bms = AdminBM.objects.filter(Q(acc_name__icontains=search_query) | Q(acc_id__icontains=search_query))
        else:
            admin_bms = AdminBM.objects.all()
        admin_bms = paginate_data(request, admin_bms, 20)
    
    elif tab == 'bm_accounts':
        if search_query:
            bm_accounts = BMAccount.objects.filter(Q(acc_name__icontains=search_query) | Q(acc_id__icontains=search_query))
        else:
            bm_accounts = BMAccount.objects.all()
        bm_accounts = paginate_data(request, bm_accounts, 20)
    
    return render(request, 'manage_admin_bm.html', {
        'admin_bms': admin_bms,
        'bm_accounts': bm_accounts,
        'search_query': search_query,
        'tab': tab
    })


@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def add_admin_bm(request):
    """Add new Admin BM account"""
    
    if request.method == 'POST':
        acc_name = request.POST.get('acc_name', '').strip()
        acc_id = request.POST.get('acc_id', '').strip()
        
        if not acc_name or not acc_id:
            messages.error(request, 'All fields are required.')
            return redirect('admin_dashboard:add_admin_bm')
        
        try:
            acc_id = int(acc_id)
            
            if AdminBM.objects.filter(acc_id=acc_id).exists():
                messages.error(request, 'BM Account with this ID already exists.')
                return redirect('admin_dashboard:add_admin_bm')
            
            AdminBM.objects.create(acc_name=acc_name, acc_id=acc_id)
            
            log_activity(
                performed_by=request.user,
                activity_type='admin_bm_created',
                description=f"Created Admin BM Account: {acc_name} ({acc_id})",
                target_user=None,
                old_value=None,
                new_value={'acc_id': acc_id, 'acc_name': acc_name},
                request=request
            )
            
            messages.success(request, 'Admin BM Account created successfully!')
            return redirect('admin_dashboard:manage_admin_bm')
        
        except ValueError:
            messages.error(request, 'Account ID must be a number.')
            return redirect('admin_dashboard:add_admin_bm')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('admin_dashboard:add_admin_bm')
    
    return render(request, 'add_admin_bm.html')


@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def edit_admin_bm(request, admin_bm_id):
    """Edit Admin BM account"""
    
    admin_bm = get_object_or_404(AdminBM, id=admin_bm_id)
    
    if request.method == 'POST':
        acc_name = request.POST.get('acc_name', '').strip()
        acc_id = request.POST.get('acc_id', '').strip()
        
        if not acc_name or not acc_id:
            messages.error(request, 'All fields are required.')
            return redirect('admin_dashboard:edit_admin_bm', admin_bm_id=admin_bm_id)
        
        try:
            acc_id = int(acc_id)
            
            if AdminBM.objects.filter(acc_id=acc_id).exclude(id=admin_bm_id).exists():
                messages.error(request, 'BM Account with this ID already exists.')
                return redirect('admin_dashboard:edit_admin_bm', admin_bm_id=admin_bm_id)
            
            old_values = {'acc_name': admin_bm.acc_name, 'acc_id': admin_bm.acc_id}
            admin_bm.acc_name = acc_name
            admin_bm.acc_id = acc_id
            admin_bm.save()
            
            log_activity(
                performed_by=request.user,
                activity_type='admin_bm_updated',
                description=f"Updated Admin BM Account: {acc_name} ({acc_id})",
                target_user=None,
                old_value=old_values,
                new_value={'acc_id': acc_id, 'acc_name': acc_name},
                request=request
            )
            
            messages.success(request, 'Admin BM Account updated successfully!')
            return redirect('admin_dashboard:manage_admin_bm')
        
        except ValueError:
            messages.error(request, 'Account ID must be a number.')
            return redirect('admin_dashboard:edit_admin_bm', admin_bm_id=admin_bm_id)
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('admin_dashboard:edit_admin_bm', admin_bm_id=admin_bm_id)
    
    return render(request, 'edit_admin_bm.html', {'admin_bm': admin_bm})


@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def delete_admin_bm(request, admin_bm_id):
    """Delete Admin BM account"""
    
    admin_bm = get_object_or_404(AdminBM, id=admin_bm_id)
    
    if request.method == 'POST':
        acc_name = admin_bm.acc_name
        acc_id = admin_bm.acc_id
        admin_bm.delete()
        
        log_activity(
            performed_by=request.user,
            activity_type='admin_bm_deleted',
            description=f"Deleted Admin BM Account: {acc_name} ({acc_id})",
            target_user=None,
            old_value={'acc_id': acc_id, 'acc_name': acc_name},
            new_value=None,
            request=request
        )
        
        messages.success(request, 'Admin BM Account deleted successfully!')
        return redirect('admin_dashboard:manage_admin_bm')
    
    return render(request, 'delete_admin_bm.html', {'admin_bm': admin_bm})


@login_required(login_url='auth')
@require_permission('can_manage_accounts')
def admin_ad_accounts(request):
    """Admin view for all ad accounts"""
    from dashboard.models import AdAccount
    
    # Get search query
    search_query = request.GET.get('search', '').strip()
    
    # Get all ad accounts
    ad_accounts = AdAccount.objects.select_related('user', 'admin_bm').all().order_by('-start_date')
    
    # Apply search filter
    if search_query:
        from django.db.models import Q
        ad_accounts = ad_accounts.filter(
            Q(name__icontains=search_query) |
            Q(acc_id__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(admin_bm__acc_name__icontains=search_query) |
            Q(admin_bm__acc_id__icontains=search_query)
        )
    
    # Paginate
    ad_accounts = paginate_data(request, ad_accounts, 20)
    
    context = {
        'ad_accounts': ad_accounts,
        'search_query': search_query,
    }
    
    return render(request, 'admin_ad_accounts.html', context)
