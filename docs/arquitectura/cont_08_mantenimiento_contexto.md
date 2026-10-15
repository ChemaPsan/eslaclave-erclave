# CONT-08 · Contexto de Mantenimiento

## Vigencia

CC-16 · CHG-320 · 2026-10-12. Implementado y probado Local. Verify general posterior a conciliación documental; no acredita UAT ni promoción QA. Head Local `20261012_0059`; migración aditiva comprobada up/down/up, sin backfill. Conserva [materiales CC-14](cont_08_inventario_productores.md), fabricación CC-12 y Compras CC-15. Accounting continúa apagado; datos CC-19 y aceptación CC-20 permanecen separados.

## Autoridades y reglas

Maintenance conserva orden correctiva, contexto, técnico, tiempo, costo laboral y solicitudes de refacciones. Admin gobierna División/Sociedad/moneda y alcance; RH gobierna trabajador, puesto, asignaciones, capacidad nominal y tarifa confirmada. Production conserva máquina/orden productiva y bloqueo/liberación; Inventory conserva reservas, existencias, movimientos y costo material. Sin escritura entre schemas ni nuevas FKs cruzadas.

Instalación u otro objetivo requiere División explícita autorizada. Máquina deriva su División física. Origen productivo hereda `organization_context` de su orden y exige coincidencia con la máquina. Una División enviada que contradiga la autoridad se rechaza. Sociedad y moneda base derivan de Admin; no se capturan libremente. Contexto fijo al guardar; Centro de costos no se exige fuera de un flujo de imputación habilitado.

Asignar, iniciar, reanudar, reabrir y registrar tiempo revalidan trabajador y puesto activos, elegibles para Mantenimiento en la División de la orden. RH devuelve sólo proyección operacional, con tarifa explícita confirmada en moneda de esa Sociedad. No usar salario, tarifa global o condiciones de otra División como respaldo. Tarifa cero es válida; tarifa ausente o sin moneda confirmada bloquea uso nuevo.

Cada tiempo conserva `organization_context`, `labor_cost_snapshot` y costo/moneda. Snapshot: trabajador, puesto/nombre, revisiones de asignación del trabajador y puesto, minutos nominales por persona, tarifa horaria, moneda/Sociedad, fecha de confirmación, segundos exactos, costo y regla `half_up_6`. Cálculo Decimal: segundos × tarifa / 3600, redondeado a seis decimales. Fechas con zona obligatoria normalizadas UTC, fin posterior a inicio y no futuro. No calcular costo a partir de minutos enteros de presentación ni recostear tiempos anteriores. Revisión esperada de tarifa evita guardar una condición distinta de la mostrada.

El control de solapamiento y minutos diarios se aplica a la misma persona en todas las órdenes de Maintenance del tenant, incluso en distintas Divisiones, con serialización concurrente por trabajador. El día se corta en UTC y los intervalos que cruzan medianoche se distribuyen entre días. **No reserva capacidad transversal Sales/Production** ni suma capacidades nominales de asignaciones para multiplicar una persona. No equivale a agenda global.

## Alcance y recuperación

Orden, detalle, tiempos, materiales y CSV exigen permiso puntual y alcance antes de devolver un replay o producir efectos. Los nuevos comandos documentales vinculan la clave al actor y payload; alcance revocado bloquea el reintento. No hay bypass por nombre de rol. Los endpoints de bloqueo/liberación Production validan directamente el alcance físico antes de replay/efecto, también cuando los llama otro cliente. Una máquina legacy sin División sólo admite recuperar bloqueo/liberación con alcance completo; no se inventa su contexto.

Documentos antiguos sin contexto no reciben División/moneda/tarifa por suposición. Su lectura y recuperación admitida requieren alcance completo; nuevas mutaciones ordinarias exigen revisión histórica. Las refacciones CC-14 con snapshot auténtico conservan prueba de productor, reserva/consumo/liberación/retorno y costo original. Una solicitud nueva hereda contexto de orden y exige almacén de su misma División. El legado no habilita consultas globales para usuarios con alcance limitado.

Resolver conserva diagnóstico, trabajo, verificación, tiempo y conciliación de materiales como requisitos. Liberar máquina no reanuda automáticamente Production. Conciliar continúa el mismo intento durable y no crea otra solicitud, salida o devolución.

## Campos y APIs afectadas

