# production-service

Duenio de productos/servicios productivos, recetas, ordenes, etapas y maquinaria productiva. RH es duenio de areas y puestos; Inventory es duenio de movimientos, reservas y consumos fisicos.

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
