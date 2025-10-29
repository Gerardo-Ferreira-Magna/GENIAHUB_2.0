# AppWeb/middleware.py
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple, Optional

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.http import HttpRequest, HttpResponse
from django.urls import resolve, ResolverMatch

from .models_audit import AuditLog


EXCLUDED_PREFIXES_DEFAULT = (
    "/admin/",
    "/static/",
    "/media/",
    "/favicon.ico",
    "/robots.txt",
    "/api/healthcheck/",
)

# Claves sensibles a ofuscar si aparecen en cuerpos JSON/form
SENSITIVE_KEYS = {
    "password",
    "password1",
    "password2",
    "old_password",
    "new_password",
    "token",
    "csrfmiddlewaretoken",
    "authorization",
    "secret",
    "api_key",
    "apikey",
    "key",
}

# Para detectar IDs en kwargs o paths
PK_CANDIDATES = ("pk", "id", "uuid", "slug")


def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Obtiene IP real considerando X-Forwarded-For / X-Real-IP."""
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        # toma el primero (cliente) sin espacios
        return xff.split(",")[0].strip()
    xri = request.META.get("HTTP_X_REAL_IP")
    if xri:
        return xri.strip()
    return request.META.get("REMOTE_ADDR")


def is_excluded_path(path: str, extra: Tuple[str, ...]) -> bool:
    for p in EXCLUDED_PREFIXES_DEFAULT + extra:
        if path.startswith(p):
            return True
    return False


def scrub_value(val: Any) -> Any:
    """Ofusca valores potencialmente sensibles."""
    if isinstance(val, (dict, list)):
        return scrub_payload(val)
    if isinstance(val, str):
        if len(val) <= 4:
            return "***"
        # muestra primeras/últimas 2 chars máximo
        return f"{val[:2]}***{val[-2:]}"
    return "***"


def scrub_payload(data: Any) -> Any:
    """Ofusca claves sensibles en payload JSON/dict/list."""
    try:
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                if k and str(k).lower() in SENSITIVE_KEYS:
                    clean[k] = scrub_value(v)
                else:
                    clean[k] = scrub_payload(v)
            return clean
        if isinstance(data, list):
            return [scrub_payload(x) for x in data]
    except Exception:
        pass
    return data


def coerce_json(obj: Any, max_len: int = 10_000) -> Any:
    """Intenta serializar a JSON; trunca si es muy grande."""
    try:
        s = json.dumps(obj, ensure_ascii=False, default=str)
        if len(s) > max_len:
            return {"__truncated__": True, "size": len(s)}
        return json.loads(s)
    except Exception:
        # Como fallback, devuelve string truncada
        txt = str(obj)
        if len(txt) > max_len:
            txt = txt[:max_len] + "…(truncated)"
        return {"__nonjson__": True, "value": txt}


def infer_object_ref(request: HttpRequest) -> Tuple[str, str]:
    """
    Intenta inferir modelo/objeto_id:
    - Usa resolver_match.view_name / func.__qualname__
    - Toma pk/id/uuid/slug de kwargs o de la URL con regex
    """
    modelo = ""
    objeto_id = ""

    try:
        match: ResolverMatch = resolve(request.path_info)
        # nombre de vista (namespace:view) o callable
        if match.view_name:
            modelo = match.view_name
        else:
            modelo = getattr(match.func, "__qualname__", "") or getattr(match.func, "__name__", "")

        # Busca en kwargs
        for key in PK_CANDIDATES:
            if key in match.kwargs:
                objeto_id = str(match.kwargs[key])
                break

        # Si no encontró, intenta extraer último segmento "parecido" a pk
        if not objeto_id:
            m = re.search(r"/(?P<id>[0-9a-fA-F-]{6,}|[\w-]{6,})/?$", request.path_info)
            if m:
                objeto_id = m.group("id")
    except Exception:
        pass

    return modelo[:150], objeto_id[:150]


def method_to_severity(method: str, status: int) -> str:
    """
    Severidad automática por método + status:
    - GET → INFO (sube a WARNING/ERROR/CRITICAL por status)
    - POST/PUT/PATCH → MEDIUM
    - DELETE → HIGH
    - status >= 500 → CRITICAL
    - 400–499 → WARNING
    """
    method = (method or "").upper()
    base = "INFO"
    if method in {"POST", "PUT", "PATCH"}:
        base = "MEDIUM"
    elif method == "DELETE":
        base = "HIGH"

    if status >= 500:
        return "CRITICAL"
    if 400 <= status <= 499:
        return "WARNING"
    return base


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware Enterprise de Auditoría:
    - Solo usuarios autenticados (menos ruido).
    - Excluye admin/static/media/healthcheck por defecto (configurable).
    - Registra navegación (GET) y cambios (POST/PUT/PATCH/DELETE).
    - Captura: usuario, sesión, método, URL, query, status, IP, UA.
    - Guarda payload en forma segura (ofuscando claves sensibles).
    - Heurística para modelo/objeto_id.
    """

    def __init__(self, get_response=None):
        super().__init__(get_response)
        from django.conf import settings

        extra: Tuple[str, ...] = tuple(getattr(settings, "AUDIT_EXCLUDE_PREFIXES", ()))
        self.exclude_extra = extra
        self.capture_gets: bool = bool(getattr(settings, "AUDIT_CAPTURE_GET", True))  # sí, también GET

        # Límite de bytes a leer del body para no saturar
        self.max_body_bytes: int = int(getattr(settings, "AUDIT_MAX_BODY_BYTES", 100_000))

    def process_request(self, request: HttpRequest):
        # Marcar inicio/guardar algunos datos para usar en response
        request._audit_started = timezone.now()
        request._audit_body = None

        # Si no autenticado o ruta excluida → no capturar
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            request._audit_skip = True
            return

        if is_excluded_path(request.path, self.exclude_extra):
            request._audit_skip = True
            return

        # Para GET: no tocar body; para otros, captura prudente
        method = request.method.upper()
        if method in {"POST", "PUT", "PATCH", "DELETE"}:
            try:
                raw = request.body or b""
                if len(raw) > self.max_body_bytes:
                    body_info = {"__truncated__": True, "size": len(raw)}
                else:
                    # Intentar JSON; si no, x-www-form-urlencoded
                    try:
                        body_info = json.loads(raw.decode(request.encoding or "utf-8"))
                    except Exception:
                        body_info = request.POST.dict() if hasattr(request, "POST") else {"__raw__": raw.decode(errors="ignore")}
                request._audit_body = scrub_payload(body_info)
            except Exception:
                request._audit_body = {"__read_error__": True}

        elif method == "GET" and self.capture_gets:
            # Nada que leer del body
            request._audit_body = None

        request._audit_skip = False

    def process_response(self, request: HttpRequest, response: HttpResponse):
        try:
            if getattr(request, "_audit_skip", True):
                return response

            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                return response

            path = request.path
            if is_excluded_path(path, self.exclude_extra):
                return response

            method = request.method.upper()
            status = getattr(response, "status_code", 0) or 0
            ip = get_client_ip(request)
            ua = request.META.get("HTTP_USER_AGENT", "")[:500]
            query = request.META.get("QUERY_STRING", "")

            modelo, objeto_id = infer_object_ref(request)
            sesion_id = getattr(request, "session", None) and request.session.session_key or None

            # Construir payload/metadata
            payload = {}
            if request._audit_body is not None:
                payload["request_body"] = request._audit_body

            meta_extra: Dict[str, Any] = {
                "view_time_ms": int(((timezone.now() - getattr(request, "_audit_started", timezone.now())).total_seconds()) * 1000),
                "resolver_view": modelo,
                "headers": {
                    "host": request.META.get("HTTP_HOST"),
                    "content_type": request.META.get("CONTENT_TYPE"),
                    "content_length": request.META.get("CONTENT_LENGTH"),
                    "accept": request.META.get("HTTP_ACCEPT"),
                    "accept_language": request.META.get("HTTP_ACCEPT_LANGUAGE"),
                },
            }

            # Determinar acción semántica
            if method == "GET":
                accion = "NAVIGATE_VIEW"
            elif method == "POST":
                accion = "CREATE_OR_ACTION"
            elif method == "PUT":
                accion = "UPDATE_REPLACE"
            elif method == "PATCH":
                accion = "UPDATE_PARTIAL"
            elif method == "DELETE":
                accion = "DELETE"
            else:
                accion = f"HTTP_{method}"

            severidad = method_to_severity(method, status)

            # Guardar registro
            AuditLog.objects.create(
                fecha_evento=timezone.now(),
                usuario=user,
                sesion_id=sesion_id,
                accion=accion,
                modelo=modelo or "",
                objeto_id=objeto_id or "",
                datos_antes=None,          # El diff detallado lo cubren LAS SEÑALES de modelo
                datos_despues=None,        # (este middleware registra el contexto de la petición)
                diff=None,
                ip=ip,
                user_agent=ua,
                metodo_http=method,
                url_path=path[:255],
                query_string=(query or "")[:1000],
                status_http=status,
                severidad=severidad,
                mensaje="",
                meta_extra=coerce_json(meta_extra),
                payload=coerce_json(payload) if payload else None,
            )

        except Exception:
            # Nunca romper la respuesta del sitio por el logging
            pass

        return response
