# Inventory Service

## CC-14 Local · CHG-317

Proof autenticado Purchasing/Maintenance; transferencias misma Sociedad y sobrantes preservan contexto/costo y scope. Local head0057; `ERCLAVE_PURCHASING_SERVICE_URL` obligatorio para despliegue futuro. [Contrato](../../../docs/arquitectura/cont_08_inventario_productores.md). Sin promoción QA.


Microservicio propietario de Almacenes e Inventarios. El MVP implementa almacenes, articulos, movimientos manuales, transferencias con salida, tránsito, recepción parcial y retorno, reversas, reservas, recepcion de producto terminado, existencias calculadas y Kardex.

La recepcion consulta exclusivamente `production-service /v1/production/finished-goods-candidates/{id}`. Esa proyeccion contiene los datos minimos para validar y valuar la entrada; los permisos Inventory no abren ordenes, recetas o productos completos de Produccion.

## Reglas

- Toda consulta y escritura filtra por `tenant_id`.
- Firebase identifica; `admin-service /v1/session/context` valida tenant, modulo `inventory` y permiso exacto.
- Las escrituras requieren `Idempotency-Key` y generan `inventory.audit_events`.
- Los movimientos no se editan ni eliminan. Una correccion genera un movimiento inverso y marca el original como reversado.
- Salidas, transferencias, ajustes negativos y reversas de entradas no pueden producir saldo negativo.
- Existencias y Kardex se calculan desde movimientos registrados; no tienen formularios de captura.
- Las recepciones de produccion se vinculan por ID a una orden terminada; admiten parciales y nunca exceden la cantidad producida.

## Ejecucion local

El entorno aislado de Windows usa PostgreSQL portatil en `C:\tmp\erclave-postgresql17`, base `erclave_local` y puerto `5434`. No comparte proceso, puerto ni datos con Cloud SQL QA.

Desde `backend/` puede arrancarse PostgreSQL e Inventory API con:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start_inventory_local.ps1
```

La instalacion manual equivalente es:

```powershell
alembic upgrade head
uvicorn services.inventory_service_adapter:app --reload --port 8004
```

Variables compartidas:

```text
ERCLAVE_ENVIRONMENT=local
ERCLAVE_AUTH_MODE=firebase
ERCLAVE_FIREBASE_PROJECT_ID=demo-erclave
FIREBASE_AUTH_EMULATOR_HOST=127.0.0.1:9099
ERCLAVE_ADMIN_SERVICE_URL=http://127.0.0.1:8000
ERCLAVE_DATABASE_URL=postgresql+psycopg://.../erclave_local
```

El cliente frontend local usa `inventoryApiMode: "api"` y `http://127.0.0.1:8004` una vez validada la migracion local.

## Endpoints MVP

```text
GET/POST       /v1/inventory/warehouses
PATCH          /v1/inventory/warehouses/{warehouse_id}
GET/POST       /v1/inventory/items
PATCH          /v1/inventory/items/{item_id}
GET/POST       /v1/inventory/movements
POST           /v1/inventory/movements/{movement_id}/reverse
GET/POST       /v1/inventory/finished-goods-receipts
GET            /v1/inventory/balances
GET            /v1/inventory/kardex
```

## Rollback

No usar un downgrade al origen del MVP sobre el head actual: revertiría migraciones posteriores de varios servicios. Cada revisión define sus guards; con historia usar forward-fix. Procedimiento y ambiente en [fronteras](../../../docs/arquitectura/fronteras_ambientes_local_qa_produccion.md).

## Preparación contable y alcance vigente

Almacenes/artículos dimensionados, stock→reserva→entrega, manuales/reversas y costo original implementados Local. Transferencias, otros productores, sobrantes y recepciones dimensionadas siguen pendientes (CC-14). Véase [CONTROL_CONTABLE](../../../docs/contexto/CONTROL_CONTABLE.md) y [estado por ambiente](../../../docs/contexto/ESTADO_ACTUAL.md). La preparación no activa Accounting.
