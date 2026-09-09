# Solicitudes compactas en Movimientos — CHG-267

Evidencia histórica Local del 8 de septiembre de 2026; estado vivo en `docs/contexto/ESTADO_ACTUAL.md`. Se preservan CHG-262–266.

## Alcance y aceptación

Movimientos muestra primero un único desplegable «Solicitudes de entrada y salida», cerrado al entrar. El historial queda inmediatamente debajo. Al abrir aparecen las siete bandejas existentes: producto terminado, materiales productivos, compras, ventas, transferencias, devolución de materiales y refacciones. Sus acciones, permisos, paginación y propietarios no cambian.

El resumen muestra aviso semántico con texto e icono si alguna fuente consultada contiene pendientes; no presenta el tamaño de una página como total global. Diferencia carga, error y páginas posteriores vacías de «sin pendientes». Las fuentes no autorizadas no se suman al diagnóstico. Las actualizaciones parciales de bandejas también refrescan el aviso sin abrir el desplegable. Una falla al consultar producto terminado permite reintentar desde el contenido expandido.

Se conserva abierto/cerrado durante recargas de la pantalla y comandos, pero al salir y volver comienza cerrado. Usa details/summary nativo, teclado, estado anunciado y CSS acotado a `.warehouse-pending` con container query de 520 px. No cambia el riel compartido ni otras pantallas. ES/EN y viewport ancho con paneles reales 1100/520/360 px. El texto del historial ahora describe los movimientos registrados y dirige al desplegable.

## Fronteras y responsabilidades

Consulta documental sin delegación: agentes negocio/técnicos de Inventarios, Sinergia, UX/i18n, Arquitectura/API, Seguridad, QA y Gobierno documental. Skills erclave-feature y erclave-environment-boundaries. Frontend propietario Almacenes; cada servicio conserva autoridad de documentos e inventario.

Local aislado: frontend 127.0.0.1:4173, APIs loopback, PostgreSQL 127.0.0.1:5434/erclave_local y Firebase Emulator demo-erclave. Tenant `ten_739ee59d765d5e14818674800d`. Pruebas usan sesión real Local, estado sintético en navegador y comandos interceptados; no mutan documentos persistentes. Sin seeds, migración, grants, recursos remotos, despliegue, commit, push ni PR. QA no cambia.

## APIs afectadas

Contratos modificados: **Ninguna**. Clientes HTTP y requests/responses sin cambio. Lecturas reutilizadas para el resumen/reintento:

| Servicio | Método y ruta | Permiso |
|---|---|---|
| Production | GET /v1/production/finished-goods-candidates | inventory.finished_goods_receipt.read o inventory.finished_goods_receipt.receive |
| Inventory | GET /v1/inventory/finished-goods-receipts | inventory.finished_goods_receipt.read |
| Production | GET /v1/production/warehouse-material-requests | inventory.movement.read |
| Maintenance | GET /v1/maintenance/warehouse-material-requests | inventory.movement.read |
| Purchasing | GET /v1/purchasing/warehouse-receipts | inventory.movement.read |
| Sales | GET /v1/sales/warehouse-deliveries | inventory.movement.read |
| Inventory | GET /v1/inventory/transfers | inventory.movement.read |
| Inventory | GET /v1/inventory/material-returns | inventory.movement.read |

Los comandos de las bandejas y las lecturas auxiliares de artículos, almacenes e historial continúan exactamente como CHG-263–266. APIs no tocadas: todos los contratos y runtimes; ninguna topología o modelo persistente cambia, por lo que los diagramas siguen vigentes.

## Evidencia y rollback

`warehouse-pending-summary.spec.js`: cerrado inicial, historial visible, teclado, conservación al renderizar, cierre al volver, aviso para las siete fuentes, carga/error/paginación, actualizaciones asíncronas, permisos, responsive ES/EN y reintento de producto terminado. Las suites de refacciones, materiales productivos y handoffs ahora abren explícitamente el bloque antes de comprobar sus comandos; mantienen sus aserciones previas. Capturas revisadas en `test-results/`. Resultados de verify y navegador registrados en CHG-267 de TRAZABILIDAD.md.

Rollback: restaurar solo composición/estilos/i18n/cachebuster y pruebas de CHG-267. Sin downgrade ni reversa de movimientos. Pendiente aceptación manual del usuario en Local; promoción QA requiere autorización explícita.
