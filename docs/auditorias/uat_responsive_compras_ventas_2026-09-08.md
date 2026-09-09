# UAT Local: distribución y acciones operativas — CHG-266

Evidencia histórica del 8 de septiembre de 2026. Estado vivo: `docs/contexto/ESTADO_ACTUAL.md`. Preserva CHG-262–265; no constituye release QA.

## Criterios de aceptación y solución

- Producción / Órdenes: cerrar la guía no comprime Control de orden ni las bandejas de materiales/devoluciones. La guía es hija directa del layout; las tarjetas de control viven en la columna principal y las bandejas de CHG-265 se insertan en `.production-orders-main`.
- Compras / Proveedores: entrada por listado, Nuevo proveedor y Editar en modal independiente. Guardar vuelve al listado; cancelar no escribe; un error conserva captura y permite reintento. Se mantienen los códigos fiscales/comerciales existentes aunque no sean opciones predeterminadas. Permisos create/update antes de abrir y autorización backend sin cambio.
- Compras / Requisiciones: la distribución anterior tenía seis controles en cinco columnas. Ahora el artículo ocupa seis de doce columnas, toda la fila bajo 680 px del formulario; bajo 380 px todos los campos se apilan. El select fuente invisible conserva 1 px sin padding ni desplazamiento que aumente el scroll. Se preservan búsqueda, identidad y ID estable.
- Ventas / Cotizaciones: mensajes explican Borrador → Emitir cotización → Cotizada → Aprobar cotización → Aprobada. Acciones solo con su permiso; orientación cuando falte. Un rechazo conserva el estado confirmado. Botones y tarjetas permiten envolver líneas.

Las clases explícitas `.production-orders-layout` y `.purchasing-requisitions-layout` apilan guía y contenido bajo 720 px del contenedor `module-panel`. Excepción acotada: el componente compartido conserva su riel lateral fuera de estos ámbitos. El modal de proveedores responde a su propio contenedor.

## Configuración Local de cotizaciones

No cambia el ciclo ni se inventan permisos. Admin Local solo tenía create/read/update en su catálogo de cotizaciones. Se repusieron los cuatro códigos existentes en OpenAPI (`sales.quote.submit`, `.approve`, `.expire`, `.cancel`) mediante inserción acotada de metadatos del extractor canónico. Se asignaron al Owner del tenant permitido mediante API auditada de Admin, preservando cada asignación/alcance y enviando `expected_revision=1`. La sesión real posterior confirmó los cuatro permisos. Restaura el baseline del seed demo; runtime no concede autoridad por nombre de rol.

`local-write`: frontend 127.0.0.1:4173; APIs loopback; PostgreSQL 127.0.0.1:5434/erclave_local; Firebase Emulator demo-erclave. Tenant exclusivo `ten_739ee59d765d5e14818674800d`, actor `admin.qa@erclave.local`, Owner `rol_0040d63992545b9f9db16e1366`. Únicas escrituras persistentes del corte: cuatro registros del catálogo global local y sus asignaciones a ese Owner. No se asignaron a Supervisor ni a otros tenants. No se ejecutó el seed completo ni se mutaron documentos comerciales reales. Sin migración, escritura remota, despliegue, commit, push o PR.

Consulta documental sin delegación: negocio/técnicos de Producción, Compras, Ventas y Administración; Arquitectura/API, Seguridad, UX/i18n, QA y Gobierno documental en AGENTES.md. Skills erclave-feature y erclave-environment-boundaries. Ownership permanece en cada servicio; sin FK ni escrituras de servicios entre schemas.

## APIs afectadas

**Contratos modificados: Ninguna.** Requests/responses y permisos existentes se conservan. Endpoints involucrados, consumidos sin cambio:

| Servicio | Método y ruta | Permiso / propósito |
|---|---|---|
| Purchasing | GET /v1/purchasing/suppliers | purchasing.supplier.read; listado y recarga |
| Purchasing | POST /v1/purchasing/suppliers | purchasing.supplier.create; alta desde modal |
| Purchasing | PATCH /v1/purchasing/suppliers/{id} | purchasing.supplier.update; edición sin reenviar código |
| Purchasing | GET /v1/purchasing/requisitions | purchasing.requisition.read; listado |
| Purchasing | POST /v1/purchasing/requisitions | purchasing.requisition.create; captura existente |
| Purchasing | PATCH /v1/purchasing/requisitions/{id} | purchasing.requisition.update; captura existente |
| Inventory | GET /v1/inventory/items | inventory.item.read; artículos del selector |
| Sales | GET /v1/sales/quotes | sales.quote.read; listado y recarga |
| Sales | POST /v1/sales/quotes/{id}/submit | sales.quote.submit; emitir |
| Sales | POST /v1/sales/quotes/{id}/approve | sales.quote.approve; aprobar |
| Sales | POST /v1/sales/quotes/{id}/expire | sales.quote.expire; vencer |
| Sales | POST /v1/sales/quotes/{id}/cancel | sales.quote.cancel; cancelar |
| Admin | GET /v1/session/context | identidad autenticada y membresía; permisos efectivos |
| Admin | GET /v1/roles | admin.role.read; revisión del Owner Local |
| Admin | PUT /v1/roles/{role_id}/permissions | admin.role.permissions.manage; reparación Local auditada con revisión/alcances |

Lecturas auxiliares del workspace, comandos de Producción, handoffs, PDF, edición de cotizaciones, recepciones y entregas permanecen como en CHG-265. APIs no tocadas: contratos y runtime de todos los servicios. Ninguna integración, persistencia o topología cambia; sus diagramas permanecen vigentes.

## Validación y rollback

Pruebas: `tests/e2e/local-uat-layout.spec.js`, regresión de proveedor con códigos no predeterminados en `frontend-contracts.spec.js` y catálogo de permisos de cotización en Admin. Browser usa Firebase Emulator y sesión Admin real, mutaciones comerciales interceptadas (éxito/rechazo), tenant comprobado y red no local bloqueada. Capturas ES/EN revisadas: requisiciones con paneles 1100/780/520/320 px, Órdenes 1000/520 px con riel abierto/cerrado, modal proveedores 480/320 px y tarjeta de cotización 320 px. Resultado final de verify y regresión registrado en CHG-266 de TRAZABILIDAD.md.

Rollback: revertir solo UI/i18n/index/pruebas CHG-266 preservando CHG-262–265. Si se retira la reparación de acceso, quitar únicamente esos cuatro permisos del Owner mediante Admin con su revisión actual, conservando otras asignaciones y auditoría. Los metadatos canónicos pueden permanecer sin conceder acceso. No hay downgrade ni reversa de inventario.

Pendiente: aceptación manual y autorización explícita antes de preparar/promover QA. Los cambios y la reparación de datos no se transfieren automáticamente.
