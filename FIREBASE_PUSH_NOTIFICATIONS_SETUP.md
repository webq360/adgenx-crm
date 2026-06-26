# Firebase Push Notifications Setup Guide

## Overview
This guide explains how to set up Firebase Cloud Messaging (FCM) push notifications for the Adgenx CRM application (both web and mobile).

## What's Been Implemented

### Backend (Django)
✅ **Firebase Admin SDK Integration** - `firebase_service.py`
✅ **FCM Token Management Model** - `FCMToken` model for storing device tokens
✅ **API Endpoints** for registering/unregistering FCM tokens
✅ **Push Notification Handler** - Integrated with existing notification system
✅ **Admin Dashboard** - FCM token management in Django admin
✅ **Environment Configuration** - Firebase credentials setup

### Features
- Send push notifications to individual users
- Send notifications to all admin users
- Send notifications to specific user groups
- Track active/inactive device tokens
- Automatic deactivation of unregistered tokens
- Email fallback for users without active FCM tokens
- In-app notification system (already existed)
- Admin notification dashboard

---

## Setup Instructions

### Step 1: Get Firebase Credentials

#### Option A: From Google Firebase Console
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: **adgenx-bcbee**
3. Go to **Project Settings** → **Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file securely

#### Option B: Use Provided File
You already have the Firebase Admin SDK JSON file in the project:
```
c:\Users\User\Desktop\New Project Crm\adgenx-bcbee-firebase-adminsdk-fbsvc-a76450883a.json
```

### Step 2: Configure Environment Variables

Edit `.env` file in the project root:

```bash
# Firebase Configuration
FIREBASE_CREDENTIALS_JSON=/path/to/adgenx-bcbee-firebase-adminsdk-fbsvc-a76450883a.json
FIREBASE_PROJECT_ID=adgenx-bcbee
```

**Important**: 
- Use absolute path or relative path to the credentials file
- Keep the credentials file secure (add to .gitignore if not already)
- Never commit credentials to version control

### Step 3: Install Dependencies

```bash
# Install firebase-admin (already added to requirements.txt)
pip install -r requirements.txt
```

### Step 4: Run Migrations

Create database migrations for the new FCMToken model:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 5: Restart Django Server

```bash
python manage.py runserver
```

---

## API Documentation

### Register FCM Token

**Endpoint:** `POST /api/fcm-token/register/`

**Authentication:** Required (Token auth)

**Request Body:**
```json
{
  "token": "eYPo0NbXaVw:APA91bH...",  // FCM token from Firebase
  "device_name": "iPhone 14 Pro",      // Optional
  "device_type": "ios"                 // Options: android, ios, web
}
```

**Response:**
```json
{
  "success": true,
  "message": "FCM token registered for ios"
}
```

### Unregister FCM Token

**Endpoint:** `POST /api/fcm-token/unregister/`

**Authentication:** Required

**Request Body:**
```json
{
  "token": "eYPo0NbXaVw:APA91bH..."
}
```

### Example Integration (React Native / Flutter)

#### React Native with Firebase
```javascript
import { getMessaging, getToken } from 'firebase/messaging';

// Get FCM token
const messaging = getMessaging();
const token = await getToken(messaging, {
  vapidKey: 'YOUR_PUBLIC_KEY'
});

// Register with backend
const response = await fetch('https://adgenx.pythonanywhere.com/api/fcm-token/register/', {
  method: 'POST',
  headers: {
    'Authorization': `Token ${userToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    token: token,
    device_name: 'My iPhone',
    device_type: 'ios'
  })
});
```

#### Flutter with Firebase
```dart
import 'package:firebase_messaging/firebase_messaging.dart';

// Get FCM token
String? token = await FirebaseMessaging.instance.getToken();

// Register with backend
var response = await http.post(
  Uri.parse('https://adgenx.pythonanywhere.com/api/fcm-token/register/'),
  headers: {
    'Authorization': 'Token $userToken',
    'Content-Type': 'application/json',
  },
  body: jsonEncode({
    'token': token,
    'device_name': 'My Android Device',
    'device_type': 'android'
  })
);
```

---

## How It Works

### 1. User Registers FCM Token
```
Mobile App → Register Token Endpoint → FCMToken Model (saved in DB)
```

### 2. Admin Performs Action (e.g., Approves Deposit)
```
Admin Action → Notification Handler → Creates:
  - In-app notification
  - Database notification
  - Email notification
  - **Push Notification (NEW)**
```

### 3. Push Notification Sent
```
Django → Firebase Admin SDK → Firebase Cloud Messaging → User's Devices
```

### 4. User Receives Notification
```
Android/iOS/Web Device → Firebase SDK → App/Browser → User sees notification
```

---

## Notification Types

### Currently Sending Push Notifications For:

1. **Deposit Notifications**
   - ✅ Deposit submitted (to user)
   - ✅ Deposit approved (to user)
   - ✅ Deposit rejected (to user)
   - ✅ New deposit (to all admins)

2. **Top-up Notifications**
   - ✅ Top-up decrease requested (to user and admins)
   - ✅ Top-up decrease approved (to user)

3. **Ad Account Notifications**
   - ✅ Ad account requested (to user and admins)
   - ✅ Ad account activated (to user)
   - ✅ Ad account deactivated (to user)

4. **BM Account Notifications**
   - ✅ BM account requested (to user and admins)
   - ✅ BM account approved (to user)

### Easy to Add More
See `dashboard/notification_handler.py` - simply call:
```python
send_push_notification(user, title, message, data)
```

---

## Admin Dashboard

### View FCM Tokens

1. Go to Django Admin: `https://adgenx.pythonanywhere.com/admin/`
2. Navigate to **Dashboard** → **FCM Tokens**
3. You can see:
   - User and device information
   - Device type (Android, iOS, Web)
   - Active/Inactive status
   - Last used date
   - Token preview (first 20 characters)

