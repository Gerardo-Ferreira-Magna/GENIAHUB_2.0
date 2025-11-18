from django.urls import path
from AppWeb import views
from .views_audit import auditoria_dashboard
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path("", views.index, name="index"),
    path("nosotros/", views.nosotros, name="nosotros"),
    path("tareas/", views.tareas, name="tareas"),
    path("proyectos/", views.proyectos, name="proyectos"),
    path("registro/", views.registro, name="registro"),
    path("login/", views.login, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("panel/", views.panel, name="panel"),
    path("usuarios/", views.usuarios_panel, name="usuarios_panel"),
    path("api/usuario/<int:pk>/", views.usuario_detail_api, name="usuario_detail_api"),
    path("api/usuario/<int:pk>/update/", views.usuario_update_api, name="usuario_update_api"),
    path("api/usuario/<int:pk>/delete/", views.usuario_delete_api, name="usuario_delete_api"),
    path("registro_empresa/", views.registro_empresa, name="registro_empresa"),
    path("estado-solicitud/<uuid:uuid>/", views.estado_solicitud, name="estado_solicitud"),
    path("estado-solicitud/<uuid:uuid>/reenviar/", views.reenviar_estado, name="reenviar_estado"),
    path("panel/solicitudes/", views.panel_solicitudes, name="panel_solicitudes"),
    path("panel/solicitudes/<int:pk>/<str:nuevo_estado>/",views.cambiar_estado_solicitud,name="cambiar_estado_solicitud"),
    path("solicitudes/<int:pk>/editar/", views.editar_solicitud, name="editar_solicitud"),
    path("auditoria_dashboard", auditoria_dashboard, name="auditoria_dashboard"),
    path("api/registro-empresa/exists/", views.verificar_solicitud, name="verificar_solicitud"),
    path("api/registro-empresa/create/", views.crear_solicitud, name="crear_solicitud"),
    path('api/usuario/create/', views.usuario_create_api, name='usuario_create_api'),
    path("perfil/estudiante/", views.perfil_estudiante, name="perfil_estudiante"),
    path("perfil/estudiante/", views.perfil_estudiante, name="perfil_estudiante"),
    path("perfil/estudiante/<int:pk>/", views.perfil_estudiante, name="perfil_estudiante_detalle"),
    path("perfil/editar/", views.editar_perfil, name="perfil_editar"),
    path("perfiles/", views.busqueda_perfiles, name="busqueda_perfiles"),
    path("api/perfiles/buscar/", views.buscar_perfiles_ajax, name="buscar_perfiles_ajax"),
    path("creacion_proyecto/", views.crear_proyecto, name="creacion_proyecto"),
    path("proyecto/editar/", views.proyecto_editar_modal, name="proyecto_editar_modal"),
    path("proyecto/eliminar/", views.proyecto_eliminar_modal, name="proyecto_eliminar_modal"),
    path("solicitud_empresa/", views.solicitud_empresa_crear, name="solicitud_empresa_crear"),
    path("empresa/estado-solicitud/", views.empresa_estado_solicitud, name="empresa_estado_solicitud"),
    path("proyectos/tabla/", views.proyectos_tabla, name="proyectos_tabla"),
    path("asistente-ia/", views.asistente_ia, name="asistente_ia"),
    path("asistente-ia/api/", views.asistente_ia_api, name="asistente_ia_api"),
    path("generar_pdf/", views.generar_pdf, name="generar_pdf"),
    path("generar_ppt/", views.generar_ppt, name="generar_ppt"),
    path("generar_excel/", views.generar_excel, name="generar_excel"),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)