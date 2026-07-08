from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class AccountsConfig(AppConfig):
    name = 'accounts'
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = _("Accounts")
