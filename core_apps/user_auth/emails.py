from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger
from core_apps.common.tasks import send_email_task

def get_email_base():
    from djoser import email
    return email.BaseEmailMessage

class BaseDjoserEmailTask:
    def send(self, to, *args, **kwargs):
        self.render()
        subject = self.subject
        # Djoser's body might be empty if we're not careful with context
        plain_email = self.body
        html_email = getattr(self, "html", None)
        
        # Log for debugging
        logger.info(f"Sending email task: Subject={subject}, To={to}, HasHTML={bool(html_email)}")
        
        from_email = self.from_email
        send_email_task.delay(subject, plain_email, from_email, to, html_email)

class ActivationEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        # The path is relative to the directory in DIRS: /app/core_apps/templates
        self.template_name = "emails/activation_email.html"
        self.__class__ = type('ActivationEmail', (BaseDjoserEmailTask, email.ActivationEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)

class ConfirmationEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        self.__class__ = type('ConfirmationEmail', (BaseDjoserEmailTask, email.ConfirmationEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)

class PasswordResetEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        self.__class__ = type('PasswordResetEmail', (BaseDjoserEmailTask, email.PasswordResetEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)

class PasswordChangedConfirmationEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        self.__class__ = type('PasswordChangedConfirmationEmail', (BaseDjoserEmailTask, email.PasswordChangedConfirmationEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)

class UsernameChangedConfirmationEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        self.__class__ = type('UsernameChangedConfirmationEmail', (BaseDjoserEmailTask, email.UsernameChangedConfirmationEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)

class UsernameResetEmail(BaseDjoserEmailTask):
    def __init__(self, *args, **kwargs):
        from djoser import email
        self.__class__ = type('UsernameResetEmail', (BaseDjoserEmailTask, email.UsernameResetEmail), {})
        super(self.__class__, self).__init__(*args, **kwargs)


def send_otp_email(email, otp):
    subject = _('Your OTP code for Login')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    context = {
            "otp" : otp,
            "expiry_time" : settings.OTP_EXPIRATION,
            "site_name" : settings.SITE_NAME,
    }
    html_email = render_to_string("core_apps/templates/emails/otp_email.html", context)
    plain_email = strip_tags(html_email)
    
    send_email_task.delay(subject, plain_email, from_email, recipient_list, html_email)


def send_account_locked_email(user):
    subject = _('Your account has been locked')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    context = {
            "user" : user,
            "lockout_duration" : int(settings.LOCKOUT_DURATION.total_seconds() // 60),
            "site_name" : settings.SITE_NAME,
    }
    html_email = render_to_string("core_apps/templates/emails/account_locked.html", context)
    plain_email = strip_tags(html_email)
    
    send_email_task.delay(subject, plain_email, from_email, recipient_list, html_email)
