import json # Necesario dentro de usuario_update_api

from django.http import JsonResponse 
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.views.decorators.http import require_POST, require_http_methods
from django.contrib.auth.decorators import user_passes_test
from django.middleware.csrf import get_token
from django.utils.timezone import now, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from .forms import RegistroForm, LoginForm
from .models import Usuario
from .models_audit import AuditLog

# Vista Index
def index(request):
    return render(request, "webs/index.html")

# Vista Nosotros
def nosotros(request):
    return render(request, "webs/nosotros.html")


# Vista usuario
def usuario(request):
    return render(request, "webs/usuario.html")


# Vista panel
def panel(request):
    return render(request, "webs/panel.html")


# Vista proyectos
def proyectos(request):
    proyectos = [
        {"id": 1, "nombre": "GENIA HUB - Plataforma de Innovación Académica", "docente": "Gerardo Ferreira", "estado": "En Desarrollo",
         "estado_icono": "bi-unlock-fill", "estado_color": "success", "fecha_modificacion": "Oct 15",
         "imagen_url": "/static/img/proyecto_geniahub.jpg", "categoria": "Informática",
         "descripcion": "Plataforma web que centraliza proyectos académicos y empresariales usando IA para emparejar estudiantes y empresas."},

        {"id": 2, "nombre": "Sistema Predictivo de Mantenimiento Industrial", "docente": "Andrea Soto", "estado": "En Proceso",
         "estado_icono": "bi-hourglass-split", "estado_color": "warning", "fecha_modificacion": "Sep 30",
         "imagen_url": "/static/img/proyecto_mantenimiento.jpg", "categoria": "Mecánica",
         "descripcion": "Modelo predictivo basado en machine learning que anticipa fallas en maquinaria industrial."},

        {"id": 3, "nombre": "Asistente Virtual para Estudiantes (Chat IA)", "docente": "Camila Rojas", "estado": "En Desarrollo",
         "estado_icono": "bi-robot", "estado_color": "info", "fecha_modificacion": "Sep 20",
         "imagen_url": "/static/img/proyecto_ia.jpg", "categoria": "Tecnología Aplicada",
         "descripcion": "Chatbot educativo que guía a los estudiantes en sus consultas académicas utilizando IA conversacional."},

        {"id": 4, "nombre": "Optimización Logística con Visión Computacional", "docente": "Paula Méndez", "estado": "Finalizado",
         "estado_icono": "bi-lock-fill", "estado_color": "danger", "fecha_modificacion": "Ago 28",
         "imagen_url": "/static/img/proyecto_logistica.jpg", "categoria": "Logística",
         "descripcion": "Sistema de conteo de cajas en tiempo real mediante visión computacional y cámaras IP."},

        {"id": 5, "nombre": "Monitor de Energía Solar Inteligente", "docente": "Javier Morales", "estado": "En Desarrollo",
         "estado_icono": "bi-sun", "estado_color": "success", "fecha_modificacion": "Ago 05",
         "imagen_url": "/static/img/proyecto_solar.jpg", "categoria": "Energía",
         "descripcion": "Plataforma IoT que monitorea el rendimiento de paneles solares en instituciones educativas."},

        {"id": 6, "nombre": "Dashboard de Indicadores Financieros", "docente": "Lucía Herrera", "estado": "En Proceso",
         "estado_icono": "bi-bar-chart", "estado_color": "primary", "fecha_modificacion": "Jul 18",
         "imagen_url": "/static/img/proyecto_finanzas.jpg", "categoria": "Administración",
         "descripcion": "Dashboard Power BI para monitorear KPIs de rendimiento financiero empresarial."},

        {"id": 7, "nombre": "Control de Inventario con RFID", "docente": "Mauricio Silva", "estado": "Finalizado",
         "estado_icono": "bi-lock-fill", "estado_color": "danger", "fecha_modificacion": "Jun 10",
         "imagen_url": "/static/img/proyecto_rfid.jpg", "categoria": "Logística",
         "descripcion": "Sistema de control de inventario basado en etiquetas RFID y dashboard analítico."},

        {"id": 8, "nombre": "Plataforma de Aprendizaje Adaptativo", "docente": "María López", "estado": "En Desarrollo",
         "estado_icono": "bi-unlock-fill", "estado_color": "success", "fecha_modificacion": "May 25",
         "imagen_url": "/static/img/proyecto_educativo.jpg", "categoria": "Educación",
         "descripcion": "Sistema educativo con IA que ajusta contenidos según el progreso del estudiante."},
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


# Vista registro
def registro(request):
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


# Vista login
def login(request):
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


# --- LOGOUT ---
def logout_view(request):
    logout(request)
    messages.success(request, "👋 Has cerrado sesión correctamente.")
    return redirect('login')


# -------------------------------------
# PANEL (SOLO PARA USUARIOS AUTENTICADOS)
# -------------------------------------
@login_required(login_url='login')
def panel(request):
    return render(request, 'webs/panel.html', {'usuario': request.user})


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url='/login/')(view_func)

@staff_required
def usuarios_panel(request):
    # Filtros
    qs = Usuario.objects.all().order_by(request.GET.get('sort', '-date_joined'))

    # OPCIÓN: excluir superusuarios del listado (evita que admin "se vea")
    exclude_super = request.GET.get('exclude_super', '1')  # por defecto excluir
    if exclude_super == '1':
        qs = qs.exclude(is_superuser=True)

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
    if activo in ('0','1'):
        qs = qs.filter(is_active=(activo == '1'))
    staff = request.GET.get('staff')
    if staff in ('0','1'):
        qs = qs.filter(is_staff=(staff == '1'))

    # paginación
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # URLs admin dinámicas (si aún quieres botón "Nuevo usuario" que vaya al admin)
    admin_user_change_url = f"admin:{Usuario._meta.app_label}_{Usuario._meta.model_name}_change"
    admin_user_add_url    = f"admin:{Usuario._meta.app_label}_{Usuario._meta.model_name}_add"

    # CSRF token para JS
    csrf_token = get_token(request)

    return render(request, 'webs/usuarios_panel.html', {
        'page_obj': page_obj,
        'admin_user_change_url': admin_user_change_url,
        'admin_user_add_url': admin_user_add_url,
        'csrf_token': csrf_token,
    })

@staff_required
def usuario_detail_api(request, pk):
    u = get_object_or_404(Usuario, pk=pk)
    # no incluir password en la respuesta
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
    import json
    u = get_object_or_404(Usuario, pk=pk)
    # Parsear payload JSON
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    # Campos editables (lista explícita por seguridad)
    fields = ['nombre','apellido_paterno','apellido_materno','rut','email','rol','is_active','is_staff']
    for f in fields:
        if f in data:
            setattr(u, f, data[f])

    # Manejo de password: si viene no vacío => set_password
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
    u = get_object_or_404(Usuario, pk=pk)
    # evitar borrar al propio superuser accidentalmente
    if u.is_superuser:
        return JsonResponse({"ok": False, "error": "No se puede eliminar un superusuario"}, status=403)
    u.delete()
    return JsonResponse({"ok": True, "message": "Usuario eliminado"})