| Campo/consulta | Tarea y autoridad | Captura y conservación |
|---|---|---|
| `OrderCreate.division_ref_id` | División autorizada Admin | Requerida instalación/otro; máquina/origen derivan. ID hasta 40 caracteres; fija tras alta. |
| `organization_context` | División/Sociedad/moneda efectivas | Generado servidor, heredado por tiempos/materiales. |
| `assigned_worker_id`, `worker_id` | Técnico elegible RH | Selección acotada por División y propósito maintenance; no texto libre. |
| `expected_position_assignment_revision` | Confirmar tarifa mostrada | Entero positivo opcional API; si presente debe coincidir. |
| `started_at`, `ended_at` | Trabajo ejecutado | Zona horaria obligatoria; UTC servidor; sin futuro/solape/exceso diario. |
| Tarifa, costo, moneda y revisiones | Evidencia laboral RH/Maintenance | Sólo lectura, Decimal exacto congelado por tiempo. |
| `warehouse_id` | Destino físico Inventory | Misma División de orden; prueba y costo CC-14 conservados. |

Contratos modificados: [Maintenance 1.1](../../contracts/api/maintenance-service.openapi.yaml), [RH 0.2](../../contracts/api/hr-service.openapi.yaml), [Production 0.3](../../contracts/api/production-service.openapi.yaml). Maintenance incorpora `GET /v1/maintenance/document-divisions` (`maintenance.order.create`, `q/limit/offset`), contexto en `POST/GET /orders`, `GET/PATCH /orders/{id}`, `POST /orders/{id}/transitions`, `POST /orders/{id}/reconcile`, `GET/POST /orders/{id}/time-entries`, lecturas/alta de materiales, bandejas y `GET /reports/{report_code}/export`; cada acción conserva sus permisos puntuales.

RH amplía `GET /v1/hr/division-workers?purpose=maintenance` para `hr.worker.read` o permisos consumidores Maintenance pertinentes, con proyección de tarifa/capacidad confirmadas, `division_id`, `resource_id`, búsqueda y paginación. Permisos sólo Sales no permiten consultar la tarifa técnica de Maintenance. Production endurece `POST /v1/production/machines/{machine_id}/maintenance-block` y `/maintenance-release`; conserva permisos request/reopen y resolve/cancel, respectivamente. Inventory se consume por contratos existentes; no se cambia su ownership ni se habilita Accounting.

## Evidencia y aceptación

Backend final Local: seis suites Maintenance **50 aprobadas, 0 omitidas, 1 advertencia, 26.77 s** (`chg320-maintenance-tests.log`), incluidos **11 casos CC-16 nuevos: 2 puros y 9 PostgreSQL**. La adaptación unitaria previa de dos archivos sumó 22 aprobadas (`chg320-maintenance-api-unit.log`); es parte del trabajo, no se suma como cobertura independiente a la suite final. RH **6 PostgreSQL/API** más negativa de acceso Sales-only y Production **3 de alcance/legacy** aprobadas según integración raíz. Migración0059 up/down/up y guardrail de revisión tipada aprobados Local. Suite cruzada RH/Production final 123 aprobadas/0 omitidas (chg320-cross-tests-final.log). Navegador final 271 aprobadas/0 omitidas/0 fallos,3.7 minutos, incluye16CC16 ES/EN y regresión CC14/15 (cc16-browser-regression-final.log), APIs interceptadas. Verify final aprobado: validadores, compilación y backend738 aprobadas/233 omitidas/1 warning sin DB (chg320-verify-final.log); omisiones no cuentan como aprobaciones. No atribuir estos resultados a aceptación transversal CC-20.

Casos requeridos: máquina/origen/almacén de otra División; scope vacío/revocado antes de replay y efectos; legado sin backfill; trabajador reasignado/inactivo; tarifa cero, ausente, moneda distinta y revisión cambiada; costo de seis decimales; simultaneidad/solape entre órdenes y días UTC; conservación histórica y recuperación CC-14. Navegador ES/EN debe conservar captura y clave, mostrar errores por campo y probar ancho real de contenedor; interceptores no sustituyen integración HTTP ni CC-20.

[Ficha Mantenimiento](../../modulos/11_mantenimiento.md) · [Manual](../manuales_solucion/fuentes/11_mantenimiento.md) · [Control](../contexto/CONTROL_CONTABLE.md) · [Estado](../contexto/ESTADO_ACTUAL.md).
