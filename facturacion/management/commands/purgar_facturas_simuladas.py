from django.core.management.base import BaseCommand, CommandError
from pathlib import Path
from django.conf import settings
from typing import Any


class Command(BaseCommand):
    help = "Elimina las imagenes de facturas generadas en modo simulacion (directorio definido en WHATSAPP_SIMULATION_DIR dentro de MEDIA_ROOT)."

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.DEBUG:
            raise CommandError("Este comando solo puede ejecutarse con DJANGO_DEBUG=true.")

        directorio = Path(settings.MEDIA_ROOT) / settings.WHATSAPP_SIMULATION_DIR

        if not directorio.exists():
            self.stdout.write(self.style.WARNING("No hay directorio de simulaciones para purgar."))
            return

        archivos = list(directorio.glob("factura_*.jpg"))

        for archivo in archivos:
            archivo.unlink()

        self.stdout.write(self.style.SUCCESS(f"Se eliminaron {len(archivos)} imagenes de simulacion."))
