import json
import time
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now
from django.http import HttpRequest
from .models_audit import AuditLog
from .audit_context import set_request, clear_request


EXCLUDE_PREFIXES = (
    '/static/', '/media/',
)
EXCLUDE_EXACT = set((
    '/admin/jsi18n/',    # ruido
))

SENSITIVE_KEYS = {'password', 'password1', 'password2', 'pwd', 'token', 'csrfmiddlewaretoken'}


def _client_ip(request: HttpRequest):
    xf = request.META.get('HTTP_X_FORWARDED_FOR')
    if xf:
        # XFF puede traer "ip1, ip2, ip3"
        return xf.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def _clean_payload(d: dict):
    if not isinstance(d, dict):
        return None
    out = {}
    for k, v in d.items():
        if k.lower() in SENSITIVE_KEYS:
            out[k] = '***'
        else:
            out[k] = v
    return out


class AuditMiddleware(MiddlewareMixin):
    """
    - Registra todas las requests (salvo estáticos).
    - Captura payload en POST/PUT/PATCH/DELETE (sanitizado).
    - Mide latencia ms.
    - Marca severidad por tipo de ruta / método / status.
    - Deja request en threadlocal para que signals generen diffs CREATE/UPDATE/DELETE.
    """

    def process_request(self, request: HttpRequest):
        set_request(request)
        request._audit_start = time.perf_counter()

    def process_view(self, request, view_func, view_args, view_kwargs):
        # nada especial aquí; se podría marcar vistas sensibles por nombre
        return None

    def process_response(self, request: HttpRequest, response):
        try:
            path = request.path or ''
            if path.startswith(EXCLUDE_PREFIXES) or path in EXCLUDE_EXACT:
                return response

            metodo = request.method.upper()
            ip = _client_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')[:512]
            ref = request.META.get('HTTP_REFERER', '')

            payload = None
            if metodo in ('POST', 'PUT', 'PATCH', 'DELETE'):
                if request.content_type and 'application/json' in request.content_type:
                    try:
                        payload = _clean_payload(json.loads(request.body.decode('utf-8') or '{}'))
                    except Exception:
                        payload = {'_raw': 'no-json/parse-error'}
                else:
                    payload = _clean_payload(request.POST.dict())

            status = getattr(response, 'status_code', 200)
            dur = None
            if hasattr(request, '_audit_start'):
                dur = int((time.perf_counter() - request._audit_start) * 1000)

            # Severidad heurística simple
            if status >= 500:
                sev = 'CRIT'
                accion = 'ERROR'
            elif metodo in ('POST', 'PUT', 'PATCH', 'DELETE'):
                sev = 'WARN'
                accion = 'UPDATE' if metodo != 'DELETE' else 'DELETE'
            else:
                sev = 'INFO'
                accion = 'VIEW'

            AuditLog.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                session_key=getattr(request, 'session', None) and request.session.session_key or None,
                ip=ip,
                user_agent=ua,
                referrer=ref,
                metodo=metodo,
                path=path,
                status_code=status,
                accion=accion,
                severidad=sev,
                payload=payload,
                timestamp=now(),
                latency_ms=dur,
                mensaje=None,
            )
        finally:
            clear_request()
        return response

    def process_exception(self, request: HttpRequest, exception):
        # Registrar error crítico
        try:
            path = request.path or ''
            if path.startswith(EXCLUDE_PREFIXES) or path in EXCLUDE_EXACT:
                return None
            ip = _client_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')[:512]
            ref = request.META.get('HTTP_REFERER', '')

            AuditLog.objects.create(
                usuario=request.user if request.user.is_authenticated else None,
                session_key=getattr(request, 'session', None) and request.session.session_key or None,
                ip=ip,
                user_agent=ua,
                referrer=ref,
                metodo=request.method.upper(),
                path=path,
                status_code=500,
                accion='ERROR',
                severidad='CRIT',
                payload=None,
                timestamp=now(),
                latency_ms=None,
                mensaje=f'{type(exception).__name__}: {exception}',
            )
        finally:
            clear_request()
        # dejar que Django siga manejando la excepción
        return None
