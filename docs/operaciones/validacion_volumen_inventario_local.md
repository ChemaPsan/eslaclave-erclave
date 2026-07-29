# Validacion local de volumen de Inventario

Esta validacion comprueba la semantica propuesta de busqueda, filtros y paginacion con datos sinteticos. No abre conexiones, no modifica PostgreSQL y no toca QA.

## Ejecutar

Desde la raiz del repositorio:

```powershell
node tools/benchmarks/inventory-volume.js
```

El proceso genera en memoria 10,000 articulos, dos almacenes por articulo y dos tenants. Comprueba busqueda parcial, filtros combinados, aislamiento, paginacion sin duplicados y la regla temporal `available = on_hand`.

Salida esperada:

```text
PASS inventory-volume ...
```

Un tiempo mayor a 2,000 ms falla el guardrail local. Si falla, registrar sistema operativo, version de Node, CPU, memoria, duracion y asercion. No elevar el umbral sin explicar la regresion.

## Validacion con PostgreSQL local

Procedimiento reproducible:

1. crear datos exclusivamente en una base local desechable;
2. usar un tenant sintetico, nunca el tenant del equipo QA;
3. cargar al menos 10,000 articulos, multiples almacenes y una distribucion representativa de movimientos;
4. probar `q`, filtros individuales, combinaciones y recorrido completo por cursor;
5. ejecutar `EXPLAIN (ANALYZE, BUFFERS)` para consultas representativas;
6. registrar p50, p95, p99, filas examinadas y plan;
7. destruir solo la base local desechable tras verificar su ruta y nombre.

Resultado del corte 2026-07-27 sobre `erclave_local` aislado en `127.0.0.1:5434`:

- 10,000 articulos y 10,000 movimientos registrados para un tenant sintetico;
- busqueda de `algodon` encontro nombres almacenados como `Algodón`;
- pagina limitada a 50 filas;
- `EXPLAIN (ANALYZE, BUFFERS)` reporto 30.896 ms de ejecucion tras actualizar estadisticas con `ANALYZE`;
- memoria del agregado: 369 kB;
- el tenant sintetico fue eliminado y se verificaron conteos `0|0|0` en articulos, movimientos y almacenes.

Una carga masiva recien insertada puede producir un plan deficiente antes de que PostgreSQL actualice estadisticas. Todo proceso local de carga de volumen debe ejecutar `ANALYZE` antes del benchmark; en operacion normal esta tarea corresponde a autovacuum/analyze.

No ejecutar cargas, seeds, benchmarks ni migraciones contra Cloud SQL QA como parte de esta guia.
