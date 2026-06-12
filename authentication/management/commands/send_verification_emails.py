
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from dashboard.models import User
from authentication.tokens import account_activation_token

class Command(BaseCommand):
    help = 'Sends verification emails to all unverified users.'

    def handle(self, *args, **options):
        unverified_users = User.objects.filter(is_verified=False)
        for user in unverified_users:
            protocol = 'https'
            current_site = '127.0.0.1:8000'
            mail_subject = 'Activate your CRM account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'protocol': protocol,
                'domain': current_site,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            to_email = user.email
            send_mail(
                mail_subject,
                message,
                settings.EMAIL_HOST_USER,
                [to_email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully sent verification email to {user.email}'))