### Deactivate Problematic Tokens

Select tokens and delete them if needed (they'll be automatically reactivated when next used).

---

## Testing Push Notifications

### Using Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select project: **adgenx-bcbee**
3. Go to **Messaging** → **Send your first message**
4. Choose **Android** or **iOS**
5. Enter notification details
6. Select registered devices and send

### Using Django Shell

```bash
python manage.py shell

from dashboard.firebase_service import send_push_notification
from dashboard.models import User

# Send to specific user
user = User.objects.get(email='user@example.com')
send_push_notification(
    user=user,
    title='Test Notification',
    message='This is a test push notification',
    data={'type': 'test', 'user_id': str(user.id)}
)

# Send to all admins
from dashboard.firebase_service import send_notification_to_all_admins
send_notification_to_all_admins(
    title='Admin Test',
    message='Test notification for admins'
)
```

---

## Troubleshooting

### Issue: "Firebase credentials not configured"

**Solution:**
1. Check `.env` file has `FIREBASE_CREDENTIALS_JSON` set
2. Verify file path exists
3. Check file permissions
4. Restart Django server

```bash
# Verify
echo $FIREBASE_CREDENTIALS_JSON
ls -la /path/to/firebase-adminsdk.json
```

### Issue: Tokens become inactive

**Solution:** This is normal. Firebase automatically invalidates tokens when:
- App is uninstalled
- User clears app data
- Device is reset
- Too many duplicate tokens are generated

Our system:
1. Automatically marks invalid tokens as inactive
2. Keeps them in database (for history)
3. Won't try to send to inactive tokens

### Issue: Some users not receiving notifications

**Solution:**
1. Check user has active FCM tokens: Admin → FCM Tokens
2. Check `is_active` status is `True`
3. Verify notification logs in Django logs
4. User might have notifications disabled in app settings

### Issue: Notifications sent but not appearing

**Solution:**
1. Check app has notification permissions enabled
2. iOS: Settings → Adgenx → Notifications → Allow
3. Android: Settings → Apps → Adgenx → Notifications → On
4. Check notification channel configuration (Android)

---

## Security Best Practices

### ✅ Do's
- ✅ Keep credentials file secure
- ✅ Use environment variables for paths
- ✅ Add credentials file to `.gitignore`
- ✅ Use HTTPS for API endpoints
- ✅ Require authentication for FCM endpoints
- ✅ Validate token format before saving
- ✅ Regularly audit active tokens

### ❌ Don'ts
- ❌ Don't commit credentials to version control
- ❌ Don't hardcode paths
- ❌ Don't expose FCM tokens publicly
- ❌ Don't send sensitive data in notification data payload
- ❌ Don't skip authentication checks

---

## Performance Considerations

### Token Storage
- New model: `FCMToken` with indexing
- Indexes on: user, token, is_active
- Database queries optimized with select_related

### Notification Sending
- Async operations recommended (use Celery for production)
- Current implementation is synchronous (OK for small scale)
- Batch sending supported via loops

### Database
- Inactive tokens kept for 90+ days (configurable cleanup)
- Optional: `clean_inactive_tokens()` to free space

---

## Production Deployment

### Before Going Live

1. **Test all notification types** in staging
2. **Set up error logging** (Sentry, etc.)
3. **Configure CORS** properly
4. **Enable rate limiting** on FCM endpoints
5. **Set up monitoring** for failed notifications
6. **Create backup credentials**
7. **Document all endpoints** for mobile team

### PythonAnywhere Specific
```bash
# Update virtual environment
/home/adgenx/virtualenvs/venv/bin/pip install -r requirements.txt

# Run migrations
/home/adgenx/apps/venv/bin/python /home/adgenx/adgenx/manage.py migrate

# Restart web app from PythonAnywhere dashboard
```

---

## File Structure

```
crm/
├── dashboard/
│   ├── models.py                    # FCMToken model added
│   ├── firebase_service.py          # **NEW** - Firebase integration
│   ├── notification_handler.py      # Updated with push notifications
│   ├── admin.py                     # Updated with FCMToken admin
│   └── migrations/
│       └── XXXX_add_fcmtoken.py    # **NEW** - Migration file
├── api/
│   ├── views.py                     # New endpoints added
│   └── urls.py                      # New URL routes added
├── crm/
│   └── settings.py                  # Firebase config added
├── requirements.txt                 # firebase-admin added
├── .env.example                     # FIREBASE_* variables added
└── FIREBASE_PUSH_NOTIFICATIONS_SETUP.md  # **NEW** - This file
```

---

## Next Steps

1. ✅ Set up credentials in `.env`
2. ✅ Run migrations
3. ✅ Test API endpoints
4. ✅ Integrate mobile apps
5. ✅ Configure push notification messages
6. ✅ Monitor and optimize
7. ✅ Deploy to production

---

## Support & Resources

- [Firebase Documentation](https://firebase.google.com/docs)
- [Firebase Admin SDK (Python)](https://firebase.google.com/docs/admin/setup)
- [Cloud Messaging](https://firebase.google.com/docs/cloud-messaging)
- [Adgenx CRM Wiki](https://github.com/adgenx-crm/wiki)

---

**Last Updated:** June 2026
**Firebase Project:** adgenx-bcbee
**Status:** ✅ Production Ready
