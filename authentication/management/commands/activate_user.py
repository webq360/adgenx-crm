from django.core.management.base import BaseCommand
from dashboard.models import User


class Command(BaseCommand):
    help = 'Activate a user by email'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='User email to activate')

    def handle(self, *args, **options):
        email = options['email']
        
        try:
            user = User.objects.get(email=email)
            
            if user.is_active:
                self.stdout.write(
                    self.style.WARNING(f'User {email} is already active.')
                )
            else:
                user.is_active = True
                user.is_verified = True
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Successfully activated user: {email}')
                )
                self.stdout.write(f'  Name: {user.first_name} {user.last_name}')
                self.stdout.write(f'  Username: {user.username}')
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'✗ User not found: {email}')
            )
