# ERClave — Módulo de Administración y Configuración

## Selector de Sociedad / División · CHG-329 · Local

La barra superior presenta la Sociedad y División activas en un control dedicado. La lista muestra los nombres completos y código de cada División autorizada; elegir otra revalida la sesión y conserva la preferencia por usuario/tenant. Soporta mouse, foco de teclado y Escape. Centro de costos se consulta y edita desde Administración → Organización → Divisiones → Centros de costos; no forma parte del selector global.

## CC-18 - CHG-323 - Local

Admin controla las secuencias de Puestos RH, movimientos Inventory, proveedor/requisicion/orden/recepcion Purchasing y orden Maintenance. El consumidor autorizado consulta su configuracion y solicita el siguiente folio con clave idempotente. En modo manual el operador captura el codigo; movimientos automaticos Inventory derivan uno estable del origen. Admin filtra tipos por permiso. Los codigos previos permanecen intactos; CC-20 y QA pendientes.


## Vigencia y relaciones · conciliación CHG-311

Núcleo administrativo desplegado en QA. Sólo Local: organización normalizada, sesión y alcances por División, plantilla por alcance, catálogo de Centros de costos, presentación histórica CC-17 y consumidores de folios CC-18. CC-19 aún requiere mapeo y asignación de datos reales; CC-20 requiere aceptación integrada.

Estado por ambiente: [ESTADO_ACTUAL](../docs/contexto/ESTADO_ACTUAL.md). Brechas y cierre: [CONTROL_CONTABLE](../docs/contexto/CONTROL_CONTABLE.md). Relación operativa: [06_costos_centros_de_costos](06_costos_centros_de_costos.md). Contrato/regla: [cont_04_configuracion_por_alcance](../docs/arquitectura/cont_04_configuracion_por_alcance.md). Navegación: [índice de módulos](README.md).

Las referencias CHG conservan procedencia; no se suman como pendientes vigentes. La historia de implementación está en [TRAZABILIDAD](../TRAZABILIDAD.md). Costos y tarifas deben usar moneda base de Sociedad (CHG-309); su aplicación se verifica por flujo en el control, sin reinterpretar historia. Centro requerido sólo donde el flujo de imputación esté habilitado.

**CHG-297 Local:** [CONT-05 catálogo básico](../docs/arquitectura/cont_05_catalogo_centros.md) ya permite administrar centros por División desde Administración, con dueño Costing y permisos propios. No habilita cálculos ni Accounting. Centro obligatorio únicamente por flujo de imputación habilitado; asignaciones CONT-07 implementadas y consumidores CONT-08 parciales según CONTROL_CONTABLE.

**CHG-296 Local:** [plantilla por Sociedad/División y disponibilidad de capacidades](../docs/arquitectura/cont_04_configuracion_por_alcance.md). Herencia y ajustes administrativos disponibles. CHG-322 integró la presentación histórica de cotizaciones y órdenes de producción; los demás productores se revisan según su contrato y la aceptación integrada sigue pendiente.


**CHG-294 — modularidad opcional:** organización y operación no requieren Accounting. Catálogo básico de centros en Administración, propiedad de Costing; análisis de Costos y ejecución contable tienen activaciones independientes. Diseño y obligatoriedad condicional; autorización puntual del catálogo implementada en CONT-05 en [frontera de capacidades](../docs/arquitectura/contabilidad_opcional_y_capacidades.md). No cambia runtime ni habilita módulos.


## CONT-03 / CHG-293 — Sesión y alcance en Local

Administración → Usuarios → Alcance organizacional permite seleccionar Divisiones concretas o todas, incluidas futuras. Consulta requiere `admin.user.read`; guardar usa `admin.user.update`; buscar Divisiones usa `admin.division.read`. La sesión muestra Sociedad/División autorizadas y deriva Emisor. Vacío no fabrica Matriz. Edición versionada, auditoría y reintento idempotente; las invitaciones nuevas tienen alcance vacío y deben asignarse explícitamente. [Contrato y límites](../docs/arquitectura/cont_03_sesion_alcances.md). Configuración por alcance y catálogo de centros están implementados Local; persistencia operativa CONT-07/08 tiene cobertura parcial según CONTROL_CONTABLE.

