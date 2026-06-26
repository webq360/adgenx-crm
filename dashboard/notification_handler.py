"""
Comprehensive Notification & Email Handler
Sends notifications to users and emails to admins for all important actions
"""

from django.core.mail import send_mail
from django.conf import settings
from dashboard.models import Notification, User


def send_admin_email(subject, message):
    """Send email to all admin users"""
    try:
        admins = User.objects.filter(is_staff=True, is_active=True)
        admin_emails = [admin.email for admin in admins]
        
        if not admin_emails:
            print(f"⚠️  No admins found for email: {subject}")
            return False
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=admin_emails,
            fail_silently=True,
        )
        print(f"✓ Admin email sent: {subject} to {len(admin_emails)} admins")
        return True
    except Exception as e:
        print(f"✗ Error sending admin email: {e}")
        return False


def send_user_email(user, subject, message):
    """Send email to a specific user"""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        print(f"✓ User email sent to {user.email}: {subject}")
        return True
    except Exception as e:
        print(f"✗ Error sending user email to {user.email}: {e}")
        return False


# ─── DEPOSIT NOTIFICATIONS ────────────────────────────────────────────────────

def notify_deposit_submitted(deposit):
    """User submitted a deposit request"""
    user = deposit.user
    
    # In-app notification for user
    Notification.objects.create(
        user=user,
        notification_type='deposit_pending',
        title='Deposit Request Submitted',
        message=f'Your deposit of ${deposit.usd_amount} (৳{deposit.bdt_amount}) via {deposit.method} has been submitted. Awaiting admin review.'
    )
    
    # Email to user
    user_message = f"""Dear {user.first_name},

Your deposit request has been submitted successfully!

Details:
- Amount: ${deposit.usd_amount} (৳{deposit.bdt_amount})
- Payment Method: {deposit.method}
- Transaction ID: {deposit.trx_id}

Our admin team will review your deposit and update you soon.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Deposit Submitted - Awaiting Review', user_message)
    
    # Email to admins
    admin_message = f"""New Deposit Request!

User: {user.first_name} {user.last_name}
Email: {user.email}

Amount: ${deposit.usd_amount} (৳{deposit.bdt_amount})
Payment Method: {deposit.method}
Transaction ID: {deposit.trx_id}

Please review and approve/reject this deposit in the admin panel.

Adgenx Admin System"""
    
    send_admin_email(f'New Deposit Request: ${deposit.usd_amount} from {user.first_name} {user.last_name}', admin_message)


def notify_deposit_approved(deposit):
    """Admin approved deposit"""
    user = deposit.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='deposit_approved',
        title='Deposit Approved ✓',
        message=f'Your deposit of ${deposit.usd_amount} (৳{deposit.bdt_amount}) has been approved! Wallet balance updated.'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Great news! Your deposit has been approved! 🎉

Details:
- Amount: ${deposit.usd_amount} (৳{deposit.bdt_amount})
- Payment Method: {deposit.method}

Your wallet balance has been updated and you can now use the funds.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Deposit Approved!', message)


def notify_deposit_rejected(deposit, reason=''):
    """Admin rejected deposit"""
    user = deposit.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='deposit_rejected',
        title='Deposit Rejected',
        message=f'Your deposit of ${deposit.usd_amount} (৳{deposit.bdt_amount}) has been rejected. {reason if reason else "Please contact support for details."}'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Unfortunately, your deposit request has been rejected.

Details:
- Amount: ${deposit.usd_amount} (৳{deposit.bdt_amount})
- Payment Method: {deposit.method}
- Reason: {reason if reason else 'Verification failed'}

Please contact our support team for more information.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Deposit Rejected', message)


# ─── TOPUP NOTIFICATIONS ──────────────────────────────────────────────────

def notify_topup_requested(topup):
    """User requested topup decrease (withdrawal)"""
    user = topup.ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='topup_pending',
        title='Top-up Decrease Requested',
        message=f'Your top-up decrease request of ${topup.amount} from {topup.ad_account.name} is under review.'
    )
    
    # Email to admins
    admin_message = f"""New Top-up Decrease Request!

User: {user.first_name} {user.last_name}
Email: {user.email}

Amount: ${topup.amount}
Ad Account: {topup.ad_account.name}

Please review this request in the admin panel.

Adgenx Admin System"""
    
    send_admin_email(f'New Top-up Decrease Request: ${topup.amount} from {user.first_name} {user.last_name}', admin_message)


def notify_topup_approved(topup):
    """Admin approved topup"""
    user = topup.ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='topup_decrease_approved',
        title='Top-up Decrease Approved ✓',
        message=f'Your top-up decrease of ${topup.amount} has been approved. ${topup.amount} returned to wallet.'
    )


# ─── WITHDRAWAL NOTIFICATIONS ─────────────────────────────────────────────────

def notify_withdrawal_requested(withdrawal):
    """User submitted a withdrawal request"""
    user = withdrawal.user
    
    # In-app notification for user
    Notification.objects.create(
        user=user,
        notification_type='withdrawal_pending',
        title='Withdrawal Request Submitted',
        message=f'Your withdrawal request of ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt}) via {withdrawal.payment_method} has been submitted. Awaiting admin review.'
    )
    
    # Email to user
    user_message = f"""Dear {user.first_name},

Your withdrawal request has been submitted successfully!

Details:
- Amount: ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt})
- Payment Method: {withdrawal.payment_method}
- Account Details: {withdrawal.account_details}

