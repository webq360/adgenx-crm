# Generated migration to remove custom UserRole model
# This migration removes the UserRole model and the user.role field
# The system now uses Django's built-in Group and Permission system instead

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0041_add_withdrawal_notification_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        migrations.DeleteModel(
            name='UserRole',
        ),
    ]
