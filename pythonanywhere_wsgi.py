# +++++++++++ DJANGO ++++++++++++ 
# PythonAnywhere WSGI configuration for Adgenx CRM

import os
import sys
from pathlib import Path

# Add the project directory to the Python path
project_home = '/home/webq/adgenx-crm/crm'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Add parent directory too
parent_home = '/home/webq/adgenx-crm'
if parent_home not in sys.path:
    sys.path.insert(0, parent_home)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'

# Load environment variables from .env file if it exists
env_file = '/home/webq/adgenx-crm/crm/.env'
if os.path.exists(env_file):
    from dotenv import load_dotenv
    load_dotenv(env_file)

# Set default environment variables for PythonAnywhere
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'django-insecure-r0@81a_=&zh4(4ikf@d)eq)!i(1e842zd0sru+@4l#01pq(edc'

if not os.environ.get('DEBUG'):
    os.environ['DEBUG'] = 'False'

if not os.environ.get('ALLOWED_HOSTS'):
    os.environ['ALLOWED_HOSTS'] = 'webq.pythonanywhere.com,*.pythonanywhere.com'

# Get the WSGI application
try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as e:
    # Log the error for debugging
    import traceback
    print(f"Error loading WSGI application: {e}")
    traceback.print_exc()
    raise
