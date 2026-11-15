from base.dashboard.comun import rango_comparable_mes_anterior, meses_recientes, formato_moneda, formato_numero, serie_mensual, distribucion, etiqueta_mes, sumar_meses, porcentaje, variacion
from django.test import SimpleTestCase
from datetime import date, datetime
from decimal import Decimal


class FormatoTests(SimpleTestCase):
    def test_formato_moneda_usa_punto_de_miles_y_sin_decimales(self):
        self.assertEqual(formato_moneda(Decimal("1250000.40")), "$ 1.250.000")
        self.assertEqual(formato_moneda(None), "$ 0")
        self.assertEqual(formato_moneda(-5000), "-$ 5.000")

    def test_formato_numero(self):
        self.assertEqual(formato_numero(1250), "1.250")
        self.assertEqual(formato_numero(None), "0")

    def test_porcentaje_acotado_y_sin_division_por_cero(self):
        self.assertEqual(porcentaje(5, 0), 0.0)
        self.assertEqual(porcentaje(150, 100), 100.0)
        self.assertEqual(porcentaje(25, 100), 25.0)

    def test_variacion(self):
        self.assertIsNone(variacion(10, 0))
        sube = variacion(120, 100)
        self.assertEqual(sube["valor"], "20%")
        self.assertEqual(sube["variante"], "success")
        baja = variacion(50, 100)
        self.assertEqual(baja["valor"], "50%")
        self.assertEqual(baja["variante"], "danger")


class FechasTests(SimpleTestCase):
    def test_sumar_meses_cruza_anios(self):
        self.assertEqual(sumar_meses(date(2026, 1, 20), -1), date(2025, 12, 1))
        self.assertEqual(sumar_meses(date(2026, 11, 15), 2), date(2027, 1, 1))

    def test_rango_comparable_mismo_tramo_de_dias(self):
        self.assertEqual(
            rango_comparable_mes_anterior(date(2026, 11, 15)),
            (date(2026, 10, 1), date(2026, 10, 15)),
        )

    def test_rango_comparable_no_pasa_del_fin_del_mes_anterior(self):
        self.assertEqual(
            rango_comparable_mes_anterior(date(2026, 3, 31)),
            (date(2026, 2, 1), date(2026, 2, 28)),
        )

    def test_meses_recientes_incluye_el_actual_en_orden(self):
        meses = meses_recientes(date(2026, 2, 10), cantidad=3)
        self.assertEqual(meses, [date(2025, 12, 1), date(2026, 1, 1), date(2026, 2, 1)])

    def test_etiqueta_mes_en_espanol(self):
        self.assertEqual(etiqueta_mes(date(2026, 11, 1)), "Nov 26")


class SeriesTests(SimpleTestCase):
    def test_serie_mensual_rellena_meses_sin_datos(self):
        meses = [date(2026, 9, 1), date(2026, 10, 1), date(2026, 11, 1)]
        filas = [
            {"mes": date(2026, 9, 1), "total": Decimal("100")},
            {"mes": datetime(2026, 11, 1, 0, 0), "total": 3},
        ]
        self.assertEqual(serie_mensual(filas, meses), [100.0, 0.0, 3.0])

    def test_distribucion_ordena_y_agrupa_el_resto(self):
        filas = [("A", 1), ("B", 5), ("C", 3), ("D", 1)]
        resultado = distribucion(filas, total=10, limite=2)
        self.assertEqual([fila["etiqueta"] for fila in resultado], ["B", "C", "Otras"])
        self.assertEqual(resultado[-1]["cantidad"], 2)
        self.assertEqual(resultado[0]["porcentaje"], "50.0")
        self.assertEqual(resultado[0]["detalle"], "5 (50%)")
