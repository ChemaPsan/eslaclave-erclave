# Maintenance Service

Servicio propietario de las ordenes de mantenimiento, asignaciones, tiempos de trabajo y solicitudes internas de refacciones.

## Estado

`implemented` en Local desde la revision `20260824_0027` y endurecido en `20260824_0028`. Incluye flujo correctivo, tiempos, refacciones, compensaciones y reintentos durables contra RH, Production e Inventory. El ciclo base está en QA según [release documentado](../../../docs/operaciones/release_qa_20260914.md); no se acredita despliegue productivo.

CC-16 CHG-320 integra contexto fijo de orden, técnicos RH por División, snapshots de tarifa/costo laboral y alcance en lecturas, comandos, replays y CSV. Migración0059 aditiva sin backfill; contrato1.1. Maintenance50, RH/Production123 y navegador271 aprobadas; aceptación CC-20 pendiente. [Reglas, APIs y evidencia](../../../docs/arquitectura/cont_08_mantenimiento_contexto.md).

Los tiempos usan fechas con zona normalizadas UTC y Decimal con redondeo HALF_UP a seis decimales; conservan revisiones RH y moneda base de Sociedad. Solapamiento/capacidad se controlan por tenant+trabajador entre órdenes Maintenance y día UTC, sin reserva transversal Sales/Production. Nuevas refacciones heredan la División de orden; recuperación y costo CC-14 permanecen. Legacy sin contexto requiere alcance completo para consulta/recuperación permitida, sin atribución histórica inventada.

## Fronteras

- RH conserva areas, puestos, trabajadores y elegibilidad para mantenimiento.
- Inventory conserva almacenes, articulos, existencias, reservas, salidas, devoluciones y valuacion.
- Production conserva maquinas y ordenes de produccion. Mantenimiento solo solicita su bloqueo o liberacion mediante contrato.
- Una ubicacion del edificio u otro objetivo sin identificador se describe dentro de la orden; no se inventa un activo externo.

El contrato implementado esta en `contracts/api/maintenance-service.openapi.yaml` y el alcance funcional en `modulos/11_mantenimiento.md`.

## Preparación contable y alcance vigente

El ciclo correctivo existe; la separación global de órdenes/tiempos está implementada Local CC-16 CHG-320. CC-14 añade snapshot inmutable a solicitudes de material, derivado del almacén y de Admin, contrastado con máquina/origen Production cuando existen. El endpoint `GET /v1/maintenance/orders/{id}/inventory-context?line_id=...` prueba el intento durable a Inventory; reserva y reintento conservan contexto original. Inventory conserva reservas, movimientos y costo; los retornos validan contexto/costo contra la solicitud original. Las bandejas de materiales y sus comandos aplican alcance vigente. No se asigna dimensión retroactivamente a solicitudes legacy.

Este cambio requiere la migración Local de `maintenance.material_requests.organization_context` y validación integrada antes de declarar aceptación; no acredita despliegue QA. Véase [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). La preparación no activa Accounting.

Para solicitar materiales de una orden vinculada a Production, el actor conserva los permisos de lectura de sus autoridades: `production.order.read` para origen productivo y `production.machine.read` o `maintenance.order.create` para máquina. No se amplían permisos ni se omite la comprobación ante un 403. Las órdenes de instalaciones sin origen Production no requieren estas lecturas. Los roles son configurables: validar la combinación del actor durante la aceptación integrada.

Reservas y conciliaciones conservan `original_unit_cost` de Inventory, incluido cero, antes de recurrir al campo legacy `unit_cost_snapshot`. La validación de sobrantes entrega el costo como cadena decimal exacta para evitar pérdida de seis decimales al serializar importes grandes; la reconciliación conserva ese mismo costo.