## CONT-02 / CHG-292 — Organización disponible en Local

Administración → Organización muestra Emisores, Sociedades y Divisiones con búsquedas acotadas, alta/edición, estados, permisos y feedback ES/EN. Cada Sociedad selecciona un único Emisor y moneda activa (MXN inicial); cada División selecciona Sociedad. Los datos corporativos se conservan en un panel desplegable. Los datos fiscales se editan en Emisor y no se duplican en Sociedad. Los dependientes activos impiden desactivar un padre.

Las tablas normalizadas son autoridad tras el switch revisado; los contratos antiguos siguen como adaptadores deprecados. Revisión Local 0038. Contrato de campos, permisos, rutas, recuperación y pruebas: [CONT-02](../docs/arquitectura/cont_02_administracion_organizacional.md). CONT-03 agrega sesión/scopes en CHG-293. Centros de costos están implementados mediante contrato con Costing; Accounting sigue planned.

## Estructura organizacional CHG-289 — etapa previa al switch

El usuario definió un Emisor para varias Sociedades y exactamente un Emisor por Sociedad, con libros a nivel Sociedad. CONT-01 implementa en Local las tablas y la importación compatible; `organization.profile` conservó autoridad operativa durante CONT-01. CONT-02 ya implementa APIs/formularios; scopes siguen en CONT-03. Ver [CONT-01](../docs/arquitectura/cont_01_estructura_organizacional.md).

Administración ofrece en Local el alta de Centros de costos por División (CONT-05); la Sociedad se deriva de División. Costing conserva el catálogo técnico y Admin lo opera mediante contrato. Los formularios de asignaciones admiten centro opcional validado por División; sólo los flujos de imputación habilitados pueden exigirlo (CONT-07/08). La moneda base de Sociedad será configurable, inicialmente MXN; operaciones en otra moneda conservan tipo de cambio e importe convertido. Estas pantallas/afectaciones no se declaran implementadas por existir las tablas. [Plan vigente](../docs/arquitectura/plan_preparacion_contabilidad.md).

## Feedback de formularios — Local y QA

Alta de rol conserva codigo, nombre y descripcion al fallar. Backoffice integra login, onboarding, editor y filtros; no persiste contrasenas para restaurar la captura. Se aplica el helper transversal con ES/EN, foco, ARIA y rutas estructuradas. Skill obligatoria: [.agents/skills/erclave-form-feedback/SKILL.md](../.agents/skills/erclave-form-feedback/SKILL.md). Evidencia: [docs/auditorias/formularios_feedback_2026-09-13.md](../docs/auditorias/formularios_feedback_2026-09-13.md).

Feedback desplegado en Local y QA mediante el release `e57237f`. Las pruebas 422 de pantalla usan respuestas simuladas; no sustituyen UAT ni cobertura exhaustiva del módulo. Estado y pendientes autenticados: [docs/contexto/ESTADO_ACTUAL.md](../docs/contexto/ESTADO_ACTUAL.md) y [docs/operaciones/release_qa_20260914.md](../docs/operaciones/release_qa_20260914.md).

## Coherencia de consultas Local (CHG-262)

El dashboard consulta solo los recursos permitidos por la sesion: una lectura de Roles no exige permisos de Usuarios, Tenant o Configuracion. Las colecciones omitidas por falta de permiso no conceden autoridad ni fabrican datos. Backoffice conserva el control allowlisted y se verifica en lectura con Firebase Emulator. Evidencia: [docs/auditorias/frontend_backend_2026-09-07.md](../docs/auditorias/frontend_backend_2026-09-07.md).

## 1. Objetivo

El módulo de Administración y Configuración permitirá controlar la configuración funcional del sistema por tenant, módulos, submódulos, usuarios, roles, permisos, centros de negocio, catálogos y parámetros operativos.

