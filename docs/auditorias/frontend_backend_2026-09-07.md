# Auditoria de coherencia frontend/backend — CHG-262

Fecha de inicio: 2026-09-07. Ambiente: **Local aislado**. Base de codigo revisada: `735312b`, posterior a CHG-261. Los cambios de esta auditoria permanecen en el working tree; no estan publicados en QA.

## Alcance y criterio

Revision de consumidores `frontend/api/`, formularios y handlers de `frontend/app.js`, Backoffice, schemas Pydantic, rutas/permisos y OpenAPI de los siete servicios implementados. Se contrastaron campos condicionales, propiedades admitidas en alta/edicion, valores iniciales, transiciones, permisos de lectura y comandos compuestos. Los modulos futuros no se consideran implementados por mostrar una maqueta o tener contrato.

Criterio: un formulario no promete guardar campos que el contrato ignora; un campo oculto no bloquea ni contamina otra rama; los permisos se comprueban antes del primer comando de una operacion compuesta; las consultas autorizadas no dependen de permisos ajenos; el rechazo backend conserva el formulario y no confirma exito.

No es una certificacion de todas las combinaciones posibles de roles, datos y fallas distribuidas. La matriz de fallas Production–Inventory, paginacion contractual y volumen productivo continúan en `docs/contexto/PENDIENTES.md`.

## Frontera efectiva

| Recurso | Destino comprobado |
|---|---|
| Frontend y Backoffice | `http://127.0.0.1:4173/` y `/backoffice/` |
| Admin / Production / Inventory / RH | Loopback: `8000`, `8002`, `8004`, `8006` |
| Sales / Purchasing / Maintenance | Loopback: `8008`, `8010`, `8012` |
| PostgreSQL | `127.0.0.1:5434/erclave_local` |
| Identidad | Firebase Auth Emulator `demo-erclave`, `9099`; UI `4000` |
| Tenant operativo | `ten_739ee59d765d5e14818674800d`, ERClave Demo QA |
| Actor Local | `usr_595f3cd6d4325901a8dbd028e1`, cuenta sintetica del Emulator |

Clasificacion: `read-only` para inspeccion; `local-write` para codigo, evidencia y fixtures de pruebas. Se arranco el stack desde la configuracion canonica con una copia temporal que omite ambos seeds. El sandbox requirio elevacion para iniciar PostgreSQL fuera del workspace. No hubo migraciones, seeds, cargas operativas, Cloud SQL Proxy, acceso QA/Produccion, deploy, push ni PR. El Emulator preparo su cuenta sintetica; las pruebas PostgreSQL usan sus fixtures aisladas. Los nuevos ensayos de formularios interceptan las mutaciones y bloquean destinos remotos; no crean documentos, movimientos, proveedores ni consumen folios reales. Backoffice se recorre en lectura.

## Agentes consultados

Consulta de las fichas de `AGENTES.md`, sin delegacion: negocio y tecnica de Produccion, Inventory, RH, Compras, Ventas, Mantenimiento y Administracion/Backoffice; Arquitectura SaaS/API, Seguridad, QA/validadores, Sinergia, UX/i18n y Gobierno de documentacion viva. Ownership y permisos pertenecen al backend existente; no se agregan permisos, tablas ni escrituras entre schemas. No aplica migracion DB ni release QA.

Skills aplicadas: `.agents/skills/erclave-feature/SKILL.md` y `.agents/skills/erclave-environment-boundaries/SKILL.md`.

## Hallazgos corregidos

