# 🚀 Production Deployment Guide

## ✅ Recent Changes Summary

### 1. **Ad Account Table Enhancements**
- ✅ Added 4 new columns: Monthly Budget, Remaining Balance, Total Spent, Limit
- ✅ Updated both `/dashboard/` and `/ad_accounts/` pages
- ✅ Functional balance tracking with TopupHistory
- ✅ Auto-calculation on page load

### 2. **User Activation Fix**
- ✅ Email verification now activates users automatically
- ✅ Better error messages for inactive accounts
- ✅ Management commands for manual activation:
  - `python manage.py activate_user email@example.com`
  - `python manage.py activate_pending_users`

### 3. **CORS Configuration**
- ✅ Added proper CORS for `https://adgenx.pythonanywhere.com`
- ✅ CSRF trusted origins configured
- ✅ Removed insecure `CORS_ALLOW_ALL_ORIGINS`
- ✅ Test endpoint: `/api/cors-test/`

### 4. **reCAPTCHA Fix**
- ✅ Made reCAPTCHA optional via environment variable
- ✅ Better error handling for network issues
- ✅ Graceful fallback when Google API unreachable
- ✅ Disabled for PythonAnywhere (`.env.pythonanywhere`)

---

## 📋 Pre-Deployment Checklist

### 1. **Database Migration**
```bash
python manage.py makemigrations
python manage.py migrate
```

### 2. **Static Files**
```bash
python manage.py collectstatic --noinput
```

### 3. **Environment Variables**
Make sure `.env.pythonanywhere` has:
```bash
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,webq.pythonanywhere.com,*.pythonanywhere.com
RECAPTCHA_ENABLED=False
```

### 4. **Test Locally**
```bash
python manage.py runserver
# Visit: http://127.0.0.1:8000
# Test: Login, Registration, Ad Accounts table
```

---

## 🔧 PythonAnywhere Deployment Steps

### Step 1: Upload Code
```bash
# On your local machine
git add .
git commit -m "Production ready: Ad Account enhancements, User activation, CORS, reCAPTCHA fixes"
git push origin main
```

### Step 2: Pull on PythonAnywhere
```bash
# SSH to PythonAnywhere
cd ~/your-project-folder
git pull origin main
```

### Step 3: Update Environment
```bash
# Copy production environment file
cp .env.pythonanywhere .env

# Or manually edit .env to ensure:
# RECAPTCHA_ENABLED=False
```

### Step 4: Install Dependencies (if any new)
```bash
pip install --user -r requirements.txt
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

### Step 7: Activate Pending Users
```bash
# Check if any users need activation
python manage.py activate_pending_users
```

### Step 8: Reload Web App
- Go to PythonAnywhere dashboard
- Click "Web" tab
- Click "Reload" button
- Wait for green "✓" confirmation

---

## 🧪 Post-Deployment Testing

### 1. **Basic Access**
- ✅ Visit: `https://adgenx.pythonanywhere.com`
- ✅ Should load without errors

### 2. **User Registration**
- ✅ Go to registration page
- ✅ Fill form and submit
- ✅ Should succeed without CAPTCHA error
- ✅ Check email for verification link

### 3. **User Login**
- ✅ Try logging in with test account
- ✅ Should redirect to dashboard

### 4. **Ad Accounts Table**
- ✅ Go to Ad Accounts page
- ✅ Check new columns are visible:
  - Monthly Budget
  - Remaining Balance  
  - Total Spent
  - Limit
- ✅ Check Action buttons work (Top Up, More dropdown)

### 5. **CORS Test**
- ✅ Visit: `https://adgenx.pythonanywhere.com/api/cors-test/`
- ✅ Should return JSON with success message

### 6. **API Endpoints**
```bash
# Test API login
curl -X POST https://adgenx.pythonanywhere.com/auth/api/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password"}'
```

---

## 🐛 Troubleshooting

### Issue: "500 Internal Server Error"
**Solution:**
1. Check error log in PythonAnywhere
2. Go to Web tab → Error log
3. Look for Python traceback

### Issue: "Static files not loading"
**Solution:**
```bash
python manage.py collectstatic --noinput
```
Then reload web app

### Issue: "CAPTCHA verification failed"
**Solution:**
```bash
# Make sure in .env:
RECAPTCHA_ENABLED=False
```

### Issue: "User can't login"
**Solution:**
```bash
# Activate the user
python manage.py activate_user user@example.com
```

### Issue: "CORS errors in browser console"
**Solution:**
- Check `settings.py` has:
```python
CORS_ALLOWED_ORIGINS = [
    'https://adgenx.pythonanywhere.com',
]
```

### Issue: "Database migration errors"
**Solution:**
```bash
# Check migration status
python manage.py showmigrations

# If needed, fake migrate
python manage.py migrate --fake-initial
```

---

## 📊 Database Changes

### New Migrations:
- `dashboard.0043_adaccount_limit_adaccount_remaining_balance_and_more.py`
  - Adds `limit` field to AdAccount
  - Adds `remaining_balance` field to AdAccount
  - Adds `total_spent` field to AdAccount

### Data Migration:
- Existing AdAccounts will have default values (0.00)
- Values will be calculated on first page load

---

## 🔒 Security Notes

### Production Settings (Already Configured):
- ✅ `DEBUG=False` in production
- ✅ `ALLOWED_HOSTS` properly set
- ✅ `SESSION_COOKIE_SECURE=True`
- ✅ `CSRF_COOKIE_SECURE=True`
- ✅ CORS restricted to specific domain
- ✅ CSRF protection enabled

### reCAPTCHA Disabled:
- Email verification still required
- Admin activation still required
- User must verify email to activate

---

## 📝 Quick Command Reference

```bash
# Activate all pending users
python manage.py activate_pending_users

# Activate specific user
python manage.py activate_user email@example.com

# Check deployment issues
python manage.py check --deploy

# Create admin user (if needed)
python manage.py createsuperuser

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic

# Test CORS
curl https://webq.pythonanywhere.com/api/cors-test/
```

---

## 🎉 Expected Results After Deployment

### User Experience:
1. ✅ Registration works without CAPTCHA errors
2. ✅ Email verification activates account
3. ✅ Login works for verified users
4. ✅ Dashboard shows enhanced Ad Accounts table
5. ✅ All new columns display correctly
6. ✅ Top Up and actions work properly

### Admin Experience:
1. ✅ Can manually activate users if needed
2. ✅ Can see all new Ad Account fields
3. ✅ Can manage users from admin dashboard
4. ✅ Activity logs track all changes

---

## 🔄 Rollback Plan (If Issues)

If something goes wrong:

```bash
# Revert to previous version
git reset --hard HEAD~1
git push -f origin main

# On PythonAnywhere
git pull origin main
python manage.py migrate
python manage.py collectstatic --noinput
# Reload web app
```

---

## 📞 Support

If you encounter any issues:
1. Check error logs on PythonAnywhere
2. Review this guide's troubleshooting section
3. Test locally first to isolate issues
4. Check database migrations are applied

---

## ✅ Final Verification

After deployment, verify:
- [ ] Website loads: https://webq.pythonanywhere.com
- [ ] Registration works
- [ ] Login works
- [ ] Dashboard loads
- [ ] Ad Accounts table shows new columns
- [ ] No console errors
- [ ] API endpoints respond
- [ ] CORS working

**All done! Your application is production ready! 🚀**