Este módulo será transversal y deberá soportar el crecimiento modular de ERClave.

---

## 2. Alcance

- tenants;
- centros de negocio;
- áreas;
- usuarios;
- roles;
- permisos;
- módulos;
- submódulos;
- catálogos base;
- unidades de medida;
- idiomas;
- monedas;
- condiciones de pago;
- configuraciones por módulo;
- bitácora de cambios;
- parámetros por tenant.

---

## 3. Entidades principales

| Entidad | Descripción |
|---|---|
| Tenant | Cliente o empresa que usa ERClave. |
| Centro de negocio | Unidad operativa dentro del tenant. |
| Área | División funcional interna. |
| Usuario | Persona con acceso al sistema. |
| Rol | Conjunto de permisos. |
| Permiso | Acción autorizada sobre un recurso. |
| Módulo | Bloque funcional principal. |
| Submódulo | Funcionalidad dentro de un módulo. |
| Catálogo | Lista administrable de valores. |
| Parámetro | Configuración específica del tenant o módulo. |

---

## 4. Modularidad

ERClave deberá permitir:

- n módulos;
- n submódulos por módulo;
- activación por tenant;
- activación por plan;
- permisos por rol;
- permisos por centro de negocio;
- configuración por cliente;
- dependencias entre módulos.

### Ejemplo

```text
Modulo: Producción
  Submódulo: Productos y servicios
  Submódulo: Recetas
  Submódulo: Ordenes de producción
  Submódulo: Asignación por área
  Submódulo: Costeo estimado
```

---

## 5. Roles iniciales sugeridos

| Rol | Alcance |
|---|---|
| Propietario del tenant | Control general del cliente. |
| Administrador corporativo | Control sobre varios centros de negocio. |
| Administrador de centro | Control limitado a un centro. |
| Supervisor de producción | Gestión operativa de producción. |
| Operador | Ejecución de tareas asignadas. |
| Compras | Gestión de requisiciones y órdenes. |
| Ventas | Gestión comercial. |
| Finanzas/Gastos | Gestión de gastos y pagos. |
| Consulta/reportes | Solo lectura y reportes autorizados. |
| Integrador técnico | Gestión de apps/API según permisos. |

---

## 6. Reglas de negocio

- Ningún usuario cliente deberá acceder a la consola interna de EsLaClave.
- Los usuarios solo deberán ver información de su tenant.
- Los permisos deberán considerar módulo, submódulo, acción y alcance.
- Algunos roles podrán crear usuarios, pero solo dentro de su alcance.
- Los módulos desactivados no deberán mostrarse ni permitir operación.
- Los catálogos podrán tener valores globales y valores propios del tenant.
- Los cambios de configuración relevantes deberán auditarse.
- Las dependencias entre módulos deberán estar configuradas para evitar operaciones incompletas.
- Si un módulo depende de otro no contratado, deberá existir modo degradado definido.
- Los catálogos compartidos deberán ser reutilizados por todos los módulos para evitar duplicidad.

---

## 7. Permisos sugeridos

Los permisos deberán nombrarse de forma consistente.

Ejemplos:

```text
production.recipes.read
production.recipes.create
production.recipes.update
production.orders.approve
warehouses.movements.create
purchases.orders.approve
sales.orders.cancel
expenses.documents.validate
reports.costs.read
admin.users.create
```

---

## 8. Catálogos base

Los catalogos base son configuraciones transversales que deberan administrarse desde este modulo para evitar valores duplicados o quemados dentro de cada modulo funcional.

La referencia ampliada se documenta en [docs/catalogos_base.md](../docs/catalogos_base.md).

En Local, `currencies` y `payment_terms` ya son catalogos tenant-safe administrables desde una vista dedicada. Ventas acepta solo valores activos; los defaults iniciales pueden inactivarse y el cliente puede agregar valores propios. Estados de cotizacion, pedido y entrega no son catalogos editables: son maquinas de estado protegidas por cada backend.

