from django.db import models
from django.conf import settings

class AuditLog(models.Model):
    """Registro ENTERPRISE de auditoría detallada."""

    ACCION_CHOICES = [
        ('LOGIN', 'Inicio de sesión'),
        ('LOGOUT', 'Cierre de sesión'),
        ('CREATE', 'Creación'),
        ('UPDATE', 'Actualización'),
        ('DELETE', 'Eliminación'),
        ('VIEW', 'Visualización'),
        ('ACCESS', 'Acceso a página/módulo'),
    ]

    # Actor
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs_realizados'
    )

    # Dónde ocurrió
    url = models.CharField(max_length=500, null=True, blank=True)
    metodo_http = models.CharField(max_length=10, null=True, blank=True)
    ip_origen = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    session_key = models.CharField(max_length=50, null=True, blank=True)

    # Qué modelo / registro
    modelo = models.CharField(max_length=200, null=True, blank=True)
    objeto_id = models.CharField(max_length=200, null=True, blank=True)

    # Tipo de acción
    accion = models.CharField(max_length=10, choices=ACCION_CHOICES, db_index=True)

    # Detalle crudo y diff
    datos_antes = models.JSONField(null=True, blank=True)
    datos_despues = models.JSONField(null=True, blank=True)
    diff = models.JSONField(null=True, blank=True)

    # Severidad para SOC/SIEM
    severidad = models.CharField(
        max_length=10,
        choices=[
            ('INFO', 'Info'),
            ('WARN', 'Advertencia'),
            ('CRIT', 'Crítico'),
        ],
        default='INFO',
        db_index=True
    )

    fecha_evento = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name = "Log de Auditoría"
        verbose_name_plural = "Logs de Auditoría"
        ordering = ['-fecha_evento']
        indexes = [
            models.Index(fields=['accion', 'severidad', 'modelo']),
            models.Index(fields=['fecha_evento']),
        ]

    def __str__(self):
        u = self.usuario.email if self.usuario else 'Usuario desconocido'
        return f"[{self.fecha_evento:%Y-%m-%d %H:%M:%S}] {u} → {self.accion} ({self.modelo}:{self.objeto_id})"
