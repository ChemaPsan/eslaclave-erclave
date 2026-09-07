# Reanudacion despues de reinicio: CHG-254 y CHG-255

Fecha del handoff: 2026-09-01.

> Handoff historico, sustituido el 2026-09-07 por `docs/contexto/REANUDACION_CHG261.md`. No usar sus referencias a archivos sin commit como estado vigente.

Este archivo conserva el punto exacto de trabajo antes de reiniciar la computadora. No sustituye `AGENTS.md`, `AGENTES.md`, `ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md`, `PENDIENTES.md` ni `TRAZABILIDAD.md`; los complementa con el estado transitorio del working tree.

## Punto de partida Git

- Repositorio: `eslaclave-erclave`.
- Rama: `agent/chg-254-qa-release-record`.
- Commit base y `HEAD`: `a119ddf5e8d42376b8557b234e15e3681b19c2a7`.
- El working tree contiene cambios sin commit de CHG-254 y CHG-255. Deben preservarse: no ejecutar `git reset --hard`, `git checkout --`, `git clean` ni restauraciones masivas.
- CHG-254 documenta un release QA ya ejecutado y no debe confundirse con una solicitud de volver a desplegarlo.
- CHG-255 permanece solo en Local, pero ya esta aplicado y certificado en PostgreSQL `127.0.0.1:5434/erclave_local` con `20260901_0030`. No se ha desplegado a QA o Produccion.

## CHG-254: cierre del release QA

El release gobernado promovio el SHA `a119ddf5e8d42376b8557b234e15e3681b19c2a7` mediante las ejecuciones `33470879111` y `33473077996`.

- QA quedo en Alembic `20260825_0029`.
- Admin, Produccion, Inventory, RH, Ventas, Compras y Mantenimiento reportaron `/health`, `/ready` y `/version` correctamente.
- Firebase Hosting publico las siete URL sanitizadas.
- La evidencia completa esta en `docs/operaciones/resultado_release_qa_20260901.md`.
- La matriz UAT sigue pendiente segun `docs/contexto/PENDIENTES.md`.
- No repetir IAM, migracion, configuracion, despliegue, trafico o Hosting sin una solicitud nueva, autorizacion explicita y la skill `$erclave-qa-release`.

## CHG-255: funcionalidad aplicada y certificada en Local

### Ventas

- Confirmar un Pedido crea exactamente una Orden de servicio por cada partida `service`.
- La orden conserva folio `sales.service_order`, snapshots de pedido, cliente y servicio, unidad y cantidad.
- Ciclo implementado: `draft -> planned -> assigned -> in_progress -> on_hold -> in_progress -> pending_acceptance -> accepted`; `cancelled` es terminal.
- Planeacion, asignacion, inicio, espera, reanudacion, envio a aceptacion, aceptacion y cancelacion usan permisos puntuales derivados de la accion.
- Tiempos, costos y evidencia se guardan en Sales con tenant, actor, idempotencia y auditoria.
- RH valida trabajadores activos mediante su proyeccion minima; Sales guarda referencia externa y snapshot, sin FK ni escritura en `hr`.
- Las partidas de servicio ya no usan el modo de surtido `service`, no aparecen en Entregas y no generan reservas, consumos ni movimientos de Inventory.
- La UI agrega `Ventas > Ordenes de servicio`, formularios/modales, filtros, permisos, estados, mensajes ES/EN y comportamiento responsive.

### Compras

- `purchasing` deja de exigir `inventory` como dependencia absoluta del modulo.
- Toda partida valida `unit_code` contra el catalogo activo tenant-safe de Admin.
- `inventory_item` exige articulo y almacen y conserva Inventory como autoridad condicional.
- `service` prohibe articulo y almacen; su recepcion es comercial, parcial o total, y no llama Inventory.
- Los fallos parciales de una recepcion multipardida conservan movimientos confirmados y dejan solo las lineas pendientes para reconciliacion.

### Admin e Inventory

- Admin incorpora la unidad estructural `E48` (`Unidad de servicio` / `Service unit`).
- Admin incorpora permisos `sales.service_order.*` y el folio administrado `sales.service_order`.
- Backoffice permite Compras para tenants de servicios sin Inventory.
- Inventory mantiene sus proyecciones de articulo/almacen para permisos de Compras cuando Inventory si esta activo; no concede escritura arbitraria de movimientos.

### Persistencia

La cabeza Local aplicada es `backend/alembic/versions/20260901_0030_sales_service_orders.py`, con `down_revision = 20260825_0029`.

Agrega en schema `sales`:

- `service_orders`;
- `service_time_entries`;
- `service_cost_entries`;
- `service_evidence`;
- constraints, indices tenant-first y FKs internas compuestas por tenant.

Tambien endurece discriminadores de partidas en `purchasing`, permite `warehouse_ref_id = null` para recepciones de servicio y agrega defaults estructurales idempotentes. No crea FKs entre schemas de servicios.

El downgrade debe ejecutarse solo en Local y despues de comprobar que no existan recepciones de servicio incompatibles. No aplicar migraciones directamente a QA; QA usa exclusivamente el gate protegido del pipeline.