Administracion tambien es propietaria de `document.template`: logo, color primario, acento, texto, pie y numeracion. Cotizaciones y ordenes de Produccion consumen la misma configuracion al imprimir/guardar como PDF; todo generador documental futuro debe leer este contrato. El administrador puede reemplazar o quitar el logo. El data URL de logo (PNG/JPEG/WebP, maximo decodificado de 1 MB y firma binaria validada) es una solucion Local; antes de promover a QA se sustituira por una referencia de object storage sin cambiar el contrato consumidor. La regla transversal vive en [[docs/arquitectura/plantillas_documentales.md](../docs/arquitectura/plantillas_documentales.md)](../docs/arquitectura/plantillas_documentales.md).

| Grupo | Catalogos iniciales |
|---|---|
| Transversales | centros de negocio, areas, roles, permisos, unidades de medida, monedas, impuestos, prioridades, idiomas. |
| Produccion | tipos de producto/servicio, tipos de recurso, estados de receta, estados de orden, motivos de pausa, motivos de reproceso. |
| Almacenes | tipos de almacen, politicas de inventario, tipos de movimiento, motivos de ajuste, estados de inventario, tipos de ubicacion fisica. |
| Compras | tipos de proveedor, condiciones de pago, metodos de entrega, estados de requisicion, estados de orden de compra, motivos de rechazo. |
| Ventas | tipos de cliente, listas de precio, condiciones comerciales, estados de cotizacion, estados de pedido, canales de venta. |
| Gastos | tipos de gasto, categorias de gasto, metodos de pago, estados de gasto, tipos de comprobante, motivos de rechazo. |
| Costos | centros de costo, drivers de prorrateo, metodos de costeo, tipos de variacion, tipos de costo. |
| Contabilidad | cuentas contables, periodos contables, tipos de poliza, tipos de documento origen, tipos de operacion, estados contables, reglas de mapeo contable. |

### 8.1 Unidades de medida

Estado: implementado en Local y QA. El catalogo pertenece a Administracion, se aisla por tenant y se provisiona con 50 unidades UN/CEFACT Rec. 20. La tarjeta de Configuracion base abre una vista dedicada, sin extender indefinidamente el panel principal. Soporta consulta bilingue, alta de unidades propias, edicion e inactivacion; cada comando exige `Idempotency-Key`, conserva `X-Correlation-Id` y genera auditoria. Produccion e Inventarios resuelven `GET /v1/catalogs/units-of-measure/by-code/{code}`, validan el codigo activo y sus formularios usan seleccion en lugar de captura libre.

### 8.2 Folios y consecutivos

Estado: implementado en Local y QA. Cada tenant recibe configuraciones iniciales para productos, recetas, ordenes de produccion, maquinaria, almacenes, articulos, movimientos, areas, puestos, empleados, clientes, cotizaciones, pedidos y entregas.

| Campo | Significado |
|---|---|
| Prefijo | Texto estable anterior al numero, por ejemplo `REC`, `OP` o `COT`. |
| Separador | Caracter entre prefijo y numero. |
| Siguiente numero | Consecutivo que se reservara en la proxima alta; no puede retroceder. |
| Longitud | Cantidad de digitos con ceros a la izquierda. |
| Modo administrado | ERClave reserva el siguiente folio de forma atomica e idempotente. |
| Modo manual | El usuario captura el codigo; el servicio propietario valida formato y unicidad. |

Cambiar una configuracion no renombra documentos historicos. La reserva de un folio requiere el permiso de alta del documento consumidor; consultar o editar el catalogo requiere `admin.setting.read` o `admin.setting.update` respectivamente.

---

## 9. Dependencias funcionales entre módulos

Administración deberá permitir configurar dependencias como:

