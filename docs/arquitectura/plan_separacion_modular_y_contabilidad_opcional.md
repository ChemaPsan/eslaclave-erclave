# Plan de separación operativa y Contabilidad opcional

## Estado y fuentes de vigencia

La conciliación por submódulo vive en [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md); [ESTADO_ACTUAL](../contexto/ESTADO_ACTUAL.md) distingue Local de QA y [PENDIENTES](../contexto/PENDIENTES.md) fija la continuación. Evidencia de cada corte en [TRAZABILIDAD](../../TRAZABILIDAD.md). No sumar pendientes históricos como trabajo nuevo.

Organización/sesión, [centros CONT-05](cont_05_catalogo_centros.md), asignaciones CONT-07 y [condiciones explícitas sin herencia](cont_07_commercial_condiciones.md) ya están implementados Local. CONT-04 es parcial y CONT-06 sigue abierto. CONT-08 conserva [cotización](cont_08_cotizaciones_contexto.md) → [pedido](cont_08_pedidos_contexto.md), [servicios](cont_08_servicios_contexto.md), [stock/entrega y movimientos manuales](cont_08_stock_contexto.md). [Producción manual CHG-313](cont_08_produccion_contexto.md) y [fabricación comercial CHG-315](cont_08_fabricacion_contexto.md) conectan contexto, recursos, recepción y entrega/costo; recorrido HTTP Local real aprobado, aceptación transversal CC-20 pendiente.

Política CHG-309 confirmada: costos y tarifas en moneda base de Sociedad; documento en otra moneda conserva original, tasa explícita y convertido. La adaptación completa sigue pendiente, incluidos servicios; no reinterpretar historia. Analítica Costing y Accounting permanecen planned. Datos reales y aceptación integrada siguen abiertos; estos cortes no fueron promovidos a QA.

## Objetivo y punto de partida

Permitir operar por Sociedad y División sin activar Contabilidad, preparar Centros de costos sin habilitar cálculos automáticamente y activar posteriormente Costos o Contabilidad con controles propios. La ubicación de una pantalla no cambia el dueño del dato.

CONT-01/02/03 y CONT-05 ya aportan organización, sesión y catálogo básico Local; CONT-07 implementa asignaciones y condiciones. CONT-08 es parcial. Analítica Costing y Accounting siguen planned. Este plan ordena el [programa CONT existente](plan_preparacion_contabilidad.md) bajo la [frontera opcional](contabilidad_opcional_y_capacidades.md); no crea un programa paralelo ni declara completados sus cortes.

## Reglas de diseño

- Admin posee organización, membresías y activación; cada servicio posee sus maestros, asignaciones y documentos.
- Costing posee catálogo de centros y cálculo de costos. El catálogo básico se presenta en Administración mediante contrato; analítica de Costos es una capacidad separada.
- Accounting posee libros por Sociedad, cuentas, periodos, mapeos y pólizas. Crear una Sociedad no crea ni activa su libro.
- Organización, permisos y operación no dependen de Accounting. Contabilidad apagada no exige cuentas, periodos ni mapeos y no genera efectos contables.
- Toda capacidad exige implementación real, disponibilidad para el tenant, permiso y alcance. Menús, API y procesos automáticos respetan la misma regla.
- Nuevas dimensiones se incorporan con expansión, migración explícita, validación y exigencia posterior. No usar «Matriz» ni un centro ficticio para rellenar historia.

## Secuencia de ejecución

| Fase | Cortes relacionados | Entregable | Responsables principales | Criterio de salida |
|---|---|---|---|---|
| 1. Contrato de capacidades | Preparación de CONT-04/05 | Matriz de catálogo básico, analítica y Accounting; autorización y obligatoriedad explícitas | Administración, Arquitectura, Seguridad, Costos y Contabilidad | Ninguna capacidad se habilita implícitamente por otra ni por aparecer en Admin. |
| 2. Configuración por División | CONT-04 | Herencia Corporativo → Sociedad → División, override reversible y origen visible del valor | Admin y cada servicio dueño; Datos y Sinergia | Herencia sin empates, referencias del scope correcto e historia sin recalcular. |
| 3. Centros y códigos | CONT-05/06 | Catálogo Costing por División, UI Admin, permisos puntuales, códigos estables y lectura elegible | Costos, Administración, API y UX | Alta/edición/estado auditados e idempotentes; centros ajenos o inactivos rechazados para uso nuevo. |
| 4. Maestros y recursos | CONT-07 | Asignaciones de maestros compartidos; División de almacenes y máquinas; referencias elegibles | Inventory, Production, HR, Sales y Purchasing | Recursos asignados y maestros sin duplicar; tenant/División validados en backend. |
| 5. Documentos y movimientos | CONT-08 | Dimensiones y snapshots por documento/línea; filtros y validación en todos los consumidores | Agentes de cada módulo, Sinergia y Seguridad | Rechazos cruzados comprobados; Sociedad/Emisor derivados; División inmutable tras primer efecto; operación válida con Accounting apagado. |
| 6. Integración económica opcional | CONT-09/10/11 y capacidad analítica de Costos | Eventos/outbox, contratos de consumo y habilitación independiente por tenant | Operación, Costos, Arquitectura/API y Datos | Reentrega sin duplicados, conciliación y ningún efecto contable para tenants fuera del periodo habilitado. |
| 7. Contabilidad activable | CONT-12/13/14 | Libros/cuentas/periodos/mapeos, activación con fecha y ciclo de apagado/reactivación | Contabilidad, Administración, Seguridad y QA | Configuración validada; asientos balanceados e inmutables; cierre, reversas e historia controlados. |

