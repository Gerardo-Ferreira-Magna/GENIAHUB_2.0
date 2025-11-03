# ============================================================
# 📦 IMPORTS
# ============================================================

# --- Python estándar ---
import json  # Usado en usuario_update_api

# --- Django Core / HTTP / Utilidades ---
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.middleware.csrf import get_token
from django.utils.timezone import now, timedelta
from django.db.models import Q, Count, Avg


# --- Django Autenticación / Permisos ---
from django.contrib.auth import authenticate, login as auth_login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required

# --- Django Mensajes y Validaciones ---
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods

# --- Django Configuración / Sitio / Email ---
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.urls import reverse
from django.utils.crypto import get_random_string

# --- Modelos y Formularios ---
from .models import Usuario, RegistroEmpresa
from .models_audit import AuditLog
from .forms import RegistroForm, LoginForm, RegistroEmpresaForm
from .models import RegistroEmpresa

# ============================================================
# VISTAS PÚBLICAS BÁSICAS
# ============================================================

def index(request):
    """Página de inicio."""
    return render(request, "webs/index.html")

def nosotros(request):
    """Página 'Sobre nosotros'."""
    return render(request, "webs/nosotros.html")

def tareas(request):
    """Vista de tareas (en desarrollo)."""
    return render(request, "webs/tareas.html")

def panel(request):
    """Vista panel (general, posiblemente duplicada con la versión autenticada)."""
    return render(request, "webs/panel.html")


# ============================================================
# 🏢 REGISTRO DE EMPRESA SIN LOGIN
# ============================================================

def _enviar_correo_estado(request, registro: RegistroEmpresa):
    """
    Enviar correo con el enlace de seguimiento de solicitud de empresa.
    Maneja automáticamente el dominio local si no hay Site configurado.
    """
    try:
        dominio = get_current_site(request).domain
    except Site.DoesNotExist:
        dominio = "127.0.0.1:8000"

    link = f"http://{dominio}{reverse('estado_solicitud', args=[registro.uuid_seguimiento])}"
    asunto = "Seguimiento de tu solicitud - GENIAHUB"
    mensaje = (
        f"Hola,\n\n"
        f"Gracias por registrar a {registro.nombre_empresa} en GENIAHUB.\n"
        f"Puedes revisar el estado de tu solicitud aquí:\n{link}\n\n"
        f"Saludos,\nEquipo GENIAHUB"
    )

    send_mail(
        subject=asunto,
        message=mensaje,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@geniahub.cl"),
        recipient_list=[registro.email_tracking],
        fail_silently=True,
    )


def registro_empresa(request):
    """
    Permite enviar solicitud sin login. 
    Crea o reutiliza un usuario EMP inactivo y guarda un registro con estado 'PEN'.
    """
    if request.method == 'POST':
        form = RegistroEmpresaForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            email = data['correo_contacto']
            UserModel = get_user_model()

            # Si ya existe una solicitud pendiente, mostrar modal "en proceso"
            if RegistroEmpresa.objects.filter(email_tracking=email, estado="PEN").exists():
                messages.warning(request, "Ya tienes una solicitud en proceso de revisión.")
                return render(request, 'webs/registro_empresa.html', {'form': form})

            # Crear o reutilizar usuario EMP inactivo
            user, created = UserModel.objects.get_or_create(
                email=email,
                defaults={
                    'nombre': data['nombre_empresa'],
                    'apellido_paterno': 'Empresa',
                    'apellido_materno': 'GENIAHUB',
                    'rut': get_random_string(9),  # dummy
                    'rol': 'EMP',
                    'is_active': False,
                }
            )

            # Si ya existía, asegurar estado EMP e inactividad
            if not created:
                if getattr(user, 'rol', None) != 'EMP':
                    user.rol = 'EMP'
                user.is_active = False
                user.save(update_fields=['rol', 'is_active'])

            # Crear registro
            registro = form.save(commit=False)
            registro.created_by = user
            registro.updated_by = user
            registro.email_tracking = email
            registro.estado = "PEN"
            registro.save()

            # Enviar correo
            _enviar_correo_estado(request, registro)

            # Mensaje para mostrar modal de éxito
            messages.success(request, "Tu solicitud fue enviada correctamente.")
            return render(request, "webs/solicitud_enviada.html", {"correo": email})
        else:
            messages.error(request, "⚠️ Revisa los campos e intenta nuevamente.")
    else:
        form = RegistroEmpresaForm()

    return render(request, 'webs/registro_empresa.html', {'form': form})


