<div align="center">
    <img src="base/static/images/logo-nucleo.svg" alt="NucleoISP Logo" width="200"/>
    <h1>NucleoISP</h1>
    <p><strong>Plataforma para la gestión de proveedores de servicio de internet</strong></p>
</div>

## Descripción General

NucleoISP es una plataforma diseñada con arquitectura multi-tenant, aislando completamente los datos de cada proveedor de internet a nivel de esquema en PostgreSQL. Desarrollada sobre el ecosistema de Python y Django, la plataforma permite a empresas proveedoras de internet administrar toda su lógica de negocios, facturación, automatización y control de infraestructura de red de manera centralizada.

El sistema funciona mediante un esquema público que orquesta la creación y administración de los proveedores de internet, asignando a cada uno un subdominio dedicado para acceder a su panel de control independiente de marca blanca.

## Capacidades Arquitectónicas

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

## Stack Tecnológico

* **Backend:** Python 3.13, Django 5.x, Django Tenants, Celery
* **Base de Datos:** PostgreSQL 17
* **Caché y Mensajería:** Redis 7
* **Despliegue y Contenedores:** Docker, Docker Compose, Nginx
* **Gestor de Paquetes:** UV
* **Interfaz de Administración:** Django Unfold

## Proceso de Despliegue Local

1. **Clonar el repositorio:**

```bash
git clone https://github.com/gminos/NucleoISP.git
cd NucleoISP
```

2. **Configuración de Entorno:**

Crear un archivo `.env.dev` en el directorio raíz basado en los requerimientos de la plataforma:

```env
# Configuracion Base de Datos
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=contrasena_segura

# Configuracion Django
DJANGO_SECRET_KEY=clave_ultra_secreta_aqui
DJANGO_ALLOWED_HOSTS=.nucleoisp.localhost,127.0.0.1
DEBUG=True

# Configuracion Correo Electronico
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=tu_correo@gmail.com
EMAIL_HOST_PASSWORD=tu_contrasena_de_aplicacion

# Configuracion WireGuard
WG_PASSWORD=contrasena_admin_vpn
```

3. **Construcción y Arranque de Contenedores:**

El entorno inicializa la base de datos, el servidor web, trabajadores de Celery y el balanceador proxy inverso local.

3. **Inicialización de la Arquitectura Multi-Tenant:**

1. Construye y levanta los contenedores:
   ```bash
   docker compose up -d --build
   ```

2. Crea el inquilino principal (Public Tenant) para la administración central:
   ```bash
   docker compose exec web uv run python manage.py create_tenant --schema_name=public --domain-domain=localhost --domain-is_primary=True --name="NucleoISP Central"
   ```

3. Crea el usuario administrador maestro (Superuser):
   ```bash
   docker compose exec web uv run python manage.py create_tenant_superuser --schema_name=public
   ```

4. **Acceso al Panel Central:**

Ingresar mediante el dominio principal configurado (ej. `http://nucleoisp.localhost:8000`) utilizando las credenciales maestras generadas. Desde este panel público se podrán aprovisionar las nuevas empresas, las cuales recibirán inmediatamente su propia base de datos y su propio subdominio.

---
