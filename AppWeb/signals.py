import json
import threading
from datetime import datetime, date # ¡Importación necesaria para la serialización!
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.forms.models import model_to_dict

from .models import (
    Usuario, Proyecto, SolicitudEmpresa, AsignacionProyecto,
    HistorialProyectoParticipantes, Carrera, Sede
)
from .models_audit import AuditLog

# Thread-local para guardar "estado anterior" entre pre_save y post_save
_local = threading.local() 

# --- HELPERS ---
SENSITIVE_FIELDS = {"password", "documento_pdf", "archivo_adjunto"}

def _get_client_ip(request):
    if not request:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")

def _severity_for(action, status_code=None, model_name=None, user=None):
    if action in ("login_failed", "delete"):
        return "HIGH"
    if action in ("update", "create"):
        return "MEDIUM"
    if action in ("view", "login", "logout"):
        return "LOW"
    return "LOW"

def _scrub(d: dict):
    """
    Oculta campos sensibles y convierte objetos datetime a string ISO 8601
    para asegurar la serialización JSON.
    """
    if not d:
        return d
    dd = dict(d)
    
    for k in list(dd.keys()):
        v = dd[k]

        # 1. Manejo de campos sensibles
        if k in SENSITIVE_FIELDS:
            dd[k] = "***"
        
        # 2. Manejo de objetos de fecha y hora (CORRECCIÓN)
        elif isinstance(v, (datetime, date)):
            dd[k] = v.isoformat()
            
    return dd

def _model_name(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"

def _pk_str(instance):
    return str(getattr(instance, "pk", ""))

def _diff(old: dict, new: dict):
    if old is None and new is None:
        return ""
    old = old or {}
    new = new or {}
    lines = []
    keys = sorted(set(old.keys()) | set(new.keys()))
    for k in keys:
        ov = old.get(k)
        nv = new.get(k)
        if ov != nv:
            if k not in SENSITIVE_FIELDS:
                lines.append(f"* {k}: '{ov}' → '{nv}'")
    return "\n".join(lines)


# FUNCIÓN _LOG CORREGIDA
def _log(usuario_obj, request, 
         datos_antes=None, datos_despues=None, diff_text=None, 
         **payload):
    
    # Eliminar claves que no existen en AuditLog antes de mapear
    payload.pop('module', None) 
    payload.pop('status_code', None)

    # Mapeo de argumentos a nombres de campos del modelo AuditLog
    mapped_payload = {
        # Mapeo de campos de actor y sesión
        'usuario': usuario_obj,
        'session_key': (request.session.session_key if request and hasattr(request, "session") else None),
        'ip_origen': _get_client_ip(request),
        'user_agent': (request.META.get("HTTP_USER_AGENT") if request else None),
        
        # Mapeo de campos de modelo/objeto
        'modelo': payload.pop('object_model', None),
        'objeto_id': payload.pop('object_pk', None),
        'accion': payload.pop('action', None),
        
        # Mapeo de campos de método/url
        'metodo_http': payload.pop('method', None),
        'url': payload.pop('url', None),
        
        # Mapeo de campos de datos de cambio
        'datos_antes': datos_antes,
        'datos_despues': datos_despues,
        'diff': payload.pop('diff', diff_text),
        
        'severidad': payload.pop('severity', None),
        
        **payload
    }
    
    AuditLog.objects.create(**mapped_payload)


# --- SIGNALS AUTH ---
@receiver(user_logged_in)
def audit_login(sender, request, user, **kwargs):
    _log(user, request, 
         action="LOGIN",
         object_model="auth.session",
         object_pk=str(user.pk),
         url=getattr(request, "path", None),
         method=getattr(request, "method", None),
         severidad=_severity_for("login"))

@receiver(user_logged_out)
def audit_logout(sender, request, user, **kwargs):
    _log(user, request, 
         action="LOGOUT",
         object_model="auth.session",
         object_pk=str(user.pk),
         url=getattr(request, "path", None),
         method=getattr(request, "method", None),
         severidad=_severity_for("logout"))

@receiver(user_login_failed)
def audit_login_failed(sender, credentials, request, **kwargs):
    _log(None, request, 
         action="LOGIN",
         object_model="auth.session",
         object_pk=credentials.get("username") if credentials else None,
         url=getattr(request, "path", None),
         method=getattr(request, "method", None),
         severidad=_severity_for("login_failed"))

# --- SIGNALS MODELOS CLAVE ---
TRACKED = (Usuario, Proyecto, SolicitudEmpresa, AsignacionProyecto, HistorialProyectoParticipantes, Carrera, Sede)

@receiver(pre_save)
def audit_presave(sender, instance, **kwargs):
    if sender not in TRACKED:
        return
        
    # Inicialización de 'before' (Corrección del Attribute Error)
    if not hasattr(_local, 'before'):
        _local.before = {}

    try:
        old = sender.objects.get(pk=instance.pk)
        # _scrub se llama aquí para sanitizar los datos antes de guardarlos en thread-local
        _local.before[_pk_str(instance) + ":" + _model_name(instance)] = _scrub(model_to_dict(old))
    except sender.DoesNotExist:
        _local.before[_pk_str(instance) + ":" + _model_name(instance)] = None

@receiver(post_save)
def audit_postsave(sender, instance, created, **kwargs):
    if sender not in TRACKED:
        return
        
    if not hasattr(_local, 'before'):
        _local.before = {}
        
    key = _pk_str(instance) + ":" + _model_name(instance)
    before = _local.before.pop(key, None)
    after = _scrub(model_to_dict(instance))
    action = "CREATE" if created else "UPDATE" 

    _log(None, None,
        datos_antes=before,
        datos_despues=after,
        diff_text=_diff(before, after),
        
        action=action,
        object_model=_model_name(instance),
        object_pk=_pk_str(instance),
        severidad=_severity_for(action.lower())
    )

@receiver(pre_delete)
def audit_predelete(sender, instance, **kwargs):
    if sender not in TRACKED:
        return
        
    if not hasattr(_local, 'before'):
        _local.before = {}
        
    _local.before["DEL:" + _pk_str(instance) + ":" + _model_name(instance)] = _scrub(model_to_dict(instance))

@receiver(post_delete)
def audit_postdelete(sender, instance, **kwargs):
    if sender not in TRACKED:
        return
        
    if not hasattr(_local, 'before'):
        _local.before = {}
        
    key = "DEL:" + _pk_str(instance) + ":" + _model_name(instance)
    before = _local.before.pop(key, None)
    
    _log(None, None,
        datos_antes=before,
        datos_despues=None,
        diff_text=_diff(before, None),
        
        action="DELETE",
        object_model=_model_name(instance),
        object_pk=_pk_str(instance),
        severidad=_severity_for("delete")
    )