def estado_solicitud(request, uuid):
    """Permite a la empresa revisar el estado actual de su solicitud."""
    solicitud = get_object_or_404(RegistroEmpresa, uuid_seguimiento=uuid)
    return render(request, 'webs/estado_solicitud.html', {'solicitud': solicitud})


def reenviar_estado(request, uuid):
    """Permite reenviar el enlace de seguimiento al correo registrado."""
    solicitud = get_object_or_404(RegistroEmpresa, uuid_seguimiento=uuid)
    _enviar_correo_estado(request, solicitud)
    messages.success(request, "📧 Enlace reenviado al correo registrado.")
    return redirect('estado_solicitud', uuid=uuid)


# ============================================================
# 🧩 PANEL DE SOLICITUDES (SOLO ADMINISTRADORES)
# ============================================================

@staff_member_required
def panel_solicitudes(request):
    """Lista todas las solicitudes de empresas para revisión interna."""
    solicitudes = RegistroEmpresa.objects.all().order_by('-created_at')
    return render(request, 'webs/panel_solicitudes.html', {'solicitudes': solicitudes})


@staff_member_required
def cambiar_estado_solicitud(request, pk, nuevo_estado):
    """Permite a un administrador aprobar o rechazar una solicitud."""
    solicitud = get_object_or_404(RegistroEmpresa, pk=pk)
    solicitud.estado = nuevo_estado
    solicitud.save(update_fields=['estado'])
    _enviar_correo_estado(request, solicitud)
    messages.success(request, f"✅ Estado cambiado a {solicitud.get_estado_display()}")
    return redirect('panel_solicitudes')


# ============================================================
# 📚 PROYECTOS (DEMOS / VISTA PÚBLICA)
# ============================================================

def proyectos(request):
    """Proyectos de ejemplo con sugerencias IA (datos mock)."""
    proyectos = [
        {"id": 1, "nombre": "GENIA HUB - Plataforma de Innovación Académica", "docente": "Gerardo Ferreira", "estado": "En Desarrollo",
         "estado_icono": "bi-unlock-fill", "estado_color": "success", "fecha_modificacion": "Oct 15",
         "imagen_url": "/static/img/proyecto_geniahub.jpg", "categoria": "Informática",
         "descripcion": "Plataforma web que centraliza proyectos académicos y empresariales usando IA para emparejar estudiantes y empresas."},
        # ... (mantener tus proyectos existentes)
    ]

    recomendaciones_ia = [
        {"titulo": "Proyectos relacionados con tus habilidades", "descripcion": "Basado en tu perfil técnico (Python, Django, BI).", "icono": "bi-stars"},
        {"titulo": "Proyectos con mayor demanda", "descripcion": "Estos proyectos tienen más vacantes disponibles.", "icono": "bi-fire"},
        {"titulo": "Proyectos interdisciplinarios", "descripcion": "Combinan IA con logística o sostenibilidad.", "icono": "bi-diagram-3"}
    ]

    return render(request, "webs/proyectos.html", {
        "proyectos": proyectos,
        "recomendaciones_ia": recomendaciones_ia
    })


# ============================================================
# 👤 REGISTRO / LOGIN / LOGOUT DE USUARIOS
# ============================================================

def registro(request):
    """Registro de nuevos usuarios."""
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Usuario creado con éxito. Ya puedes iniciar sesión.")
            return redirect("login")
        else:
            messages.error(request, "❌ Corrige los errores indicados abajo.")
    else:
        form = RegistroForm()
    return render(request, "webs/registro.html", {"form": form})


def login(request):
    """Inicio de sesión."""
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, email=email, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"👋 Bienvenido {user.nombre} {user.apellido_paterno}")
                return redirect('proyectos')
            else:
                messages.error(request, "❌ Correo o contraseña incorrectos.")
    else:
        form = LoginForm()
    return render(request, 'webs/login.html', {'form': form})


def logout_view(request):
    """Cerrar sesión."""
    logout(request)
    messages.success(request, "👋 Has cerrado sesión correctamente.")
    return redirect('login')


# ============================================================
# ⚙️ PANEL DE ADMINISTRACIÓN DE USUARIOS
# ============================================================

@login_required(login_url='login')
def panel(request):
    """Panel general del usuario autenticado."""
    return render(request, 'webs/panel.html', {'usuario': request.user})


def staff_required(view_func):
    """Decorador auxiliar para vistas staff personalizadas."""
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/login/')(view_func)


