# Inventario: consulta escalable de existencias

## Decisiones de interfaz y compatibilidad

- El modulo visible conserva el nombre **Almacenes** y su identificador tecnico `almacenes`.
- El submodulo visible **Existencias** pasa a llamarse **Inventario**, conservando el id tecnico `existencias` y sus rutas existentes.
- **Almacenes** sigue siendo el catalogo de espacios fisicos; **Inventario** es la consulta operativa de saldos.
- El cambio de nombre no autoriza migraciones de claves de `localStorage`, permisos, codigos de modulo ni datos persistentes.

## Fuente de verdad

Los movimientos `recorded` no reversados son la fuente de verdad. Existencias es una consulta calculada y nunca se captura ni edita directamente.

Desde la revision Local `20260818_0017`, se adopta explicitamente:

```text
available_quantity = max(on_hand_quantity - reserved_quantity, 0)
reserved_quantity = sum(reservas activas no vencidas)
```

La interfaz no debe inventar reservas ni tratar una lectura previa como garantia. La promesa concurrente se confirma al crear la reserva bajo bloqueo transaccional; contrato, calculo, migracion y pruebas cambian juntos en este corte.

## Busqueda, filtros y orden

La consulta de Existencias debe resolverse en `inventory-service`, siempre dentro de `tenant_id`. El navegador solo conserva estado de consulta y presenta la pagina recibida.

Parametros objetivo:

| Parametro | Semantica |
|---|---|
| `q` | Coincidencia parcial, sin distinguir mayusculas, sobre codigo y nombre de articulo y codigo y nombre de almacen. |
| `warehouse_id` | Almacen exacto del tenant activo. |
| `inventory_item_id` | Articulo exacto del tenant activo. |
| `unit` | Unidad exacta normalizada. |
| `stock_status` | `negative`, `out_of_stock`, `below_minimum`, `normal` o `above_maximum`, derivado del saldo y sus limites. |
| `item_type`, `category`, `inventory_policy`, `item_status` | Filtros del catalogo de articulos realmente guardado. |
| `sort` | Orden estable con `inventory_item_id` y `warehouse_id` como desempate. |
| `limit`, `cursor` | Paginacion por cursor. Default 50, maximo 200. |

Los filtros se combinan con semantica AND. `q` se normaliza con trim y debe admitir coincidencias al inicio, en medio y al final. Los indices y el plan SQL deben revisarse con `EXPLAIN (ANALYZE, BUFFERS)` antes de promover el contrato.

## Criterio local de volumen

El corte se considera preparado para continuar cuando, con un conjunto sintetico de al menos 10,000 articulos:

1. la busqueda parcial devuelve solo coincidencias correctas;
2. los filtros combinados no mezclan tenants;
3. cada pagina contiene como maximo el `limit` solicitado y el cursor no omite ni duplica filas;
4. el orden es determinista entre ejecuciones;
5. una consulta en memoria de referencia completa en menos de 2 segundos en una estacion de desarrollo;
6. la prueba no usa credenciales, red, Firebase, Cloud SQL ni datos de QA.

El punto 5 es un guardrail local para detectar regresiones gruesas, no un SLO de produccion. La validacion definitiva del API debera medir percentiles sobre PostgreSQL local y registrar hardware, plan SQL, volumen de movimientos y cardinalidad de filtros.

## Limites del corte

Este corte actualiza frontend, API, OpenAPI, migracion local, pruebas y documentacion. No autoriza despliegues, migraciones ni escrituras en QA. La categoria permanece como texto libre; su normalizacion jerarquica queda para una decision funcional posterior.
