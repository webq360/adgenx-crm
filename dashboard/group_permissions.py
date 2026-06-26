"""
DJANGO GROUP-BASED PERMISSION SYSTEM
Using Django's built-in Groups & Permissions (much more reliable!)
No custom UserRole model needed
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


class GroupPermissionManager:
    """Manage permissions using Django's built-in Group system"""
    
    # Permission codenames we'll use
    PERMISSIONS = {
        'can_view_dashboard': 'Can view dashboard',
        'can_manage_users': 'Can manage users',
        'can_review_deposits': 'Can review deposits',
        'can_manage_payments': 'Can manage payments',
        'can_manage_accounts': 'Can manage ad accounts',
        'can_edit_settings': 'Can edit settings',
    }
    
    @staticmethod
    def setup_permissions():
        """
        Create custom permissions on User model
        Run this once: python manage.py setup_group_permissions
        """
        from dashboard.models import User
        content_type = ContentType.objects.get_for_model(User)
        
        created_perms = []
        for codename, name in GroupPermissionManager.PERMISSIONS.items():
            perm, created = Permission.objects.get_or_create(
                codename=codename,
                content_type=content_type,
                defaults={'name': name}
            )
            if created:
                created_perms.append(codename)
        
        return created_perms
    
    @staticmethod
    def create_default_groups():
        """
        Create default groups with permissions
        Run: python manage.py setup_group_permissions
        """
        groups_config = {
            'Manager': [
                'can_view_dashboard',
                'can_manage_users',
                'can_review_deposits',
                'can_manage_payments',
                'can_manage_accounts',
            ],
            'Accountant': [
                'can_view_dashboard',
                'can_review_deposits',
                'can_manage_payments',
            ],
            'Viewer': [
                'can_view_dashboard',
            ],
            'Regular User': [
                'can_view_dashboard',
                'can_manage_payments',
                'can_manage_accounts',
            ],
        }
        
        from dashboard.models import User
        content_type = ContentType.objects.get_for_model(User)
        
        for group_name, perm_codenames in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            # Clear existing permissions
            group.permissions.clear()
            
            # Add permissions
            for codename in perm_codenames:
                try:
                    perm = Permission.objects.get(
                        codename=codename,
                        content_type=content_type
                    )
                    group.permissions.add(perm)
                except Permission.DoesNotExist:
                    pass
            
            print(f"✓ Created/Updated group: {group_name} with {len(perm_codenames)} permissions")
        
        return list(groups_config.keys())
    
    @staticmethod
    def user_has_permission(user, permission_codename):
        """
        Check if user has specific permission
        Works for both staff and group-based permissions
        """
        if not user or not user.is_authenticated:
            return False
        
        # Staff always has all permissions
        if user.is_staff or user.is_superuser:
            return True
        
        # Check if user has permission through groups
        return user.has_perm(f'dashboard.{permission_codename}')
    
    @staticmethod
    def get_user_permissions(user):
        """
        Get all permissions for a user
        Returns dict with permission status
        """
        if not user or not user.is_authenticated:
            return {}
        
        # Staff gets everything
        if user.is_staff or user.is_superuser:
            return {perm: True for perm in GroupPermissionManager.PERMISSIONS.keys()}
        
        # Check each permission
        permissions = {}
        for perm_codename in GroupPermissionManager.PERMISSIONS.keys():
            permissions[perm_codename] = user.has_perm(f'dashboard.{perm_codename}')
        
        return permissions
    
    @staticmethod
    def assign_group_to_user(user, group_name):
        """
        Assign a group to user
        Removes all other groups first
        """
        # Clear existing groups
        user.groups.clear()
        
        # Add new group
        try:
            group = Group.objects.get(name=group_name)
            user.groups.add(group)
            return True
        except Group.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_groups(user):
        """Get list of group names for user"""
        return [g.name for g in user.groups.all()]
    
    @staticmethod
    def get_all_groups():
        """Get all available groups"""
        return Group.objects.all()


def require_group_permission(permission_codename):
    """
    Decorator to check permission using Django Groups
    
    Usage:
        @require_group_permission('can_manage_users')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if GroupPermissionManager.user_has_permission(request.user, permission_codename):
                return view_func(request, *args, **kwargs)
            
            messages.error(
                request,
                f'Access Denied: You do not have the required permission.'
            )
            return redirect('index')
        
        return wrapper
    return decorator


def group_permissions_context(request):
    """
    Context processor for templates
    Provides user_permissions dict
    """
    context = {
        'user_permissions': {},
        'user_groups': [],
    }
    
    if request.user.is_authenticated:
        context['user_permissions'] = GroupPermissionManager.get_user_permissions(request.user)
        context['user_groups'] = GroupPermissionManager.get_user_groups(request.user)
    
    return context