@staff_required
def usuarios_panel(request):
    """Panel de gestión de usuarios para staff."""
    qs = Usuario.objects.all().order_by(request.GET.get('sort', '-date_joined'))
    exclude_super = request.GET.get('exclude_super', '1')
    if exclude_super == '1':
        qs = qs.exclude(is_superuser=True)

    # Filtros dinámicos
    q = request.GET.get('q')
    if q:
        qs = qs.filter(
            Q(nombre__icontains=q) |
            Q(apellido_paterno__icontains=q) |
            Q(apellido_materno__icontains=q)
        )
    rut = request.GET.get('rut')
    if rut:
        qs = qs.filter(rut__icontains=rut)
    email = request.GET.get('email')
    if email:
        qs = qs.filter(email__icontains=email)
    rol = request.GET.get('rol')
    if rol:
        qs = qs.filter(rol=rol)
    activo = request.GET.get('activo')
    if activo in ('0', '1'):
        qs = qs.filter(is_active=(activo == '1'))
    staff = request.GET.get('staff')
    if staff in ('0', '1'):
        qs = qs.filter(is_staff=(staff == '1'))

    # Paginación
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # URLs dinámicas admin
    admin_user_change_url = f"admin:{Usuario._meta.app_label}_{Usuario._meta.model_name}_change"
    admin_user_add_url = f"admin:{Usuario._meta.app_label}_{Usuario._meta.model_name}_add"

    csrf_token = get_token(request)

    return render(request, 'webs/usuarios_panel.html', {
        'page_obj': page_obj,
        'admin_user_change_url': admin_user_change_url,
        'admin_user_add_url': admin_user_add_url,
        'csrf_token': csrf_token,
    })


# ============================================================
# 🧾 API USUARIOS (DETALLE / UPDATE / DELETE)
# ============================================================

@staff_required
def usuario_detail_api(request, pk):
    """API: devuelve detalle de un usuario."""
    u = get_object_or_404(Usuario, pk=pk)
    data = {
        "id": u.id,
        "nombre": u.nombre,
        "apellido_paterno": u.apellido_paterno,
        "apellido_materno": u.apellido_materno,
        "rut": u.rut,
        "email": u.email,
        "rol": u.rol,
        "is_active": u.is_active,
        "is_staff": u.is_staff,
        "date_joined": u.date_joined.isoformat(),
    }
    return JsonResponse({"ok": True, "usuario": data})


@staff_required
@require_http_methods(["POST"])
def usuario_update_api(request, pk):
    """API: actualiza usuario via JSON."""
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    u = get_object_or_404(Usuario, pk=pk)
    campos = ['nombre', 'apellido_paterno', 'apellido_materno', 'rut', 'email', 'rol', 'is_active', 'is_staff']
    for f in campos:
        if f in data:
            setattr(u, f, data[f])

    pwd = data.get('password')
    pwd_confirm = data.get('password_confirm')
    if pwd or pwd_confirm:
        if pwd != pwd_confirm:
            return JsonResponse({"ok": False, "error": "Las contraseñas no coinciden"}, status=400)
        if len(pwd) < 6:
            return JsonResponse({"ok": False, "error": "La contraseña debe tener al menos 6 caracteres"}, status=400)
        u.set_password(pwd)

    u.save()
    return JsonResponse({"ok": True, "message": "Usuario actualizado", "usuario_id": u.id})


@staff_required
@require_POST
def usuario_delete_api(request, pk):
    """API: elimina usuario (seguro para no borrar superusuarios)."""
    u = get_object_or_404(Usuario, pk=pk)
    if u.is_superuser:
        return JsonResponse({"ok": False, "error": "No se puede eliminar un superusuario"}, status=403)
    u.delete()
    return JsonResponse({"ok": True, "message": "Usuario eliminado"})


# ============================================================
@require_POST
def verificar_solicitud(request):
    """
    Verifica si ya existe una solicitud 'PEN' para el correo o el NIF/CIF.
    Devuelve: { exists_email, exists_nif, exists_any }
    """
    correo = (request.POST.get('correo') or '').strip()
    nif_cif = (request.POST.get('nif_cif') or '').strip()

    q = RegistroEmpresa.objects.filter(estado="PEN")
    exists_email = bool(correo) and q.filter(email_tracking__iexact=correo).exists()
    exists_nif   = bool(nif_cif) and q.filter(nif_cif__iexact=nif_cif).exists()

    return JsonResponse({
        "exists_email": exists_email,
        "exists_nif": exists_nif,
        "exists_any": exists_email or exists_nif
    })


