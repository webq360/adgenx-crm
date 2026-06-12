# Test WSGI for debugging PythonAnywhere issues

import os
import sys
from pathlib import Path

print("=" * 60)
print("WSGI Test - Debugging Information")
print("=" * 60)

# Print Python version
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")

# Print paths
print(f"\nPython Path:")
for p in sys.path:
    print(f"  - {p}")

# Check project paths
project_home = '/home/webq/adgenx-crm/crm'
print(f"\nProject home exists: {os.path.exists(project_home)}")
print(f"Project home: {project_home}")

# Add paths
if project_home not in sys.path:
    sys.path.insert(0, project_home)

parent_home = '/home/webq/adgenx-crm'
if parent_home not in sys.path:
    sys.path.insert(0, parent_home)

# Set Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'

# Try to import Django
print("\n" + "=" * 60)
print("Attempting to import Django...")
print("=" * 60)
try:
    import django
    print(f"✓ Django imported successfully: {django.__version__}")
except Exception as e:
    print(f"✗ Failed to import Django: {e}")
    import traceback
    traceback.print_exc()

# Try to setup Django
print("\nAttempting Django setup...")
try:
    from django.core.wsgi import get_wsgi_application
    print("✓ Django WSGI imported successfully")
    
    application = get_wsgi_application()
    print("✓ WSGI application created successfully")
except Exception as e:
    print(f"✗ Failed to create WSGI application: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("Test complete!")
print("=" * 60)

# Simple test app
def application(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-Type', 'text/plain')]
    start_response(status, response_headers)
    return [b'Hello from Adgenx CRM test WSGI\n']
