from base.dashboard.comun import rango_comparable_mes_anterior, meses_recientes, formato_moneda, formato_numero, datos_grafica, serie_mensual, distribucion, etiqueta_mes, inicio_mes, porcentaje, variacion, plural
from django.db.models.functions import Coalesce, TruncMonth
from facturacion.models import Cargo, Transaccion
from django.db.models import Count, Min, Q, Sum
from instalaciones.models import Instalacion
from clientes.models import Cliente
from django.utils import timezone
from django.db import connection
from django.urls import reverse
from redes.models import Router
from datetime import timedelta

ESTADOS_PENDIENTES = ["pendiente", "parcial"]
LIMITE_LISTAS = 5

TRAMOS_CARTERA = [
    ("por_vencer", "Aun no vence", "bg-primary-600 dark:bg-primary-500"),
    ("d1_30", "1 a 30 dias de atraso", "bg-orange-500"),
    ("d31_60", "31 a 60 dias de atraso", "bg-red-500"),
    ("d61_90", "61 a 90 dias de atraso", "bg-red-600"),
    ("d90", "Mas de 90 dias de atraso", "bg-red-700"),
]


def metricas_inquilino() -> dict:
    hoy = timezone.localdate()
    meses = meses_recientes(hoy)

    return {
        "kpi": {
            "cobrado": _kpi_cobrado(hoy),
            "cartera": _kpi_cartera(hoy),
            "servicios": _kpi_servicios(hoy),
            "recaudo": _kpi_recaudo(hoy),
        },
        "grafica_facturacion": _grafica_facturacion(meses),
        "grafica_altas": _grafica_altas(meses),
        "cartera_tramos": _cartera_por_tramos(hoy),
        "mayores_deudores": _mayores_deudores(hoy),
        "por_suspender": _por_suspender(hoy),
        "uso_paquete": _uso_paquete(),
        "planes": _distribucion_planes(),
        "veredas": _distribucion_veredas(),
    }


def _cargos_pendientes():
    return Cargo.objects.filter(
        estado__in=ESTADOS_PENDIENTES, saldo_pendiente__gt=0
    ).annotate(referencia=Coalesce("fecha_vencimiento", "fecha_emision"))


def _kpi_cobrado(hoy) -> dict:
    inicio_anterior, fin_anterior = rango_comparable_mes_anterior(hoy)
    transacciones_mes = Transaccion.objects.filter(fecha_pago__range=(inicio_mes(hoy), hoy))

    cobrado_mes = transacciones_mes.aggregate(total=Sum("monto_total"))["total"] or 0
    cobrado_anterior = Transaccion.objects.filter(
        fecha_pago__range=(inicio_anterior, fin_anterior)
    ).aggregate(total=Sum("monto_total"))["total"] or 0

    por_metodo = (
        transacciones_mes.exclude(metodo_pago="no aplica")
        .values("metodo_pago")
        .annotate(total=Sum("monto_total"))
        .order_by("-total")
    )
    metodos = [
        f"{fila['metodo_pago'].capitalize()} {porcentaje(fila['total'], cobrado_mes):.0f}%"
        for fila in por_metodo
    ]

    return {
        "valor": formato_moneda(cobrado_mes),
        "variacion": variacion(cobrado_mes, cobrado_anterior),
        "detalle": " - ".join(metodos) if metodos else "Sin pagos este mes",
        "href": reverse("admin:facturacion_transaccion_changelist"),
    }


def _kpi_cartera(hoy) -> dict:
    resumen = _cargos_pendientes().aggregate(
        total=Sum("saldo_pendiente"),
        vencido=Sum("saldo_pendiente", filter=Q(referencia__lt=hoy)),
        clientes=Count("cliente", distinct=True),
    )
    return {
        "valor": formato_moneda(resumen["total"]),
        "vencido": formato_moneda(resumen["vencido"]),
        "hay_vencido": bool(resumen["vencido"]),
        "detalle": plural(resumen["clientes"], "cliente pendiente de pago", "clientes pendientes de pago"),
        "href": reverse("admin:facturacion_cargo_changelist") + "?estado__in=pendiente,parcial",
    }