| Módulo | Dependencias recomendadas |
|---|---|
| Producción | Almacenes, Costos, Centros de costos. |
| Almacenes | Catálogo de productos/recursos, Costos. |
| Compras | Proveedores, Almacenes, Gastos, Contabilidad opcional. |
| Ventas | Clientes, Almacenes, Producción opcional, Costos, Contabilidad opcional. |
| Gastos | Proveedores, Centros de costos, Contabilidad opcional. |
| Costos | Producción, Almacenes, Compras, Gastos, Ventas. |
| Contabilidad | Cuentas contables, periodos, anexos y mapeos. |
| Reportes | Todos los módulos activos y permisos. |

### Reglas de activación

- Un módulo podrá activarse aunque otro no esté contratado solo si existe un modo degradado funcional.
- Si Contabilidad está activa, Ventas, Gastos, Compras, Almacenes y Costos deberán validar mapeos contables.
- Si Almacenes está activo, Producción y Ventas deberán usar reservas y movimientos reales.
- Si Costos está activo, Producción, Compras, Gastos y Ventas deberán alimentar costos reales.
- Si Reportes está activo, todos los módulos deberán enviar dimensiones comunes.

---

## 10. Integraciones

| Módulo | Relación |
|---|---|
| Todos los módulos | Control de permisos, catálogos y configuración. |
| Infraestructura SaaS | Tenants, planes, módulos activos y límites. |
| APIs | Scopes, apps externas y permisos técnicos. |
| Reportes | Alcance de visibilidad por rol. |

---

## 11. Pendientes

- Definir matriz inicial de permisos.
- Definir roles del MVP.
- Definir catálogo de módulos y submódulos.
- Definir qué configuraciones serán por tenant.
- Definir bitácora de cambios administrativos.
- Implementar los catalogos pendientes desde su tarjeta en `Administracion > Catalogos base`; Unidades de medida ya esta completo en una vista dedicada.
- Migrar las opciones fijas restantes del MVP a catalogos administrables cuando el flujo lo requiera.

## 11.1 Gobierno de modulos por tenant

Estado: implementado en Local y QA.

La disponibilidad de un modulo se resuelve en dos niveles que no pueden sustituirse entre si:

1. Backoffice interno controla el entitlement contractual mediante `status`: `active`, `inactive` o `suspended`.
2. El administrador del tenant controla solamente `tenant_enabled` sobre un entitlement `active` concedido previamente por Backoffice.

Un modulo es efectivo cuando `status = active` y `tenant_enabled = true`. El catalogo `admin` es obligatorio y no puede retirarse ni apagarse. Backoffice puede editar nombre comercial, razon social, plan, zona horaria e idioma regional del tenant, y solo habilita modulos con runtime `implemented`; los modulos `planned` se muestran bloqueados. Cada cambio exige idempotencia, correlacion, aislamiento por `tenant_id` y auditoria. Retirar un entitlement no elimina datos ni permisos configurados: bloquea su ejecucion y permite recuperarlos al rehabilitarlo.

El catalogo declara dependencias efectivas. En el corte actual `sales` requiere `hr` y `production`: Backoffice, onboarding y Administracion rechazan activar Ventas si falta alguna, y rechazan apagar RH o Produccion mientras Ventas siga efectivo. La validacion se repite dentro de la transaccion que bloquea los entitlements del tenant para evitar combinaciones invalidas por concurrencia. Durante onboarding se insertan primero los modulos y despues se asignan al owner sus permisos, de modo que el primer `session/context` coincide con lo contratado.

En ambientes con Firebase, Backoffice tambien coordina el ciclo de identidad del owner. La persistencia administrativa y la entrega/limpieza Firebase se informan como resultados separados: una invitacion puede quedar `pending` despues de crear el tenant, y una eliminacion confirmada puede devolver `firebase_identity_cleanup.status=pending` para reconciliacion. El runtime Admin necesita el rol minimo `roles/firebaseauth.admin`; ese rol administra identidades del proveedor, pero no concede membresias, modulos ni permisos ERClave.

---

## 12. Editor de permisos por rol

El editor administra un rol a la vez y conserva personalizacion permiso por permiso. No incluye plantillas, presets ni seleccion automatica basada en el nombre del rol.

