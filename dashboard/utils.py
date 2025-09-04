from django.core.paginator import Paginator
from django.db.models import Sum
from .models import DepositTransaction, AdAccount
from .fb_api_reqs import get_ad_account_info

def paginate_data(request, data, num_per_page):
    paginator = Paginator(data, num_per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

def get_user_utils(user):
    pending_deposits = DepositTransaction.objects.filter(user=user, status='pending').count()
    pending_accounts = AdAccount.objects.filter(user=user, status='inactive').count()
    active_accounts = AdAccount.objects.filter(user=user, status='active').count()
    return {
        'pending_deposits': pending_deposits,
        'pending_accounts': pending_accounts,
        'active_accounts': active_accounts,
    }

def get_processed_ad_accounts_data(ad_accounts_qs):
    ad_accounts_data = []
    for acc in ad_accounts_qs:
        if acc.admin_bm and acc.status == 'active':
            ad_info = get_ad_account_info(acc.acc_id, acc.admin_bm.acc_id)
            if ad_info:
                acc_balance = ad_info.get('balance', 0)
                acc_total_spent = ad_info.get('amount_spent', 0)
                acc_limit = ad_info.get('spend_cap', 0)
            else:
                acc_balance = 'N/A'
                acc_limit = 'N/A'
                acc_total_spent = 'N/A'
        else:
            acc_balance = 'N/A'
            acc_limit = 'N/A'
            acc_total_spent = 'N/A'

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
            'start_date': str(acc.start_date), # Convert date to string
            'monthly_budget': str(acc.monthly_budget), # Convert Decimal to string
            'status': acc.status,
            'balance': acc_balance,
            'limit': acc_limit,
            'total_spent': acc_total_spent,
            'bm_accounts': bm_accounts_list,
        })
    return ad_accounts_data