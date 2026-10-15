# CONT-08 — Contexto de cotizaciones por División

CHG-303 · 2026-10-05 · Local aislado, working tree sobre HEAD 213f75c. Primer corte de CONT-08; no separación operativa completa.

## Continuación CHG-304

La conversión dimensionada ya está implementada en [Pedidos](cont_08_pedidos_contexto.md). La matriz API de CHG-303 conserva el bloqueo histórico, superado por CHG-304. [Servicios CHG-305](cont_08_servicios_contexto.md) y [stock/entrega CHG-307](cont_08_stock_contexto.md) también están implementados Local. [Fabricación dimensionada CHG-315](cont_08_fabricacion_contexto.md) implementada Local; las brechas restantes están en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md).

## Comportamiento y fronteras

Desde Ventas → Cotizaciones → Contexto organizacional se consulta la copia guardada y, con permiso de actualización, se busca y selecciona una División para un borrador existente. Requiere cliente/asociación activos, condiciones explícitas confirmadas y recursos elegibles. Sales conserva la cotización y snapshot; Admin autoriza División/Sociedad; RH y Producción sólo exponen elegibilidad por HTTP. No hay escritura cruzada entre schemas ni FK a otros servicios.

La primera asignación fija División y cliente. Se requiere moneda idéntica entre borrador y condiciones: no hay conversión ni reinterpretación de importes. Las condiciones de pago se toman del registro explícito de esa División. La copia incluye valores, revisión de condiciones e identidad de División/Sociedad; el límite de crédito guardado no implementa control de exposición. Cambios posteriores en condiciones no cambian documentos; el usuario puede actualizar explícitamente la copia en borrador. Si cambió la moneda, debe preparar otro borrador con moneda/importes correctos. Tras abandonar borrador no se actualiza la copia.

El servidor aplica alcance en listado/detalle/CSV de cotizaciones dimensionadas y en sus mutaciones. Revalida recursos al editar/enviar/aprobar; cliente/asociación dentro de la transacción propia. Orden de locks: cotización, maestro, asociación. expected_revision controla cambios del contexto; Idempotency-Key y auditoría conservan el resultado atómico. Reintentar no evita comprobar autorización vigente. Fallo remoto no produce guardado parcial; no se promete atomicidad distribuida con autoridades externas.

La conversión dimensionada fue bloqueada sólo en CHG-303; [CHG-304](cont_08_pedidos_contexto.md) la habilitó conservando contexto. Cotizaciones legacy mantienen comportamiento por tenant y no reciben asignación automática. Emisor/impresión, fabricación, documentos Compras, folios y mapeo real siguen abiertos; stock y servicios ya tienen sus recorridos Local. Accounting y analítica permanecen planned.

## Persistencia

Alembic `20261005_0046`, padre 0045: sales.quotes añade division_ref_id, society_ref_id, organization_revision y commercial_terms_snapshot JSONB. Constraint de contexto completo o ausente; índice tenant/División/status. Filas anteriores quedan sin contexto/revisión cero. Downgrade sólo si no existen cotizaciones dimensionadas ni auditoría quote.context; con historia corresponde forward-fix. Pruebas con rollback en tenant ten_739ee59d765d5e14818674800d, PostgreSQL loopback 5434/erclave_local. Sin asociaciones ni condiciones ficticias permanentes.

## APIs afectadas

Matriz histórica del delta CHG-303; los bloqueos superados remiten a la continuación vigente descrita arriba.

| Servicio / método / ruta | Permiso | Cambio |
|---|---|---|
| Sales GET /v1/sales/organization/quote-divisions | sales.quote.update | Nuevo lookup acotado q/offset/limit, alcance Admin. |
| Sales PUT /v1/sales/quotes/{quote_id}/organization-context | sales.quote.update | Nuevo body division_ref_id + expected_revision; Idempotency-Key; respuesta QuoteRead con copia/revisión. No acepta Sociedad enviada. |
| Sales GET /v1/sales/quotes | sales.quote.read | Filtra dimensionadas por alcance; campos nuevos en QuoteRead. |
| Sales GET /v1/sales/quotes/{quote_id} | sales.quote.read | Alcance y campos nuevos. |
| Sales POST /v1/sales/quotes | sales.quote.create | Request sin cambio; respuesta añade contexto nullable y revisión 0. |
| Sales PATCH /v1/sales/quotes/{quote_id} | sales.quote.update | Request sin cambio; contexto fija cliente/moneda/pago; revalida recursos. Respuesta ampliada. |
| Sales POST /v1/sales/quotes/{quote_id}/submit | sales.quote.submit | Alcance, disponibilidad y respuesta ampliada. |
| Sales POST /v1/sales/quotes/{quote_id}/approve | sales.quote.approve | Alcance, disponibilidad y respuesta ampliada. |
| Sales POST /v1/sales/quotes/{quote_id}/expire | sales.quote.expire | Alcance y respuesta ampliada. |
| Sales POST /v1/sales/quotes/{quote_id}/cancel | sales.quote.cancel | Alcance y respuesta ampliada. |
| Sales POST /v1/sales/orders | sales.order.create | Request/response conservados; 409 si origen dimensionado. |
| Sales GET /v1/sales/reports/{report_code}/export | Permiso del reporte; quotes: sales.quote.read | CSV quotes filtra alcance; otros reportes conservados. |
| HR GET /v1/hr/division-workers | hr.worker.read o sales.quote.update/submit/approve | resource_id opcional exacto; exige módulo consumidor habilitado además de HR. Respuesta sin cambio. |
| Production GET /v1/production/division-product-services | production.product_service.read o sales.quote.update/submit/approve | resource_id opcional exacto; exige módulo consumidor habilitado además de Production. Respuesta sin cambio. |

Consumidas sin cambio: Admin GET /v1/session/context; GET /v1/catalogs/commercial/{catalog_code}/by-code/{code}; GET /v1/catalogs/commercial/{catalog_code}; GET /v1/catalogs/units-of-measure/by-code/{code}; HR GET /v1/hr/workers/sales-eligible; Production GET /v1/production/product-services/{product_id}; Inventory GET /v1/inventory/items/{item_id}. Condiciones se leen dentro de Sales, sin llamada HTTP ni escritura en Admin. APIs Purchasing, Inventory, Maintenance, Costing y Accounting sin cambios en este corte.

## Evidencia y agentes

Fichas de negocio/técnica de Ventas, RH, Producción, Administración y Contabilidad y guardianes Arquitectura/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA consultadas; sin delegación. Skills feature, accounting, module-boundaries, db-migration, environment-boundaries, form-contract/form-feedback, qa-evidence y solution-manuals. Interfaz ES/EN, búsqueda acotada, feedback negativo y captura conservada. Fuente del manual actualizada; Word pendiente del runtime documents requerido y revisión visual (python-docx sí está disponible).

Pruebas focales PostgreSQL/API: 99 aprobadas sin omisiones. Interfaz focal: 6 aprobadas ES/EN, incluyendo retry con misma clave, permisos, borrador/historia, error de recurso/moneda y contenedor 320px. Migración upgrade/downgrade vacío/upgrade aprobados. Gate general aprobado: 528 backend aprobadas/133 omitidas sin DB, validadores y compilación correctos. Suite browser transversal 197 aprobadas. Smoke Emulator/API Local read-only aprobado; Sales/HR/Production recargados. Captura 320px inspeccionada. Evidencia final en TRAZABILIDAD CHG-303. No equivale a UAT ni promoción QA.
