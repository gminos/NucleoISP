from facturacion.services.whatsapp import enviar_factura_cliente, enviar_comprobante_pago
from facturacion.models import Factura, Transaccion
from django.core.management import call_command
from django_tenants.utils import tenant_context
from nucleo_admin.models import EmpresaISP
from celery import shared_task, Task
from django.utils import timezone
from django.conf import settings

@shared_task(bind=True)
def procesar_envio_facturas(self: Task, schema_name: str | None = None) -> str:
    if settings.WHATSAPP_SIMULATION_MODE and not schema_name:
        raise ValueError("En modo simulacion se debe indicar schema_name para no procesar todos los inquilinos.")

    hoy = timezone.now().date()

    inquilinos = EmpresaISP.objects.exclude(schema_name='public')

    if schema_name:
        inquilinos = inquilinos.filter(schema_name=schema_name)

    resultado_total = []

    for inquilino in inquilinos:
        with tenant_context(inquilino):
            facturas_a_enviar = Factura.objects.filter(
                periodo_inicio__year=hoy.year,
                periodo_inicio__month=hoy.month,
                cargo__estado__in=["pendiente", "parcial"],
                notificacion_enviada=False
            ).select_related('instalacion__cliente').prefetch_related('cargo__detallepagos')

            facturas_exitosas = []
            total_errores = 0

            for factura in facturas_a_enviar:
                exito = enviar_factura_cliente(factura)

                if exito:
                    facturas_exitosas.append(factura.pk)
                else:
                    total_errores += 1

            if facturas_exitosas:
                Factura.objects.filter(pk__in=facturas_exitosas).update(notificacion_enviada=True)

            if facturas_exitosas or total_errores > 0:
                res = f"[{inquilino.schema_name}] Enviadas: {len(facturas_exitosas)}, Errores: {total_errores}"
                print(res)
                resultado_total.append(res)

    if not resultado_total:
        return "No hubo facturas para enviar en ningún inquilino."

    return " | ".join(resultado_total)

@shared_task(bind=True, max_retries=5)
def procesar_envio_comprobando_whatsapp(self: Task, transaccion_id, schema_name: str) -> None:
    tenant = EmpresaISP.objects.get(schema_name=schema_name)
    with tenant_context(tenant):
        try:
            transaccion = Transaccion.objects.get(pk=transaccion_id)
            exito = enviar_comprobante_pago(transaccion)
            if not exito:
                retraso = 60 * (2 ** self.request.retries)
                print(f"Reintentando envio de recibo {transaccion_id} en {retraso} segundos...")
                raise self.retry(countdown=retraso)
        except Transaccion.DoesNotExist:
            pass

@shared_task
def procesar_generacion_masiva_facturas() -> str:
    inquilinos = EmpresaISP.objects.exclude(schema_name='public')
    total_procesados = 0

    for inquilino in inquilinos:
        with tenant_context(inquilino):
            try:
                call_command('generar_facturas')
                total_procesados += 1
            except Exception as e:
                print(f"Error generando facturas para {inquilino.schema_name}: {e}")

    return f"Comando generar_facturas ejecutado con éxito en {total_procesados} inquilinos."
