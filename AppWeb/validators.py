from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class LongitudMinimaValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                _("La contraseña es demasiado corta. Debe contener al menos %(min_length)d caracteres."),
                code='password_too_short',
                params={'min_length': self.min_length},
            )

    def get_help_text(self):
        return _("Tu contraseña debe contener al menos %(min_length)d caracteres.") % {'min_length': self.min_length}


class ContraseñaComunValidator:
    def validate(self, password, user=None):
        comunes = ['123456', 'password', 'contraseña', 'admin', 'qwerty']
        if password.lower() in comunes:
            raise ValidationError(_("Esta contraseña es demasiado común."), code='password_too_common')

    def get_help_text(self):
        return _("No uses contraseñas demasiado comunes o fáciles de adivinar.")


class NumericaValidator:
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(_("La contraseña no puede ser completamente numérica."), code='password_entirely_numeric')

    def get_help_text(self):
        return _("Tu contraseña no debe ser solo números.")
