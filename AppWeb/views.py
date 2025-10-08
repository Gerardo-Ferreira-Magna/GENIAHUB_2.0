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
    return render(request, "webs/proyectos.html")


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
                return redirect('panel')
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