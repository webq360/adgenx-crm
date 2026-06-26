"""
Firebase Cloud Messaging Service for Push Notifications
Handles sending push notifications to user devices via Firebase
"""

import firebase_admin
from firebase_admin import messaging
from django.conf import settings
from django.utils import timezone
from dashboard.models import FCMToken, User
import logging

logger = logging.getLogger(__name__)


def send_push_notification(user, title, message, data=None, token=None):
    """
    Send a push notification to a specific user or device
    
    Args:
        user: User object or user ID
        title: Notification title
        message: Notification message
        data: Optional dict of custom data
        token: Optional specific FCM token (if not provided, sends to all user devices)
    
    Returns:
        bool: True if notification sent successfully, False otherwise
    """
    try:
        # Get user if ID provided
        if isinstance(user, int):
            try:
                user = User.objects.get(id=user)
            except User.DoesNotExist:
                logger.warning(f"User with id {user} not found")
                return False
        
        # If specific token provided, send to that token only
        if token:
            return _send_to_token(token, title, message, data)
        
        # Otherwise send to all active tokens for the user
        tokens = FCMToken.objects.filter(user=user, is_active=True).values_list('token', flat=True)
        
        if not tokens:
            logger.warning(f"No active FCM tokens found for user {user.email}")
            return False
        
        success_count = 0
        for fcm_token in tokens:
            if _send_to_token(fcm_token, title, message, data):
                success_count += 1
        
        if success_count == 0:
            logger.warning(f"Failed to send notification to all tokens for user {user.email}")
            return False
        
        logger.info(f"✓ Push notification sent to {success_count}/{len(list(tokens))} tokens for user {user.email}")
        return True
    
    except Exception as e:
        logger.error(f"✗ Error sending push notification: {e}")
        return False


def _send_to_token(token, title, message, data=None):
    """
    Send push notification to a specific FCM token
    """
    try:
        notification = messaging.Notification(
            title=title,
            body=message,
        )
        
        message_obj = messaging.Message(
            notification=notification,
            data=data or {},
            token=token,
        )
        
        response = messaging.send(message_obj)
        logger.info(f"✓ Message sent to token: {response}")
        return True
    
    except messaging.UnregisteredError:
        logger.warning(f"Token {token} is unregistered - deactivating")
        FCMToken.objects.filter(token=token).update(is_active=False)
        return False
    
    except messaging.InvalidArgumentError as e:
        logger.error(f"Invalid FCM token: {e}")
        FCMToken.objects.filter(token=token).update(is_active=False)
        return False
    
    except Exception as e:
        logger.error(f"✗ Error sending to token {token}: {e}")
        return False


def send_notification_to_all_admins(title, message, data=None):
    """Send notification to all admin users"""
    try:
        admins = User.objects.filter(is_staff=True, is_active=True)
        success_count = 0
        
        for admin in admins:
            if send_push_notification(admin, title, message, data):
                success_count += 1
        
        logger.info(f"✓ Notification sent to {success_count}/{admins.count()} admins")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"✗ Error sending notification to admins: {e}")
        return False


def send_notification_to_user_group(group_name, title, message, data=None):
    """Send notification to all users in a specific group"""
    try:
        from django.contrib.auth.models import Group
        
        group = Group.objects.get(name=group_name)
        users = User.objects.filter(groups=group)
        success_count = 0
        
        for user in users:
            if send_push_notification(user, title, message, data):
                success_count += 1
        
        logger.info(f"✓ Notification sent to {success_count}/{users.count()} users in group {group_name}")
        return success_count > 0
    
    except Exception as e:
        logger.error(f"✗ Error sending notification to group: {e}")
        return False


def register_fcm_token(user, token, device_name='', device_type='android'):
    """
    Register or update FCM token for a user
    
    Args:
        user: User object
        token: FCM token from mobile device
        device_name: Optional device name/identifier
        device_type: Device type (android, ios, web)
    
    Returns:
        bool: True if successful
    """
    try:
        # Get or create FCM token
        fcm_token, created = FCMToken.objects.get_or_create(
            user=user,
            token=token,
            defaults={
                'device_name': device_name,
                'device_type': device_type,
                'is_active': True,
            }
        )
        
        # Update if already exists
        if not created:
            fcm_token.device_name = device_name
            fcm_token.device_type = device_type
            fcm_token.is_active = True
            fcm_token.last_used = timezone.now()
            fcm_token.save()
        
        logger.info(f"✓ FCM token registered for user {user.email} (device: {device_type})")
        return True
    
    except Exception as e:
        logger.error(f"✗ Error registering FCM token: {e}")
        return False


def unregister_fcm_token(user, token):
    """Remove/deactivate FCM token"""
    try:
        FCMToken.objects.filter(user=user, token=token).update(is_active=False)
        logger.info(f"✓ FCM token deactivated for user {user.email}")
        return True
    except Exception as e:
        logger.error(f"✗ Error deactivating FCM token: {e}")
        return False


def get_user_active_tokens(user):
    """Get count of active FCM tokens for a user"""
    try:
        count = FCMToken.objects.filter(user=user, is_active=True).count()
        return count
    except Exception as e:
        logger.error(f"✗ Error getting active tokens: {e}")
        return 0


def clean_inactive_tokens():
    """Remove old inactive tokens (optional cleanup task)"""
    try:
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=90)
        
        deleted_count, _ = FCMToken.objects.filter(
            is_active=False,
            last_used__lt=old_date
        ).delete()
        
        logger.info(f"✓ Cleaned up {deleted_count} old inactive tokens")
        return deleted_count
    except Exception as e:
        logger.error(f"✗ Error cleaning inactive tokens: {e}")
        return 0
