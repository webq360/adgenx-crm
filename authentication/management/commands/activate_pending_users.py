from django.core.management.base import BaseCommand
from dashboard.models import User


class Command(BaseCommand):
    help = 'Activate all pending users who have verified their email but are not active'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Activate specific user by email',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        
        if email:
            # Activate specific user
            try:
                user = User.objects.get(email=email, is_active=False)
                user.is_active = True
                user.is_verified = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully activated user: {user.email}')
                )
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User not found or already active: {email}')
                )
        else:
            # Activate all pending verified users
            pending_users = User.objects.filter(is_verified=True, is_active=False)
            count = pending_users.count()
            
            if count == 0:
                self.stdout.write(
                    self.style.WARNING('No pending users found.')
                )
                return
            
            # List users before activation
            self.stdout.write(
                self.style.WARNING(f'\nFound {count} pending user(s):')
            )
            for user in pending_users:
                self.stdout.write(f'  - {user.email} ({user.first_name} {user.last_name})')
            
            # Activate all
            pending_users.update(is_active=True)
            
            self.stdout.write(
                self.style.SUCCESS(f'\nSuccessfully activated {count} user(s)!')
            )
