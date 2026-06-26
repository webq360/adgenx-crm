"""
Visual permission test page with better formatting
"""
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from dashboard.permissions import PermissionManager

@login_required
def visual_permission_test(request):
    """Beautiful visual test page for permissions"""
    
    # Get user permissions
    permissions = PermissionManager.get_user_permissions(request.user)
    
    # Load fresh user
    from dashboard.models import User
    try:
        db_user = User.objects.get(pk=request.user.pk)
    except User.DoesNotExist:
        db_user = request.user
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Permission Test - {username}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .header h1 {{
                color: #667eea;
                font-size: 32px;
                margin-bottom: 10px;
            }}
            .user-info {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }}
            .info-box {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 10px;
                border-left: 4px solid #667eea;
            }}
            .info-label {{
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                font-weight: 600;
                margin-bottom: 5px;
            }}
            .info-value {{
                font-size: 18px;
                color: #212529;
                font-weight: 600;
            }}
            .card {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                margin-bottom: 20px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            .card h2 {{
                color: #667eea;
                font-size: 24px;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 3px solid #f1f3f5;
            }}
            .perm-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 15px;
            }}
            .perm-item {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                display: flex;
                align-items: center;
                gap: 15px;
                transition: transform 0.2s, box-shadow 0.2s;
            }}
            .perm-item:hover {{
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }}
            .perm-item.granted {{
                border-left: 5px solid #28a745;
            }}
            .perm-item.denied {{
                border-left: 5px solid #dc3545;
            }}
            .perm-icon {{
                font-size: 32px;
            }}
            .perm-icon.granted {{
                color: #28a745;
            }}
            .perm-icon.denied {{
                color: #dc3545;
            }}
            .perm-details {{
                flex: 1;
            }}
            .perm-name {{
                font-size: 16px;
                font-weight: 600;
                color: #212529;
                margin-bottom: 5px;
            }}
            .perm-desc {{
                font-size: 13px;
                color: #6c757d;
            }}
            .menu-preview {{
                background: #2c3e50;
                color: white;
                border-radius: 10px;
                padding: 20px;
            }}
            .menu-item {{
                padding: 12px 15px;
                margin: 5px 0;
                border-radius: 5px;
                background: rgba(255,255,255,0.1);
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .menu-item.visible {{
                opacity: 1;
                background: rgba(255,255,255,0.15);
            }}
            .menu-item.hidden {{
                opacity: 0.3;
                text-decoration: line-through;
            }}
            .status-badge {{
                display: inline-block;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
            }}
            .badge-granted {{
                background: #28a745;
                color: white;
            }}
            .badge-denied {{
                background: #dc3545;
                color: white;
            }}
            .badge-staff {{
                background: #ffc107;
                color: #212529;
            }}
            .actions {{
                display: flex;
                gap: 10px;
                margin-top: 20px;
            }}
            .btn {{
                padding: 12px 25px;
                border-radius: 8px;
                border: none;
                font-weight: 600;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.2s;
            }}
            .btn-primary {{
                background: #667eea;
                color: white;
            }}
            .btn-primary:hover {{
                background: #5568d3;
                transform: translateY(-1px);
            }}
            .btn-danger {{
                background: #dc3545;
                color: white;
            }}
            .btn-danger:hover {{
                background: #c82333;
            }}
            .section-divider {{
                text-align: center;
                margin: 15px 0;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
                font-weight: 600;
                color: #6c757d;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Permission System Test</h1>
                <p style="color: #6c757d; margin-top: 10px;">Complete role & permission analysis for logged-in user</p>
                
                <div class="user-info">
                    <div class="info-box">
                        <div class="info-label">Username</div>
                        <div class="info-value">{username}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Email</div>
                        <div class="info-value">{email}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">User Type</div>
                        <div class="info-value">{user_type}</div>
                    </div>
                    <div class="info-box">
                        <div class="info-label">Assigned Role</div>
                        <div class="info-value">{role_name}</div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h2>📊 Your Permissions</h2>
                <p style="color: #6c757d; margin-bottom: 20px;">These are the final merged permissions (Base + Role)</p>
                
                <div class="perm-grid">
                    {permission_items}
                </div>
            </div>
            
            <div class="card">
                <h2>📱 Admin Panel Preview</h2>
                <p style="color: #6c757d; margin-bottom: 20px;">What you should see in the sidebar navigation</p>
                
                <div class="menu-preview">
                    <div class="section-divider" style="background: rgba(255,255,255,0.1); color: white;">Regular Menu</div>
                    <div class="menu-item visible">
                        <span>📊</span>
                        <span>Dashboard</span>
                    </div>
                    <div class="menu-item visible">
                        <span>💳</span>
                        <span>Ad Accounts</span>
                    </div>
                    <div class="menu-item visible">
                        <span>💰</span>
                        <span>Deposit</span>
                    </div>
                    
                    {admin_panel_section}
                </div>
            </div>
            
            <div class="actions">
                <a href="/dashboard/" class="btn btn-primary">← Back to Dashboard</a>
                <a href="/force-logout/" class="btn btn-danger">🚪 Force Logout & Clear Session</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Build permission items
    perm_descriptions = {
        'can_view_dashboard': 'Access main dashboard page',
        'can_manage_accounts': 'Manage own ad accounts',
        'can_manage_payments': 'Make deposits & top-ups',
        'can_review_deposits': 'Review & approve user deposits',
        'can_manage_users': 'Manage users & assign roles',
        'can_edit_settings': 'Edit site appearance & settings',
    }
    
    permission_items_html = []
    for perm_name, perm_value in permissions.items():
        status = 'granted' if perm_value else 'denied'
        icon = '✅' if perm_value else '❌'
        desc = perm_descriptions.get(perm_name, 'No description')
        
        permission_items_html.append(f"""
            <div class="perm-item {status}">
                <div class="perm-icon {status}">{icon}</div>
                <div class="perm-details">
                    <div class="perm-name">{perm_name.replace('_', ' ').title()}</div>
                    <div class="perm-desc">{desc}</div>
                </div>
                <span class="status-badge badge-{status}">{status.upper()}</span>
            </div>
        """)
    
    # Build admin panel section
    admin_panel_visible = (
        request.user.is_staff or 
        permissions.get('can_review_deposits', False) or 
        permissions.get('can_manage_users', False) or 
        permissions.get('can_edit_settings', False)
    )
    
    if admin_panel_visible:
        admin_items = []
        admin_items.append('<div class="section-divider" style="background: rgba(255,255,255,0.1); color: white;">✅ Admin Panel (VISIBLE)</div>')
        
        if request.user.is_staff:
            admin_items.append('<div class="menu-item visible"><span>📈</span><span>Overview (Staff Only)</span></div>')
        
        if permissions.get('can_review_deposits'):
            admin_items.append('<div class="menu-item visible"><span>⏰</span><span>Review</span></div>')
        
        if permissions.get('can_manage_users'):
            admin_items.append('<div class="menu-item visible"><span>👥</span><span>Manage Users</span></div>')
            admin_items.append('<div class="menu-item visible"><span>🛡️</span><span>User Roles</span></div>')
        
        if permissions.get('can_manage_payments'):
            admin_items.append('<div class="menu-item visible"><span>💳</span><span>Payment Methods</span></div>')
        
        if permissions.get('can_edit_settings'):
            admin_items.append('<div class="menu-item visible"><span>🎨</span><span>Appearance</span></div>')
        
        admin_panel_section = '\n'.join(admin_items)
    else:
        admin_panel_section = '<div class="section-divider" style="background: rgba(255,255,255,0.1); color: #dc3545;">❌ Admin Panel NOT VISIBLE (no admin permissions)</div>'
    
    # Fill template
    user_type = 'Staff User' if request.user.is_staff else 'Normal User'
    role_name = 'Using Django Groups' if not request.user.is_staff else 'Administrator'
    
    html = html.format(
        username=request.user.username,
        email=request.user.email,
        user_type=user_type,
        role_name=role_name,
        permission_items='\n'.join(permission_items_html),
        admin_panel_section=admin_panel_section,
    )
    
    return HttpResponse(html)
