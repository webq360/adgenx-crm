# Firebase Push Notifications - Deployment Checklist

## Pre-Deployment Phase

### Code Review
- [ ] Review `firebase_service.py` for errors
- [ ] Review `notification_handler.py` updates
- [ ] Check `models.py` for FCMToken model
- [ ] Verify `api/views.py` new endpoints
- [ ] Verify `api/urls.py` new routes
- [ ] Check `admin.py` FCMTokenAdmin

### Local Development
- [ ] Install `firebase-admin`: `pip install firebase-admin==6.5.0`
- [ ] Set up `.env` with test Firebase credentials
- [ ] Run migrations locally: `python manage.py makemigrations && python manage.py migrate`
- [ ] Start dev server: `python manage.py runserver`
- [ ] No errors in Django startup logs

### Local Testing
- [ ] Test FCM token registration via API
  ```bash
  curl -X POST http://localhost:8000/api/fcm-token/register/ \
    -H "Authorization: Token YOUR_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"token":"test_token_123","device_type":"android"}'
  ```
- [ ] Test unregister endpoint
- [ ] Verify FCMToken appears in admin: `http://localhost:8000/admin/dashboard/fcmtoken/`
- [ ] Test sending notification via Django shell
  ```bash
  python manage.py shell
  >>> from dashboard.firebase_service import send_push_notification
  >>> from dashboard.models import User
  >>> user = User.objects.first()
  >>> send_push_notification(user, "Test", "Testing")
  ```
- [ ] Verify no database errors
- [ ] Verify no import errors
- [ ] Check logs for Firebase initialization message

### Git Workflow
- [ ] Commit all changes with meaningful message:
  ```bash
  git add .
  git commit -m "feat: Add Firebase push notifications support"
  ```
- [ ] Push to feature branch (NOT master):
  ```bash
  git push origin feature/firebase-push-notifications
  ```
- [ ] Create pull request with description

---

## Staging Deployment

### Pre-Deployment Setup
- [ ] Have PythonAnywhere admin access
- [ ] Firebase credentials JSON downloaded and secured
- [ ] `.env.production` file prepared with correct paths
- [ ] Database backup created

### Upload Files
- [ ] Connect to PythonAnywhere via SSH/Web Console
- [ ] Navigate to project directory
- [ ] Update requirements.txt:
  ```bash
  pip install -r requirements.txt
  ```
- [ ] Copy Firebase credentials file to secure location:
  ```bash
  # Example path
  /home/adgenx/private/firebase-creds.json
  chmod 600 /home/adgenx/private/firebase-creds.json
  ```
- [ ] Update `.env` with production paths

### Database Migrations
- [ ] SSH into PythonAnywhere
- [ ] Activate virtual environment:
  ```bash
  source /home/adgenx/virtualenvs/venv/bin/activate
  ```
- [ ] Run migrations:
  ```bash
  python /home/adgenx/adgenx/manage.py makemigrations
  python /home/adgenx/adgenx/manage.py migrate
  ```
- [ ] Verify no migration errors
- [ ] Check database contains FCMToken table:
  ```bash
  python manage.py dbshell
  > .tables  # Should show dashboard_fcmtoken
  ```

### Django Configuration Check
- [ ] Verify Firebase config loads:
  ```bash
  python manage.py shell
  >>> import firebase_admin
  >>> print(firebase_admin._apps)  # Should show adgenx-bcbee app
  ```
- [ ] Check for initialization message in logs
- [ ] No import errors for firebase_service

### Web App Restart
- [ ] Reload web app in PythonAnywhere dashboard
- [ ] Check for errors in error log: `/var/log/adgenx.pythonanywhere.com.error.log`
- [ ] Verify app responds: `curl https://adgenx.pythonanywhere.com/`

### Staging Testing
- [ ] Test FCM registration API:
  ```bash
  curl -X POST https://adgenx.pythonanywhere.com/api/fcm-token/register/ \
    -H "Authorization: Token YOUR_STAGING_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"token":"staging_token_123","device_type":"android"}'
  ```
- [ ] Verify token in admin dashboard
- [ ] Test notification sending via Django shell
- [ ] Monitor error logs for issues
- [ ] Test withdrawal API if available
- [ ] Verify admin can see FCM tokens:
  - Log in to admin: `https://adgenx.pythonanywhere.com/admin/`
  - Navigate to Dashboard → FCM Tokens
  - Should see registered test token

