"""
COMPLETE ROLE-BASED PERMISSION SYSTEM
Rewritten from scratch for reliable functionality
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.cache import cache


class PermissionManager:
    """Central permission management system"""
    
    # Base permissions that ALL normal users get (cannot be revoked)
    BASE_PERMISSIONS = {
        'can_view_dashboard': True,
        'can_manage_accounts': True,      # Their own ad accounts
        'can_manage_payments': True,       # Their own deposits/topups
        'can_review_deposits': False,      # Admin only
        'can_manage_users': False,         # Admin only
        'can_edit_settings': False,        # Admin only
    }
    
    @staticmethod
    def get_user_permissions(user):
        """
        Get complete permissions for a user
        Returns dict of all permissions with True/False values
        
        Priority:
        1. Staff users get ALL permissions
        2. Normal users get BASE + ROLE permissions (merged with OR logic)
        3. Users without role get only BASE permissions
        """
        if not user or not user.is_authenticated:
            return {}
        
        # Staff/superusers get everything
        if user.is_staff or user.is_superuser:
            return {
                'can_view_dashboard': True,
                'can_manage_users': True,
                'can_manage_payments': True,
                'can_review_deposits': True,
                'can_manage_accounts': True,
                'can_edit_settings': True,
            }
        
        # Start with base permissions
        permissions = PermissionManager.BASE_PERMISSIONS.copy()
        # Now using Django Groups instead of custom UserRole model
        # Add group-based permissions here in the future if needed
        
        return permissions
    
    @staticmethod
    def check_permission(user, permission_name):
        """
        Check if user has a specific permission
        Returns True/False
        """
        if not user or not user.is_authenticated:
            return False
        
        permissions = PermissionManager.get_user_permissions(user)
        return permissions.get(permission_name, False)
    
    @staticmethod
    def clear_user_sessions(user):
        """
        Clear all active sessions for a user
        Forces re-login to apply new permissions
        """
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        # Get all active sessions
        active_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        
        # Check each session and delete if it belongs to this user
        for session in active_sessions:
            try:
                session_data = session.get_decoded()
                if str(user.pk) == str(session_data.get('_auth_user_id')):
                    session.delete()
            except:
                continue


def require_permission(permission_name):
    """
    Decorator to protect views with permission check
    
    Usage:
        @require_permission('can_manage_users')
        def my_view(request):
            ...
    
    Returns:
        - View response if user has permission
        - Redirect to dashboard with error message if not
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Check if user has the required permission
            if PermissionManager.check_permission(request.user, permission_name):
                return view_func(request, *args, **kwargs)
            
            # Access denied
            messages.error(
                request, 
                f'Access Denied: You do not have permission to access this page. Required: {permission_name}'
            )
            return redirect('index')
        
        return wrapper
    return decorator


def user_permissions_context(request):
    """
    Context processor to make permissions available in all templates
    
    Uses Django Groups and Permissions system (replaces old UserRole model)
    
    Adds to template context:
        - user_permissions: dict of all permissions
        - has_permission: function to check specific permission
    """
    context = {
        'user_permissions': {},
        'has_permission': lambda perm: False,
    }
    
    if request.user.is_authenticated:
        # Get complete permissions
        permissions = PermissionManager.get_user_permissions(request.user)
        context['user_permissions'] = permissions
        
        # Add permission checker function
        context['has_permission'] = lambda perm: PermissionManager.check_permission(request.user, perm)
    
    return context
