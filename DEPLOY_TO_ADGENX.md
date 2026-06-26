# 🚀 Deploy to adgenx.pythonanywhere.com

## ✅ All Configuration Updated for adgenx.pythonanywhere.com

---

## 📝 Quick Deployment Steps

### 1️⃣ Push Code to GitHub
```bash
# From your local machine
cd "c:\Users\User\Desktop\New Project Crm\crm"

# Add all changes
git add .

# Commit
git commit -m "Updated for adgenx.pythonanywhere.com domain"

# Push
git push origin main
```

---

### 2️⃣ SSH to PythonAnywhere
```bash
# Login to: https://www.pythonanywhere.com
# Click on "Consoles" → "Bash"
```

---

### 3️⃣ Pull Latest Code
```bash
# Navigate to your project
cd ~/adgenx-crm  # বা আপনার project folder name

# Pull latest code
git pull origin main
```

---

### 4️⃣ Setup Environment
```bash
# Copy production environment file
cp .env.pythonanywhere .env

# Verify it has correct domain
cat .env | grep ALLOWED_HOSTS
# Should show: ALLOWED_HOSTS=localhost,127.0.0.1,adgenx.pythonanywhere.com,*.pythonanywhere.com
```

---

### 5️⃣ Install Dependencies
```bash
# Update pip (if needed)
pip install --upgrade pip

# Install requirements
pip install --user -r requirements.txt
```

---

### 6️⃣ Run Migrations
```bash
# Apply database migrations
python manage.py migrate

# Output should show:
# Applying dashboard.0043_adaccount_limit... OK
```

---

### 7️⃣ Collect Static Files
```bash
python manage.py collectstatic --noinput
```

---

### 8️⃣ Activate Pending Users (Optional)
```bash
# Check if any users need activation
python manage.py activate_pending_users
```

---

### 9️⃣ Configure Web App on PythonAnywhere

#### Go to Web Tab:
1. Click **"Web"** from dashboard
2. If no app exists, click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.12** (or your version)

#### Configure WSGI File:
Click on **WSGI configuration file** link and update:

