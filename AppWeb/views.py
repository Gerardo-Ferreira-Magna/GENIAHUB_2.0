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

