"""
Force logout view to clear session
Add to urls: path('force-logout/', force_logout_view.force_logout, name='force_logout'),
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.http import HttpResponse

def force_logout(request):
    """Force logout and clear all session data"""
    logout(request)
    request.session.flush()
    return HttpResponse("""
        <html>
        <head>
            <meta http-equiv="refresh" content="2;url=/auth" />
        </head>
        <body style="font-family: Arial; text-align: center; padding: 50px;">
            <h1>✅ Session Cleared!</h1>
            <p>All session data has been cleared.</p>
            <p>Redirecting to login page in 2 seconds...</p>
            <p><a href="/auth">Click here if not redirected</a></p>
        </body>
        </html>
    """)
