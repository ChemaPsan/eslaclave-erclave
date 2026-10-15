# CONT-07 — Clientes y proveedores por División

**Ampliación CHG-302:** [condiciones explícitas por División](cont_07_commercial_condiciones.md) implementadas Local, sin herencia del maestro. El contrato de disponibilidad descrito en CHG-301 se conserva; sus límites comerciales quedan ampliados por ese corte. CONT-08 ya incluye cotización/pedido/servicios/stock Sales; documentos Purchasing siguen pendientes según [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md).

CHG-301 · 2026-09-28 · Local aislado, working tree sobre HEAD `213f75c`. Agentes consultados mediante sus fichas: negocio/técnico Compras, Ventas, Administración y Contabilidad; Arquitectura SaaS/API, Datos/Custodio DB, Seguridad, Sinergia, Diseño/i18n, Manuales y QA. Skills feature, accounting, module-boundaries, db-migration, environment-boundaries, form-contract, form-feedback, qa-evidence y solution-manuals. Sin delegación.

## Alcance y propiedad

Un solo maestro de cliente en Sales y de proveedor en Purchasing. Cada dueño conserva sus asociaciones de disponibilidad por División y su Sociedad derivada, sin FKs ni escrituras cruzadas. Admin resuelve sesión, permisos y Divisiones autorizadas por HTTP. No depende de Costing ni activa Accounting o analítica. No asigna un maestro a todas las Divisiones de una Sociedad por herencia implícita.

El contrato de disponibilidad CHG-301 conserva identidad única. [CHG-302](cont_07_commercial_condiciones.md) ya añadió moneda, pago, crédito o plazo explícitos por División, sin herencia del maestro. Cotizaciones/pedidos dimensionados consumen la copia correspondiente; documentos Purchasing aún requieren integración. Documentos legacy mantienen su comportamiento por tenant hasta migración explícita. Disponibilidad no acredita separación completa.

## Contrato funcional y formulario

| Campo | Propósito y autoridad | Persistencia |
|---|---|---|
| División | Disponibilidad del cliente/proveedor; búsqueda paginada de Divisiones efectivas Admin | PK tenant/recurso/División; explícita por asociación. |
| Sociedad | Identificar la entidad de la División autorizada | society_ref_id derivada en servidor; no editable en request. |
| Estado | Habilitar o retirar disponibilidad sin eliminar maestro/historia | active/inactive. |
| Revisión | Evitar sobrescritura concurrente | expected_revision requerido, 0 al crear; incremento del servidor. |

Activar exige maestro activo y División vigente autorizada. Clientes prospect/blocked/inactive y proveedores inactive no son elegibles. Elegibilidad exige asociación activa, maestro activo y Sociedad guardada coincidente con la División vigente. Ante un cambio de Sociedad se necesita confirmación explícita mediante guardado activo; no se reinterpreta el historial. Desactivar conserva Sociedad y permite historial de División retirada sólo con alcance histórico autorizado (wildcard explícito); nunca crea una asociación inexistente.

En Ventas → Clientes y Compras → Proveedores, la tarjeta ofrece **Disponibilidad por División** sólo en modo API, módulo activo, scope v2 y permiso de lectura. Búsqueda acotada, identidad código/nombre, Sociedad derivada visible, paginación de historia y controles de estado ES/EN. Permiso update para guardar; lectura no ofrece mutaciones. Se conserva captura ante errores, se vinculan errores estructurados a controles y se mantiene clave idempotente en reintentos idénticos. Cambiar División reinicia clave/revisión desde su asociación real. CSS propio comprobado en contenedor de 320px, sin cambios globales.

## Autorización, transacción y datos

Todas las rutas nuevas consultan Admin incluso en demo: tenant/usuario activos, Admin y módulo comercial activos, scope v2, permiso exacto. Alcance vacío no otorga acceso global. Asignaciones filtradas por alcance; lectura de elegibles minimiza respuesta a ID/código/nombre/División/Sociedad, sin datos fiscales, contacto, crédito ni términos. Auditoría sólo registra asociación before/after, actor, correlación y clave.

Alembic `20260928_0044` crea sales.customer_division_assignments y purchasing.supplier_division_assignments: PK compuesta, FK tenant/recurso dentro del servicio, estados acotados, revisión positiva, timestamps e índice tenant/División/estado. No hay seeds ni backfill inferido. Reutiliza unique tenant/id de los maestros.

