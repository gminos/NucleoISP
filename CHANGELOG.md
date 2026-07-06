# Registro de Cambios (Changelog)

Todas las novedades, cambios y correcciones del proyecto Administrador ISP serán documentadas en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/), y este proyecto se adhiere a [Versionamiento Semántico (SemVer)](https://semver.org/lang/es/).

## [2.3.4] - 2026-07-06

### Arreglado
- **Multitenencia:** Se eliminó el dominio base estático (`localhost`) al crear nuevas empresas (inquilinos). Ahora el dominio se hereda dinámicamente consultando el dominio primario del esquema público, garantizando el funcionamiento transparente en entornos de producción y desarrollo.
- **Documentación:** Se corrigió el dominio público de desarrollo en el `README.md` (`nucleoisp.localhost` -> `localhost`) siguiendo las convenciones estándar.

### Cambiado
- **Refactorización:** Se reorganizaron las importaciones de dependencias en `nucleo_admin/admin.py` adoptando el estilo visual de "pirámide invertida" (orden descendente por longitud) y se eliminaron las importaciones en línea (`inline imports`) para mejorar la legibilidad y las buenas prácticas.

## [2.3.3] - 2026-07-01

### Arreglado
- **Infraestructura (Docker):** Se solucionó una condición de carrera (race condition) en el arranque de la base de datos PostgreSQL que causaba que los contenedores de Celery (Worker y Beat) colapsaran (`DuplicateTable`). Ahora, las migraciones de Django se ejecutan exclusivamente en el contenedor `web` mediante la variable condicional `RUN_MIGRATIONS=true` en los archivos `docker-compose.yml` y `docker-compose.dev.yml`.

## [2.3.2] - 2026-07-01

### Arreglado
- **Facturación y Contabilidad:** Se cambió la regla de borrado en cascada (`models.CASCADE`) por protección estricta (`models.PROTECT`) en las relaciones de `Factura`, `Cargo` y `Transaccion` hacia los modelos de `Instalacion` y `Cliente`. Esto impide la eliminación accidental de historiales financieros y transacciones huérfanas al borrar una instalación o cliente del sistema.

## [2.3.1] - 2026-07-01

### Arreglado
- **Instalaciones:** Se eliminó la propiedad `null=True` del campo `router` en la base de datos y se aplicó protección en cascada (`on_delete=models.PROTECT`). Esto obliga a que toda instalación tenga un router asignado para garantizar la creación automática de usuarios PPPoE y evita borrar routers que tengan instalaciones activas.

## [2.3.0] - 2026-07-01

### Añadido
- **Panel de Administración (Routers):** Se integró una nueva acción personalizada ("Mikrotik: Ver usuarios conectados") que permite consultar en tiempo real el listado y la cantidad de sesiones activas directamente desde la API de Mikrotik (`/ppp/active`).
- **Lógica de Red (Mikrotik):** Se implementó la función `obtener_conectados` en el core de interacción con Mikrotik (`redes/mikrotik_cliente.py`).
- **Infraestructura:** Se añadió el mapeo del volumen `./redes:/app/redes` en el archivo `docker-compose.yml` para los servicios `web` y `celery`, garantizando la correcta sincronización de código en el entorno de producción.

## [2.2.1] - 2026-07-01

### Cambiado
- **Interfaz (Facturas PDF):** Se optimizó la hoja de estilos (CSS) de la plantilla de facturación (`factura_pdf.html`). Se ajustaron los márgenes (`1.5cm`), tipografía (`11pt`) y espaciados internos a un "punto medio" para evitar que facturas con 2 cargos generen un desbordamiento hacia una segunda página sin perder el diseño premium.
- **Nomenclatura Contable:** Se renombró la cabecera de la tabla de cargos de "Subtotal" a "Total" para eliminar la redundancia cognitiva con la fila inferior.
- **Diseño Responsivo (Nombres Largos):** Se forzó un salto de línea (`<br>`) debajo de la etiqueta "Facturado a:" para asegurar que los nombres de clientes inusualmente largos tengan el ancho total de la columna, evitando cortes asimétricos o desalineaciones visuales en la tabla.

## [2.2.0] - 2026-06-30

### Añadido
- **WhatsApp API (Multipage PDF):** Se implementó una lógica de concatenación vertical usando la librería `Pillow` en el servicio de WhatsApp. Esto asegura que si una factura o comprobante de pago abarca múltiples páginas, todas las hojas se fusionarán en una sola imagen (tipo pergamino) de manera transparente, evitando descartar datos de los cargos de los clientes.

## [2.1.9] - 2026-06-30

### Corregido
- **Base de Datos (Migraciones):** Se aplicaron y generaron las migraciones correspondientes a la base de datos para reflejar el cambio estructural de los campos `DateField` (de `timezone.now` a `timezone.localdate`). Esto asegura que la integridad de esquema concuerde con el código fuente.
- **Zonas Horarias (Facturación):** Se reparó el desfase de horas UTC en transacciones y facturas.

## [2.1.8] - 2026-06-30

### Cambiado
- **Correos Electrónicos (UX/UI):** Se actualizó la paleta de colores de la plantilla HTML `bienvenida_isp.html` para coincidir con la identidad corporativa de NucleoISP (azul/índigo profundo `#4f46e5`). Se removió la firma genérica duplicada.
- **Correos Electrónicos (Fix):** Se implementó un identificador invisible dinámico (`timestamp` UNIX) al final de los correos del sistema para evitar que clientes como Gmail colapsen el pie de página bajo la etiqueta de "Contenido recortado" (`[...]`) en hilos de correos múltiples.

## [2.1.7] - 2026-06-30

### Corregido
- **Seguridad / Rendimiento (Debug Toolbar):** Se solucionó una fuga de información y rendimiento en producción donde el panel `django-debug-toolbar` se inyectaba en las páginas incluso si `DJANGO_DEBUG` estaba en `false`. El módulo se removió de las listas quemadas (`TENANT_APPS` y `MIDDLEWARE`) y ahora se carga dinámicamente solo si `DEBUG` es verdadero.

## [2.1.6] - 2026-06-30

### Cambiado
- **Documentación (README):** Se eliminó el paso manual redundante de ejecutar `migrate_schemas --shared` de la guía de despliegue inicial, ya que esta acción ahora está automatizada en el script de arranque de Docker (`entrypoint.sh`).

## [2.1.5] - 2026-06-30

### Corregido
- **Entrypoint de Docker (Migraciones):** Se parcheó un bug crítico en `entrypoint.sh` donde las migraciones no se estaban ejecutando al inicializar los contenedores. Se agregaron los comandos obligatorios de `django-tenants` (`migrate_schemas --shared` y `migrate_schemas --tenant`) para asegurar que cualquier base de datos en blanco despliegue todas las tablas automáticamente antes de iniciar Gunicorn, evitando el error 500 "relation does not exist".

## [2.1.4] - 2026-06-30

### Corregido
- **Infraestructura Nginx/Docker:** Se corrigió un error crítico arquitectónico en el proxy inverso y en la orquestación de Docker que impedía la persistencia y carga de archivos subidos por el usuario (logos de inquilinos). Se creó el volumen `media_data` en Docker Compose y se mapeó a la ruta `/media/` en `nginx.conf`.
- **Seguridad Web:** Se añadieron cabeceras X-Forwarded-Proto al Proxy Inverso para proteger contra ataques CSRF y permitir que Django construya URIs absolutas correctas detrás de una terminación SSL (HTTPS). Adicionalmente, se configuraron cabeceras HTTP Upgrade para soporte de WebSockets y timeouts optimizados.

## [2.1.3] - 2026-06-30

### Cambiado
- **UX/UI (Navegación):** Se reordenó el menú lateral del panel de administración (Django Unfold). La sección "Redes e Infraestructura" ahora aparece por encima de "Ajustes generales", siguiendo el principio de diseño de jerarquizar las operaciones core del modelo de negocio por sobre las configuraciones estáticas de un solo uso.

## [2.1.2] - 2026-06-30

### Cambiado
- **Documentación del Proyecto:** Reescritura completa del archivo `README.md` para reflejar la evolución arquitectónica del proyecto hacia una plataforma B2B SaaS Multi-Tenant. Se integró el logotipo oficial de NucleoISP, se estandarizó la terminología (ej. "multi-tenant", "secrets"), se agregó la mención de notificaciones por WhatsApp, y se actualizaron las instrucciones de despliegue local para incluir configuraciones de correo electrónico (`EMAIL_HOST`), la nueva estructura `.env.dev` y el aprovisionamiento de subdominios. Se eliminó la sección de infraestructura por ser redundante.

## [2.1.1] - 2026-06-30

### Cambiado
- **Refactorización de Importaciones:** Refactorización estética (chore) en los módulos de `tasks.py` y `signals.py` dentro de la aplicación de `redes`. Se movieron todas las importaciones locales e internas hacia la cabecera del archivo, y se aplicó una regla de ordenamiento estricta por longitud de caracteres (de mayor a menor) para asegurar un código más limpio y legible según los estándares del proyecto.

## [2.1.0] - 2026-06-29

### Agregado
- **Adoctrinamiento Automático de Routers:** Nuevo sistema de señales (`signals.py`) en la aplicación de redes que detecta cuando un ISP registra un nuevo enrutador Mikrotik. Al ser detectado, se dispara una tarea asíncrona en Celery que busca todos los planes existentes en la base de datos del inquilino y los inyecta automáticamente en el nuevo equipo, eliminando la necesidad de sincronización manual y mejorando la experiencia de onboarding (UX).

## [2.0.1] - 2026-06-29

### Corregido
- **Caché y Assets Estáticos:** Implementado nuevo logotipo vectorial (`.svg`) de fondo transparente con branding oficial de NucleoISP. Se forzó la invalidación del caché estático cambiando las referencias en `settings.py` para asegurar que el cambio se refleje instantáneamente en las interfaces en la nube.

## [2.0.0] - 2026-06-29

Esta versión marca la evolución del proyecto de un Gestor ISP individual a una Plataforma SaaS B2B Multi-Inquilino. Ahora el sistema es capaz de alojar y gestionar a múltiples ISPs simultáneamente con aislamiento de bases de datos, control financiero y automatización de clientes.

### Agregado
- **Facturación SaaS B2B:** Nuevo modelo de gestión financiera para inquilinos (EmpresaISP) que incluye campos de estado de cuenta, fecha de próximo pago y días de gracia.
- **Middleware "Kill Switch":** Sistema de seguridad y proxy reverso que bloquea automáticamente a los ISPs morosos, redirigiendo su tráfico a una pantalla de "Servicio Suspendido".
- **Onboarding Automatizado:** Envío automático de credenciales (usuario y contraseña temporal) por correo electrónico al registrar un nuevo ISP, garantizando el principio de "Cero Confianza" (Zero Trust).
- **App Usuarios:** Nueva aplicación dedicada para la gestión del modelo de usuarios base (`usuarios`).

### Modificado
- **Arquitectura Multi-tenant:** Refactorización masiva de bases de datos utilizando esquemas de PostgreSQL (`django-tenants`), rompiendo la compatibilidad con el esquema público original de la v1.0.0 para lograr aislamiento de datos por ISP.
- **Estructura de Señales (Signals):** Implementación de archivos `signals.py` separados para las apps de facturación, instalaciones y planes para desacoplar la lógica de negocio.
- **Dependencias Docker:** Actualización de `pyproject.toml` y `docker-compose.yml` para reflejar el uso del gestor de paquetes `uv`.

### Corregido
- **Filtro Celery WhatsApp:** Solucionado error en el modelo de consultas asíncronas de facturación, asegurando que los recibos solo se generen para facturas en mora o estado parcial.

## [1.0.0] - 2026-06-21

Esta es la primera versión oficial estable ("Lanzamiento Inicial"). Convierte el proyecto de una prueba de concepto en un software completo de gestión para Proveedores de Servicios de Internet (ISP), incorporando control total sobre la red y automatización de cobros.

### Agregado (Nuevas Funciones)
- **Integración Mikrotik:** Comunicación bidireccional con equipos RouterOS mediante la API (Puerto 8728).
- **Control de Red:** Posibilidad de verificar usuarios conectados (Active Sessions) directamente desde el panel de instalaciones.
- **Botones de Acción (Admin):** Botones manuales en el panel para Suspender y Reactivar clientes de forma instantánea.
- **Corte Automático (Celery):** Sistema en segundo plano (Celery Beat) programado diariamente a las 00:01 AM para identificar y desconectar a los clientes morosos.
- **Reactivación Inmediata:** Restauración automática de la conexión del cliente al momento de registrar un pago en caja.
- **Inteligencia de Facturación:** El sistema de "Caja Rápida" ahora distribuye los pagos aplicando un peso jerárquico que prioriza las mensualidades sobre los cobros de instalación.
- **Notificaciones WhatsApp:** Generación de recibos PDF y envío automático por WhatsApp utilizando PyWa.

### Modificado
- El archivo `README.md` fue reescrito para eliminar detalles de proyectos anteriores y reflejar la naturaleza real de este sistema como un producto ISP.
- Refactorización de las vistas y modelos de la aplicación `facturacion` para soportar las tareas automáticas en segundo plano.

### Corregido
- Solucionado error visual (formato `NoneType`) al intentar eliminar instalaciones que provocaba la caída del panel.
- Solucionado error donde los pagos en caja absorbían el dinero a favor de las instalaciones viejas en lugar de las mensualidades activas.
