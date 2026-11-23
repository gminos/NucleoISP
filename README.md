<div align="center">
    <picture>
        <source media="(prefers-color-scheme: dark)" srcset="base/static/images/logo-dark.svg"/>
        <img src="base/static/images/logo-nucleo.svg" alt="NucleoISP Logo" width="140"/>
    </picture>
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
* **Despliegue y Contenedores:** Docker, Docker Compose, Caddy
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
WG_EASY_API_PASSWORD=secret_dev_password
PASSWORD_HASH=$$2a$$12$$F9Uc/Tf81FZNpKT6gYzLFORiqrvLHlo1xmxGa0XbJIWgfopdSQv9O

# Configuracion whatsapp (solo funciona con DJANGO_DEBUG=true)
WHATSAPP_SIMULATION_MODE=true

# Configuracion celery (procesos del worker, por defecto 2)
CELERY_WORKER_CONCURRENCY=2
```

3. **Construcción y arranque de contenedores:**

Levantar los contenedores:
```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Si cambian las dependencias (`uv.lock`), agregar `-V` para recrear el volumen anonimo de `.venv`; sin el, los contenedores conservan el entorno anterior:
```bash
docker compose -f docker-compose.dev.yml up -d --build -V
```

4. **Inicialización de la arquitectura multi-tenant:**

1. Crea el inquilino principal para la administración central:
   ```bash
   docker compose -f docker-compose.dev.yml exec web python manage.py create_tenant --schema_name=public --domain-domain=localhost --domain-is_primary=True --name="NucleoISP Central"
   ```

2. Crea el usuario administrador maestro:
   ```bash
   docker compose -f docker-compose.dev.yml exec web python manage.py create_tenant_superuser --schema_name=public
   ```

5. **Acceso al panel central:**

Ingresar mediante el dominio principal configurado (ej. `http://localhost:8000`) utilizando las credenciales maestras generadas. Desde este panel público se podrán aprovisionar las nuevas empresas, las cuales recibirán inmediatamente su propia base de datos y su propio subdominio.

## Despliegue en produccion

En produccion, [Caddy](https://caddyserver.com) es el unico punto de entrada: termina HTTPS, redirige HTTP a HTTPS, sirve `/static/` y `/media/` y pasa el resto a gunicorn. Usa un certificado wildcard de Let's Encrypt para el dominio base y todos sus subdominios, asi que cada inquilino nuevo funciona sin tocar Caddy ni el DNS. El certificado se obtiene y se renueva solo con el desafio DNS-01 a traves de la API de Cloudflare.

1. **Requisitos previos:**

* Un servidor donde Caddy pueda usar los puertos 80 y 443 (TCP) y 443 (UDP), y WireGuard el 51820 (UDP). Si el servidor ya tiene otro proxy en esos puertos, esta configuracion no aplica tal cual.
* Un dominio con el DNS gestionado en Cloudflare.
* En Cloudflare, dos registros `A` con la IP publica del servidor: uno para el dominio base (`@`) y otro para `*`. Ambos en modo **Solo DNS** (nube gris); con el proxy de Cloudflare activo, el TLS terminaria en Cloudflare y no en Caddy, y el UDP de WireGuard no pasaria.
* Un token de API de Cloudflare con los permisos **Zona: Leer** y **DNS: Editar**, limitado a la zona del dominio. Cuando el servidor tenga IP fija, conviene restringir el token a esa IP.

2. **Configuracion de entorno:**

Crear un archivo `.env` en el directorio raiz. Ademas de las variables de la base de datos, el correo y WireGuard (iguales a las de `.env.dev`), produccion necesita:

```env
# Configuracion Django
DJANGO_SECRET_KEY=clave_larga_y_aleatoria
DJANGO_ALLOWED_HOSTS=.tudominio.com
DJANGO_DEBUG=false
SECURE_HSTS_SECONDS=3600

# Configuracion Caddy
DOMINIO_BASE=tudominio.com
CF_API_TOKEN=token_de_cloudflare
ACME_EMAIL=tu_correo@ejemplo.com

# Configuracion wireguard
WG_HOST=ip_publica_del_servidor

# Concurrencia (gunicorn y Celery)
WEB_CONCURRENCY=3
CELERY_WORKER_CONCURRENCY=2
```

* `DJANGO_ALLOWED_HOSTS` lleva un punto al inicio para aceptar el dominio base y todos sus subdominios.
* `CF_API_TOKEN`, `DOMINIO_BASE` y `ACME_EMAIL` son obligatorias: si falta alguna, `docker compose` no arranca e indica cual. El servicio `caddy` recibe solo estas tres variables, no el `.env` completo.
* `ACME_EMAIL` es el correo donde Let's Encrypt avisa si hay problemas con el certificado.
* `SECURE_HSTS_SECONDS` empieza en una hora. Cuando produccion este probada y estable, subirlo a un año (`31536000`). HSTS hace que los navegadores recuerden usar solo HTTPS durante ese tiempo, asi que un valor alto con un problema de certificados deja el sitio inaccesible hasta que expire.

3. **Arranque:**

```bash
docker compose up -d --build
```

Caddy pide el certificado al arrancar. Para comprobarlo:

```bash
docker compose logs -f caddy
```

Debe aparecer `certificate obtained successfully` para el dominio base y para `*.tudominio.com`. Si falla con `Invalid request headers`, el token no llego al contenedor; con `expected 1 zone, got 0`, el dominio no se resuelve por un DNS publico.

Para probar sin gastar solicitudes del limite de Let's Encrypt, se puede agregar temporalmente `acme_ca https://acme-staging-v02.api.letsencrypt.org/directory` al bloque global de `caddy/Caddyfile`. El certificado de staging no es de confianza para los navegadores; una vez que funcione, quitar la linea completa y reiniciar Caddy.

4. **Inicializacion de la arquitectura multi-tenant:**

El dominio principal del inquilino publico debe ser el dominio base: de el salen los subdominios de las empresas nuevas (`slug.tudominio.com`).

```bash
docker compose exec web python manage.py create_tenant --schema_name=public --domain-domain=tudominio.com --domain-is_primary=True --name="NucleoISP Central"
docker compose exec web python manage.py create_tenant_superuser --schema_name=public
```

5. **Notas de operacion:**

* La imagen de Caddy se compila con el modulo de Cloudflare (`caddy/Dockerfile`). Para actualizarla, cambiar la version en los dos `FROM` y en el nombre de la imagen del compose, y reconstruir con `docker compose build caddy`.
* El volumen `caddy_data` guarda los certificados y la cuenta de Let's Encrypt; debe persistir entre despliegues.
* `python manage.py check --deploy` muestra dos advertencias a proposito:
    * **W008** (`SECURE_SSL_REDIRECT`): la redireccion a HTTPS la hace Caddy. Activarla tambien en Django causaria un bucle de redirecciones si el proxy dejara de enviar `X-Forwarded-Proto`, y romperia los chequeos internos por HTTP.
    * **W021** (`SECURE_HSTS_PRELOAD`): no se solicita la lista de precarga HSTS de los navegadores, porque salir de ella tarda meses.

---
