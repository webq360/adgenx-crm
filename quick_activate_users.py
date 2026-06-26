#!/usr/bin/env python
"""
Quick script to activate all pending users
Run this on production server: python quick_activate_users.py
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm.settings')
django.setup()

from dashboard.models import User

def activate_all_pending_users():
    """Activate all users who are not active"""
    pending_users = User.objects.filter(is_active=False, is_staff=False)
    
    if not pending_users.exists():
        print("✓ No pending users found. All users are already active!")
        return
    
    print(f"\n{'='*60}")
    print(f"Found {pending_users.count()} pending user(s):")
    print(f"{'='*60}\n")
    
    for user in pending_users:
        print(f"  📧 {user.email}")
        print(f"     Name: {user.first_name} {user.last_name}")
        print(f"     Verified: {'✓' if user.is_verified else '✗'}")
        print()
    
    response = input("Do you want to activate all these users? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        count = 0
        for user in pending_users:
            user.is_active = True
            user.is_verified = True
            user.save()
            count += 1
            print(f"✓ Activated: {user.email}")
        
        print(f"\n{'='*60}")
        print(f"✓ Successfully activated {count} user(s)!")
        print(f"{'='*60}\n")
    else:
        print("\n✗ Operation cancelled.")

if __name__ == '__main__':
    activate_all_pending_users()