---

## Mobile App Integration (Mobile Team)

### Pre-Integration
- [ ] Mobile team has Firebase project access
- [ ] `google-services.json` (Android) downloaded
- [ ] `GoogleService-Info.plist` (iOS) downloaded
- [ ] Staging backend URL confirmed: `https://adgenx.pythonanywhere.com/`
- [ ] API token generation method documented

### Android Integration
- [ ] Add Firebase dependency: `implementation 'com.google.firebase:firebase-messaging:23.x.x'`
- [ ] Add `google-services.json` to app
- [ ] Initialize Firebase Messaging
- [ ] Get FCM token:
  ```kotlin
  FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    val token = task.result
    // Send to backend
  }
  ```
- [ ] Register token with backend on app startup
- [ ] Handle incoming messages:
  ```kotlin
  class MyMessagingService : FirebaseMessagingService() {
    override fun onMessageReceived(remoteMessage: RemoteMessage) {
      // Handle push notification
    }
  }
  ```
- [ ] Test receiving notification on test device

### iOS Integration
- [ ] Add Firebase pod: `pod 'Firebase/Messaging'`
- [ ] Add `GoogleService-Info.plist`
- [ ] Request user notification permission
- [ ] Initialize Firebase Messaging
- [ ] Get FCM token:
  ```swift
  Messaging.messaging().token { token, error in
    // Send to backend
  }
  ```
- [ ] Register token with backend
- [ ] Handle incoming notifications
- [ ] Test receiving notification on test device

### React Native Integration
- [ ] Install: `npm install @react-native-firebase/messaging`
- [ ] Initialize Firebase
- [ ] Get token and register with backend
- [ ] Set up foreground message handler
- [ ] Set up background message handler
- [ ] Test on Android emulator
- [ ] Test on iOS simulator

### Flutter Integration
- [ ] Add dependency: `firebase_messaging`
- [ ] Initialize Firebase Messaging
- [ ] Request notification permissions:
  ```dart
  final settings = await messaging.requestPermission();
  ```
- [ ] Get token:
  ```dart
  String? token = await messaging.getToken();
  ```
- [ ] Register with backend API
- [ ] Listen for incoming messages:
  ```dart
  FirebaseMessaging.onMessage.listen((message) {
    // Handle notification
  });
  ```
- [ ] Test on physical device

---

## Pre-Production (Final Checks)

### Performance Testing
- [ ] Test with 100+ FCM tokens
- [ ] Monitor database query performance
- [ ] Check API response times (should be < 1s)
- [ ] Monitor server memory usage
- [ ] Verify no database connection leaks

### Security Review
- [ ] Firebase credentials NOT in version control
- [ ] `.env` file NOT in version control
- [ ] API endpoints require authentication
- [ ] HTTPS enforced for all API calls
- [ ] CORS properly configured
- [ ] Rate limiting on notification endpoints (recommended)

### Error Handling Testing
- [ ] Send notification with invalid token
  - Should auto-deactivate token
  - Should log error
  - Should not crash app
- [ ] Test with Firebase service down
  - Should gracefully handle
  - Should not block other operations
- [ ] Test with invalid credentials
  - Should show clear error in logs
  - Should disable push notifications

### Documentation Review
- [ ] Setup guide is up to date
- [ ] Implementation summary is complete
- [ ] Code comments are clear
- [ ] API documentation is accurate
- [ ] Troubleshooting section is useful

### Backup & Recovery
- [ ] Database backup created
- [ ] Firebase credentials backed up securely
- [ ] Rollback plan documented
- [ ] Previous version deployable if needed

---

## Production Deployment

### Final Verification
- [ ] All staging tests passed ✅
- [ ] Mobile team ready for integration ✅
- [ ] Database migrations successful ✅
- [ ] Admin dashboard working ✅
- [ ] Error logging configured ✅
- [ ] Performance acceptable ✅
- [ ] Security review complete ✅
- [ ] Documentation complete ✅