Our admin team will review your withdrawal and process it soon. Once approved, the funds will be transferred to your provided account.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Withdrawal Requested - Awaiting Review', user_message)
    
    # Email to admins
    admin_message = f"""New Withdrawal Request!

User: {user.first_name} {user.last_name}
Email: {user.email}

Amount: ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt})
Payment Method: {withdrawal.payment_method}
Account Details: {withdrawal.account_details}

Please review and process this withdrawal in the admin panel.

Adgenx Admin System"""
    
    send_admin_email(f'New Withdrawal Request: ${withdrawal.amount_usd} from {user.first_name} {user.last_name}', admin_message)


def notify_withdrawal_approved(withdrawal):
    """Admin approved withdrawal"""
    user = withdrawal.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='withdrawal_approved',
        title='Withdrawal Approved ✓',
        message=f'Your withdrawal of ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt}) has been approved. Funds will be transferred shortly.'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Great news! Your withdrawal has been approved!

Details:
- Amount: ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt})
- Payment Method: {withdrawal.payment_method}
- Status: Approved

The funds will be transferred to your account soon.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Withdrawal Approved', message)


def notify_withdrawal_rejected(withdrawal):
    """Admin rejected withdrawal"""
    user = withdrawal.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='withdrawal_rejected',
        title='Withdrawal Rejected ✗',
        message=f'Your withdrawal of ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt}) has been rejected. {withdrawal.admin_notes or "Please contact support for details."}'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Unfortunately, your withdrawal request has been rejected.

Details:
- Amount: ${withdrawal.amount_usd} (৳{withdrawal.amount_bdt})
- Payment Method: {withdrawal.payment_method}
- Status: Rejected
- Reason: {withdrawal.admin_notes or "No specific reason provided"}

Please contact our support team for more information.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Withdrawal Rejected', message)



    # Email to user
    message = f"""Dear {user.first_name},

Your top-up decrease request has been approved! 🎉

Details:
- Amount Returned: ${topup.amount}
- Ad Account: {topup.ad_account.name}
- Amount Added to Wallet: ${topup.amount}

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Top-up Decrease Approved!', message)


# ─── AD ACCOUNT NOTIFICATIONS ─────────────────────────────────────────────────

def notify_ad_account_requested(ad_account):
    """User submitted ad account request"""
    user = ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='ad_account_pending',
        title='Ad Account Request Submitted',
        message=f'Your ad account "{ad_account.name}" request has been submitted. Awaiting admin verification.'
    )
    
    # Email to admins
    admin_message = f"""New Ad Account Request!

User: {user.first_name} {user.last_name}
Email: {user.email}

Account Name: {ad_account.name}
Account Link: {ad_account.acc_link}
Monthly Budget: ${ad_account.monthly_budget}

Please review and activate this account in the admin panel.

Adgenx Admin System"""
    
    send_admin_email(f'New Ad Account Request: {ad_account.name} from {user.first_name} {user.last_name}', admin_message)


def notify_ad_account_activated(ad_account):
    """Admin activated ad account"""
    user = ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='ad_account_activated',
        title='Ad Account Activated ✓',
        message=f'Your ad account "{ad_account.name}" has been activated! You can now top-up and run ads.'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Great news! Your ad account has been activated! 🎉

Account Name: {ad_account.name}

You can now:
- Top-up your account
- Run advertisements
- Manage your campaigns

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Ad Account Activated!', message)


def notify_ad_account_deactivated(ad_account, reason=''):
    """Admin deactivated ad account"""
    user = ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='ad_account_deactivated',
        title='Ad Account Deactivated',
        message=f'Your ad account "{ad_account.name}" has been deactivated. {reason if reason else "Please contact support."}'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Your ad account has been deactivated.

Account Name: {ad_account.name}
Reason: {reason if reason else 'Administrative action'}

Please contact our support team for more information.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'Ad Account Deactivated', message)


# ─── BM ACCOUNT NOTIFICATIONS ─────────────────────────────────────────────────

def notify_bm_requested(bm_account, ad_account):
    """User requested BM account"""
    user = ad_account.user
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='bm_pending',
        title='BM Account Request Submitted',
        message=f'Your BM account request for "{ad_account.name}" has been submitted. Awaiting admin review.'
    )
    
    # Email to admins
    admin_message = f"""New BM Account Request!

User: {user.first_name} {user.last_name}
Email: {user.email}

BM Name: {bm_account.acc_name}
BM ID: {bm_account.acc_id}
Ad Account: {ad_account.name}

Please review this request in the admin panel.

Adgenx Admin System"""
    
    send_admin_email(f'New BM Account Request: {bm_account.acc_name} from {user.first_name} {user.last_name}', admin_message)


def notify_bm_approved(bm_account):
    """Admin approved BM account"""
    try:
        ad_account = bm_account.adaccount_set.first()
        if not ad_account:
            return
        user = ad_account.user
    except:
        return
    
    # In-app notification
    Notification.objects.create(
        user=user,
        notification_type='bm_approved',
        title='BM Account Approved ✓',
        message=f'Your BM account "{bm_account.acc_name}" has been approved!'
    )
    
    # Email to user
    message = f"""Dear {user.first_name},

Great news! Your BM account has been approved! 🎉

BM Name: {bm_account.acc_name}
BM ID: {bm_account.acc_id}

You can now use this BM account for your campaigns.

Best regards,
Adgenx Team"""
    
    send_user_email(user, 'BM Account Approved!', message)


# ─── WALLET NOTIFICATIONS ────────────────────────────────────────────────────

def notify_wallet_updated(user, old_balance, new_balance, reason=''):
    """Wallet balance was updated"""
    Notification.objects.create(
        user=user,
        notification_type='wallet_updated',
        title='Wallet Updated',
        message=f'Your wallet balance changed from ${old_balance} to ${new_balance}. {reason}'
    )
