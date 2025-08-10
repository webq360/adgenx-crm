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
    pending_deposits = models.IntegerField(default=0)
    pending_accounts = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s Wallet"


class AdminBM(models.Model):
    bm_id = models.CharField(max_length=100)
    bm_name = models.CharField(max_length=100)

    def __str__(self):
        return self.bm_name

class AdAccount(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    )
    name = models.CharField(max_length=100)
    acc_id = models.CharField(max_length=100)
    acc_link = models.URLField()
    bm_client_id = models.CharField(max_length=100)
    mb_admin_reference = models.ForeignKey(AdminBM, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='inactive')

    def __str__(self):
        return self.name