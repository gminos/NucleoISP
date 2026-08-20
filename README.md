<div align="center">
    <img src="base/static/images/logo-nucleo.svg" alt="NucleoISP Logo" width="200"/>
    <h1>NucleoISP</h1>
    <p><strong>Plataforma para la gestión de proveedores de servicio de internet</strong></p>
</div>

## Descripción general

NucleoISP es una plataforma diseñada con arquitectura multi-tenant, aislando completamente los datos de cada proveedor de internet a nivel de esquema en PostgreSQL. Desarrollada sobre el ecosistema de Python y Django, la plataforma permite a empresas proveedoras de internet administrar toda su lógica de negocios, facturación, automatización y control de infraestructura de red de manera centralizada.

El sistema funciona mediante un esquema público que orquesta la creación y administración de los proveedores de internet, asignando a cada uno un subdominio dedicado para acceder a su panel de control independiente de marca blanca.

## Capacidades arquitectónicas

* **Arquitectura multi-tenant aislada:** Uso de esquemas de bases de datos independientes para asegurar privacidad absoluta de los datos y escalabilidad de alto rendimiento.
* **Integración directa con infraestructura:** Comunicación bidireccional mediante la API de RouterOS con equipos Mikrotik.
* **Aprovisionamiento automático:** Sincronización transparente e instantánea de perfiles PPPoE, secrets y configuraciones de planes desde la nube hacia los enrutadores físicos.
* **Procesamiento asíncrono de alto rendimiento:** Uso intensivo de Celery y Redis para manejar tareas críticas en segundo plano, tales como:
    * Corte automatizado de servicios para clientes en mora masiva.
    * Sincronización de planes a routers recién integrados.
    * Generación en lote de comprobantes y facturas.
* **Gestión financiera de alta precisión:** Sistema de priorización matemática de deuda para procesar abonos parciales, reconexiones e instalaciones.
* **Túneles seguros incorporados:** Despliegue empaquetado con WireGuard para garantizar accesos seguros a la red de gestión y monitoreo.
* **Notificaciones automatizadas por WhatsApp:** Integración para el envío automático de comprobantes de pago y alertas de cobro directamente a los clientes de cada ISP.

## Stack tecnológico

* **Backend:** Python 3.13, Django 5.x, Django Tenants, Celery
* **Base de Datos:** PostgreSQL 17
* **Caché y Mensajería:** Redis 7
* **Despliegue y Contenedores:** Docker, Docker Compose, Nginx
* **Gestor de Paquetes:** UV
* **Interfaz de Administración:** Django Unfold

## Proceso de despliegue local

1. **Clonar el repositorio:**

```bash
git clone https://github.com/gminos/NucleoISP.git
cd NucleoISP
```

2. **Configuración de entorno:**

Crear un archivo `.env.dev` en el directorio raíz basado en los requerimientos de la plataforma:

```env
# Configuracion base de datos
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=contrasena_segura
POSTGRES_PORT=5432

# Configuracion Django
DJANGO_SECRET_KEY=clave_ultra_secreta_aqui
DJANGO_ALLOWED_HOSTS=.localhost,127.0.0.1
DJANGO_DEBUG=true

# Configuracion correo electronico
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contrasena_de_aplicacion

# Configuracion wireguard
WG_HOST=127.0.0.1
WG_PASSWORD=contrasena_admin_vpn
```

3. **Construcción y arranque de contenedores:**

Levantar los contenedores:
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

4. **Inicialización de la arquitectura multi-tenant:**

1. Crea el inquilino principal para la administración central:
   ```bash
   docker compose -f docker-compose.dev.yml exec web uv run python manage.py create_tenant --schema_name=public --domain-domain=localhost --domain-is_primary=True --name="NucleoISP Central"
   ```

2. Crea el usuario administrador maestro:
   ```bash
   docker compose -f docker-compose.dev.yml exec web uv run python manage.py create_tenant_superuser --schema_name=public
   ```

5. **Acceso al panel central:**

Ingresar mediante el dominio principal configurado (ej. `http://localhost:8000`) utilizando las credenciales maestras generadas. Desde este panel público se podrán aprovisionar las nuevas empresas, las cuales recibirán inmediatamente su propia base de datos y su propio subdominio.

---
