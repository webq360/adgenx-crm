from django.core.paginator import Paginator
from django.db.models import Sum
from .models import DepositTransaction, AdAccount, ActivityLog
from .fb_api_reqs import get_ad_account_info
import json

def paginate_data(request, data, num_per_page):
    paginator = Paginator(data, num_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

def get_user_utils(user):
    from .models import WithdrawalRequest
    pending_deposits = DepositTransaction.objects.filter(user=user, status='pending').count()
    pending_accounts = AdAccount.objects.filter(user=user, status='inactive').count()
    active_accounts = AdAccount.objects.filter(user=user, status='active').count()
    pending_withdrawals = WithdrawalRequest.objects.filter(user=user, status='pending').count()
    return {
        'pending_deposits': pending_deposits,
        'pending_accounts': pending_accounts,
        'active_accounts': active_accounts,
        'pending_withdrawals': pending_withdrawals,
    }

def log_activity(performed_by, activity_type, description, target_user=None, old_value=None, new_value=None, request=None):
    """
    Log user activities for audit trail
    
    Args:
        performed_by: User who performed the action
        activity_type: Type of activity (from ActivityLog.ACTIVITY_TYPES)
        description: Human-readable description
        target_user: User affected by the action (optional)
        old_value: Previous value (dict or simple value)
        new_value: New value (dict or simple value)
        request: HTTP request object for IP and user agent (optional)
    """
    try:
        # Get IP address from request
        ip_address = None
        user_agent = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
        
        # Convert values to JSON-serializable format
        if old_value is not None and not isinstance(old_value, dict):
            old_value = {'value': str(old_value)}
        if new_value is not None and not isinstance(new_value, dict):
            new_value = {'value': str(new_value)}
        
        ActivityLog.objects.create(
            performed_by=performed_by,
            target_user=target_user,
            activity_type=activity_type,
            description=description,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent
        )
    except Exception as e:
        # Silently fail to not disrupt main operations
        print(f"Error logging activity: {e}")

def get_processed_ad_accounts_data(ad_accounts_qs):
    ad_accounts_data = []
    for acc in ad_accounts_qs:
        # Update balances from TopupHistory
        from dashboard.models import TopupHistory
        topup_history = TopupHistory.objects.filter(ad_account=acc)
        total_spent = sum(t.amount for t in topup_history if t.type == 'increase')
        total_decreased = sum(t.amount for t in topup_history if t.type == 'decrease')
        
        # Update model fields
        acc.total_spent = total_spent
        acc.remaining_balance = acc.monthly_budget - total_spent + total_decreased
        if acc.limit == 0:
            acc.limit = acc.monthly_budget
        acc.save()
        
        # Get Facebook API data if available (optional, can be removed if not needed)
        if acc.admin_bm and acc.status == 'active':
            ad_info = get_ad_account_info(acc.acc_id, acc.admin_bm.acc_id)
            if ad_info:
                acc_balance = ad_info.get('balance', 0)
                fb_total_spent = ad_info.get('amount_spent', 0)
                fb_limit = ad_info.get('spend_cap', 0)
            else:
                acc_balance = 'N/A'
                fb_limit = 'N/A'
                fb_total_spent = 'N/A'
        else:
            acc_balance = 'N/A'
            fb_limit = 'N/A'
            fb_total_spent = 'N/A'

        bm_accounts_list = []
        for bm in acc.bm_accounts.all():
            bm_accounts_list.append({
                'id': bm.id,
                'acc_name': bm.acc_name,
                'acc_id': bm.acc_id,
                'status': bm.status,
                'request_type': bm.request_type,
            })

        ad_accounts_data.append({
            'id': acc.id,
            'name': acc.name,
            'acc_id': acc.acc_id,
            'acc_link': acc.acc_link,
            'start_date': str(acc.start_date),
            'monthly_budget': str(acc.monthly_budget),
            'remaining_balance': str(acc.remaining_balance),
            'total_spent': str(acc.total_spent),
            'limit': str(acc.limit),
            'status': acc.status,
            'balance': acc_balance,  # Facebook API balance (optional)
            'bm_accounts': bm_accounts_list,
        })
    return ad_accounts_data