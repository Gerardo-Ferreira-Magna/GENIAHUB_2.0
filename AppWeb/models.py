from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
import uuid



# ----------------------------
# Auditoría obligatoria (abstract)
# ----------------------------
class AuditStampedModel(models.Model):
    """
    Auditoría obligatoria: requiere request.user al crear/actualizar.
    Se debe setear created_by / updated_by en Admin, Views o DRF.
    """
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_creados",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s_actualizados",
    )

    class Meta:
        abstract = True


# ----------------------------
# Usuario (sin auditoría obligatoria para no romper bootstrap)
# ----------------------------
class UsuarioManager(BaseUserManager):
    def create_user(self, email, nombre, apellido_paterno, apellido_materno, rut, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio")
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            rut=rut,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nombre, apellido_paterno, apellido_materno, rut, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'ADM')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, nombre, apellido_paterno, apellido_materno, rut, password, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    TIPO_USUARIO = (
        ('EST', 'Estudiante'),
        ('DOC', 'Docente'),
        ('EMP', 'Empresa'),
        ('ADM', 'Administrador'),
    )

    nombre = models.CharField(max_length=50)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    rut = models.CharField(max_length=12, unique=True)
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=3, choices=TIPO_USUARIO, default='EST')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    sobre_mi = models.TextField(blank=True, null=True, verbose_name="Sobre mí")
    habilidades = models.TextField(blank=True, null=True, verbose_name="Habilidades (separadas por comas)")
    experiencia = models.TextField(blank=True, null=True, verbose_name="Experiencia o descripción laboral")
    industrias_interes = models.TextField(blank=True, null=True, verbose_name="Industrias de interés (separadas por comas)")
    tecnologias_preferidas = models.TextField(blank=True, null=True, verbose_name="Tecnologías preferidas (separadas por comas)")

    carrera = models.ForeignKey(
        'Carrera',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    sede = models.ForeignKey(
        'Sede',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios'
    )

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'apellido_paterno', 'apellido_materno', 'rut']

    def __str__(self):
        return f"{self.nombre} {self.apellido_paterno} ({self.get_rol_display()})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ['-date_joined']


# ----------------------------
# Catálogos institucionales
# ----------------------------
class Sede(AuditStampedModel):
    nombre = models.CharField(max_length=100, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    class Meta:
        verbose_name = "Sede"
        verbose_name_plural = "Sedes"
        ordering = ['nombre']


class Carrera(AuditStampedModel):
    nombre = models.CharField(max_length=120)
    codigo = models.CharField(max_length=10, unique=True)
    nivel = models.CharField(
        max_length=20,
        choices=[('T', 'Técnico'), ('P', 'Profesional')],
        default='P'
    )
    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name='carreras')
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre} - {self.sede.codigo}"

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['sede__codigo', 'nombre']
        unique_together = (('nombre', 'sede'),)


# ----------------------------
# Proyecto
# ----------------------------
class Proyecto(AuditStampedModel):
    TIPO_PROYECTO = (
        ('EST', 'Estudiantil'),
        ('DOC', 'Docente'),
        ('EMP', 'Empresarial'),
    )

    ESTADO = (
        ('BOR', 'Borrador'),
        ('REV', 'En revisión'),
        ('APR', 'Aprobado'),
        ('ACT', 'En ejecución / Activo'),
        ('DET', 'Detenido / En pausa'),
        ('FIN', 'Finalizado'),
        ('PUB', 'Publicado'),
        ('ARC', 'Archivado'),
    )

    titulo = models.CharField(max_length=255, db_index=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    resumen = models.TextField(max_length=500, help_text="Resumen ejecutivo")
    descripcion = models.TextField()

    tipo = models.CharField(max_length=3, choices=TIPO_PROYECTO, db_index=True)
    estado = models.CharField(max_length=3, choices=ESTADO, default='BOR', db_index=True)

    anio = models.PositiveIntegerField(
        validators=[MinValueValidator(1900), MaxValueValidator(2100)],
        db_index=True
    )

    autor = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='proyectos_creados'
    )

    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos'
    )

    sede = models.ForeignKey(
        Sede,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='proyectos'
    )

    palabras_clave = models.CharField(max_length=255, blank=True, null=True)
    documento_pdf = models.FileField(upload_to='proyectos/', null=True, blank=True)

    es_publico = models.BooleanField(default=False, db_index=True)

    def __str__(self):
        return f"{self.titulo} ({self.anio})"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.titulo}-{self.anio}")
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['estado', 'es_publico', 'anio']),
            models.Index(fields=['tipo', 'anio']),
        ]


# ----------------------------
# Solicitud de Empresa
# ----------------------------
class SolicitudEmpresa(AuditStampedModel):
    ESTADO_SOLICITUD = (
        ('REC', 'Recibida (pendiente de revisión)'),
        ('REV', 'En revisión por docente / comité'),
        ('APR', 'Aprobada internamente'),
        ('ASI', 'Asignada a estudiante(s)'),
        ('REJ', 'Rechazada'),
        ('FIN', 'Finalizada / cerrada'),
    )

    empresa = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='solicitudes_enviadas',
        limit_choices_to={'rol': 'EMP'}
    )

    titulo = models.CharField(max_length=255, db_index=True)
    descripcion = models.TextField(help_text="Detalle completo del desafío o necesidad de la empresa")
    sector = models.CharField(max_length=100, help_text="Ej: Logística, Energía, Retail, Salud, etc.", db_index=True)
    fecha_limite = models.DateField(null=True, blank=True)

    palabras_clave = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Ej: IA, logística, inventario, energía solar"
    )

    archivo_adjunto = models.FileField(
        upload_to='solicitudes_empresas/',
        null=True,
        blank=True,
        help_text="PDF, Excel, imágenes, etc."
    )

    estado = models.CharField(max_length=3, choices=ESTADO_SOLICITUD, default='REC', db_index=True)

    def __str__(self):
        return f"Solicitud #{self.id} - {self.titulo} ({self.empresa.email})"

    class Meta:
        verbose_name = "Solicitud de empresa"
        verbose_name_plural = "Solicitudes de empresa"
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['estado', 'sector']),
        ]


