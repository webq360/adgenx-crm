from django.contrib import admin
from .models import User, DepositTransaction, Wallet, AdAccount, AdminBM

# Register your models here.
admin.site.register(User)
admin.site.register(DepositTransaction)
admin.site.register(Wallet)
admin.site.register(AdAccount)
admin.site.register(AdminBM)