@require_POST
def crear_solicitud(request):
    """
    Crea la solicitud real en BD usando el mismo Form (soporta archivo).
    Devuelve: { ok: True } o { ok: False, errors: {...} }
    """
    form = RegistroEmpresaForm(request.POST, request.FILES)
    if not form.is_valid():
        # Retorna errores del form para mostrarlos en el front
        return JsonResponse({"ok": False, "errors": form.errors}, status=400)

    data = form.cleaned_data

    # Crear o reutilizar usuario EMP inactivo
    email = data.get('correo_contacto')
    UserModel = get_user_model()
    user, created = UserModel.objects.get_or_create(
        email=email,
        defaults={
            'nombre': data.get('nombre_empresa') or 'Empresa',
            'apellido_paterno': 'Empresa',
            'apellido_materno': 'GENIAHUB',
            'rut': get_random_string(9),  # dummy
            'rol': 'EMP',
            'is_active': False,
        }
    )
    if not created:
        changed = False
        if getattr(user, 'rol', None) != 'EMP':
            user.rol = 'EMP'
            changed = True
        if user.is_active:
            user.is_active = False
            changed = True
        if changed:
            user.save(update_fields=['rol', 'is_active'])

    # Crear el registro
    registro = form.save(commit=False)
    registro.created_by = user
    registro.updated_by = user
    registro.email_tracking = email
    registro.estado = "PEN"
    registro.save()

    # Si quieres: _enviar_correo_estado(request, registro)

    return JsonResponse({"ok": True})


# === PANEL DE SOLICITUDES ===
def panel_solicitudes(request):
    """Listado de solicitudes de empresas"""
    solicitudes = RegistroEmpresa.objects.all().order_by('-created_at')
    return render(request, 'webs/panel_solicitudes.html', {'solicitudes': solicitudes})


# === EDITAR SOLICITUD ===
def editar_solicitud(request, pk):
    """Permite editar los datos de una solicitud (empresa, correo, NIF/CIF, estado, motivo)"""
    solicitud = get_object_or_404(RegistroEmpresa, pk=pk)

    if request.method == 'POST':
        solicitud.nombre_empresa = request.POST.get('nombre_empresa', solicitud.nombre_empresa)
        solicitud.nif_cif = request.POST.get('nif_cif', solicitud.nif_cif)
        solicitud.email_tracking = request.POST.get('correo_contacto', solicitud.email_tracking)
        solicitud.estado = request.POST.get('estado', solicitud.estado)
        solicitud.motivo_rechazo = request.POST.get('motivo_rechazo', solicitud.motivo_rechazo)

        solicitud.save()

        # Mensaje dinámico según el nuevo estado
        if solicitud.estado == 'APR':
            messages.success(request, f"✅ La solicitud de {solicitud.nombre_empresa} fue aprobada correctamente.")
        elif solicitud.estado == 'REJ':
            messages.warning(request, f"⚠️ La solicitud de {solicitud.nombre_empresa} fue rechazada.")
        else:
            messages.info(request, f"✏️ La solicitud de {solicitud.nombre_empresa} fue actualizada.")

        return redirect('panel_solicitudes')

    return redirect('panel_solicitudes')


# === CAMBIAR ESTADO (Aprobar / Rechazar) ===
def cambiar_estado_solicitud(request, pk, nuevo_estado):
    """Cambia el estado de una solicitud a Aprobado o Rechazado"""
    solicitud = get_object_or_404(RegistroEmpresa, pk=pk)

    # Validar el nuevo estado
    if nuevo_estado not in ['APR', 'REJ', 'PEN']:
        messages.error(request, "Estado inválido.")
        return redirect('panel_solicitudes')

    solicitud.estado = nuevo_estado

    # Si se rechaza sin motivo, asignar texto por defecto
    if nuevo_estado == 'REJ' and not solicitud.motivo_rechazo:
        solicitud.motivo_rechazo = "Rechazada por revisión interna."

    solicitud.save()

    if nuevo_estado == 'APR':
        messages.success(request, f"✅ Solicitud de {solicitud.nombre_empresa} aprobada.")
    elif nuevo_estado == 'REJ':
        messages.warning(request, f"⚠️ Solicitud de {solicitud.nombre_empresa} rechazada.")
    else:
        messages.info(request, f"📋 Estado actualizado para {solicitud.nombre_empresa}.")

    return redirect('panel_solicitudes')