# ----------------------------
# Asignación Proyecto (flujo flexible)
# ----------------------------
class AsignacionProyecto(AuditStampedModel):
    solicitud = models.OneToOneField(
        SolicitudEmpresa,
        on_delete=models.CASCADE,
        related_name='asignacion'
    )

    docente_responsable = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        limit_choices_to={'rol': 'DOC'},
        related_name='proyectos_asignados_como_docente'
    )

    estudiantes = models.ManyToManyField(
        Usuario,
        limit_choices_to={'rol': 'EST'},
        related_name='proyectos_asignados_como_estudiante',
        blank=True
    )

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    estado = models.CharField(
        max_length=3,
        choices=[
            ('ACE', 'Aceptado por docente'),
            ('PRO', 'En progreso (con estudiantes activos)'),
            ('FIN', 'Finalizado por docente'),
            ('CAN', 'Cancelado / Rechazado'),
        ],
        default='ACE',
        db_index=True
    )

    comentarios_docente = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Asignación Solicitud #{self.solicitud.id} → Docente: {self.docente_responsable.email}"

    class Meta:
        verbose_name = "Asignación de proyecto"
        verbose_name_plural = "Asignaciones de proyectos"
        ordering = ['-updated_at', '-created_at']
        indexes = [
            models.Index(fields=['estado']),
        ]


# ------------------------------------------------------------
# HISTORIAL DE PARTICIPANTES EN PROYECTOS
# ------------------------------------------------------------
class HistorialProyectoParticipantes(models.Model):
    # --- Relaciones principales ---
    proyecto = models.ForeignKey(
        Proyecto,
        on_delete=models.CASCADE,
        related_name='historial_participantes'
    )
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='participaciones_proyectos'
    )

    # --- ROLES AGRUPADOS POR ÁREA ---
    ROLES = [
        # --- ÁREA TECNOLÓGICA ---
        ('LID', 'Líder del Proyecto / Scrum Master'),
        ('DEV', 'Desarrollador / Programador'),
        ('AI', 'Especialista en Inteligencia Artificial / Machine Learning'),
        ('DS', 'Científico/a de Datos'),
        ('UX', 'Diseñador UX/UI'),
        ('QA', 'Tester / Control de Calidad'),

        # --- ÁREA DE NEGOCIOS ---
        ('ANA', 'Analista de Negocios / Data Analyst'),
        ('PMO', 'Coordinador PMO / Gestión de Proyectos'),
        ('MKT', 'Especialista en Marketing Digital / Comercial'),
        ('FIN', 'Analista Financiero'),

        # --- ÁREA ACADÉMICA ---
        ('DOC', 'Docente Supervisor / Profesor Guía'),
        ('INV', 'Investigador / Innovación / I+D'),

        # --- ÁREA INDUSTRIAL ---
        ('LOG', 'Especialista en Logística / Supply Chain'),
        ('IOT', 'Integrador IoT / Automatización Industrial'),
    ]
    rol = models.CharField(max_length=10, choices=ROLES)

    # --- Fechas y estado de participación ---
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # --- Auditoría estándar ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='participaciones_creadas'
    )
    updated_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='participaciones_actualizadas'
    )

    class Meta:
        verbose_name = "Historial de Participación en Proyecto"
        verbose_name_plural = "Historial de Participaciones en Proyectos"
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.usuario} — {self.get_rol_display()} ({self.proyecto.titulo})"


# ------------------------------------------------------------
# REGISTRO DE EMPRESA
# ------------------------------------------------------------

class RegistroEmpresa(AuditStampedModel):
    """
    Registro de empresas sin login. Se crea un usuario EMP inactivo y
    se genera un enlace de seguimiento por UUID.
    """
    ESTADO = (
        ('PEN', 'Pendiente'),
        ('APR', 'Aprobada'),
        ('REJ', 'Rechazada'),
    )

    # Para seguimiento público
    uuid_seguimiento = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Datos visibles del formulario
    nombre_empresa = models.CharField(max_length=255)
    direccion_fiscal = models.CharField(max_length=255)
    nif_cif = models.CharField(max_length=20, verbose_name="NIF/CIF")
    telefono_contacto = models.CharField(max_length=30, blank=True, null=True)
    correo_contacto = models.EmailField(max_length=150)
    documento_adjunto = models.FileField(
        upload_to="empresas/documentos/",
        null=True,
        blank=True,
        help_text="Documento de respaldo (PDF o Word)."
    )

    # Estado workflow
    estado = models.CharField(max_length=3, choices=ESTADO, default="PEN", db_index=True)
    motivo_rechazo = models.TextField(blank=True, null=True)

    # Para trazabilidad de reenvíos/notificaciones
    email_tracking = models.EmailField(help_text="Correo que dejó el usuario para seguimiento.")

    def __str__(self):
        return f"{self.nombre_empresa} - {self.get_estado_display()}"

    class Meta:
        verbose_name = "Registro de Empresa"
        verbose_name_plural = "Registros de Empresas"
        ordering = ['-created_at']
        indexes = [models.Index(fields=['estado'])]


