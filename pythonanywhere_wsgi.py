# +++++++++++ DJANGO ++++++++++++ 
# PythonAnywhere WSGI configuration for Adgenx CRM

import os
import sys

# Add the project directory to the Python path
# Assuming the project is at /home/webq/crm
project_home = '/home/webq/crm'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'

# Get the WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
