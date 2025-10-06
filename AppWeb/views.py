from django.shortcuts import render

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