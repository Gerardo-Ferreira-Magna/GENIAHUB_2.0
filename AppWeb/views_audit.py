from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Avg
from django.shortcuts import render
from django.utils.timezone import now, timedelta
from .models_audit import AuditLog


# AppWeb/views.py

from datetime import timedelta
from django.db.models import Count, Avg
from django.shortcuts import render
from django.utils.timezone import now
from django.contrib.admin.views.decorators import staff_member_required

# Asume que AuditLog está importado correctamente

@staff_member_required
def auditoria_dashboard(request):
    """
    Dashboard de auditoría que muestra estadísticas clave de los logs de los últimos 7 días.
    """
    # Últimos 7 días
    since = now() - timedelta(days=7)

    # 1. Total de logs en los últimos 7 días
    # CORREGIDO: Usamos 'fecha_evento'
    total_logs = AuditLog.objects.filter(fecha_evento__gte=since).count()

    # 2. Top 10 Rutas (URLs)
    # CORREGIDO: Usamos 'fecha_evento'
    top_paths = (AuditLog.objects
                 .filter(fecha_evento__gte=since)
                 .values('url') 
                 .annotate(n=Count('id'))
                 .order_by('-n')[:10])

    # 3. Top 10 IPs.
    # CORREGIDO: Usamos 'fecha_evento'
    top_ips = (AuditLog.objects
               .filter(fecha_evento__gte=since)
               .values('ip_origen') 
               .annotate(n=Count('id'))
               .order_by('-n')[:10])

    # 4. Logs por Severidad
    # CORREGIDO: Usamos 'fecha_evento'
    by_severity = (AuditLog.objects
                   .filter(fecha_evento__gte=since)
                   .values('severidad')
                   .annotate(n=Count('id'))
                   .order_by('-n'))

    # 5. Logs por Acción
    # CORREGIDO: Usamos 'fecha_evento'
    by_action = (AuditLog.objects
                 .filter(fecha_evento__gte=since)
                 .values('accion')
                 .annotate(n=Count('id'))
                 .order_by('-n'))

    # 6. Latencia Promedio (Métrica no soportada sin el campo en el modelo, por lo que es None)
    avg_latency = None 
    # (Si añades 'duration_ms' al modelo, descomenta y ajusta el filtro si usas 'fecha_evento')

    # 7. Sesiones activas.
    active_since = now() - timedelta(hours=1)
    # CORREGIDO: Usamos 'fecha_evento'
    active_sessions = (AuditLog.objects
                       .filter(fecha_evento__gte=active_since)
                       .exclude(session_key__isnull=True)
                       .values('session_key')
                       .distinct()
                       .count())

    context = {
        'since': since,
        'total_logs': total_logs,
        'top_paths': list(top_paths),
        'top_ips': list(top_ips),
        'by_severity': list(by_severity),
        'by_action': list(by_action),
        'avg_latency': round(avg_latency or 0, 1),
        'active_sessions': active_sessions,
    }
    return render(request, 'webs/auditoria_dashboard.html', context)