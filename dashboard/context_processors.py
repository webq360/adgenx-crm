"""
Context processors for role-based access control using Django Groups
These make user permissions available to all templates
"""

def user_permissions(request):
    """
    Add user permissions to template context using Django Groups and Permissions.
    This replaces the old custom UserRole system.
    Available in templates as:
    - user_has_permission (function to check permission)
    - user_groups (user's assigned groups)
    """
    # Base permissions for all normal users (always available)
    base_permissions = {
        'can_view_dashboard': True,
        'can_manage_accounts': True,
        'can_manage_payments': True,
        'can_review_deposits': False,
        'can_manage_users': False,
        'can_edit_settings': False,
    }
    
    context = {
        'user_has_permission': has_permission,
        'user_permissions': base_permissions,  # Default to base permissions
    }
    
    # If user is authenticated, calculate merged permissions
    if request.user.is_authenticated:
        # Staff users get all permissions
        if request.user.is_staff:
            context['user_permissions'] = {
                'can_view_dashboard': True,
                'can_manage_users': True,
                'can_manage_payments': True,
                'can_review_deposits': True,
                'can_manage_accounts': True,
                'can_edit_settings': True,
            }
        # Normal users get base permissions (now using Django Groups instead of custom UserRole)
        else:
            context['user_permissions'] = base_permissions
    
    return context


def has_permission(user, permission_name):
    """
    Check if user has a specific permission
    Usage in template: {% if user_has_permission(request.user, 'can_manage_users') %}
    """
    # Staff users have all permissions
    if user.is_staff:
        return True
    
    # Base permissions for all normal users
    base_permissions = {
        'can_view_dashboard': True,
        'can_manage_accounts': True,
        'can_manage_payments': True,
        'can_review_deposits': False,
        'can_manage_users': False,
        'can_edit_settings': False,
    }
    
    # Check base permission
    return base_permissions.get(permission_name, False)
