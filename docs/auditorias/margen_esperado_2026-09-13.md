# Margen esperado sin tope porcentual — CHG-273

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.

## Regla y alcance

El dato capturado expresa utilidad esperada sobre costo: `(precio - costo) / costo * 100` como definición, no cálculo automático nuevo. Costo900 y venta200000 equivale aproximadamente a22122.22%;400% equivale a precio cinco veces el costo. Los porcentajes de margen sobre ingresos de reportes de Ventas no cambian.

No se impone máximo comercial; se conservan valores finitos >=0 y captura con dos decimales. La API conserva su tipo numérico. PostgreSQL amplía NUMERIC(9,4) a NUMERIC, sin backfill ni reinterpretación de los dos valores existentes. No existen cambios de entidad, índice, tenant ni ownership. Dueño: production-service, tabla production.product_services.

La tarjeta antes sustituía el porcentaje guardado por un cálculo sobre venta cuando había costo y precio; ahora muestra expected_margin. Ayuda ES/EN distingue los conceptos. La skill transversal prohíbe imponer100% a cualquier porcentaje sin revisar su significado y todas las capas.

## Validación

- 14 pruebas focalizadas aprobadas (13 API/schema y1 integración PostgreSQL real), sin omisiones en la selección. Create y update aceptan0,100,400,22122.22 y1000000; negativos e infinitos/NaN rechazados.
- PostgreSQL probado en127.0.0.1:5434/erclave_local, tenant ten_739ee59d765d5e14818674800d. Inserciones/updates sintéticos para producto y servicio, consulta del valor y constraints; fixtures enteramente revertidas por transacción.
- Migración0035 aplicada; ensayo downgrade/upgrade y protección de reversa con valores altos en transacción, preservando los dos registros existentes. Servicio Production Local reiniciado con Firebase Emulator.
- Navegador: frontend-contracts23/23 (34.3s), incluidos tres casos nuevos de valores altos/reapertura/tarjeta y ES/EN; suite feedback98/98 (37.3s). Mutaciones de UI interceptadas.
- `npm run verify` aprobado: validadores, sintaxis79, compilación y275 backend;56 omitidas en la corrida sin DB. De esas56, la nueva integración de margen fue ejecutada aparte con PostgreSQL y aprobó; las55 integraciones generales anteriores permanecen pendientes.
- API Local reiniciada y OpenAPI servido en8002 comprobado sin máximo100. Alembic final0035 y ausencia de fixtures sintéticos confirmadas.

Las pruebas API usan repositorio doble; la prueba PostgreSQL usa DDL/DML real. No equivale a UAT ni prueba HTTP con escritura de negocio real. Las55 integraciones generales omitidas anteriormente no quedan cubiertas por esta prueba focalizada.

## APIs afectadas

| Servicio | Método y ruta | Permiso / cambio |
|---|---|---|
| production-service | POST /v1/production/product-services | production.product_service.create; expected_margin finito >=0 sin máximo100 |
| production-service | PATCH /v1/production/product-services/{product_service_id} | production.product_service.update; misma ampliación |
| production-service | GET /v1/production/product-services y GET /v1/production/product-services/{product_service_id} | Lectura sin cambio de estructura; semántica documentada en OpenAPI |

Otros contratos y servicios: sin cambios. QA requiere0035 antes del frontend/API nuevo mediante promoción autorizada; este corte no despliega.

## Reversa

0035 comprueba que todos los valores caben en el formato previo antes de restaurar NUMERIC(9,4) y máximo100. Si existen valores >100 o más de cuatro decimales, falla sin truncar datos. Resolverlos requiere decisión explícita de negocio; no hacerlo automáticamente. La migración es transaccional PostgreSQL.

## Reproducir

`npm run verify`; `npm run test:form-feedback`; `npx playwright test frontend-contracts.spec.js`. Para integración focalizada definir ERCLAVE_TEST_DATABASE_URL únicamente a loopback5434/erclave_local y ejecutar desde backend `python ../tools/run_pytest.py services/production-service/tests/test_expected_margin_integration.py services/production-service/tests/test_production_api.py -k expected_margin -q`.