CHG-236 incorpora en Local capacidades puntuales para cada transicion de Produccion y Mantenimiento y para recibir producto terminado. El catalogo las deriva de OpenAPI y las presenta como asignaciones independientes. Un permiso nuevo nace sin asignarse a roles existentes; el administrador decide que rol y, por herencia, que usuarios reciben cada autoridad.

Flujo:

1. Abrir un rol y seleccionar **Editar permisos**.
2. Cargar el catalogo completo asignable y las asignaciones actuales con su `scope`.
3. Buscar por nombre humano, descripcion o codigo tecnico; filtrar por asignados, no asignados o cambios.
4. Seleccionar o quitar permisos individuales, por modulo o solo sobre resultados visibles.
5. Revisar el resumen de permisos agregados y retirados.
6. Guardar una sola vez con revision esperada e idempotencia.

Reglas:

- Los nombres visibles usan verbo + objeto en Espanol/Ingles; el codigo estable permanece como detalle tecnico.
- Filtrar o colapsar un modulo nunca altera permisos ocultos.
- Los permisos de un modulo inactivo se conservan como configuracion historica, pero no pueden agregarse ni ejecutarse hasta reactivarlo.
- Permisos `internal`, `public` o de credenciales de integracion no son asignables a roles humanos del tenant.
- Un permiso nuevo aparece desmarcado; no se agrega implicitamente a roles existentes.
- La UI mantiene `original` y `draft`; salir con cambios exige confirmar descarte.
- El backend rechaza revision obsoleta, permiso no asignable, modulo no disponible, rol de otro tenant o intento inseguro sobre rol de sistema.
- El guardado aplica diferencias y conserva `scope` de asignaciones no modificadas.
- La auditoria registra actor, revision anterior/nueva, agregados, retirados y scopes modificados.

Responsive y accesibilidad:

- En contenedor amplio se usa matriz por recurso y accion.
- En contenedor estrecho cada recurso se transforma en tarjeta etiquetada sin scroll horizontal de pagina.
- Checkboxes nativos, labels completos, foco visible, controles de modulo con estado mixto y resumen `aria-live`.

## CHG-209: seleccion escalable

Rol, sucursal activa y entidad legal usan búsqueda por identidad visible. Permisos conservan su buscador especializado y selección por matriz. Categorías, estados y opciones estructurales breves permanecen como listas directas; activar módulos no es un catálogo operativo masivo.

## CHG-211: excepcion de portada

Administración conserva en su primera vista el centro de configuración de organización, usuarios, roles, permisos, módulos activos y catálogos base. No adopta la portada de reportes estándar de los módulos operativos porque es el lugar donde se gobierna el sistema. La excepción es funcional y está protegida por el validador transversal.


## Ajustes UAT Local CHG-266

Se repusieron en el catálogo Local los cuatro permisos existentes sales.quote.submit/approve/expire/cancel y se asignaron al Owner del tenant permitido mediante API auditada, preservando sus asignaciones y alcances. No se ejecutó el seed completo ni se concedieron a otros roles/tenants; no existe bypass por nombre Owner.

Evidencia y APIs: [docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md](../docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md).


## Disponibilidad QA CHG-270

Los cambios Local documentados hasta CHG-268 fueron promovidos en el release `b63cdad` a QA el 9 de septiembre de 2026. Salud/readiness/versión y rechazo de accesos no autenticados comprobados; aceptación funcional autenticada pendiente del tester. Datos QA existentes preservados. Evidencia: [docs/operaciones/release_qa_20260908.md](../docs/operaciones/release_qa_20260908.md).

## CC-17 - presentacion efectiva de documentos - CHG-322 Local

Administracion resuelve plantilla Corporativo > Sociedad > Division e identidad de Emisor, Sociedad y Division por contrato de solo lectura para consumidores autorizados. El editor existente conserva propiedad de los overrides. Sales y Production almacenan snapshots en sus propios documentos; cambios posteriores en Admin no modifican impresiones aprobadas/liberadas. [Contrato](../docs/arquitectura/cont_04_configuracion_por_alcance.md).
