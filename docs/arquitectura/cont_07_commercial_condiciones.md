# CONT-07 — Condiciones comerciales explícitas por División

CHG-302 · 2026-09-28 · Local aislado sobre HEAD `213f75c`, working tree sin commit. Fichas consultadas: negocio/técnico Compras, Ventas, Administración y Contabilidad; Arquitectura/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature, accounting, module-boundaries, db-migration, environment-boundaries, form-contract/form-feedback, qa-evidence y solution-manuals. Sin delegación.

## Decisión aprobada

El usuario elige **opción 2: condiciones explícitas por División, sin herencia**. Cambiar el maestro no modifica las condiciones de ninguna División. No se copian automáticamente desde el maestro ni desde otra División; no existe restaurar herencia. La jerarquía de plantillas CONT-04 conserva sus reglas propias: esta decisión corresponde a condiciones comerciales de clientes/proveedores.

Las asociaciones CHG-301 existentes siguen siendo disponibilidad del maestro. Sin un registro de condiciones, GET devuelve values null, revisión 0 y requires_confirmation true. No se infieren condiciones ni se crean datos en una migración. La disponibilidad de un maestro no acredita que su configuración comercial esté completa.

## Campos y flujo

| Campo | Dueño/origen | Contrato y tarea |
|---|---|---|
| Cliente/proveedor y División | Asociación comercial propia autorizada por Admin | Ya existentes; varias Divisiones conservan un solo maestro. |
| Sociedad confirmada | Derivada de División en servidor | Se guarda al confirmar; no se captura ni se hereda. |
| Moneda | Catálogo Admin, código persistido por Sales/Purchasing | Requerida, código activo, 3–12 caracteres. Define la unidad monetaria de las condiciones. |
| Condiciones de pago | Catálogo Admin | Requeridas, código activo, 1–40 caracteres; no texto libre. |
| Límite de crédito del cliente | Sales | Requerido, Decimal no negativo, Numeric(18,2), máximo 9999999999999999.99; cero válido. Configuración, no control de saldo/exposición. |
| Plazo de entrega del proveedor | Purchasing | Requerido, entero 0–3650 días; cero válido. No infiere fechas prometidas. |
| Revisión | Dueño del registro de condiciones | Independiente de la revisión de disponibilidad; expected_revision 0 al crear. |

En Ventas → Clientes o Compras → Proveedores → Disponibilidad por División, selecciona una asociación guardada y abre **Condiciones de esta División**. Alta muestra campos vacíos; edición carga exclusivamente condiciones guardadas. Captura completa, guardado explícito y lectura tras recarga. No hay defaults del maestro ni botón para heredar. ES/EN, CSS del panel comercial en contenedor de 320px.

Leer requiere permiso read propio y alcance actual/histórico autorizado. Guardar requiere update propio, maestro y asociación activos, División efectiva y Sociedad de la asociación coincidente con Admin. Si cambia la Sociedad: primero confirmar la asociación, después revisar y guardar condiciones; no se reinterpreta historia. La desactivación de la asociación conserva sus condiciones y bloquea su edición hasta reactivarla.

Valores históricos de catálogo se muestran sin sustituirlos por una opción vigente; un guardado vuelve a validar todos los códigos. Si el catálogo falla, la lectura confirmada sigue visible y se bloquea guardar. Sólo lectura no consulta catálogos de captura. Rechazos conservan captura, usan rutas values.currency/payment_terms/credit_limit/lead_time_days y nunca muestran mensajes SQL. Reintento idéntico conserva Idempotency-Key; revisión obsoleta obliga a recargar y revisar.

## Propiedad y consistencia

Sales posee sales.customer_division_terms; Purchasing posee purchasing.supplier_division_terms. Admin sólo autoriza contexto y valida catálogos por HTTP; ningún consumidor escribe tablas Admin. Sin Costing, centros, Accounting ni analítica. La política confirmada de Centro de costos obligatorio sólo por flujo habilitado se conserva.

Alembic `20260928_0045`, padre 0044: tablas aditivas, PK tenant/recurso/División, FK compuesta a la asociación del mismo servicio, Sociedad externa sin FK cruzada, campos explícitos no nulos, constraints de códigos/rangos/revisión y timestamps, índice tenant/División. Sin backfill. Downgrade bloquea tablas y rechaza si existen condiciones o auditoría; con historia se requiere forward-fix.

