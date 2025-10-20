from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from .forms import RegistroForm, LoginForm
from django.contrib.auth.decorators import login_required
from .models import Usuario


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