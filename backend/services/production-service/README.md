# production-service

Duenio de productos/servicios productivos, recetas, ordenes, etapas y maquinaria productiva. RH es duenio de areas y puestos; Inventory es duenio de movimientos, reservas y consumos fisicos.

En Local, repetir una evidencia inmutable de inicio o cierre exige el actor que la registró y el mismo contenido. Otro actor recibe `403 idempotency_actor_mismatch`; el mismo actor con contenido distinto recibe `409 service_evidence_already_recorded`. La lectura autorizada de la orden y sus evidencias conserva su permiso y alcance propios.

Para la recepcion de producto terminado publica `GET /v1/production/finished-goods-candidates[/{id}]`. El contrato entrega solo folio, producto vinculado, cantidad, unidad, estado terminado y costo unitario; las lecturas generales conservan permisos propios de Produccion.

No debe escribir inventario, compras, costos o contabilidad directamente; debe publicar eventos o llamar contratos.

## Primer corte MVP real

Este primer corte implementa el catalogo base de productos/servicios productivos:

```text
GET /v1/production/product-services
POST /v1/production/product-services
GET /v1/production/product-services/{product_service_id}
PATCH /v1/production/product-services/{product_service_id}
PATCH /v1/production/product-services/{product_service_id}/status
```

Todas las rutas requieren `X-Tenant-Id`. Las mutaciones de creacion y cambio de estatus requieren `Idempotency-Key`.

El modelo fisico inicial vive en el schema `production` y crea `production.product_services`. No usa FK cruzada hacia `admin.tenants`; `tenant_id` se conserva como referencia externa validada por contrato y backend.

## Segundo corte: recetas versionadas

Incluye recetas, versiones, recursos y etapas con aislamiento por `tenant_id`. Una versión sólo puede editarse en borrador y sigue el flujo `draft -> pending_approval -> approved -> obsolete`. La aprobación exige recursos y etapas, actualiza la versión vigente del producto y deja obsoleta la aprobación anterior.

## Ciclo operativo local

La revision `20260804_0012` incorpora maquinaria, ordenes, snapshots de receta/validacion, etapas ejecutables y auditoria. La validacion de recursos es una observacion efimera: se recalcula al crear la orden y no reserva ni consume inventario. Ordenes y etapas usan transiciones backend, permisos e idempotencia; `completed` y `cancelled` son terminales.

La revision `20260805_0013` enlaza cada nueva etapa de receta con `labor_area_ref_id` de RH y conserva `labor_area_name` como snapshot. Es una referencia externa sin FK cruzada: Produccion no escribe el schema `hr`.

La revision `20260825_0029` incorpora planeacion multi-dia. La receta conserva una duracion sugerida y la orden define inicio y numero de dias productivos; el backend distribuye los minutos de mano de obra y maquinaria de lunes a viernes, descuenta compromisos existentes por fecha y persiste una fila diaria por recurso. Los materiales siguen validandose una sola vez y no se multiplican por dias. La fecha requerida no puede preceder el fin planeado. Turnos, festivos, ausencias y excepciones de mantenimiento configurables aun no forman parte de este corte.

Una receta puede referir maquinaria activa o en mantenimiento aunque su area RH este pendiente: la receta define el proceso. La validacion de la orden define la disponibilidad y asigna cero capacidad a una maquina en mantenimiento. Maquinaria inactiva o inexistente se rechaza.

Crear/liberar la orden reserva materiales por almacén. Desde CHG-264 Almacén confirma la entrega por `POST /v1/production/orders/{order_id}/issue-materials`; Production conserva el intento durable y orquesta consumo en Inventory. Iniciar/reanudar valida entregas completas y recursos vigentes, sin volver a consumir. Cancelar libera reservas restantes y conserva salidas; sobrantes se devuelven mediante su recorrido auditado. [Contrato y evidencia](../../../docs/auditorias/materiales_produccion_movimientos_2026-09-08.md).

La entrada a `in_validation` exige que todas las etapas tengan `progress_percent=100` y esten `completed` o `skipped`. El cliente captura un porcentaje: `0` corresponde a pendiente, `1..99` a en proceso y `100` a terminada. La ultima etapa al 100% mueve automaticamente la orden a validacion. El cierre `completed` no exige minutos ni cantidades reales de mano de obra/maquinaria en este corte; esos campos permanecen opcionales para una futura medicion de eficiencia. El cliente no debe ofrecer transiciones incompatibles ni presentar los codigos de precondicion como errores tecnicos genericos.

## Preparación contable y alcance vigente

Máquinas/productos asignados por División implementados. CHG-308 prepara contexto/intento durable y scope, sin habilitar fabricación dimensionada (CC-10/11/12). Véase [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). La preparación no activa Accounting.
