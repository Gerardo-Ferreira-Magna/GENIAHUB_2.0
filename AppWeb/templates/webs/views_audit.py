from datetime import timedelta
from django.db.models import Count, Avg, Max
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from .models_audit import AuditLog

@staff_member_required
def auditoria_dashboard(request):
    now = timezone.now()
    since_7d = now - timedelta(days=7)
    since_24h = now - timedelta(hours=24)
    since_10m = now - timedelta(minutes=10)

    total_7d = AuditLog.objects.filter(created_at__gte=since_7d).count()
    crit_7d = AuditLog.objects.filter(created_at__gte=since_7d, severity="CRITICAL").count()
    high_7d = AuditLog.objects.filter(created_at__gte=since_7d, severity="HIGH").count()
    medium_7d = AuditLog.objects.filter(created_at__gte=since_7d, severity="MEDIUM").count()
    low_7d = AuditLog.objects.filter(created_at__gte=since_7d, severity="LOW").count()

    # Top usuarios por actividad (7d)
    top_users = (AuditLog.objects
                 .filter(created_at__gte=since_7d, user__isnull=False)
                 .values("user__email")
                 .annotate(cnt=Count("id"))
                 .order_by("-cnt")[:10])

    # Top endpoints/módulos (7d)
    top_modules = (AuditLog.objects
                   .filter(created_at__gte=since_7d)
                   .values("module")
                   .annotate(cnt=Count("id"))
                   .order_by("-cnt")[:10])

    top_urls = (AuditLog.objects
                .filter(created_at__gte=since_7d)
                .values("url")
                .annotate(cnt=Count("id"))
                .order_by("-cnt")[:10])

    # Serie diaria por severidad (últimos 7 días)
    series = {}
    for sev in ["CRITICAL","HIGH","MEDIUM","LOW"]:
        qs = (AuditLog.objects
              .filter(created_at__gte=since_7d, severity=sev)
              .extra(select={"d":"date(created_at)"})
              .values("d")
              .annotate(cnt=Count("id"))
              .order_by("d"))
        series[sev] = [{"date": r["d"], "count": r["cnt"]} for r in qs]

    # Sesiones activas ~ últimas 10 min (distintas session_id)
    active_sessions = (AuditLog.objects
                       .filter(created_at__gte=since_10m, session_id__isnull=False)
                       .values("session_id").distinct().count())

    # Últimas alertas críticas / altas (24h)
    alerts = (AuditLog.objects
              .filter(created_at__gte=since_24h, severity__in=["CRITICAL","HIGH"])
              .order_by("-created_at")[:20])

    context = {
        "kpis": {
            "total_7d": total_7d,
            "crit_7d": crit_7d,
            "high_7d": high_7d,
            "medium_7d": medium_7d,
            "low_7d": low_7d,
            "active_sessions": active_sessions,
        },
        "top_users": list(top_users),
        "top_modules": list(top_modules),
        "top_urls": list(top_urls),
        "series": series,
        "alerts": alerts,
        "since_7d": since_7d,
        "since_24h": since_24h,
    }
    return render(request, "webs/auditoria_dashboard.html", context)
