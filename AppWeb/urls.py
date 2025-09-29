from django.urls import path
from AppWeb import views

urlpatterns = [
    path("", views.index, name="index"),
   path("nosotros/", views.nosotros, name="nosotros"),
   path("usuario/", views.usuario, name="usuario"),
]