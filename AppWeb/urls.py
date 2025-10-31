from django.urls import path
from AppWeb import views
from .views_audit import auditoria_dashboard

urlpatterns = [
    path("", views.index, name="index"),
    path("nosotros/", views.nosotros, name="nosotros"),
    path("tareas/", views.tareas, name="tareas"),
    path("panel/", views.panel, name="panel"),
    path("proyectos/", views.proyectos, name="proyectos"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path('usuarios/', views.usuarios_panel, name='usuarios_panel'),
    path('api/usuario/<int:pk>/', views.usuario_detail_api, name='usuario_detail_api'),
    path('api/usuario/<int:pk>/update/', views.usuario_update_api, name='usuario_update_api'),
    path('api/usuario/<int:pk>/delete/', views.usuario_delete_api, name='usuario_delete_api'),
    path("auditoria_dashboard", auditoria_dashboard, name="auditoria_dashboard"),
]