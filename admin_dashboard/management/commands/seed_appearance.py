from django.core.management.base import BaseCommand
from admin_dashboard.models import SiteSettings, FAQ, Testimonial


class Command(BaseCommand):
    help = 'Seed default appearance data (FAQs, Testimonials, SiteSettings)'

    def handle(self, *args, **kwargs):
        # ── Site Settings ──
        settings = SiteSettings.get()
        settings.hero_title_line1    = 'Scale Your Ads.'
        settings.hero_title_line2    = 'Faster & Smarter.'
        settings.hero_subtitle       = 'Get premium ad accounts for Facebook, TikTok & Google Ads. Top up instantly, manage everything from one dashboard.'
        settings.hero_badge_text     = 'Trusted Ad Account Platform'
        settings.stat_users          = '500+'
        settings.stat_ad_spend       = '$2M+'
        settings.about_title         = 'We Help Advertisers Run Ads Without Limits'
        settings.about_body1         = 'Adgenx was founded by a team of performance marketers who were tired of getting ad accounts banned, restricted, or limited. We built a platform that gives advertisers access to premium, stable ad accounts across Facebook, TikTok, and Google.'
        settings.about_body2         = 'Our team manages every account personally — ensuring fast top-ups, zero downtime, and full transparency in every transaction. We don\'t just provide accounts; we become your advertising backbone.'
        settings.about_founded_year  = '2022'
        settings.about_stat_clients  = '500+'
        settings.about_stat_spend    = '$2M+'
        settings.about_stat_uptime   = '99%'
        settings.whatsapp_number     = '8801XXXXXXXXX'
        settings.email_support       = 'support@adgenx.com'
        settings.facebook_url        = '#'
        settings.telegram_url        = '#'
        settings.tiktok_url          = '#'
        settings.instagram_url       = '#'
        settings.footer_tagline      = 'Premium ad account management platform for Facebook, TikTok & Google Ads. Scale without limits.'
        settings.save()
        self.stdout.write(self.style.SUCCESS('✔ Site settings seeded.'))

        # ── FAQs ──
        if FAQ.objects.exists():
            self.stdout.write('  FAQs already exist — skipping.')
        else:
            faqs = [
                (1, 'What is Adgenx and how does it work?',
                 'Adgenx is an ad account management platform that provides premium Facebook, TikTok, and Google Ads accounts. You register, deposit funds into your wallet, and use those funds to top up your ad account balances directly from our dashboard.'),
                (2, 'How long does account approval take?',
                 'After registering and verifying your email, our team typically reviews and activates your account within 24 hours. In most cases it\'s much faster — often within a few hours during business hours.'),
                (3, 'What payment methods are accepted for deposits?',
                 'We accept multiple payment methods including mobile banking (bKash, Nagad, Rocket) and bank transfers. Available payment methods are shown on the deposit page after you log in.'),
                (4, 'Are the ad accounts safe from bans?',
                 'Yes. All our accounts are premium, verified, and maintained with best practices. While no account is 100% ban-proof (as ad platforms can make policy changes), we have a very high stability rate and provide quick replacements when needed.'),
                (5, 'Can I request multiple ad accounts for different platforms?',
                 'Absolutely. You can request ad accounts for Facebook, TikTok, and Google Ads — all managed from the same dashboard. There\'s no limit on how many accounts you can have.'),
                (6, 'How quickly does a top-up reflect in my ad account?',
                 'Top-ups are processed instantly. Once you submit a top-up request from your dashboard, the balance is updated in your ad account in real time — usually within seconds.'),
                (7, 'What if I need help or have an issue?',
                 'Our support team is available 24/7 via WhatsApp, email, and the in-dashboard support chat. We aim to respond to all queries within 15 minutes.'),
            ]
            for order, question, answer in faqs:
                FAQ.objects.create(question=question, answer=answer, order=order, is_active=True)
            self.stdout.write(self.style.SUCCESS(f'✔ {len(faqs)} FAQs seeded.'))

        # ── Testimonials ──
        if Testimonial.objects.exists():
            self.stdout.write('  Testimonials already exist — skipping.')
        else:
            testimonials = [
                (1, 'Rafiq Khan',    'E-commerce Advertiser',    'RK', '#4f46e5', 5,
                 'Adgenx completely changed how I run Facebook campaigns. No more account bans, instant top-ups, and the dashboard is super clean. Highly recommended!'),
                (2, 'Sumaiya Ahmed', 'Digital Marketing Agency', 'SA', '#ec4899', 5,
                 'I was skeptical at first but after the first week I was blown away. TikTok accounts are stable, support responds within minutes. 10/10 service.'),
                (3, 'Mahmud Hossain','Performance Marketer',     'MH', '#10b981', 5,
                 'Best Google Ads account provider I\'ve used. Unlimited spend cap, real-time balance tracking. My ROAS improved significantly after switching to Adgenx.'),
                (4, 'Tanvir Islam',  'Media Buyer',              'TI', '#f59e0b', 5,
                 'The deposit process is seamless and the wallet system is brilliant. I can manage budgets across all three platforms from one place. Saves me hours every week.'),
                (5, 'Nadia Rahman',  'Dropshipping Entrepreneur','NR', '#8b5cf6', 5,
                 'Finally a platform that understands advertisers. The BM account linking feature for Facebook is seamless. Zero complications, zero downtime.'),
                (6, 'Farhan Karim', 'Lead Generation Specialist','FK', '#3b82f6', 5,
                 'Customer support is on another level. Had an issue at 2am, got a response in 5 minutes. The team genuinely cares about your success. Won\'t use anyone else.'),
            ]
            for order, name, role, initials, color, rating, content in testimonials:
                Testimonial.objects.create(
                    name=name, role=role, avatar_initials=initials,
                    avatar_color=color, rating=rating, content=content,
                    order=order, is_active=True
                )
            self.stdout.write(self.style.SUCCESS(f'✔ {len(testimonials)} Testimonials seeded.'))

        self.stdout.write(self.style.SUCCESS('\nAll appearance data seeded successfully!'))