| ID | Caso confirmado | Comportamiento corregido |
|---|---|---|
| F01 | Editar Producto/Servicio permitia cambiar `type`, ausente en PATCH. | Tipo de solo lectura al editar; se conserva la naturaleza original y el servicio envia vinculo nulo. |
| F02 | Altas de almacenes, articulos, areas, puestos y maquinas ofrecian estatus que sus creates no admiten. | Las altas muestran Activo sin permitir otra seleccion; la edicion conserva cambios de estatus admitidos. |
| F03 | La ficha de Producto/Servicio hacia una segunda mutacion de estatus despues de guardar. | La ficha conserva el estatus; su cambio se realiza en el comando separado del catalogo y con su permiso. |
| F04 | Politica de articulo editable pero ausente de ItemUpdate; `lot` no coincidia con la opcion UI `batch`. | Politica de solo lectura al editar y representacion correcta de `lot`, sin cambiar la API. |
| F05 | Cambiar un alta vinculada de producto terminado a materia prima conservaba un producto oculto y la unidad bloqueada. | Se limpia/deshabilita el vinculo y se habilita la unidad; solo `finishedGood` puede enviar el enlace. |
| F06 | Salidas y ajustes negativos API se bloqueaban usando saldos calculados desde movimientos parciales del navegador. | Inventory valida existencia y reservas en modo API; el calculo de maqueta queda restringido a mock. |
| F07 | Al pasar de transferencia a otro movimiento se conservaba el almacen destino. | Destino solo visible, habilitado y obligatorio para transferencia; el resto envia nulo. |
| F08 | Requisicion: al volver de Servicio a Articulo podia persistir la unidad del servicio. | Se recupera la unidad del articulo seleccionado y el selector de Inventory se deshabilita para Servicio. |
| F09 | Cancelacion Compras aceptaba 1–1000 caracteres; backend exige 3–500. | Limites HTML y validacion de texto recortado alineados, con mensaje ES/EN. |
| F10 | Fecha de nacimiento editable en RH aunque WorkerUpdate no la admite. | Se conserva como solo lectura al editar; continua capturable en el alta. |
| F11 | Editar maquinaria con costo cero sustituia 0 por 1.80. | Se preserva cero mediante fallback solo para valor ausente. |
| F12 | Fechas de planeacion de servicio se insertaban como datetime y el navegador descartaba el valor date. Tiempo sin maximo de contrato. | Controles date desde el primer render y limite de 1440 minutos por registro. |
| F13 | Admin, Production, RH y Purchasing exigian permisos de todas sus colecciones para cargar una lectura puntual. | Consultas seleccionadas por permiso efectivo; no se realizan las consultas no autorizadas. Mantenimiento solicita solo maquinas/ordenes productivas pertinentes. |
| F14 | Produccion mostraba acciones sin permiso, eliminacion sin API y aprobacion compuesta que podia fallar tras enviar. La receta ofrecia Obsoleta sin comando correspondiente. | Acciones con permisos puntuales; eliminacion deshabilitada en API; preflight antes de guardar/enviar/aprobar; edicion comienza como borrador, con opciones de aprobacion autorizadas. |
| F15 | Resolver Mantenimiento siempre hacia PATCH aunque el rol solo tuviera `maintenance.order.resolve`. | Sin permiso de actualizar, usa el diagnostico ya guardado y solo ejecuta resolver; no permite editar esos campos. |
| F16 | Campos de maqueta aparentaban persistencia: numero de version/centro de receta, reserva configurable del almacen y ubicacion del movimiento. | Version/centro de receta solo lectura; controles sin respaldo API ocultos/deshabilitados en ese modo. |
| F17 | Editar proveedor sustituia codigos existentes ausentes de listas cortas y aplicaba CP mexicano a otro pais. | Conserva regimen, pais, moneda y condiciones existentes; respeta longitud de CP no mexicano. No crea nuevos catalogos fiscales. |

## Verificacion

- Baseline `npm.cmd run verify`: validadores aprobados, 234 pruebas backend y 11 omitidas por PostgreSQL apagado.
- `npm.cmd run verify:local`: validadores, compilacion, 245 pruebas backend PostgreSQL sin omisiones, mas 25 pruebas Playwright aprobadas (6 previas, 18 de coherencia y 1 de Backoffice). Resultado sincronizado en `ESTADO_ACTUAL.md`.
- `tests/e2e/current-flows.spec.js`: autenticacion, tenant, seis modulos y sus submodulos, 28 tarjetas de reportes, paginacion y Servicio sin Inventory.
- `tests/e2e/frontend-contracts.spec.js`: fixtures sinteticas solo en memoria de navegador; campos inmutables/condicionales, preservacion de valores, rechazo backend, lecturas con permisos puntuales, aprobaciones y resolucion. Las mutaciones se interceptan, nunca alcanzan los servicios.
- `tests/e2e/backoffice-readonly.spec.js`: login Local y secciones Alta, Administracion y Uso; peticiones mutantes y remotas bloqueadas.
- Responsive: modal de cancelacion en contenedor estrecho a viewport de 390 px, ES/EN, sin desbordamiento; capturas inspeccionadas bajo `test-results/`. No se cambio CSS ni composicion compartida.
- Warning ya existente: deprecacion Starlette/httpx. No se modificaron dependencias durante esta auditoria.

## APIs afectadas

**Contratos modificados: ninguno.** Cambian exclusivamente seleccion de consultas, controles y construccion de payloads frontend. No se modifica request/response, permisos backend ni persistencia. Las rutas con identificadores de prueba se interceptan en E2E.

