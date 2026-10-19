# CC-20 — Aceptación integrada en Local

## Resultado observado · 2026-10-18

CC20-01 conserva su acta aprobada. CHG-335 ejecuta los demás recorridos con HTTP/DB/Emulator y Chrome reales; [evidencia y límites por variante](paridad_local_qa_20261018.md). Se corrigieron defectos reales de actor/idempotencia, reintento de código manual y responsive. La tabla separa cobertura comprobada de variantes pendientes; ni verify ni una prueba con dobles cierran la aceptación integrada. QA y CC-19 real mantienen su autorización y evidencia independientes.

**CHG-327 · 2026-10-14 · paquete preparado, sin ejecución.** Este documento define el recorrido que se probará después en Local aislado. Ninguna fila está aprobada por redactarla. CC-19 (mapeo de datos reales) es independiente: los casos nuevos usan datos sintéticos controlados y los casos históricos sólo registros con procedencia conocida. Accounting permanece apagado.

## Objetivo y frontera

Demostrar con frontend, APIs autenticadas y PostgreSQL Local que la estructura Sociedad/División, los dueños operativos y sus intercambios funcionan juntos: autorización, moneda, cantidades, costo, snapshots, reintentos, recuperación, CSV e historia. Cada resultado necesita evidencia del recorrido completo. Los tests de navegador con respuestas interceptadas acreditan UI, pero no sustituyen el recorrido HTTP real.

**Ambiente permitido:** frontend y servicios en loopback, Firebase Auth Emulator y PostgreSQL `127.0.0.1:5434/erclave_local`; tenant `ten_739ee59d765d5e14818674800d`. No conectarse a QA/Producción, no usar otros tenants ni habilitar `ERCLAVE_TEST_ALLOW_TEMP_TENANTS`. No correr `verify:postgres` o `verify:local` como sustituto de esta matriz: la suite general incluye pruebas que crean tenants temporales y requieren autorización independiente. Las pruebas técnicas focales existentes y el recorrido CHG-315 son antecedentes, no resultado de CC-20.

## Protocolo de preparación del ensayo

1. Registrar fecha, HEAD, estado del árbol y huella del delta local; verificar host, puerto, base, tenant y configuración efectiva de cada servicio antes de cualquier escritura. Comprobar Alembic 0062 y servicios/contratos actuales. El SHA solo no identifica este árbol con cambios sin commit.
2. Confirmar que Accounting sigue `planned`/apagado. El catálogo básico de Centros de costos, si se usa, conserva permisos y capacidad propios; no activa Costing analítico ni Accounting.
3. Dentro del tenant autorizado, preparar identificadores sintéticos únicos: dos Divisiones de una misma Sociedad para traspasos, una División de otra Sociedad para rechazos, actores con alcance total y restringido/revocado, centros activos/inactivos, almacenes, artículos, producto/receta, máquina, puesto/trabajador, cliente y proveedor con asignaciones/condiciones explícitas. Moneda base y tasa se confirman; no usar `standard_cost` ni tarifa histórica como prueba de moneda.
4. Anotar IDs, claves de idempotencia, cantidades/saldos iniciales y dependencia de cada fixture. Crear sólo por APIs dueñas y registrar plan de limpieza exacto por IDs propios. No limpiar datos ajenos, historia o secuencias completas; un folio reservado puede dejar hueco sin ser defecto.
5. Para pruebas de historia usar registros legacy identificados en Local en modo lectura, sin asignarles División o costo ficticio. Si falta un caso histórico verificable, marcar su variante **Bloqueado por datos**; no fabricar un backfill CC-19.

**Disponibilidad observada en el preflight CC-19 del 2026-10-14:** el tenant Local tenía 1 Sociedad y 1 División; 3 almacenes y 3 máquinas sin División. Por ello todavía faltan los fixtures de cruces para CC20-01/04/13 y asignaciones positivas para varios recorridos. Esta observación no autoriza modificar los registros existentes. El `start_local.ps1` levanta/siembra el demo, pero no acredita por sí mismo estas precondiciones de aceptación. Ese preflight histórico no disponía de Node/npm; CHG-335 sí ejecutó Chrome y APIs reales con el runtime Node local. Consultar el acta actual para las precondiciones y resultados efectivos.

## Matriz de aceptación

Estado inicial del protocolo CHG-327: **Por ejecutar**; los resultados actuales constan en la columna Estado. `Pasa` requiere resultado observado y evidencia; `Falla` exige incidencia reproducible; `Bloqueado` identifica precondición faltante. En cada caso registrar actor, alcance, IDs, hora, request/correlation IDs cuando existan, capturas o consulta de solo lectura y limpieza.

