# Adgenx CRM - PythonAnywhere Deployment Guide

## Step-by-Step Setup Instructions

### 1. Create PythonAnywhere Account
- Go to https://www.pythonanywhere.com
- Sign up for a free or paid account
- Your site will be at: `https://webq.pythonanywhere.com` (replace `webq` with your username)

### 2. Upload Project Files

#### Option A: Using Git
```bash
# In PythonAnywhere Bash Console:
cd ~
git clone https://github.com/webq360/adgenx-crm.git
cd adgenx-crm/crm
```

#### Option B: Upload via Web Interface
- Use PythonAnywhere file manager to upload the project

### 3. Set Up Virtual Environment

```bash
# Create virtual environment
mkvirtualenv --python=/usr/bin/python3.12 mysite
pip install -r requirements.txt
```

### 4. Create Web App

1. Go to "Web" tab in PythonAnywhere
2. Click "Add a new web app"
3. Choose "Manual configuration"
4. Select Python 3.12
5. Click "Next"

### 5. Configure WSGI File

1. Go to "Web" → "Web app configuration"
2. Find the WSGI configuration file section
3. Edit the WSGI file at:
   `/var/www/webq_pythonanywhere_com_wsgi.py`

Replace the content with:

```python
import os
import sys

# Add your project to path
project_home = '/home/webq/adgenx-crm/crm'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'

# Activate virtual environment
activate_this = '/home/webq/.virtualenvs/mysite/bin/activate_this.py'
exec(open(activate_this).read())

# Load Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 6. Configure Environment Variables

In PythonAnywhere Web app settings, scroll down to "Environment variables" and add:

```
DJANGO_SETTINGS_MODULE=crm.settings
SECRET_KEY=django-insecure-r0@81a_=&zh4(4ikf@d)eq)!i(1e842zd0sru+@4l#01pq(edc
DEBUG=False
ALLOWED_HOSTS=webq.pythonanywhere.com,www.webq.pythonanywhere.com
```

### 7. Set Up Database

```bash
# In PythonAnywhere console:
cd /home/webq/adgenx-crm/crm
python manage.py migrate
python manage.py collectstatic --noinput
```

### 8. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 9. Configure Static/Media Files

In PythonAnywhere Web app settings:

**Static files:**
- URL: `/static/`
- Directory: `/home/webq/adgenx-crm/crm/staticfiles/`

**Media files:**
- URL: `/media/`
- Directory: `/home/webq/adgenx-crm/crm/media/`

### 10. Reload Web App

1. Click "Reload" button in Web app configuration
2. Visit https://webq.pythonanywhere.com

## Important Notes

- Replace `/home/webq/` with your PythonAnywhere username path
- Replace `webq` with your PythonAnywhere username
- Update `ALLOWED_HOSTS` in settings.py or environment variables
- For production, ensure `DEBUG=False`
- Keep your secret key safe

## Troubleshooting

### Import errors
- Make sure virtual environment is activated
- Check if all packages are installed: `pip list`

### Static files not loading
- Run: `python manage.py collectstatic --noinput`
- Check permissions: file should be readable

### Database errors
- Check if migrations are applied: `python manage.py migrate`
- Ensure db.sqlite3 has proper permissions

### 403/404 errors
- Check ALLOWED_HOSTS configuration
- Verify URL paths in api/urls.py

## API Endpoints

- **Login:** `POST /auth/api/login/`
- **Register:** `POST /auth/api/register/`
- **Dashboard:** `GET /api/dashboard/`
- **Notifications:** `GET /api/notifications/`
- **Profile:** `GET/PATCH /api/profile/`

## Flutter App Configuration

Update `lib/core/constants/app_constants.dart`:

```dart
static const String baseUrl = 'https://webq.pythonanywhere.com';
```

Then rebuild and deploy your Flutter app.

---

For more help, visit: https://help.pythonanywhere.com/pages/Django