def _kpi_servicios(hoy) -> dict:
    inicio_anterior, fin_anterior = rango_comparable_mes_anterior(hoy)
    resumen = Instalacion.objects.aggregate(
        activos=Count("id", filter=Q(servicio_activo=True)),
        suspendidos=Count("id", filter=Q(servicio_activo=False)),
        altas_mes=Count("id", filter=Q(fecha_instalacion__date__range=(inicio_mes(hoy), hoy))),
        altas_anterior=Count("id", filter=Q(fecha_instalacion__date__range=(inicio_anterior, fin_anterior))),
        recurrente=Sum("plan__costo", filter=Q(servicio_activo=True)),
    )
    return {
        "valor": formato_numero(resumen["activos"]),
        "altas_mes": f"{plural(resumen['altas_mes'], 'alta')} este mes",
        "variacion": variacion(resumen["altas_mes"], resumen["altas_anterior"]),
        "suspendidos": plural(resumen["suspendidos"], "suspendido"),
        "recurrente": formato_moneda(resumen["recurrente"]),
        "href": reverse("admin:instalaciones_instalacion_changelist"),
        "href_suspendidos": reverse("admin:instalaciones_instalacion_changelist") + "?servicio_activo__exact=0",
    }


def _kpi_recaudo(hoy) -> dict:
    resumen = Cargo.objects.filter(fecha_emision__range=(inicio_mes(hoy), hoy)).aggregate(
        facturado=Sum("monto_total"),
        pendiente=Sum("saldo_pendiente"),
    )
    facturado = resumen["facturado"] or 0
    pagado = facturado - (resumen["pendiente"] or 0)
    tasa = porcentaje(pagado, facturado)
    return {
        "valor": f"{tasa:.0f}%",
        "progreso": f"{tasa:.1f}",
        "detalle": f"{formato_moneda(pagado)} de {formato_moneda(facturado)} facturado",
    }


def _grafica_facturacion(meses) -> str:
    desde = meses[0]
    facturado = (
        Cargo.objects.filter(fecha_emision__gte=desde)
        .annotate(mes=TruncMonth("fecha_emision"))
        .values("mes")
        .annotate(total=Sum("monto_total"))
    )
    cobrado = (
        Transaccion.objects.filter(fecha_pago__gte=desde)
        .annotate(mes=TruncMonth("fecha_pago"))
        .values("mes")
        .annotate(total=Sum("monto_total"))
    )
    return datos_grafica(
        [etiqueta_mes(mes) for mes in meses],
        [
            {
                "label": "Cobrado",
                "data": serie_mensual(cobrado, meses),
                "backgroundColor": "var(--color-primary-600)",
                "maxBarThickness": 16,
                "order": 0,
            },
            {
                "label": "Facturado",
                "data": serie_mensual(facturado, meses),
                "backgroundColor": "var(--color-primary-200)",
                "maxBarThickness": 16,
                "order": 1,
            },
        ],
    )


def _grafica_altas(meses) -> str:
    altas = (
        Instalacion.objects.filter(fecha_instalacion__date__gte=meses[0])
        .annotate(mes=TruncMonth("fecha_instalacion"))
        .values("mes")
        .annotate(total=Count("id"))
    )
    return datos_grafica(
        [etiqueta_mes(mes) for mes in meses],
        [
            {
                "label": "Instalaciones",
                "data": serie_mensual(altas, meses),
                "backgroundColor": "var(--color-primary-600)",
                "maxBarThickness": 16,
                "maxTicksXLimit": 6,
            }
        ],
    )


def _cartera_por_tramos(hoy) -> list[dict]:
    hace_30 = hoy - timedelta(days=30)
    hace_60 = hoy - timedelta(days=60)
    hace_90 = hoy - timedelta(days=90)
    saldo = "saldo_pendiente"

    montos = _cargos_pendientes().aggregate(
        total=Sum(saldo),
        por_vencer=Sum(saldo, filter=Q(referencia__gte=hoy)),
        d1_30=Sum(saldo, filter=Q(referencia__lt=hoy, referencia__gte=hace_30)),
        d31_60=Sum(saldo, filter=Q(referencia__lt=hace_30, referencia__gte=hace_60)),
        d61_90=Sum(saldo, filter=Q(referencia__lt=hace_60, referencia__gte=hace_90)),
        d90=Sum(saldo, filter=Q(referencia__lt=hace_90)),
    )
    total = montos["total"] or 0
    return [
        {
            "etiqueta": etiqueta,
            "monto": formato_moneda(montos[clave]),
            "porcentaje": f"{porcentaje(montos[clave] or 0, total):.1f}",
            "color": color,
        }
        for clave, etiqueta, color in TRAMOS_CARTERA
    ]