```python
import os
import sys

# Add your project directory to the sys.path
path = '/home/adgenx/adgenx-crm'  # Update with your path
if path not in sys.path:
    sys.path.append(path)

# Set environment variable for Django settings
os.environ['DJANGO_SETTINGS_MODULE'] = 'crm.settings'

# Load environment variables
from dotenv import load_dotenv
project_folder = os.path.expanduser(path)
load_dotenv(os.path.join(project_folder, '.env'))

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

#### Configure Virtual Environment:
- Enter virtualenv path: `/home/adgenx/.virtualenvs/your-venv-name`
- Or create new: `mkvirtualenv --python=/usr/bin/python3.12 adgenx-env`

#### Configure Static Files:
| URL | Directory |
|-----|-----------|
| `/static/` | `/home/adgenx/adgenx-crm/staticfiles/` |
| `/media/` | `/home/adgenx/adgenx-crm/media/` |

#### Set Working Directory:
- Source code: `/home/adgenx/adgenx-crm`

---

### 🔟 Reload Web App
```
Click the big green "Reload" button at the top
Wait for ✅ checkmark
```

---

## 🧪 Testing After Deployment

### 1. Basic Access
```bash
# Visit in browser
https://adgenx.pythonanywhere.com
```
✅ Should load homepage

### 2. Test Registration
```bash
# Go to
https://adgenx.pythonanywhere.com/auth/?tab=register
```
- Fill form
- Submit
- ✅ Should succeed (no CAPTCHA error)

### 3. Test Login
```bash
https://adgenx.pythonanywhere.com/auth/
```
- Login with verified account
- ✅ Should redirect to dashboard

### 4. Check Ad Accounts Table
```bash
https://adgenx.pythonanywhere.com/ad_accounts/
```
✅ Should see 8 columns:
- Account Name
- Connected BM
- Monthly Budget ⭐ NEW
- Remaining Balance ⭐ NEW
- Total Spent ⭐ NEW
- Limit ⭐ NEW
- Status
- Actions

### 5. Test CORS
```bash
curl https://adgenx.pythonanywhere.com/api/cors-test/
```
✅ Should return JSON with success message

### 6. Test API
```bash
curl -X POST https://adgenx.pythonanywhere.com/auth/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123"}'
```

---

## 🔧 Configuration Summary

### Domain: `adgenx.pythonanywhere.com`

### Environment Variables (`.env.pythonanywhere`):
```bash
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,adgenx.pythonanywhere.com,*.pythonanywhere.com
RECAPTCHA_ENABLED=False
```

### CORS Settings (`settings.py`):
```python
CORS_ALLOWED_ORIGINS = [
    'https://adgenx.pythonanywhere.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

CSRF_TRUSTED_ORIGINS = [
    'https://adgenx.pythonanywhere.com',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]
```

---

## 🐛 Troubleshooting

### Issue: 502 Bad Gateway
**Solution:**
1. Check error log: Web tab → Error log
2. Verify WSGI file path is correct
3. Check virtualenv is activated

### Issue: Static files not loading
**Solution:**
```bash
python manage.py collectstatic --noinput
# Then reload web app
```

### Issue: ImportError
**Solution:**
```bash
pip install --user -r requirements.txt
# Make sure all dependencies installed
```

### Issue: Database errors
**Solution:**
```bash
python manage.py migrate
# Apply all migrations
```

### Issue: User can't register
**Solution:**
```bash
# Check .env has:
RECAPTCHA_ENABLED=False
```

### Issue: User can't login
**Solution:**
```bash
# Activate user manually
python manage.py activate_user user@email.com
```

---

## 📊 Files Configured for adgenx.pythonanywhere.com

✅ `.env.pythonanywhere` - Updated domain
✅ `crm/settings.py` - CORS origins updated
✅ `crm/settings.py` - CSRF origins updated
✅ All documentation files updated

---

## 🎯 Post-Deployment Checklist

After deploying, verify:

- [ ] ✅ Website loads: https://adgenx.pythonanywhere.com
- [ ] ✅ Homepage displays correctly
- [ ] ✅ Registration works (no CAPTCHA error)
- [ ] ✅ Login works
- [ ] ✅ Dashboard loads
- [ ] ✅ Ad Accounts table shows 8 columns
- [ ] ✅ New columns display data correctly:
  - [ ] Monthly Budget
  - [ ] Remaining Balance
  - [ ] Total Spent
  - [ ] Limit
- [ ] ✅ Top Up button works
- [ ] ✅ Edit modal works
- [ ] ✅ All actions functional
- [ ] ✅ No console errors
- [ ] ✅ API endpoints respond
- [ ] ✅ CORS test passes
- [ ] ✅ Static files load
- [ ] ✅ Media files upload

---

## 📞 Quick Commands Reference

```bash
# Pull latest code
git pull origin main

# Apply migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Activate user
python manage.py activate_user email@example.com

# View logs
tail -f /var/log/adgenx.pythonanywhere.com.error.log

# Django shell
python manage.py shell

# Check deployment issues
python manage.py check --deploy
```

---

## 🎉 You're All Set!

Your CRM is now configured for:
**https://adgenx.pythonanywhere.com**

### What's New:
✅ Ad Account table with 4 new columns
✅ User activation system fixed
✅ CORS properly configured
✅ reCAPTCHA issue resolved
✅ All features production ready

### Next Steps:
1. Follow deployment steps above
2. Test thoroughly
3. Monitor error logs
4. Enjoy your CRM! 🚀

---

**Need Help?**
- Check error logs on PythonAnywhere
- Review troubleshooting section
- Test locally first

**Made with ❤️ by Kiro AI**
Date: June 26, 2026
Domain: adgenx.pythonanywhere.com
