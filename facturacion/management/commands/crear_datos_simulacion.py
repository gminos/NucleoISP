from django.core.management.base import BaseCommand, CommandError, CommandParser
from django_tenants.utils import schema_context
from facturacion.models import Cargo, Factura
from instalaciones.models import Instalacion
from datetime import date, timedelta
from clientes.models import Cliente
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from redes.models import Router
from planes.models import Plan
from typing import Any
import calendar


class Command(BaseCommand):
    help = (
        "Crea clientes, instalaciones y facturas pendientes de prueba en un esquema, "
        "para probar el envio de facturas en modo simulacion. "
        "IMPORTANTE: antes de crear, elimina los datos de simulacion previos del esquema "
        "(clientes con apellido 'prueba N', sus cargos y facturas, el plan 'Plan prueba' "
        "y el router 'router prueba')."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--cantidad", type=int, default=20, help="Numero de clientes con factura a generar (default: %(default)s)")
        parser.add_argument("--schema", type=str, help="Nombre del esquema del inquilino donde se crean los datos", required=True)

    def handle(self, *args: Any, **options: Any) -> str | None:
        if not settings.DEBUG:
            raise CommandError("Este comando solo puede ejecutarse con DJANGO_DEBUG=true.")

        cantidad_clientes_a_generar = options["cantidad"]
        fecha_hoy = date.today()
        periodo_inicio = date(fecha_hoy.year, fecha_hoy.month, 1)
        ultimo_dia_del_mes = calendar.monthrange(fecha_hoy.year, fecha_hoy.month)[1]
        dia_final = 30 if ultimo_dia_del_mes >= 30 else ultimo_dia_del_mes
        periodo_final = date(fecha_hoy.year, fecha_hoy.month, dia_final)
        fecha_reconexion = periodo_final + timedelta(days=5)
        facturas_nuevas = []

        with schema_context(options["schema"]), transaction.atomic():
            clientes_prueba = Cliente.objects.filter(apellido__startswith="prueba ")
            Cargo.objects.filter(cliente__in=clientes_prueba).delete()
            Factura.objects.filter(instalacion__cliente__in=clientes_prueba).delete()
            clientes_prueba.delete()
            Router.objects.filter(nombre_identificador="router prueba").delete()
            Plan.objects.filter(nombre="Plan prueba").delete()

            self.stdout.write(self.style.WARNING("Datos de simulación anteriores eliminados del esquema."))

            plan = Plan.objects.create(
                nombre="Plan prueba",
                cantidad_megas=50,
                costo=60000
            )

            router = Router.objects.create(
                nombre_identificador="router prueba",
                usuario="prueba",
                password="prueba",
            )

            for indice in range(cantidad_clientes_a_generar):
                cliente = Cliente.objects.create (
                    nombre="Cliente",
                    apellido=f"prueba {indice}",
                    telefono="3333333333",
                    vereda="Vereda prueba"
                )

                instalacion = Instalacion.objects.create(
                    cliente=cliente,
                    fecha_instalacion=timezone.now(),
                    costo=150000,
                    plan=plan,
                    router=router,
                )

                factura = Factura(
                    instalacion=instalacion,
                    periodo_inicio=periodo_inicio,
                    periodo_final=periodo_final,
                    fecha_reconexion=fecha_reconexion
                )

                facturas_nuevas.append(factura) 

            for factura in facturas_nuevas:
                factura.save()

            self.stdout.write(self.style.SUCCESS(
                f"Se generaron {cantidad_clientes_a_generar} facturas simuladas exitosamente."
            ))

