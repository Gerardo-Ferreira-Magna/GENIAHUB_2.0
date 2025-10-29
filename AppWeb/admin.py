from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Sede, Carrera, Proyecto, SolicitudEmpresa, AsignacionProyecto, HistorialProyectoParticipantes
from .models_audit import AuditLog

# ----------------------------
# USUARIO
# ----------------------------
@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('email', 'nombre', 'apellido_paterno', 'rol', 'rut', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_active', 'is_superuser')
    search_fields = ('email', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut')
    ordering = ('-date_joined',)

    fieldsets = (
        ('Información Personal', {
            'fields': ('nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'email', 'password', 'rol')
        }),
        ('Permisos y Accesos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Fechas Importantes', {
            'fields': ('last_login', 'date_joined')
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'rol',
                'password1', 'password2', 'is_active', 'is_staff', 'is_superuser'
            ),
        }),
    )


# ----------------------------
# Mixin de Auditoría
# ----------------------------
class AuditAdminMixin:
    """Automáticamente asigna created_by y updated_by desde el usuario logueado."""
    def save_model(self, request, obj, form, change):
        if not change or not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ----------------------------
# SEDE
# ----------------------------
@admin.register(Sede)
class SedeAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "codigo", "ciudad", "region", "activa", "updated_at")
    list_filter = ("activa", "region")
    search_fields = ("nombre", "codigo", "ciudad", "region")
    ordering = ("nombre",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ----------------------------
# CARRERA
# ----------------------------
@admin.register(Carrera)
class CarreraAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("nombre", "codigo", "nivel", "sede", "activa", "updated_at")
    list_filter = ("nivel", "activa", "sede")
    search_fields = ("nombre", "codigo", "sede__nombre")
    ordering = ("sede__codigo", "nombre")
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")


# ----------------------------
# PROYECTO
# ----------------------------
@admin.register(Proyecto)
class ProyectoAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = (
        "titulo", "tipo", "estado", "anio",
        "autor", "carrera", "sede", "es_publico", "updated_at"
    )
    list_filter = ("tipo", "estado", "anio", "es_publico", "sede")
    search_fields = ("titulo", "descripcion", "autor__email", "palabras_clave")
    ordering = ("-updated_at",)

    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by", "slug")

    fieldsets = (
        ("Información General", {
            "fields": ("titulo", "resumen", "descripcion", "tipo", "estado", "anio")
        }),
        ("Relaciones", {
            "fields": ("autor", "carrera", "sede")
        }),
        ("Configuración", {
            "fields": ("palabras_clave", "documento_pdf", "es_publico")
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("slug", "created_by", "updated_by", "created_at", "updated_at")
        }),
    )


# ----------------------------
# SOLICITUD DE EMPRESA
# ----------------------------
@admin.register(SolicitudEmpresa)
class SolicitudEmpresaAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("titulo", "empresa", "sector", "estado", "fecha_limite", "updated_at")
    list_filter = ("estado", "sector")
    search_fields = ("titulo", "descripcion", "empresa__email", "palabras_clave")
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Detalles de la Solicitud", {
            "fields": ("empresa", "titulo", "descripcion", "sector", "palabras_clave", "archivo_adjunto", "fecha_limite")
        }),
        ("Estado", {
            "fields": ("estado",)
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )


# ----------------------------
# ASIGNACIÓN DE PROYECTO
# ----------------------------
@admin.register(AsignacionProyecto)
class AsignacionProyectoAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = (
        "solicitud", "docente_responsable", "estado",
        "fecha_asignacion", "updated_at"
    )
    list_filter = ("estado",)
    search_fields = ("solicitud__titulo", "docente_responsable__email", "estudiantes__email")
    ordering = ("-updated_at",)
    filter_horizontal = ("estudiantes",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Vinculación", {
            "fields": ("solicitud", "docente_responsable", "estudiantes")
        }),
        ("Estado y Comentarios", {
            "fields": ("estado", "comentarios_docente")
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )


@admin.register(HistorialProyectoParticipantes)
class HistorialProyectoParticipantesAdmin(AuditAdminMixin, admin.ModelAdmin):
    list_display = ("proyecto", "usuario", "rol", "activo", "fecha_inicio", "fecha_fin", "updated_at")
    list_filter = ("rol", "activo", "fecha_inicio", "fecha_fin")
    search_fields = ("proyecto__titulo", "usuario__email", "usuario__nombre")
    ordering = ("-updated_at",)
    readonly_fields = ("created_at", "updated_at", "created_by", "updated_by")
    fieldsets = (
        ("Participación", {
            "fields": ("proyecto", "usuario", "rol", "fecha_inicio", "fecha_fin", "activo")
        }),
        ("Auditoría", {
            "classes": ("collapse",),
            "fields": ("created_by", "updated_by", "created_at", "updated_at")
        }),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("fecha_evento", "usuario", "accion", "modelo", "objeto_id", "user_agent")
    list_filter = ("accion", "modelo", "usuario")
    search_fields = ("usuario__email", "modelo", "objeto_id", "accion", "user_agent")
    ordering = ("-fecha_evento",)