### Go-Live
- [ ] Schedule deployment window
- [ ] Notify stakeholders of deployment time
- [ ] Deploy code to production
- [ ] Verify migrations ran successfully
- [ ] Restart production web app
- [ ] Monitor error logs for 1 hour
- [ ] Test API endpoints in production
- [ ] Test admin dashboard access
- [ ] Verify Firebase initialization in logs

### Post-Deployment Monitoring
- [ ] Monitor error logs hourly for 24 hours
- [ ] Check database performance
- [ ] Monitor API response times
- [ ] Track notification delivery success rate
- [ ] Monitor memory/CPU usage
- [ ] Verify user can register tokens
- [ ] Test end-to-end notification delivery

---

## Rollback Plan (If Issues)

### If Issues Arise
1. **Quick Disable (No Rollback)**
   ```bash
   # Set env variable to disable Firebase
   FIREBASE_CREDENTIALS_JSON=""
   # Restart app - push notifications will be disabled
   # Email/in-app notifications will continue working
   ```

2. **Database Rollback (If Migration Failed)**
   ```bash
   # Revert migration
   python manage.py migrate dashboard XXXX  # Previous migration number
   # Restore from backup if needed
   ```

3. **Full Rollback**
   ```bash
   # Revert code to previous commit
   git revert HEAD
   git push
   # Rebuild, run migrations backward, restart app
   ```

---

## Success Metrics

### Deployment Success Criteria
- [x] No errors in Django startup logs
- [x] Database migrations completed successfully
- [x] FCMToken table exists with correct schema
- [x] Firebase Admin SDK initializes correctly
- [x] All new API endpoints accessible
- [x] Admin dashboard shows FCM tokens
- [ ] Mobile app can register tokens (post-integration)
- [ ] Push notifications deliver in < 5 seconds
- [ ] No database performance degradation
- [ ] Error rate remains < 1%

---

## Monitoring Setup (Post-Deployment)

### Daily Monitoring
- [ ] Check error logs for Firebase errors
- [ ] Monitor notification delivery rates
- [ ] Check database performance
- [ ] Review API endpoint metrics
- [ ] Monitor FCM token growth

### Weekly Monitoring
- [ ] Review token activity patterns
- [ ] Check for inactive token growth
- [ ] Monitor user notification preferences
- [ ] Review push notification open rates
- [ ] Check for any API abuse attempts

### Monthly Maintenance
- [ ] Clean up old inactive tokens (90+ days)
  ```bash
  python manage.py shell
  >>> from dashboard.firebase_service import clean_inactive_tokens
  >>> clean_inactive_tokens()
  ```
- [ ] Review and optimize database indexes
- [ ] Update Firebase Admin SDK if new version available
- [ ] Review notification analytics
- [ ] Plan improvements based on feedback

---

## Contact & Support

### Internal Team
- **Backend Lead:** [Your name/email]
- **DevOps:** PythonAnywhere support + your team
- **Mobile Team:** [Mobile lead email]

### External Support
- Firebase Support: https://firebase.google.com/support
- PythonAnywhere Support: https://www.pythonanywhere.com/help/
- Django Admin: https://docs.djangoproject.com/

---

## Sign-Off

### Development Team
- [ ] Code reviewed by: _________________ Date: _______
- [ ] Tests passed by: _________________ Date: _______

### Deployment Team
- [ ] Staging deployed by: _________________ Date: _______
- [ ] Production deployed by: _________________ Date: _______

### Verification
- [ ] Staging verified by: _________________ Date: _______
- [ ] Production verified by: _________________ Date: _______
- [ ] Mobile integration tested by: _________________ Date: _______

---

## Useful Commands Reference

```bash
# Local Development
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
python manage.py shell

# Production (PythonAnywhere)
cd /home/adgenx/adgenx
source ../virtualenvs/venv/bin/activate
python manage.py migrate
python manage.py shell

# Testing
curl -X POST http://localhost:8000/api/fcm-token/register/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"token":"test","device_type":"android"}'

# Monitoring
tail -f /var/log/adgenx.pythonanywhere.com.error.log

# Database Check
python manage.py dbshell
> SELECT * FROM dashboard_fcmtoken;
> SELECT COUNT(*) FROM dashboard_fcmtoken WHERE is_active=true;
```

---

**Status:** Ready for Deployment
**Last Updated:** June 2026
**Next Step:** Begin Deployment Following This Checklist
