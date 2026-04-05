from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UserProfileConfig(AppConfig):
    name = 'core_apps.user_profile'
    verbose_name = _("User Profile")