Guardar bloquea el maestro propio; revisión, upsert, auditoría y respuesta idempotente quedan en una transacción. Clave por recurso/División y hash de actor/payload; cambio de payload con misma clave rechaza 409. Autorización actual precede al replay. Admin y transacción comercial no son atómicos; CONT-08 debe revalidar antes de efectos operativos. Downgrade toma locks y rechaza si alguna tabla o su auditoría tiene historia: requiere forward-fix; no borra asociaciones de negocio.

## APIs afectadas

Contratos nuevos; requieren X-Tenant-Id y autorización efectiva. PUT requiere Idempotency-Key y acepta X-Correlation-Id. Body extra prohibido: Sociedad, centros y condiciones comerciales no se aceptan.

| Servicio | Método y ruta | Permiso | Request / response |
|---|---|---|---|
| Sales | GET /v1/sales/organization/divisions | sales.customer.read | q, limit 1–25, offset; id/code/name/society_id y meta. |
| Sales | GET /v1/sales/customers/{resource_id}/division-assignments | sales.customer.read | division_id opcional, limit 1–100, offset; asociaciones customer_id/division_ref_id/society_ref_id/status/revision y meta. |
| Sales | PUT /v1/sales/customers/{resource_id}/division-assignments/{division_id} | sales.customer.update | expected_revision y status; asociación guardada con Sociedad derivada/revisión. |
| Sales | GET /v1/sales/division-customers | sales.customer.read | division_id requerido, q, limit 1–25, offset; elegibles minimizados y meta. |
| Purchasing | GET /v1/purchasing/organization/divisions | purchasing.supplier.read | q, limit 1–25, offset; id/code/name/society_id y meta. |
| Purchasing | GET /v1/purchasing/suppliers/{resource_id}/division-assignments | purchasing.supplier.read | division_id opcional, limit 1–100, offset; asociaciones supplier_id/division_ref_id/society_ref_id/status/revision y meta. |
| Purchasing | PUT /v1/purchasing/suppliers/{resource_id}/division-assignments/{division_id} | purchasing.supplier.update | expected_revision y status; asociación guardada con Sociedad derivada/revisión. |
| Purchasing | GET /v1/purchasing/division-suppliers | purchasing.supplier.read | division_id requerido, q, limit 1–25, offset; elegibles minimizados y meta. |

Consumidas sin cambio: Admin GET /v1/session/context; Sales GET /v1/sales/customers (sales.customer.read) y Purchasing GET /v1/purchasing/suppliers (purchasing.supplier.read), para tarjetas existentes. No tocadas: contratos de pedidos/cotizaciones, Inventory, Production, HR, Maintenance, Costing y Accounting. CORS Sales/Purchasing agrega PUT.

## Evidencia y continuación

Local exclusivamente: PostgreSQL 127.0.0.1:5434/erclave_local, Firebase Emulator 9099, Sales 8008, Purchasing 8010, tenant ten_739ee59d765d5e14818674800d. Upgrade/downgrade vacío/upgrade aprobados. Pruebas sintéticas PostgreSQL con rollback; 24 pruebas de dominio/API/DB y 12 pruebas UI ES/EN aprobadas. Smoke HTTP real de lectura: contexto y rutas 200, token faltante 401, División/tenant ajenos rechazados, recurso ausente 404 y CORS PUT 200. Dos clientes y tres proveedores previos conservados; cero asociaciones permanentes. Accounting/analítica indisponibles.

Gate final npm run verify aprobado (validadores, compilación, 515 pruebas backend aprobadas/121 omitidas en la suite general); focal Local 24/24 sin omisiones. Suite transversal navegador 175/175 aprobadas. Evidencia completa en TRAZABILIDAD CHG-301; logs chg301-migrate.log, chg301-tests.log, chg301-browser.log, chg301-browser-full.log, chg301-smoke.log y chg301-verify.log. Dobles API/browser, DB con rollback y smoke de lectura son evidencias diferentes; no sustituyen UAT ni promoción. QA/Producción intactos.

CONT-07 ya incluye disponibilidad y condiciones explícitas por División; conservar esos recorridos. CONT-08 implementa cotización/pedido/servicios/stock Sales; documentos Purchasing, folios y backfill real siguen abiertos. [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md) distingue cada brecha; [REGISTRO](../manuales_solucion/REGISTRO.md) gobierna derivados de manuales.
