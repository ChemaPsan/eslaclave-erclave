# CONT-08 — Pedidos con contexto de cotización

## Continuación CHG-305

[Servicios](cont_08_servicios_contexto.md) y [stock → reserva → entrega](cont_08_stock_contexto.md) ya están implementados Local. Los 409 de la matriz API describen el delta histórico CHG-304; [fabricación dimensionada CHG-315](cont_08_fabricacion_contexto.md) implementada Local. Consultar [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md) para no reabrir recorridos cerrados.

CHG-304 · 2026-10-05 · Local aislado sobre HEAD 213f75c, working tree sin commit. Continúa CHG-303; no representa separación completa.

## Alcance del bloque

Una cotización aprobada con División ya puede convertirse en pedido. Sales revalida alcance, Sociedad vigente, cliente/asociación activos y elegibilidad de responsable/productos mediante HR/Production. El pedido copia División, Sociedad, revisión del contexto y condiciones de la cotización aprobada, NO las condiciones actuales del maestro ni de la División. Cambio de condiciones posterior no reinterpreta documentos. Sin conversión monetaria, sin control de saldo crediticio, sin Accounting ni centros obligatorios.

La transacción propia bloquea la cotización y vuelve a comprobar estado/revisión, conserva identidad única por tenant/cotización, copia snapshot y registra order.context. Reintento autorizado no duplica pedido ni órdenes de servicio. Los folios de servicio se asignan con clave estable por la autoridad Admin; no hay transacción distribuida ni garantía de folios sin huecos ante fallo posterior.

Las órdenes de servicio creadas automáticamente consultan el contexto fijo de su pedido mediante relación propia tenant/order_id; no duplican el snapshot ni leen la configuración vigente. Lecturas/listados y reportes pedidos, margen comercial y órdenes de servicio respetan alcance. Usuarios fuera de División reciben denegación en detalle/mutación y no ven documentos en listas/CSV. El actor se autoriza antes de replay y antes de efectos.

La cancelación del pedido dimensionado conserva contexto e historial y cancela sus órdenes de servicio pendientes mediante el ciclo existente. La interfaz muestra División/Sociedad/condiciones/revisión, sin campos editables para sustituirlas. El formulario de cancelación conserva motivo al fallar y reutiliza clave al reintentar el mismo motivo.

## Contrato del formulario

| Control | Tarea/origen | Contrato |
|---|---|---|
| División/Sociedad/condiciones/revisión | Consultar la copia aprobada, derivada en servidor | Sólo lectura en pedido y servicio; sin selector ni payload de reemplazo. |
| Motivo de cancelación, reason | Explicar la cancelación del pedido; captura explícita | Obligatorio sólo al cancelar, permiso sales.order.cancel; string trim de 3–500 caracteres según ActionReasonRequest, inicialmente vacío, conservado ante rechazo y registrado en auditoría. Binding reason → control reason. Mismo motivo conserva clave de reintento. |

## Frontera vigente y evolución

El bloqueo general de downstream correspondió a CHG-304. CHG-305 habilitó planeación/ejecución/tiempos/costos/evidencia de servicios; CHG-307 habilitó stock, reservas y entregas. Fabricación dimensionada todavía no se habilita por la preparación CHG-308. Los documentos legacy conservan su flujo por tenant, sin asignación automática.

Pendientes: adaptación monetaria de servicios CC-08, fabricación CC-10/11/12 y documentos Purchasing, además de folios, Emisor/impresión y datos reales. No confundir snapshot con libro contable.

## Datos y ambiente

Alembic `20261005_0047`, padre 0046. sales.orders agrega division_ref_id, society_ref_id, quote_organization_revision y commercial_terms_snapshot JSONB. Constraint contexto completo/ausente e índice tenant/División/status. Modelos y schemas alineados. Sin FK cruzada, backfill ni escrituras ajenas a Sales. Downgrade bloqueado cuando existan pedidos dimensionados o auditoría order.context; con historia usar forward-fix.

Local-write exclusivamente 127.0.0.1:5434/erclave_local y tenant ten_739ee59d765d5e14818674800d, Firebase Emulator 9099 y APIs loopback. Upgrade/downgrade vacío/upgrade comprobados. Fixtures PostgreSQL con rollback. Ninguna asignación, condición o pedido dimensionado permanente. QA/Producción intactos.