| ID | Recorrido Local | Resultado observable requerido | Estado |
|---|---|---|---|
| CC20-01 | Admin: sesión, Emisor → Sociedad → División, selección activa, permiso y alcance. Revocar una División entre lectura y comando. | Backend rechaza detalle, comando, replay y CSV fuera del alcance; la UI no concede acceso por preferencia local. Documento previo conserva contexto. | **Pasa Local · 2026-10-18** |
| CC20-02 | Costing básico y RH: centro por División, puesto/trabajador compartidos, tarifa Decimal6 en moneda base confirmada. | Centro ajeno/inactivo y moneda/Sociedad incorrecta rechazados; cero permitido; trabajador exige puesto vigente. Multiadscripción no duplica capacidad global y la historia no se recalcula. | Local API: positivos/negativos y conservación de historia propia comprobados; legado CC-19 separado |
| CC20-03 | Inventory: almacenes y artículos por División, entrada manual, reversa, Kardex y saldos. | Una entrada/reversa por origen; existencia, reserva y disponible cuadran. Costo original/moneda y contexto quedan en el movimiento; folios históricos intactos. | Local API: entrada/reversa/replay, costo y conciliación comprobados; historia real sin procedencia no certificada |
| CC20-04 | Inventory: transferencia parcial entre dos Divisiones de la misma Sociedad, recepción, rechazo/retorno y sobrante. Probar División de otra Sociedad. | Ambos extremos autorizados; tránsito y cantidades reconcilian, costo/contexto originales se conservan; cruce de Sociedad rechazado antes de efectos. | Pasa Local API · parcial/retorno, ambos extremos autorizados, cruce Sociedad y costos |
| CC20-05 | Production manual: receta, recurso RH, máquina, capacidad, reserva/salida Inventory, etapas y recepción de terminado. | Compromiso de persona y máquina global sin sobreasignación; una salida y una recepción; cantidades/costo Decimal6 y contexto se explican por documento y movimiento. | Local API + impresión comprobados; receta/capacidad/consumo/cierre/recepción reales |
| CC20-06 | Sales: cliente y condiciones por División; cotización en moneda igual y distinta de Sociedad; CC-21 costo confirmado, cero, ausente y tasa ausente. Enviar/aprobar y convertir a pedido. | Vista previa se refresca; aprobación congela origen, tasa y convertido por partida. Sin costo/tasa permite aprobar con estimado/margen nulos; pedido copia snapshots y condiciones, sin recalcular. | Pasa Local API · cinco variantes CC-21, snapshots/pedido/historia + impresión |
| CC20-07 | Sales/Inventory: pedido con stock, reserva, entrega parcial y costo real; reintentar confirmación. | Existencia y reserva concilian; costo original de Sociedad y convertido documental usan una sola tasa; replay no duplica salida/entrega. | Pasa Local API · entrega parcial/final, costo, reservas y replay legado original |
| CC20-08 | Sales → Production → Inventory: solicitud de fabricación, orden única, salida, terminado, recepción y entrega. | Una solicitud produce una orden; costo original/convertido y cantidades siguen el origen; interrupción/reintento no duplica reserva, recepción ni entrega. | Pasa Local API · recuperación tras 503, orden única, recepción y entrega conciliadas |
| CC20-09 | Purchasing: proveedor y condiciones por División, requisición → autorización → OC → recepción física y de servicio. | Condiciones quedan congeladas, bienes generan un movimiento Inventory con almacén de la misma División y servicio no genera movimiento físico; costo/tasa/partidas concilian. | Local API comprobado · flujo mixto y USD→MXN; sin UI del circuito completo |
| CC20-10 | Purchasing negativos y recuperación: proveedor/almacén ajeno, condiciones incompletas, sobrerrecepción, tasa inválida, conflicto de revisión y reintento parcial. | Rechazo sin efecto cruzado; recuperación autorizada produce una recepción/movimiento, sin recostear ni duplicar. Compra directa se cubre por API porque no hay formulario de alta UI. | Pasa Local API · negativos y recuperación tras fallo de transporte real; misma clave, movimientos por línea exactamente una vez |
| CC20-11 | Maintenance: correctivo de máquina, técnico RH/tarifa, bloqueo, tiempo, refacciones, resolución y sobrantes. | Folio/contexto fijos; máquina se bloquea/libera, sin reanudar Production sola; costo laboral y refacciones conservan origen; no cerrar con solicitud pendiente; recuperación no duplica salida. | Pasa Local API · laboral/refacciones/sobrantes; Production pausada no reanuda sola al liberar máquina; resume explícito comprobado |
| CC20-12 | Folios CC-18: puesto RH, movimiento Inventory, proveedor/requisición/OC/recepción Purchasing y orden Maintenance en modos administrado/manual. | Mismo comando e Idempotency-Key retorna la misma identidad; payload distinto se rechaza; concurrencia no duplica. Movimiento interno sin captura en modo manual usa código estable del origen. | Pasa Local API · siete tipos managed/manual, concurrencia/replay y consumidor interno; configuración restaurada sin rebobinar next |
| CC20-13 | Alcance/permisos negativos transversales: revocar entre preflight y replay; referencias de otra División/Sociedad y actor distinto con misma clave. | Cada dueño revalida antes de efectos y antes de devolver replay; no filtra datos por UI solamente ni hereda resultado de otro actor. | Local comprobado · dos actores, scope revocado, intents/recovery por dueño; regresiones API/PG y HTTP separadas en acta |
| CC20-14 | Listas, detalle, CSV e historia legacy de Sales, Purchasing, Production, Inventory y Maintenance. | Filtros de alcance también rigen exportación; historia sin snapshot/moneda no se anuncia como verificada ni se recostea. Códigos, condiciones e impresión congelados permanecen; mutación histórica incompatible exige revisión. | Local sintético: listas/CSV/snapshots comprobados; historia sin CC-19 bloqueada por procedencia |
| CC20-15 | Accounting apagado durante operación y recuperación de los recorridos anteriores. | Ningún alta exige cuenta/libro/periodo; no se crea póliza ni se invoca Accounting para guardar. El acceso contable directo sigue no disponible sin runtime/entitlement/permiso. | Local: Accounting apagado durante los circuitos; no activación ni escrituras contables |
| CC20-16 | Navegador real: formularios, errores de negocio, ES/EN, ancho del contenedor, impresión CC-17 y reintento desde pantalla en los recorridos con UI. | Captura se conserva tras error; identidad/plantilla de cotización y orden Production usa snapshot de aprobación/liberación; acciones visibles coinciden con permiso y contrato. Las variantes sólo API quedan declaradas. | Local Chrome: ES/EN, responsive, selector, validación, negocio/retry y snapshots PDF; alcance por formulario en acta |

