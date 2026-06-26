"""
Setup Django Group-based permissions
Run: python manage.py setup_group_permissions
"""
from django.core.management.base import BaseCommand
from dashboard.group_permissions import GroupPermissionManager


class Command(BaseCommand):
    help = 'Setup Django Groups and Permissions for role-based access'
    
    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🚀 SETTING UP GROUP-BASED PERMISSIONS"))
        self.stdout.write("="*70 + "\n")
        
        # Step 1: Create permissions
        self.stdout.write("📌 Step 1: Creating custom permissions...")
        created = GroupPermissionManager.setup_permissions()
        if created:
            self.stdout.write(self.style.SUCCESS(f"✅ Created permissions: {', '.join(created)}"))
        else:
            self.stdout.write(self.style.SUCCESS("✅ All permissions already exist"))
        
        # Step 2: Create default groups
        self.stdout.write("\n📌 Step 2: Creating default groups...")
        groups = GroupPermissionManager.create_default_groups()
        self.stdout.write(self.style.SUCCESS(f"✅ Created/Updated {len(groups)} groups"))
        
        # Step 3: Show all groups
        self.stdout.write("\n📌 Step 3: Available groups:\n")
        from django.contrib.auth.models import Group
        for group in Group.objects.all():
            perms = group.permissions.all()
            self.stdout.write(f"\n🛡️  {group.name}")
            self.stdout.write(f"   Permissions ({perms.count()}):")
            for perm in perms:
                self.stdout.write(f"     • {perm.codename}")
        
        # Step 4: Instructions
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("\n✅ SETUP COMPLETE!\n"))
        self.stdout.write("="*70)
        self.stdout.write("\n📋 HOW TO USE:\n")
        self.stdout.write("1. Go to Django Admin: http://127.0.0.1:8000/admin/")
        self.stdout.write("2. Login as superuser")
        self.stdout.write("3. Go to: Users → Select user → Groups section")
        self.stdout.write("4. Add user to a group (Manager, Accountant, etc.)")
        self.stdout.write("5. Save")
        self.stdout.write("6. User gets permissions automatically!")
        self.stdout.write("\n💡 You can also create custom groups with any permission combination\n")