## Contratos afectados

Nuevos endpoints Sales:

- `GET /v1/sales/service-orders` — `sales.service_order.read`.
- `GET /v1/sales/service-orders/{id}` — `sales.service_order.read`.
- `POST /v1/sales/service-orders/{id}/plan` — `sales.service_order.plan`.
- `POST /v1/sales/service-orders/{id}/time-entries` — `sales.service_order.time.create`.
- `POST /v1/sales/service-orders/{id}/cost-entries` — `sales.service_order.cost.create`.
- `POST /v1/sales/service-orders/{id}/evidence` — `sales.service_order.evidence.create`.
- `POST /v1/sales/service-orders/{id}/transitions/{action}` — permiso `sales.service_order.<action>` derivado en backend.

Contrato Sales modificado:

- `POST /v1/sales/orders/{id}/fulfillment` ya no admite `mode=service`; solo `stock` o `production`.

Purchasing conserva las mismas rutas, pero amplifica el contrato de partidas/recepciones para servicios sin articulo ni almacen. Admin cambia la dependencia declarada de Compras y publica unidad, folio y permisos. Inventory solo cambia autorizacion de proyecciones consumidas por Compras.

Production, Maintenance, Billing, Integration y Reporting no cambian contrato en CHG-255.

## Validacion ya ejecutada

- `git diff --check`: aprobado; solo aparecen avisos esperados LF/CRLF.
- Compilacion Python de servicios y migraciones: aprobada.
- Alembic: una sola cabeza, `20260901_0030`.
- 10 contratos OpenAPI parseados.
- 203 `operationId` unicos.
- Paridad entre operaciones OpenAPI implementadas y rutas FastAPI: aprobada.
- Migracion Local probada mediante `0029 -> 0030 -> 0029 -> 0030`, con limpieza comprobada antes del downgrade.
- Suite completa con PostgreSQL Local: `239 passed`, sin skips; los 10 recorridos focalizados de servicios en Ventas y Compras tambien pasan.
- `npm run verify` equivalente aprobado mediante el runtime Node de VS Code: validadores, compilacion y pruebas completas.
- OpenAPI parseado con el Python del entorno virtual y paridad runtime aprobada.

## Frontera de ambiente observada

La sesion fue `local-write` sobre archivos y PostgreSQL Local aislado:

- no se levantaron servicios;
- no se conectaron APIs;
- PostgreSQL Local se inicio en `127.0.0.1:5434/erclave_local` y quedo en `20260901_0030`;
- se ejecuto y verifico el ciclo `upgrade -> downgrade seguro -> upgrade` de CHG-255;
- las pruebas escribieron tenants y documentos transitorios y los limpiaron al finalizar;
- no se ejecutaron seeds o fixtures independientes; los defaults estructurales de la migracion quedaron idempotentes;
- no se uso Firebase; Firebase CLI no esta instalado y no se simulo una validacion de navegador;
- no se desplego ni movio trafico;
- Produccion no fue accedida.

El tenant autorizado para las pruebas Local aisladas fue `ERClave Demo QA`, ID `ten_739ee59d765d5e14818674800d`. La coincidencia del ID no autoriza escribir en QA.

## Como continuar despues del reinicio

1. Entrar a la raiz `eslaclave-erclave` y ejecutar `git status --short`; confirmar rama y `HEAD` anteriores.
2. Ejecutar `npm.cmd run session:context` si Node/npm ya esta disponible.
3. Leer `AGENTS.md`, `AGENTES.md`, este archivo, `ESTADO_ACTUAL.md`, `DECISIONES.md`, `TENANTS.md`, `PENDIENTES.md`, `modulos/04_ventas_clientes.md` y `modulos/03_compras_abastecimiento.md`.
4. Revisar el diff completo y conservar todos los cambios existentes.
5. Ejecutar `npm.cmd run verify`. Corregir cualquier drift real antes de declarar cierre.
6. Antes de nuevas escrituras Local, aplicar `$erclave-environment-boundaries` y comprobar explicitamente `127.0.0.1:5434/erclave_local` y el tenant autorizado.
7. No repetir el ciclo de migracion ya certificado salvo que cambie la revision o sea necesario diagnosticar una regresion.
8. Cuando Firebase CLI este disponible, queda como comprobacion complementaria el recorrido manual en navegador; no sustituye las pruebas PostgreSQL/API ya aprobadas.
9. Actualizar `TRAZABILIDAD.md` con cualquier correccion adicional y decidir con el usuario si desea commit/PR. No publicar ni promover por inferencia.

## Archivos nuevos sin seguimiento que no deben perderse

- `backend/alembic/versions/20260901_0030_sales_service_orders.py`.
- `backend/services/admin-service/tests/test_unit_seed_catalog.py`.
- `backend/services/purchasing-service/tests/test_purchasing_api.py`.
- `docs/operaciones/resultado_release_qa_20260901.md`.
- `docs/contexto/REANUDACION_CHG255.md`.

La lista completa de archivos modificados se obtiene con `git status --short`; el alcance funcional y contractual definitivo esta registrado en CHG-255 de `TRAZABILIDAD.md`.