Guardar bloquea maestro y asociación en el mismo orden que CHG-301. Comprueba autorización/estado/Sociedad antes de replay, luego revisión y catálogos; condiciones, auditoría before/after y respuesta idempotente se guardan en la misma transacción. Hash actor/payload y clave por recurso/División. No mezcla términos de Divisiones ni duplica auditoría en reintentos. Las llamadas Admin no son atómicas con la transacción comercial: el futuro consumidor documental debe revalidar en su frontera.

## APIs afectadas

Nuevas; tenant y autorización efectiva en todas. PUT requiere Idempotency-Key y admite X-Correlation-Id. No cambia el contrato de disponibilidad CHG-301 ni las consultas previas de elegibles.

| Servicio | Método/ruta | Permiso | Request / response |
|---|---|---|---|
| Sales | GET /v1/sales/customers/{resource_id}/division-assignments/{division_id}/commercial-terms | sales.customer.read | Identidad de ruta → recurso/División, Sociedad confirmada y actual, revision, values explícitos o null, requires_confirmation y assignment_active. |
| Sales | PUT /v1/sales/customers/{resource_id}/division-assignments/{division_id}/commercial-terms | sales.customer.update | expected_revision y values completos: currency, payment_terms, credit_limit → lectura guardada con revisión nueva. |
| Purchasing | GET /v1/purchasing/suppliers/{resource_id}/division-assignments/{division_id}/commercial-terms | purchasing.supplier.read | Igual lectura; values contiene lead_time_days en lugar de credit_limit. |
| Purchasing | PUT /v1/purchasing/suppliers/{resource_id}/division-assignments/{division_id}/commercial-terms | purchasing.supplier.update | expected_revision y values completos: currency, payment_terms, lead_time_days → lectura guardada. |

No se admite values null, cuerpo incompleto ni campos adicionales. requires_confirmation señala ausencia de condiciones o Sociedad distinta; assignment_active expresa elegibilidad de maestro/asociación/División, no validación actual de los códigos del catálogo. La lectura histórica no hace llamadas al catálogo ni promete que un código retirado pueda usarse en una nueva operación.

Consumidas sin cambio: Admin GET /v1/session/context, GET /v1/catalogs/commercial/{catalog_code}, GET /v1/catalogs/commercial/{catalog_code}/by-code/{code}; Sales GET /v1/sales/reference-data y Purchasing GET /v1/purchasing/reference-data (permisos comerciales propios). Navegación previa conserva GET /v1/sales/organization/divisions, GET /v1/purchasing/organization/divisions; GET y PUT de asignaciones CHG-301, y GET /v1/sales/customers / GET /v1/purchasing/suppliers. APIs de documentos, Inventory, Production, HR, Maintenance, Costing y Accounting no tocadas.

## Evidencia y continuación

Local exclusivamente: PostgreSQL 127.0.0.1:5434/erclave_local y tenant ten_739ee59d765d5e14818674800d validados antes de escribir; Firebase Emulator 9099, Sales 8008, Purchasing 8010. Upgrade/downgrade vacío/upgrade probados. Fixtures sintéticos con rollback; sin asociaciones/condiciones permanentes. Smoke HTTP read-only comprueba referencias/contexto, rutas nuevas, token faltante y errores de recursos/alcance; no sustituye un flujo positivo de escritura HTTP. Persistencia positiva cubierta con PostgreSQL transaccional y API cubierta con dobles.

Resultados: 42/42 backend/API/PostgreSQL focales sin omisiones, 28 browser focales y 191 transversales aprobadas; corrección final del aviso de éxito ante un rechazo posterior comprobada con 16/16 pruebas del formulario. npm run verify aprobado: validadores, compilación, 527 backend aprobadas/127 omitidas en gate general. Evidencia final en TRAZABILIDAD CHG-302 y logs chg302-migrate.log, chg302-tests.log, chg302-browser.log, chg302-browser-full.log, chg302-browser-final.log, chg302-smoke.log, chg302-verify.log. Manuales Markdown actualizados; Word pendiente según REGISTRO. QA/Producción intactos.

Continuación vigente: cotizaciones y pedidos conservan condiciones explícitas en CHG-303/304; servicios y stock tienen sus recorridos y fabricación se incorporó en CC-12 CHG-315. El consumo documental de Purchasing se implementa y valida en [CC-15 CHG-319](cont_08_compras_contexto.md). El cierre y las brechas restantes se consultan en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md). No hay control de exposición crediticia por capturar límite ni contabilización automática; folios y mapeo real siguen abiertos.
