from datetime import date, timedelta
from decimal import Decimal
import json

MESES_CORTOS = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]


def formato_moneda(valor) -> str:
    entero = int(round(Decimal(valor or 0)))
    signo = "-" if entero < 0 else ""
    return f"{signo}$ {abs(entero):,}".replace(",", ".")


def formato_numero(valor) -> str:
    return f"{int(valor or 0):,}".replace(",", ".")


def plural(cantidad, singular: str, plural_: str | None = None) -> str:
    palabra = singular if cantidad == 1 else (plural_ or f"{singular}s")
    return f"{formato_numero(cantidad)} {palabra}"


def porcentaje(parte, total) -> float:
    if not total:
        return 0.0
    return max(0.0, min(float(parte) / float(total) * 100, 100.0))


def variacion(actual, anterior) -> dict | None:
    if not anterior:
        return None
    cambio = (float(actual) - float(anterior)) / float(anterior) * 100
    sube = cambio >= 0
    return {
        "valor": f"{abs(cambio):.0f}%",
        "sube": sube,
        "variante": "success" if sube else "danger",
        "icono": "trending_up" if sube else "trending_down",
    }


def inicio_mes(fecha: date) -> date:
    return fecha.replace(day=1)


def sumar_meses(fecha: date, meses: int) -> date:
    anio, mes = divmod(fecha.month - 1 + meses, 12)
    return date(fecha.year + anio, mes + 1, 1)


def rango_comparable_mes_anterior(hoy: date) -> tuple[date, date]:
    inicio_anterior = sumar_meses(hoy, -1)
    fin_anterior = inicio_mes(hoy) - timedelta(days=1)
    dias_transcurridos = (hoy - inicio_mes(hoy)).days
    return inicio_anterior, min(inicio_anterior + timedelta(days=dias_transcurridos), fin_anterior)


def meses_recientes(hoy: date, cantidad: int = 12) -> list[date]:
    return [sumar_meses(hoy, -i) for i in range(cantidad - 1, -1, -1)]


def etiqueta_mes(fecha: date) -> str:
    return f"{MESES_CORTOS[fecha.month - 1]} {fecha.year % 100:02d}"


def serie_mensual(filas, meses: list[date], campo: str = "total") -> list[float]:
    por_mes = {}
    for fila in filas:
        mes = fila["mes"]
        if hasattr(mes, "date"):
            mes = mes.date()
        por_mes[mes.replace(day=1)] = float(fila[campo] or 0)
    return [por_mes.get(mes, 0.0) for mes in meses]


def distribucion(filas, total: int, limite: int = 8, etiqueta_resto: str = "Otras") -> list[dict]:
    ordenadas = sorted(filas, key=lambda fila: fila[1], reverse=True)
    principales, resto = ordenadas[:limite], ordenadas[limite:]
    if resto:
        principales.append((etiqueta_resto, sum(cantidad for _, cantidad in resto)))
    filas = []
    for etiqueta, cantidad in principales:
        valor = porcentaje(cantidad, total)
        filas.append({
            "etiqueta": etiqueta,
            "cantidad": cantidad,
            "detalle": f"{formato_numero(cantidad)} ({valor:.0f}%)",
            "porcentaje": f"{valor:.1f}",
        })
    return filas


def datos_grafica(etiquetas: list[str], series: list[dict]) -> str:
    return json.dumps({"labels": etiquetas, "datasets": series})