CONT-15/16 (fiscal, cartera y pagos), CONT-17 (copias) y CONT-18 (reportes/cierre) conservan su alcance posterior y deben respetar estas capacidades. La analítica de Costos requiere su propio corte vertical y evidencia; no se considera implementada sólo por completar eventos o catálogo.

## Fase 1 con decisiones concretas

Preparar una matriz por capacidad con dueño, servicio, superficie, permisos, disponibilidad para el tenant, dependencias y comportamiento apagado. Extender el contrato existente de habilitación sólo donde sea necesario; no inventar nombres de flags ni implementar un segundo sistema de permisos antes de revisar el actual.

Política confirmada y criterios futuros de activación (CHG-296; no confundir con runtime contable):

| Situación | Comportamiento propuesto |
|---|---|
| Sin Costos analítico ni Accounting | Sociedad/División operativas; catálogo básico configurable si está disponible; no exigir centro únicamente por preparación. |
| Costos activo y Accounting apagado | Centros requeridos en los flujos de imputación de costos definidos; cálculos de Costos autorizados; sin cuentas, periodos ni pólizas. |
| Accounting habilitado pero sin configurar | Asistente/configuración para usuarios autorizados; no contabilizar. La operación no espera a configurar el libro. |
| Accounting configurado y efectivo | Procesar sólo eventos elegibles desde su fecha de inicio; validar centros cuando el tipo de efecto o cuenta lo requiera. |

La obligación de centro previamente acordada no se elimina silenciosamente: especificar su condición de aplicación por flujo antes de CONT-07/08. La disponibilidad básica del catálogo y obligatoriedad condicional fueron confirmadas en CHG-296. El acceso histórico tras suspensión y la política durante activación contable incompleta siguen por concretar; no inferir acceso gratuito, licencias ni permisos. El catálogo básico ya está implementado en CONT-05, disponible desde Administración sin habilitar la analítica de Costos.

## Migración y datos existentes

1. Inventariar por tenant los recursos, maestros y documentos sin dimensiones, con conteos y referencias ambiguas.
2. Recibir la estructura real Sociedad → División → Centro de costos y la asignación explícita de los registros actuales. Esto bloquea su backfill, no el diseño ni las pruebas con fixtures autorizados.
3. Generar vista previa reproducible de asignaciones y excepciones; comprobar referencias, alcance y estado. No adivinar relaciones desde nombres libres.
4. Aplicar backfill idempotente sólo sobre el alcance revisado, con auditoría y reconciliación de conteos; conservar códigos e historia.
5. Exigir dimensiones únicamente cuando cada flujo tenga migración y política resueltas; retirar compatibilidad después de verificar consumidores.

El desarrollo y los fixtures usan exclusivamente el tenant Local autorizado. QA/Producción requieren su procedimiento y autorización de release; este plan no las concede.

## Ciclo de Contabilidad

**Antes de activar:** runtime implementado, entitlement y permisos vigentes, Sociedades seleccionadas, libros configurados, fecha de inicio, periodos y mapeos revisados. Mostrar pendientes de configuración; habilitado no significa listo.

**Durante operación:** el productor guarda su hecho operativo sin depender de una llamada síncrona a Accounting. Los efectos elegibles se procesan con idempotencia, correlación y conciliación. Un error contable debe quedar visible en su propio flujo, sin convertir una operación guardada en fracaso ficticio.

**Al apagar:** coordinar el corte con workers y transacciones en curso; detener efectos nuevos/reintentos contables y conservar historia. API directa y procesos automáticos vuelven a comprobar habilitación. La lectura/exportación histórica sigue la política autorizada, no un bypass por ser de sólo lectura.

**Al reactivar:** revisar el intervalo apagado y excepciones; no generar pólizas de todo el pasado automáticamente. Aperturas o importaciones históricas requieren alcance explícito, evidencia suficiente e idempotencia. Definir retención de eventos y no prometer recuperación de datos no conservados.

## Pruebas y cierre por fase

- Operación con ambos módulos opcionales apagados; Costos activo sin Accounting; catálogo básico sin analítica; Accounting habilitado sin configurar y plenamente configurado.
- Usuario sin permiso, módulo apagado, acceso directo a API y jobs pendientes durante desactivación.
- Dos scopes incompatibles, referencias inactivas, listas vacías, cambios concurrentes y aislamiento por tenant.
- Idempotencia, activación/desactivación concurrente, reactivación sin duplicados y snapshots históricos intactos.
- Captura ES/EN, errores recuperables, referencias escalables y responsive cuando cambie UI.
- Pruebas de dominio/API; PostgreSQL real para persistencia; navegador para recorridos; contratos, manuales, agentes, estado y trazabilidad actualizados; verify como gate del corte.

Las pruebas de este plan son criterios futuros, no resultados ejecutados. El hito de separación operativa se obtiene al cerrar fases 1–5 y su migración, incluso con Accounting apagado. El hito contable se obtiene por separado al cerrar fase 7; no se debe retrasar el primero hasta implementar todo el programa financiero.

## Próximo paso ejecutable

Continuar CC-10/11/12 de [CONTROL_CONTABLE](../contexto/CONTROL_CONTABLE.md): moneda de tarifas, capacidad y fabricación. Conservar catálogo/asignaciones/condiciones y flujos Sales/Inventory ya implementados. CC-08 requiere adaptación monetaria; CC-14–20 siguen con sus brechas específicas. No activar módulos por la mera existencia de este plan.

## APIs afectadas

Ninguna modificada o consumida en CHG-295. Cada fase futura entregará su matriz exacta de métodos/rutas, permisos, request/response, consumidores y compatibilidad antes de cerrar el corte.
