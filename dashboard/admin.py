from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import User, DepositTransaction, Wallet, AdAccount, BMAccount, AdminBM, TopupHistory, PaymentMethod


# Custom User Admin with Group management
class CustomUserAdmin(BaseUserAdmin):
    """Enhanced User admin with group-based permissions"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'groups_display', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'phone_number')}),
        ('Permissions & Groups', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': '<strong>How to assign permissions:</strong><br>'
                          '1. Add user to one or more Groups (Manager, Accountant, etc.)<br>'
                          '2. Groups automatically grant permissions<br>'
                          '3. User permissions are for additional custom access'
        }),
        ('CRM Settings', {'fields': ('is_verified', 'is_manual_client', 'dollar_rate', 'include_in_profit_reports', 'notes', 'created_by')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'groups'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions')
    
    def groups_display(self, obj):
        """Display user's groups as badges"""
        groups = obj.groups.all()
        if not groups:
            return mark_safe('<span style="color: gray;">No groups</span>')
        
        badges = []
        for group in groups:
            badges.append(
                '<span style="background-color: #667eea; color: white; '
                'padding: 2px 8px; border-radius: 3px; margin-right: 3px; '
                'font-size: 11px; font-weight: bold;">{}</span>'.format(group.name)
            )
        return mark_safe(''.join(badges))
    
    groups_display.short_description = 'Groups (Roles)'


# Unregister if already registered, then register with custom admin
admin.site.unregister(User) if admin.site.is_registered(User) else None
admin.site.register(User, CustomUserAdmin)


# Make Group admin better
class CustomGroupAdmin(admin.ModelAdmin):
    """Enhanced Group admin for role management"""
    list_display = ('name', 'permissions_count', 'users_count')
    search_fields = ('name',)
    filter_horizontal = ('permissions',)
    
    fieldsets = (
        (None, {
            'fields': ('name',),
            'description': '<strong>Groups work as Roles</strong><br>'
                          'Create groups like "Manager", "Accountant", "Viewer"<br>'
                          'Assign permissions to the group<br>'
                          'Add users to the group to grant those permissions'
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'description': 'Select all permissions this role/group should have'
        }),
    )
    
    def permissions_count(self, obj):
        count = obj.permissions.count()
        return format_html(
            '<span style="background-color: #28a745; color: white; '
            'padding: 2px 8px; border-radius: 3px;">{} permissions</span>',
            count
        )
    permissions_count.short_description = 'Permissions'
    
    def users_count(self, obj):
        count = obj.user_set.count()
        return format_html(
            '<span style="background-color: #17a2b8; color: white; '
            'padding: 2px 8px; border-radius: 3px;">{} users</span>',
            count
        )
    users_count.short_description = 'Users'


# Unregister default Group admin and register custom one
admin.site.unregister(Group)
admin.site.register(Group, CustomGroupAdmin)


# Register other models
admin.site.register(DepositTransaction)
admin.site.register(Wallet)
admin.site.register(TopupHistory)
admin.site.register(PaymentMethod)


class BMAccountAdmin(admin.ModelAdmin):
    list_display = ('acc_name', 'acc_id', 'status_badge', 'request_type', 'actions_display')
    list_filter = ('status', 'request_type')
    search_fields = ('acc_name', 'acc_id')
    readonly_fields = ('acc_id',)
    fieldsets = (
        ('Account Information', {
            'fields': ('acc_name', 'acc_id')
        }),
        ('Status & Type', {
            'fields': ('status', 'request_type')
        }),
    )
    
    def status_badge(self, obj):
        """Display status as colored badge"""
        colors = {
            'pending': '#ffc107',
            'approved': '#28a745',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def actions_display(self, obj):
        """Display action buttons"""
        return format_html(
            '<a class="button" href="/admin/dashboard/bmaccount/{}/change/">Edit</a>&nbsp;'
            '<a class="button" href="/admin/dashboard/bmaccount/{}/delete/">Delete</a>',
            obj.id, obj.id
        )
    actions_display.short_description = 'Actions'


admin.site.register(BMAccount, BMAccountAdmin)


class AdminBMAdmin(admin.ModelAdmin):
    list_display = ('acc_name', 'acc_id', 'connected_accounts_count', 'actions_display')
    list_filter = ('acc_id',)
    search_fields = ('acc_name', 'acc_id')
    readonly_fields = ('connected_accounts_count', 'connected_accounts_list')
    fieldsets = (
        ('Basic Information', {
            'fields': ('acc_name', 'acc_id')
        }),
        ('Connections', {
            'fields': ('connected_accounts_count', 'connected_accounts_list'),
            'classes': ('collapse',)
        }),
    )
    
    def connected_accounts_count(self, obj):
        """Display count of connected ad accounts"""
        count = obj.adaccount_set.count()
        return format_html(
            '<span style="background-color: #dfe; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} account(s)</span>',
            count
        )
    connected_accounts_count.short_description = 'Connected Ad Accounts'
    
    def connected_accounts_list(self, obj):
        """Display list of connected ad accounts"""
        accounts = obj.adaccount_set.all()
        if not accounts:
            return "No connected ad accounts"
        
        html = '<ul style="margin: 0; padding-left: 20px;">'
        for account in accounts:
            status_color = 'green' if account.status == 'active' else 'orange'
            html += f'<li>{account.name} ({account.acc_id}) - <span style="color: {status_color};">{account.status}</span></li>'
        html += '</ul>'
        return mark_safe(html)
    connected_accounts_list.short_description = 'Connected Ad Accounts'
    
    def actions_display(self, obj):
        """Display action buttons in list view"""
        return format_html(
            '<a class="button" href="/admin/dashboard/adminbm/{}/change/">Edit</a>&nbsp;'
            '<a class="button" href="/admin/dashboard/adminbm/{}/delete/">Delete</a>',
            obj.id, obj.id
        )
    actions_display.short_description = 'Actions'
    
    def has_add_permission(self, request):
        """Allow admins to add new BM accounts"""
        return request.user.is_superuser or request.user.is_staff
    
    def has_change_permission(self, request, obj=None):
        """Allow admins to edit BM accounts"""
        return request.user.is_superuser or request.user.is_staff
    
    def has_delete_permission(self, request, obj=None):
        """Allow admins to delete BM accounts"""
        return request.user.is_superuser


admin.site.register(AdminBM, AdminBMAdmin)


class AdAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'acc_id', 'user', 'status', 'start_date')
    list_filter = ('status', 'start_date')
    search_fields = ('name', 'acc_id', 'user__email')
    readonly_fields = ('start_date',)
    fieldsets = (
        ('Account Information', {
            'fields': ('user', 'name', 'acc_id', 'acc_link')
        }),
        ('Budget & Status', {
            'fields': ('monthly_budget', 'status', 'start_date')
        }),
        ('Connections', {
            'fields': ('bm_accounts', 'admin_bm')
        }),
    )
    filter_horizontal = ('bm_accounts',)

    def save_model(self, request, obj, form, change):
        if not change:  # New object
            from django.utils import timezone
            obj.start_date = timezone.now().date()
        super().save_model(request, obj, form, change)


admin.site.register(AdAccount, AdAccountAdmin)