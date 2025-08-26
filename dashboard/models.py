from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    pass

class DepositTransaction(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    method = models.CharField(max_length=100)
    trx_id = models.CharField(max_length=100, unique=True)
    vendor_trx_id = models.CharField(max_length=100, unique=True)
    receipt = models.ImageField(upload_to='receipts/')
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
    acc_id = models.IntegerField()

    def __str__(self):
        return self.acc_name