| Servicio | Metodos y rutas consumidos o condicionados sin cambio contractual | Permisos existentes |
|---|---|---|
| Admin | `GET /v1/session/context`; `GET /v1/tenants/{tenant_id}`; `GET /v1/tenants/{tenant_id}/entitlements` | Sesion autenticada; `admin.tenant.read` para tenant/entitlements |
| Admin | `GET /v1/settings`; `GET /v1/document-template`; `GET /v1/catalogs/code-sequences` | `admin.setting.read` en este consumidor |
| Admin | `GET /v1/users`; `GET /v1/roles`; `GET /v1/permissions` | `admin.user.read`; `admin.role.read` |
| Admin | `GET /v1/catalogs/units-of-measure`; `GET /v1/catalogs/commercial/{catalog_code}` | `admin.unit.read`; `admin.catalog.read` en dashboard |
| Admin | `POST /v1/catalogs/code-sequences/{document_type}/next` | Permiso existente del documento; interceptado en regresion de alta |
| Production | `GET /v1/production/product-services`; `GET /v1/production/recipes`; `GET /v1/production/machines`; `GET /v1/production/orders` | `production.product_service.read`, `production.recipe.read`, `production.machine.read`, `production.order.read` |
| Production | `POST /v1/production/product-services`; `PATCH /v1/production/product-services/{id}`; `PATCH /v1/production/product-services/{id}/status` | `production.product_service.create`, `.update`, `.status.update` |
| Production | `PUT /v1/production/product-services/{id}/finished-good-link` | `inventory.item.create` y `production.product_service.update` |
| Production | `POST /v1/production/recipes`; `POST /v1/production/recipes/{id}/versions`; `PATCH /v1/production/recipe-versions/{id}`; `POST /v1/production/recipe-versions/{id}/submit`; `POST /v1/production/recipe-versions/{id}/approve` | `production.recipe.create`, `.update`, `.submit`, `.approve` |
| Production | `POST /v1/production/machines`; `PATCH /v1/production/machines/{id}` | `production.machine.create`, `.update` |
| Inventory | `POST /v1/inventory/warehouses`; `PATCH /v1/inventory/warehouses/{id}`; `POST /v1/inventory/items`; `PATCH /v1/inventory/items/{id}`; `POST /v1/inventory/movements` | `inventory.warehouse.create/update`, `inventory.item.create/update`, `inventory.movement.create` |
| RH | `GET /v1/hr/areas`; `GET /v1/hr/positions`; `GET /v1/hr/workers` | `hr.area.read`, `hr.position.read`, `hr.worker.read` |
| RH | `POST /v1/hr/areas`; `POST /v1/hr/positions`; `PATCH /v1/hr/workers/{id}` | `hr.area.create`, `hr.position.create`, `hr.worker.update` |
| Purchasing | `GET /v1/purchasing/suppliers`; `GET /v1/purchasing/requisitions`; `GET /v1/purchasing/orders`; `GET /v1/purchasing/receipts` | `purchasing.supplier.read`, `.requisition.read`, `.order.read`, `.receipt.read` |
| Purchasing | `PATCH /v1/purchasing/suppliers/{id}`; `POST /v1/purchasing/requisitions`; `PATCH /v1/purchasing/requisitions/{id}`; `POST /v1/purchasing/requisitions/{id}/cancel`; `POST /v1/purchasing/orders/{id}/cancel` | `purchasing.supplier.update`, `.requisition.create/update/cancel`, `.order.cancel` |
| Sales | `POST /v1/sales/service-orders/{id}/plan`; `POST /v1/sales/service-orders/{id}/time-entries` | `sales.service_order.plan`, `.time.create` |
| Maintenance | `PATCH /v1/maintenance/orders/{id}`; `POST /v1/maintenance/orders/{id}/transitions` | `maintenance.order.update`; `maintenance.order.resolve` en el caso corregido |
| Backoffice | `GET /v1/backoffice/tenants`; `GET /v1/backoffice/modules`; `GET /v1/backoffice/usage` | Identidad interna allowlisted; sin mutaciones |

APIs no tocadas: implementaciones backend de los siete servicios, contratos/eventos internos, endpoints de los modulos futuros y ambientes remotos. Otras lecturas de catalogo y reportes se ejercitan mediante la regresion vigente sin cambiar sus consumidores.

## Rollback

Revertir solamente el diff de CHG-262 conservando cambios ajenos. No requiere downgrade ni restaurar datos operativos. La revision Local permanece `20260901_0030`; QA mantiene su release anterior. Los procesos locales pueden detenerse por sus puertos/PID identificados, sin afectar servicios remotos.
