from base.dashboard.comun import formato_moneda, formato_numero, porcentaje
from nucleo_admin.models import ESTADO_CUENTA_CHOICES, EmpresaISP
from django_tenants.utils import schema_context
from django.db.models import Count, Q
from clientes.models import Cliente
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

DIAS_AVISO_VENCIMIENTO = 7
LIMITE_LISTAS = 8

VARIANTE_ESTADO = {"activa": "success", "mora": "warning", "suspendida": "danger"}


def metricas_maestro() -> dict:
    hoy = timezone.localdate()
    empresas = list(
        EmpresaISP.objects.exclude(schema_name="public").select_related("paquete").order_by("name")
    )

    return {
        "is_public_schema": True,
        "kpi": _kpis(empresas),
        "vencimientos": _proximos_vencimientos(empresas, hoy),
        "uso_cupo": _uso_cupo(empresas),
    }


def _ingreso_mensual(empresa) -> float:
    paquete = empresa.paquete
    if paquete is None:
        return 0.0
    return float(paquete.precio + empresa.routers_extras_contratados * paquete.precio_router_extra)


def _kpis(empresas) -> dict:
    por_estado = EmpresaISP.objects.exclude(schema_name="public").aggregate(
        **{estado: Count("pk", filter=Q(estado_cuenta=estado)) for estado, _ in ESTADO_CUENTA_CHOICES}
    )
    cobrables = [empresa for empresa in empresas if empresa.estado_cuenta != "suspendida"]
    sin_paquete = sum(1 for empresa in empresas if empresa.paquete is None)
    url_empresas = reverse("admin:nucleo_admin_empresaisp_changelist")

    return {
        "empresas": {
            "valor": formato_numero(len(empresas)),
            "detalle": f"{formato_numero(sin_paquete)} sin paquete asignado" if sin_paquete else "Todas con paquete asignado",
            "href": url_empresas,
        },
        "estados": [
            {
                "etiqueta": etiqueta,
                "valor": formato_numero(por_estado[estado]),
                "variante": VARIANTE_ESTADO[estado],
                "href": f"{url_empresas}?estado_cuenta__exact={estado}",
            }
            for estado, etiqueta in ESTADO_CUENTA_CHOICES
        ],
        "ingreso": {
            "valor": formato_moneda(sum(_ingreso_mensual(empresa) for empresa in cobrables)),
            "detalle": "Paquetes y routers extra de cuentas activas y en mora",
        },
    }


def _proximos_vencimientos(empresas, hoy) -> list[dict]:
    limite = hoy + timedelta(days=DIAS_AVISO_VENCIMIENTO)
    proximas = sorted(
        (e for e in empresas if e.fecha_proximo_pago and e.fecha_proximo_pago <= limite),
        key=lambda e: e.fecha_proximo_pago,
    )[:LIMITE_LISTAS]

    filas = []
    for empresa in proximas:
        dias = (empresa.fecha_proximo_pago - hoy).days
        if dias < 0:
            cuando = f"Vencido hace {-dias} dias"
        elif dias == 0:
            cuando = "Vence hoy"
        else:
            cuando = f"Vence en {dias} dias"
        filas.append({
            "empresa": empresa.name,
            "fecha": empresa.fecha_proximo_pago,
            "cuando": cuando,
            "monto": formato_moneda(_ingreso_mensual(empresa)),
            "estado": empresa.get_estado_cuenta_display(),
            "variante": VARIANTE_ESTADO.get(empresa.estado_cuenta, ""),
            "href": reverse("admin:nucleo_admin_empresaisp_change", args=[empresa.pk]),
        })
    return filas


def _uso_cupo(empresas) -> list[dict]:
    filas = []
    for empresa in empresas:
        paquete = empresa.paquete
        if paquete is None or paquete.limite_cliente <= 0:
            continue
        with schema_context(empresa.schema_name):
            clientes = Cliente.objects.count()
        uso = porcentaje(clientes, paquete.limite_cliente)
        filas.append({
            "empresa": empresa.name,
            "paquete": paquete.nombre,
            "detalle": f"{formato_numero(clientes)} / {formato_numero(paquete.limite_cliente)}",
            "uso": uso,
            "progreso": f"{uso:.1f}",
            "alerta": uso >= 90,
        })
    filas.sort(key=lambda fila: fila["uso"], reverse=True)
    return filas[:LIMITE_LISTAS]
