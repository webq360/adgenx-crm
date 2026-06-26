from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    is_manual_client = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    include_in_profit_reports = models.BooleanField(default=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    # REMOVED: role field - using Django Groups instead
    dollar_rate = models.DecimalField(max_digits=10, decimal_places=2, default=110)

class DepositTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    trx_id = models.CharField(max_length=100, db_index=True)
    vendor_trx_id = models.CharField(max_length=100)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    bdt_amount = models.DecimalField(max_digits=10, decimal_places=2)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.trx_id}"

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    dollar_rate = models.DecimalField(max_digits=10, decimal_places=2, default=127.00)

    def __str__(self):
        return f"{self.user.username}'s Wallet"


class BMAccount(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    )
    REQUEST_TYPE_CHOICES = (
        ('N/A', 'N/A'),
        ('add', 'Add'),
        ('remove', 'Remove'),
    )
    acc_id = models.CharField(max_length=100)
    acc_name = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_type = models.CharField(max_length=10, choices=REQUEST_TYPE_CHOICES, default='N/A')

    def __str__(self):
        return self.acc_name

class AdAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    name = models.CharField(max_length=100, db_index=True)
    acc_id = models.CharField(max_length=100)
    acc_link = models.URLField()
    
    start_date = models.DateField(db_index=True)
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    limit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='inactive', db_index=True)
    bm_accounts = models.ManyToManyField(BMAccount, blank=True)
    admin_bm = models.ForeignKey('AdminBM', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['-start_date']),
        ]

    def __str__(self):
        return self.name

class AdminBM(models.Model):
    acc_name = models.CharField(max_length=100)
    acc_id = models.IntegerField(unique=True)

    def __str__(self):
        return self.acc_name


class TopupHistory(models.Model):
    TOPUP_TYPES = [
        ('increase', 'Increase'),
        ('decrease', 'Decrease'),
    ]
    TOPUP_STATUSES = [
        ('approved', 'Approved'),
        ('pending', 'Pending'),
    ]

    ad_account = models.ForeignKey(AdAccount, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    type = models.CharField(max_length=10, choices=TOPUP_TYPES, default='increase')
    status = models.CharField(max_length=10, choices=TOPUP_STATUSES, default='pending')
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Topup for {self.ad_account.name} - {self.amount} ({self.type})"

class PaymentMethod(models.Model):
    TYPE_CHOICES = (
        ('bank', 'Bank'),
        ('mobile_wallet', 'Mobile Wallet'),
    )
    method_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bank')
    method_name = models.CharField(max_length=100)
    method_logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    account_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.method_name


class ActivityLog(models.Model):
    """Audit trail for all important actions"""
    ACTIVITY_TYPES = [
        ('wallet_edit', 'Wallet Balance Edited'),
        ('rate_change', 'Dollar Rate Changed'),
        ('topup_increase', 'Top-up (Increase)'),
        ('topup_decrease', 'Top-up (Decrease Request)'),
        ('deposit_approved', 'Deposit Approved'),
        ('deposit_rejected', 'Deposit Rejected'),
        ('user_created', 'User Created'),
        ('user_activated', 'User Activated'),
        ('user_deactivated', 'User Deactivated'),
        ('user_deleted', 'User Deleted'),
        ('ad_account_created', 'Ad Account Created'),
        ('ad_account_activated', 'Ad Account Activated'),
        ('ad_account_deactivated', 'Ad Account Deactivated'),
        ('bm_added', 'BM Account Added'),
        ('bm_removed', 'BM Account Removed'),
        ('bm_approved', 'BM Account Approved'),
        ('payment_method_added', 'Payment Method Added'),
        ('payment_method_removed', 'Payment Method Removed'),
    ]
    
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions_performed')
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='actions_received')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES, db_index=True)
    description = models.TextField()
    
    # Store old and new values as JSON for comparison
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Additional context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['activity_type', '-timestamp']),
            models.Index(fields=['performed_by', '-timestamp']),
            models.Index(fields=['target_user', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.activity_type} by {self.performed_by} at {self.timestamp}"


class BusinessExpense(models.Model):
    """Track business expenses for profit calculation"""
    CATEGORY_CHOICES = [
        ('server', 'Server Costs'),
        ('marketing', 'Marketing'),
        ('salary', 'Salaries'),
        ('fb_api', 'Facebook API Costs'),
        ('software', 'Software/Tools'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ]
    
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, db_index=True)
    description = models.TextField()
    amount_bdt = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(db_index=True)
    receipt = models.ImageField(upload_to='expense_receipts/', null=True, blank=True)
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['-date']),
            models.Index(fields=['category', '-date']),
        ]
    
    def __str__(self):
        return f"{self.category} - ${self.amount_usd} on {self.date}"


class WithdrawalRequest(models.Model):
    """User withdrawal requests"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('processed', 'Processed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_usd = models.DecimalField(max_digits=10, decimal_places=2)
    amount_bdt = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=100)
    account_details = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', db_index=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='withdrawals_reviewed')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['status', '-requested_at']),
            models.Index(fields=['user', '-requested_at']),
        ]
    
    def __str__(self):
        return f"Withdrawal ${self.amount_usd} by {self.user.username} - {self.status}"


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('deposit_approved', 'Deposit Approved'),
        ('deposit_rejected', 'Deposit Rejected'),
        ('deposit_pending', 'Deposit Pending'),
        ('topup_approved', 'Topup Approved'),
        ('topup_decrease_approved', 'Topup Decrease Approved'),
        ('topup_pending', 'Topup Pending'),
        ('ad_account_activated', 'Ad Account Activated'),
        ('ad_account_deactivated', 'Ad Account Deactivated'),
        ('ad_account_pending', 'Ad Account Pending'),
        ('bm_approved', 'BM Account Approved'),
        ('bm_removed', 'BM Account Removed'),
        ('bm_pending', 'BM Pending'),
        ('withdrawal_pending', 'Withdrawal Pending'),
        ('withdrawal_approved', 'Withdrawal Approved'),
        ('withdrawal_rejected', 'Withdrawal Rejected'),
        ('wallet_updated', 'Wallet Updated'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='general')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.title}"
