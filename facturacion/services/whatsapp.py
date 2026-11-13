from pywa.types.templates import HeaderImage, BodyText, TemplateLanguage
from django.template.loader import render_to_string
from facturacion.models import Factura, Transaccion
from facturacion.utils import generar_pdf_factura
from pdf2image import convert_from_bytes
from pywa.errors import WhatsAppError
from django.conf import settings
from django.db import connection
from pywa import WhatsApp
from pathlib import Path
from PIL import Image
import weasyprint
import logging
import io

logger = logging.getLogger(__name__)

def _unir_imagenes_vertical(images):
    if len(images) == 1:
        return images[0]

    widths, heights = zip(*(i.size for i in images))
    combined = Image.new('RGB', (max(widths), sum(heights)))
    y_offset = 0

    for img in images:
        combined.paste(img, (0, y_offset))
        y_offset += img.size[1]

    return combined

def _formatear_telefono(numero: object) -> str:
    return "".join([c for c in str(numero) if c.isdigit()])

def _pdf_a_jpeg_bytes(pdf_bytes: bytes) -> bytes:
    images = convert_from_bytes(pdf_bytes, dpi=200)

    if not images:
        raise ValueError("Error al convertir PDF a imagen")

    img_byte_arr = io.BytesIO()
    final_image = _unir_imagenes_vertical(images)
    final_image.save(img_byte_arr, format='JPEG')
    jpg_bytes = img_byte_arr.getvalue()

    return jpg_bytes

def _guardar_factura_simulada(factura: Factura, jpg_bytes: bytes, telefono_limpio: str):
    directorio = Path(settings.MEDIA_ROOT) / settings.WHATSAPP_SIMULATION_DIR
    directorio.mkdir(parents=True, exist_ok=True)
    ruta_archivo = directorio / f"factura_{factura.pk}.jpg"
    ruta_archivo.write_bytes(jpg_bytes)
    logger.info(f"Factura simulada creada. ruta: {ruta_archivo}, pk: {factura.pk}, destinatario: {telefono_limpio}")

def enviar_factura_cliente(factura: Factura) -> bool:
    tenant = connection.tenant

    if not settings.WHATSAPP_SIMULATION_MODE and (not tenant.wa_token or not tenant.wa_phone_id):
        logger.error(f"El inquilino {tenant.name} no tiene configurado WhatsApp.")
        return False

    telefono_cliente = factura.cliente.telefono

    if not telefono_cliente:
        logger.warning(f"El cliente {factura.cliente} no tiene telefono registrado. Factura pk: {factura.pk}")
        return False

    telefono_limpio = _formatear_telefono(telefono_cliente)

    if len(telefono_limpio) == 10:
        telefono_limpio = f"57{telefono_limpio}"

    try:
        pdf_bytes = generar_pdf_factura(factura)
        jpg_bytes = _pdf_a_jpeg_bytes(pdf_bytes)

        if settings.WHATSAPP_SIMULATION_MODE:
            _guardar_factura_simulada(factura, jpg_bytes, telefono_limpio)
        else:
            wa = WhatsApp(phone_id=tenant.wa_phone_id, token=tenant.wa_token)

            nombre_cliente = f"{factura.cliente.nombre} {factura.cliente.apellido}"
            mes_facturado = factura.periodo_inicio.strftime('%B %Y') if factura.periodo_inicio else "este mes"
            total_a_pagar = factura.cliente.calcular_deuda_total()
            total_a_pagar_str = f"${total_a_pagar:,.0f}"

            media_id = wa.upload_media(
                media=jpg_bytes,
                mime_type="image/jpeg",
                media_type="image",
                filename=f"Factura_Arint_{factura.pk}.jpg"
            )

            logger.info(f"Enviando plantilla de factura pk: {factura.pk} a {telefono_limpio}")

            wa.send_template(
                to=telefono_limpio,
                name="envio_factura_mensual_v2",
                language=TemplateLanguage.SPANISH_CO,
                params=[
                    HeaderImage.params(
                        image=media_id.id
                    ),
                    BodyText.params(nombre_cliente, mes_facturado, total_a_pagar_str)
                ]
            )

            logger.info(f"Factura pk: {factura.pk} enviada con exito a {telefono_limpio}")

        return True
    except WhatsAppError as e:
        logger.error(f"Error de API de WhatsApp enviando factura a {telefono_cliente}: {e}", exc_info=True)
        return False
    except (ValueError, OSError, TypeError, RuntimeError) as e:
        logger.error(f"Error interno generando/enviando factura a {telefono_cliente}", exc_info=True)
        return False

def generar_pdf_comprobante(transaccion: Transaccion) -> bytes:
    tenant = connection.tenant

    html_string = render_to_string('facturacion/recibo_transaccion_pdf.html', {'transaccion': transaccion, 'tenant': tenant})
    html = weasyprint.HTML(string=html_string)

    return html.write_pdf()

def enviar_comprobante_pago(transaccion: Transaccion) -> bool:
    tenant = connection.tenant

    if not tenant.wa_token or not tenant.wa_phone_id:
        logger.error(f"El inquilino {tenant.name} no tiene configurado WhatsApp.")
        return False

    wa = WhatsApp(phone_id=tenant.wa_phone_id, token=tenant.wa_token)

    telefono_cliente = transaccion.cliente.telefono

    if not telefono_cliente:
        return False

    telefono_limpio = _formatear_telefono(telefono_cliente)

    if len(telefono_limpio) == 10:
        telefono_limpio = f"57{telefono_limpio}"

    try:
        pdf_bytes = generar_pdf_comprobante(transaccion)
        jpg_bytes = _pdf_a_jpeg_bytes(pdf_bytes)

        media_id = wa.upload_media(
            media=jpg_bytes,
            mime_type="image/jpeg",
            media_type="image",
            filename=f"Comprobante_Pago_{transaccion.pk}.jpg"
        )

        nombre_cliente = f"{transaccion.cliente.nombre} {transaccion.cliente.apellido}"
        monto_pagado_str = f"${transaccion.monto_total:,.0f}"

        wa.send_template(
            to=telefono_limpio,
            name="enviar_comprobante_pago_v2",
            language=TemplateLanguage.SPANISH_CO,
            params=[
                HeaderImage.params(
                    image=media_id.id
                ),
                BodyText.params(nombre_cliente, monto_pagado_str)
            ]
        )
        return True
    except WhatsAppError as e:
        logger.error(f"Error de API de WhatsApp enviando recibo a {telefono_cliente}: {e}", exc_info=True)
        return False
    except (ValueError, OSError, TypeError, RuntimeError) as e:
        logger.error(f"Error interno generando/enviando recibo a {telefono_cliente}", exc_info=True)
        return False
