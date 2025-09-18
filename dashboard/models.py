from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified = models.BooleanField(default=False)
    pass

class DepositTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    trx_id = models.CharField(max_length=100)
    vendor_trx_id = models.CharField(max_length=100)
    receipt = models.ImageField(upload_to='receipts/', null=True, blank=True)
    bdt_amount = models.DecimalField(max_digits=10, decimal_places=2)
    usd_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    name = models.CharField(max_length=100)
    acc_id = models.CharField(max_length=100)
    acc_link = models.URLField()
    
    start_date = models.DateField()
    monthly_budget = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='inactive')
    bm_accounts = models.ManyToManyField(BMAccount, blank=True)
    admin_bm = models.ForeignKey('AdminBM', on_delete=models.SET_NULL, null=True, blank=True)

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
    method_name = models.CharField(max_length=100)
    method_logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    account_name = models.CharField(max_length=100, null=True, blank=True)
    account_number = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    branch_name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.method_name
