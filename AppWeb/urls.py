from django.urls import path
from AppWeb import views

urlpatterns = [
    path("", views.index, name="index"),
   path("nosotros/", views.nosotros, name="nosotros"),
   path("usuario/", views.usuario, name="usuario"),
   path("panel/", views.panel, name="panel"),
   path("proyectos/", views.proyectos, name="proyectos"),
   path("registro/", views.registro, name="registro"),
    path("login/", views.login, name="login"),
]