def _dias_vencido(hoy, fecha) -> int:
    return max((hoy - fecha).days, 0) if fecha else 0


def _mayores_deudores(hoy) -> list[dict]:
    filas = (
        _cargos_pendientes()
        .values("cliente_id", "cliente__nombre", "cliente__apellido")
        .annotate(deuda=Sum("saldo_pendiente"), desde=Min("referencia"))
        .order_by("-deuda")[:LIMITE_LISTAS]
    )
    url_caja = reverse("portal_caja")
    return [
        {
            "cliente": f"{fila['cliente__nombre']} {fila['cliente__apellido']}",
            "deuda": formato_moneda(fila["deuda"]),
            "dias": _dias_vencido(hoy, fila["desde"]),
            "dias_texto": f"{_dias_vencido(hoy, fila['desde'])} d",
            "href": f"{url_caja}?q={fila['cliente_id']}",
        }
        for fila in filas
    ]


def _por_suspender(hoy) -> dict:
    vencidas = Instalacion.objects.filter(
        servicio_activo=True,
        cargos__tipo_cargo="mensualidad",
        cargos__estado__in=ESTADOS_PENDIENTES,
        cargos__fecha_vencimiento__lt=hoy,
    ).annotate(vencido_desde=Min("cargos__fecha_vencimiento"))

    filas = vencidas.select_related("cliente", "plan").order_by("vencido_desde")[:LIMITE_LISTAS]
    return {
        "total": vencidas.count(),
        "filas": [
            {
                "cliente": f"{inst.cliente.nombre} {inst.cliente.apellido}",
                "plan": inst.plan.nombre if inst.plan else "Sin plan",
                "dias_texto": f"{_dias_vencido(hoy, inst.vencido_desde)} d",
                "href": reverse("admin:instalaciones_instalacion_change", args=[inst.pk]),
            }
            for inst in filas
        ],
    }


def _uso_paquete() -> dict | None:
    paquete = getattr(connection.tenant, "paquete", None)
    if paquete is None:
        return None

    clientes = Cliente.objects.count()
    routers = Router.objects.count()
    limite_routers = paquete.limite_routers_incluidos + connection.tenant.routers_extras_contratados
    ilimitado = paquete.limite_cliente <= 0

    return {
        "nombre": paquete.nombre,
        "clientes": formato_numero(clientes),
        "clientes_ilimitados": ilimitado,
        "detalle_clientes": None if ilimitado else f"{formato_numero(clientes)} / {formato_numero(paquete.limite_cliente)}",
        "progreso_clientes": "0" if ilimitado else f"{porcentaje(clientes, paquete.limite_cliente):.1f}",
        "detalle_routers": f"{formato_numero(routers)} / {formato_numero(limite_routers)}",
        "progreso_routers": f"{porcentaje(routers, limite_routers):.1f}",
    }


def _agrupar(filas, campo: str, sin_valor: str) -> list[tuple[str, int]]:
    grupos: dict[str, list] = {}
    for fila in filas:
        etiqueta = (fila[campo] or "").strip() or sin_valor
        grupo = grupos.setdefault(etiqueta.casefold(), [etiqueta, 0])
        grupo[1] += fila["total"]
    return [tuple(grupo) for grupo in grupos.values()]


def _distribucion_planes() -> list[dict]:
    filas = Instalacion.objects.filter(servicio_activo=True).values("plan__nombre").annotate(total=Count("id"))
    pares = _agrupar(filas, "plan__nombre", "Sin plan")
    return distribucion(pares, sum(cantidad for _, cantidad in pares), etiqueta_resto="Otros")


def _distribucion_veredas() -> list[dict]:
    filas = Instalacion.objects.filter(servicio_activo=True).values("cliente__vereda").annotate(total=Count("id"))
    pares = _agrupar(filas, "cliente__vereda", "Sin vereda")
    return distribucion(pares, sum(cantidad for _, cantidad in pares))
