from django.contrib import admin
from .models import User, DepositTransaction, Wallet, AdAccount, BMAccount, AdminBM, TopupHistory, PaymentMethod

# Register your models here.
admin.site.register(User)
admin.site.register(DepositTransaction)
admin.site.register(Wallet)
admin.site.register(AdAccount)
admin.site.register(BMAccount)
admin.site.register(AdminBM)
admin.site.register(TopupHistory)
admin.site.register(PaymentMethod)