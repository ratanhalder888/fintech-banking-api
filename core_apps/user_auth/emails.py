from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from loguru import logger
from core_apps.common.tasks import send_email_task

class BaseDjoserEmailTask:
    """
    Base class for Djoser emails that routes to Celery.
    Does NOT inherit from djoser.email classes directly to avoid AppRegistry errors.
    """
    def __init__(self, request, context):
        self.request = request
        self.context = context

    def send(self, to):
        context = self.context
        
        # Ensure base context is present
        context.update({
            "site_name": settings.SITE_NAME,
            "protocol": "https" if self.request.is_secure() else "http",
            "domain": getattr(settings, "DOMAIN", self.request.get_host()),
        })

        # Djoser context data usually has 'uid' and 'token'
        if "uid" not in context or not context["uid"]:
            if "user" in context:
                from djoser import utils
                context["uid"] = utils.encode_uid(context["user"].pk)
            elif "user_id" in context:
                from djoser import utils
                context["uid"] = utils.encode_uid(context["user_id"])
        
        if "token" not in context or not context["token"]:
            from django.contrib.auth.tokens import default_token_generator
            user = context.get("user")
            if user:
                context["token"] = default_token_generator.make_token(user)

        # RE-GENERATE the URL to ensure it uses the NEW ACTIVATION_URL from settings
        from djoser.conf import settings as djoser_settings
        try:
            if self.__class__.__name__ == "ActivationEmail":
                context["url"] = djoser_settings.ACTIVATION_URL.format(**context)
            elif self.__class__.__name__ == "PasswordResetEmail":
                context["url"] = djoser_settings.PASSWORD_RESET_CONFIRM_URL.format(**context)
        except KeyError:
            logger.warning(f"Could not format URL for {self.__class__.__name__}, check context keys")

        try:
            html_email = render_to_string(self.template_name, context)
            plain_email = strip_tags(html_email)
            subject = render_to_string(self.subject_template_name, context).replace("\n", "").replace("\r", "")
            
            from_email = settings.DEFAULT_FROM_EMAIL
            send_email_task.delay(subject, plain_email, from_email, to, html_email)
            logger.info(f"Queued email task: {self.__class__.__name__} to {to}")
        except Exception as e:
            logger.error(f"Error rendering/queueing email {self.__class__.__name__}: {e}")

class ActivationEmail(BaseDjoserEmailTask):
    template_name = "emails/activation_email.html"
    subject_template_name = "emails/activation_email_subject.txt"

class ConfirmationEmail(BaseDjoserEmailTask):
    template_name = "emails/confirmation_email.html"
    subject_template_name = "emails/confirmation_email_subject.txt"

class PasswordResetEmail(BaseDjoserEmailTask):
    template_name = "emails/password_reset_email.html"
    subject_template_name = "emails/password_reset_email_subject.txt"

class PasswordChangedConfirmationEmail(BaseDjoserEmailTask):
    template_name = "emails/password_changed_confirmation_email.html"
    subject_template_name = "emails/password_changed_confirmation_email_subject.txt"

class UsernameChangedConfirmationEmail(BaseDjoserEmailTask):
    template_name = "emails/username_changed_confirmation_email.html"
    subject_template_name = "emails/username_changed_confirmation_email_subject.txt"

class UsernameResetEmail(BaseDjoserEmailTask):
    template_name = "emails/username_reset_email.html"
    subject_template_name = "emails/username_reset_email_subject.txt"


def send_otp_email(email, otp):
    subject = _('Your OTP code for Login')
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    context = {
            "otp" : otp,
            "expiry_time" : settings.OTP_EXPIRATION,
            "site_name" : settings.SITE_NAME,
    }
    html_email = render_to_string("emails/otp_email.html", context)
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
    html_email = render_to_string("emails/account_locked.html", context)
    plain_email = strip_tags(html_email)
    
    send_email_task.delay(subject, plain_email, from_email, recipient_list, html_email)