### Controles que se aplican a cada caso

- Medir antes/después por documento, partida y movimiento: estado, cantidad, existencia/reserva/disponible, importe original, moneda, tasa, convertido y snapshot aplicable. Diferencias se explican o fallan.
- Capturar HTTP autenticado y respuesta del servicio dueño, más consulta PostgreSQL de **solo lectura** cuando haga falta verificar persistencia. Registrar qué ruta se interceptó; una API simulada nunca acredita integración.
- Repetir la clave idempotente y comprobar que no haya segundo efecto; probar clave reutilizada con payload distinto, alcance revocado y fallo parcial donde aplique. El éxito visual sin conciliación no pasa.
- Mantener la matriz [QA](../qa/MATRIZ_EJECUCION_QA.md) separada: un caso Local aprobado no cambia el estado del SHA publicado en QA.

## Registro de ejecución para usar después

Copiar una fila por caso y variante en el acta de la sesión. No llenar `Pasa` por adelantado.

| Campo | Valor que se registrará |
|---|---|
| Caso, variante y resultado | CC20-NN; Pasa / Falla / Bloqueado / No aplica, con justificación. |
| Ambiente y versión | Local aislado; fecha/hora; HEAD y huella del árbol; Alembic; base/puerto sin credenciales; tenant. |
| Actor y precondiciones | Rol, permisos/alcance efectivos, datos y IDs propios, saldos iniciales. No registrar tokens ni contraseñas. |
| Pasos y observación | Acción UI/API, request/correlation ID, respuesta, estado persistido, cantidades/importes antes/después. |
| Evidencia | Log o captura local con ruta, sin secretos ni datos personales; consulta de conciliación y limitación de dobles si los hubo. |
| Cierre | Incidencia vinculada o IDs limpiados; saldos finales, documentos intencionalmente conservados y decisión pendiente. |

## Criterio de cierre

CC-20 se puede declarar aceptado **en Local** sólo tras ejecutar todos los casos aplicables, documentar resultado y evidencia por variante, resolver fallas bloqueantes y reconciliar efectos entre dueños. Variantes históricas sin datos CC-19 se identifican como bloqueadas y dejan explícito el alcance no aceptado. Un candidato QA posterior requiere su propia autorización y matriz por ambiente; este paquete no lo promueve. Word pendiente y datos reales CC-19 conservan sus estados separados.

**APIs afectadas:** CHG-327 sólo preparó el protocolo. CHG-335 corrige semántica de actor/idempotencia y recuperación en RH, Inventory, Sales, Purchasing, Maintenance y evidencia Production; GET /ready compartido añade comprobación DB/head y HTTP503 remoto. Métodos, rutas, permisos y evidencia se detallan en el [acta del corte](paridad_local_qa_20261018.md). No cambian payloads operativos ni se añade migración.
