from django.db import models

# Create your models here.

class SiteSettings(models.Model):
    """Singleton model for global site settings"""
    # Hero Section
    hero_title_line1 = models.CharField(max_length=100, default='Scale Your Ads.')
    hero_title_line2 = models.CharField(max_length=100, default='Faster & Smarter.')
    hero_subtitle = models.TextField(default='Get premium ad accounts for Facebook, TikTok & Google Ads. Top up instantly, manage everything from one dashboard.')
    hero_badge_text = models.CharField(max_length=100, default='Trusted Ad Account Platform')

    # Stats (Hero)
    stat_users = models.CharField(max_length=20, default='500+')
    stat_ad_spend = models.CharField(max_length=20, default='$2M+')

    # About Section
    about_title = models.CharField(max_length=150, default='We Help Advertisers Run Ads Without Limits')
    about_body1 = models.TextField(default='Adgenx was founded by a team of performance marketers who were tired of getting ad accounts banned, restricted, or limited.')
    about_body2 = models.TextField(default='Our team manages every account personally — ensuring fast top-ups, zero downtime, and full transparency in every transaction.')
    about_founded_year = models.CharField(max_length=10, default='2022')
    about_stat_clients = models.CharField(max_length=20, default='500+')
    about_stat_spend = models.CharField(max_length=20, default='$2M+')
    about_stat_uptime = models.CharField(max_length=20, default='99%')

    # Contact Info
    whatsapp_number = models.CharField(max_length=30, blank=True, default='8801XXXXXXXXX')
    email_support = models.EmailField(blank=True, default='support@adgenx.com')
    facebook_url = models.URLField(blank=True, default='#')
    telegram_url = models.URLField(blank=True, default='#')
    tiktok_url = models.URLField(blank=True, default='#')
    instagram_url = models.URLField(blank=True, default='#')

    # Footer
    footer_tagline = models.CharField(max_length=200, default='Premium ad account management platform for Facebook, TikTok & Google Ads. Scale without limits.')

    class Meta:
        verbose_name = 'Site Settings'

    def __str__(self):
        return 'Site Settings'

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    avatar_initials = models.CharField(max_length=3, help_text='2-3 letters shown as avatar, e.g. RK')
    avatar_color = models.CharField(max_length=7, default='#4f46e5', help_text='Hex color for avatar background')
    rating = models.PositiveSmallIntegerField(default=5)
    content = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.name} — {self.role}'
