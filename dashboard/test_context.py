"""
Test view to check user permissions in context
Add this to urls.py temporarily:
path('test-permissions/', test_context.debug_permissions, name='debug_permissions'),
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

@login_required
def debug_permissions(request):
    """Debug view to see what permissions user actually has"""
    
    output = []
    output.append("<h1>Permission Debug Info</h1>")
    output.append("<style>body{font-family:monospace; padding:20px;} .section{margin:20px 0; padding:15px; background:#f5f5f5; border-left:4px solid #333;}</style>")
    
    output.append("<div class='section'>")
    output.append(f"<h2>User Info</h2>")
    output.append(f"<p><strong>Username:</strong> {request.user.username}</p>")
    output.append(f"<p><strong>Email:</strong> {request.user.email}</p>")
    output.append(f"<p><strong>Is Staff:</strong> {request.user.is_staff}</p>")
    output.append(f"<p><strong>Is Active:</strong> {request.user.is_active}</p>")
    output.append("</div>")
    
    output.append("<div class='section'>")
    output.append(f"<h2>Role Info</h2>")
    output.append(f"<p><strong>Has 'role' attribute:</strong> {hasattr(request.user, 'role')}</p>")
    
    if hasattr(request.user, 'role'):
        output.append(f"<p><strong>role is not None:</strong> {request.user.role is not None}</p>")
        
        if request.user.role:
            output.append(f"<p><strong>Role Name:</strong> {request.user.role.get_name_display()}</p>")
            output.append(f"<p><strong>Role ID:</strong> {request.user.role.id}</p>")
            output.append("<h3>Role Permissions:</h3>")
            output.append(f"<p>can_view_dashboard: {request.user.role.can_view_dashboard}</p>")
            output.append(f"<p>can_manage_users: {request.user.role.can_manage_users}</p>")
            output.append(f"<p>can_manage_payments: {request.user.role.can_manage_payments}</p>")
            output.append(f"<p>can_review_deposits: {request.user.role.can_review_deposits}</p>")
            output.append(f"<p>can_manage_accounts: {request.user.role.can_manage_accounts}</p>")
            output.append(f"<p>can_edit_settings: {request.user.role.can_edit_settings}</p>")
        else:
            output.append(f"<p style='color:red;'><strong>NO ROLE ASSIGNED</strong></p>")
    else:
        output.append(f"<p style='color:red;'><strong>User object doesn't have 'role' attribute!</strong></p>")
    
    output.append("</div>")
    
    # Test context processor
    from dashboard.context_processors import user_permissions
    context_data = user_permissions(request)
    
    output.append("<div class='section'>")
    output.append(f"<h2>Context Processor Output</h2>")
    output.append(f"<p><strong>user_permissions keys:</strong> {list(context_data.keys())}</p>")
    
    if 'user_permissions' in context_data:
        output.append("<h3>Merged Permissions (what templates see):</h3>")
        for key, value in context_data['user_permissions'].items():
            color = 'green' if value else 'red'
            output.append(f"<p style='color:{color};'>{key}: {value}</p>")
    
    if 'user_role' in context_data:
        output.append(f"<p><strong>user_role in context:</strong> Yes - {context_data['user_role']}</p>")
    else:
        output.append(f"<p style='color:orange;'><strong>user_role NOT in context</strong></p>")
    
    output.append("</div>")
    
    # Test base permissions
    output.append("<div class='section'>")
    output.append(f"<h2>Base Permissions (for all normal users)</h2>")
    base_permissions = {
        'can_view_dashboard': True,
        'can_manage_accounts': True,
        'can_manage_payments': True,
        'can_review_deposits': False,
        'can_manage_users': False,
        'can_edit_settings': False,
    }
    for key, value in base_permissions.items():
        color = 'green' if value else 'gray'
        output.append(f"<p style='color:{color};'>{key}: {value}</p>")
    output.append("</div>")
    
    return HttpResponse('\n'.join(output))