## APIs afectadas

Matriz histórica del delta CHG-304; los bloqueos superados remiten a la continuación vigente descrita arriba.

Todos los paths Sales siguientes usan prefijo /v1/sales. Requests conservan sus campos actuales; no se captura contexto nuevo en el pedido.

| Método / ruta | Permiso | Cambio |
|---|---|---|
| GET /orders | sales.order.read | Filtra alcance; respuesta incorpora cuatro campos de contexto. |
| GET /orders/{order_id} | sales.order.read | Alcance y respuesta ampliada. |
| POST /orders | sales.order.create | Habilita conversión dimensionada; copia de cotización aprobada, revalidación, respuesta ampliada. |
| POST /orders/{order_id}/fulfillment | sales.order.fulfill | 409 para dimensionados; respuesta ampliada para pedidos. |
| POST /orders/{order_id}/cancel | sales.order.cancel | Alcance antes de efectos; conserva contexto en respuesta. |
| GET /service-orders | sales.service_order.read | Filtra alcance y expone contexto fijo del pedido. |
| GET /service-orders/{service_order_id} | sales.service_order.read | Alcance y contexto del pedido. |
| POST /service-orders/{service_order_id}/plan | sales.service_order.plan | Alcance, 409 en dimensionados; respuesta ampliada. |
| POST /service-orders/{service_order_id}/time-entries | sales.service_order.time.create | Alcance, 409 en dimensionados; respuesta ampliada. |
| POST /service-orders/{service_order_id}/cost-entries | sales.service_order.cost.create | Alcance, 409 en dimensionados; respuesta ampliada. |
| POST /service-orders/{service_order_id}/evidence | sales.service_order.evidence.create | Alcance, 409 en dimensionados; respuesta ampliada. |
| POST /service-orders/{service_order_id}/transitions/{action} | sales.service_order.{action} | Alcance, 409 en dimensionados; respuesta ampliada. |
| POST /deliveries | sales.delivery.create | Alcance de pedido; 409 en dimensionados antes de crear entrega. |
| GET /reports/{report_code}/export | sales.order.read o sales.service_order.read según reporte | Filtra orders/commercial-margin/service-orders; request/formato CSV conservados. |
| HR GET /v1/hr/division-workers | hr.worker.read o permisos Sales ya admitidos o sales.order.create | Agrega permiso de conversión; módulos HR y consumidor Sales activos, scope efectivo. Request/response sin cambio. |
| Production GET /v1/production/division-product-services | production.product_service.read o permisos Sales ya admitidos o sales.order.create | Agrega permiso de conversión; módulos Production y consumidor Sales activos. Request/response sin cambio. |

Consumidas sin modificación: Admin GET /v1/session/context, GET /v1/catalogs/commercial/{catalog_code}/by-code/{code}, GET /v1/catalogs/units-of-measure/by-code/{code}, POST /v1/catalogs/code-sequences/{document_type}/next; HR GET /v1/hr/workers/sales-eligible; Production GET /v1/production/product-services/{product_id}. APIs de cotizaciones conservadas. Inventory/Purchasing/Maintenance/Costing/Accounting no modificadas; no efectos downstream dimensionados.

## Evidencia y responsables

Fichas consultadas de negocio/técnica Ventas, RH, Producción, Inventarios, Administración y Contabilidad; guardianes Arquitectura/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature, accounting, module-boundaries, db-migration, environment-boundaries, form-contract/form-feedback, qa-evidence y solution-manuals. Sin delegación.

Migración local reversible vacía aprobada; PostgreSQL/API focal 105 aprobadas sin omisiones. Dos recorridos UI real ES/EN con mutaciones interceptadas aprobados (snapshot, escape, bloqueo de ejecución, cancelación fallida y clave estable). Verify aprobado: validadores, compilación y 528 backend aprobadas/139 omitidas sin DB. Browser transversal 197 aprobadas; formularios reales 18/24 inicialmente y 6/6 en repetición tras cuatro timeouts pre-login y corrección de dos fixtures al contrato de validación. Error 422 del motivo vinculado a control, captura 320px inspeccionada. Smoke real read-only aprobado; Sales/HR/Production recargados. Evidencia final en TRAZABILIDAD CHG-304. Fuente manual actualizada; Word sigue pendiente de runtime documents y revisión visual. No se certifica UAT ni release.
