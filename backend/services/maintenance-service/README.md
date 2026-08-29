# Maintenance Service

Servicio propietario de las ordenes de mantenimiento, asignaciones, tiempos de trabajo y solicitudes internas de refacciones.

## Estado

`implemented` en Local desde la revision `20260824_0027` y endurecido en `20260824_0028`. Incluye flujo correctivo, tiempos, refacciones, compensaciones y reintentos durables contra RH, Production e Inventory. No esta desplegado en QA ni Produccion.

## Fronteras

- RH conserva areas, puestos, trabajadores y elegibilidad para mantenimiento.
- Inventory conserva almacenes, articulos, existencias, reservas, salidas, devoluciones y valuacion.
- Production conserva maquinas y ordenes de produccion. Mantenimiento solo solicita su bloqueo o liberacion mediante contrato.
- Una ubicacion del edificio u otro objetivo sin identificador se describe dentro de la orden; no se inventa un activo externo.

El contrato implementado esta en `contracts/api/maintenance-service.openapi.yaml` y el alcance funcional en `modulos/11_mantenimiento.md`.
