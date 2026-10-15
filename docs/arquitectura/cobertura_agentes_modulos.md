# Cobertura de agentes, skills y fronteras

## CHG-310 · Custodio contable

El agente técnico de Contabilidad existente custodia [el control por submódulo](../contexto/CONTROL_CONTABLE.md), con validación de negocio contable y evidencia de cada dueño. La skill erclave-accounting incorpora seguimiento y prevención de trabajo duplicado; context-reconcile y module-boundaries conservan su función transversal. No se crea un módulo ni se reemplazan agentes operativos.


## Actualización CHG-308 · 2026-10-07

CHG-308 incorpora preparación de contexto Production bajo fichas de Producción, Inventory, RH, Sales y Contabilidad y guardianes transversales. No confundir estructura con validación monetaria o fabricación completa. Ver docs/arquitectura/cont_08_produccion_contexto.md.


## Actualización CHG-307 · 2026-10-05

Ventas/Inventarios/Producción y guardianes Contabilidad/datos/API/seguridad/formularios cubren stock y costo en moneda de Sociedad. Mantener separada habilitación Accounting de operación; otros flujos aún pendientes. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


## Actualización CHG-306 · 2026-10-05

Inventarios/Ventas y guardianes cubren fuente de contexto, persistencia/replay y filtros de consulta. Contabilidad identifica moneda de costos pendiente de decisión. No atribuir cierre del recorrido de productos a esta preparación.


## Actualización CHG-305 · 2026-10-05

Ventas cubre ejecución de servicios dimensionados; RH/Production incorporan consumidores puntuales. Seguridad/DB protegen scope, minimización, replay y cancelación concurrente. Productos/entregas todavía bloqueados.


## Actualización CHG-304 · 2026-10-05

Ventas cubre copia de contexto a pedidos y contexto de servicios, lectura/CSV y cancelación. Seguridad protege fronteras previas a efectos y replay. RH/Production validan consumidor sales.order.create activo. Accounting no se activa.


## Actualización CHG-303 · 2026-10-05

Ventas protege snapshot, scope y conversión bloqueada; RH/Production protegen proyecciones y permisos de consumidor activo. Seguridad incluye CSV. Contabilidad no se activa.


**CHG-302 Local:** [Condiciones comerciales explícitas](cont_07_commercial_condiciones.md), head `20260928_0045`: usuario confirma opción 2, sin herencia del maestro ni entre Divisiones. Sales/Purchasing conservan datos/revisión/auditoría propios; Admin autoriza y valida catálogos. Sin backfill, condiciones permanentes ni activación contable. CONT-08 documental/snapshots y CONT-06 pendientes; QA/Producción intactos.

**CHG-301 Local:** [Disponibilidad comercial CONT-07 parcial](cont_07_commercial_asignaciones.md), head `20260928_0044`: Sales/Purchasing conservan asociaciones propias cliente/proveedor–División y Sociedad derivada. Admin autoriza, sin centros ni activación contable. Condiciones comerciales siguen en el maestro; faltan condiciones por alcance y CONT-08 documental. Cero backfill/asignaciones permanentes; QA/Producción intactos.

**CHG-300 Local:** [CONT-07 HR parcial](cont_07_hr_asignaciones.md), head `20260927_0043`: puestos compartidos con tarifa/centro opcional por División y trabajadores con elegibilidad confirmada para su puesto vigente. Sin backfill; CONT-07 Sales/Purchasing y CONT-08 pendientes.

**CHG-299 Local:** [CONT-07 Production parcial](cont_07_production_asignaciones.md), head `20260927_0042`: máquinas con División fija, productos/servicios compartidos con asignaciones y centro opcional. Sin backfill; CONT-07 HR/Sales/Purchasing y CONT-08 operativos pendientes.

**CHG-298 Local:** [CONT-07 Inventory parcial](cont_07_inventory_asignaciones.md), migración `20260927_0041`: almacenes con División explícita y artículos con asignaciones, sin duplicar maestros ni backfill supuesto. Catálogos/documentos operativos heredados aún no se aíslan por División; otros dominios CONT-07 y CONT-08 pendientes.

**Vigente CHG-297 Local:** [catálogo básico CONT-05](cont_05_catalogo_centros.md) implementado en Costing/8014, disponible con Administración y cuatro permisos puntuales; migración `20260927_0040`. Admin numera y Costing persiste; sin analítica ni Accounting. CONT-04 transversal y CONT-06/07/08 siguen pendientes. Las notas fechadas anteriores describen su corte.

**Actualización CHG-296:** usuario confirma catálogo básico desde Administración y obligación de centro sólo por flujo de imputación habilitado. [Matriz y contrato de sesión implementado](matriz_capacidades_organizacionales.md). Fase 1 incorpora disponibilidad separada de permisos; CONT-04/05 y propagación siguen pendientes. El alcance comercial del catálogo ya se decidió; la autorización por acción se implementará en CONT-05. Lectura tras suspensión y configuración contable incompleta siguen siendo políticas futuras por concretar. Las propuestas anteriores se leen con esta decisión vigente.


**Criterio CHG-294:** aplicar [Contabilidad opcional y capacidades](contabilidad_opcional_y_capacidades.md). Administración y dimensiones operativas independientes de Accounting; catálogo básico Costing separado de analítica y libro. Antes de CONT-05/07/08 resolver autorización del catálogo y obligatoriedad de centro para tenants sin costos/contabilidad; antes de eventos/libros resolver activación temporal y recuperación. Documento de diseño, sin cambios de runtime.


Revisión Local del 27 de septiembre de 2026. Inventario documental, no certificación funcional ni de despliegue. Estado de cada capacidad: `docs/contexto/ESTADO_ACTUAL.md`.

Todos los dominios del índice tienen agente de negocio y técnico en `AGENTES.md`. Todos aplican feature, ambientes, migraciones cuando cambian datos, contrato/feedback de formularios, evidencia QA y manuales según el trabajo. No requieren una skill exclusiva para repetir estas protecciones. `erclave-module-boundaries` gobierna cambios entre dominios.

| Módulo / dominio | Cobertura negocio y técnica | Frontera e invariante prioritaria | Especialización adicional |
|---|---|---|---|
| Producción | Ambas fichas | Production posee recetas/órdenes; Inventory mueve existencias y RH valida capacidad. | Accounting cuando emita hechos económicos. |
| Almacenes e inventarios | Ambas fichas | Inventory posee reservas, Kardex, valuación y movimientos; evitar doble consumo/recepción. | Accounting para dimensiones/eventos. |
| Recursos Humanos | Ambas fichas | Identidad laboral, puesto vigente y capacidad; no confundir trabajador con usuario/rol. | Skills comunes; nómina continúa fuera del alcance implementado. |
| Compras | Ambas fichas | Purchasing posee requisición/orden/recepción comercial; Inventory confirma bienes; solicitante acepta servicios. | Accounting al definir recepción/factura/pasivo. |
| Ventas | Ambas fichas | Sales posee pedido/entrega comercial; Inventory confirma salida; facturación no se presume implementada. | Accounting para costo/ingreso/CxC. |
| Mantenimiento | Ambas fichas | Maintenance posee orden/tiempos; Inventory refacciones y devoluciones, RH elegibilidad. | Incluido ahora en validación obligatoria de agentes. |
| Gastos y cuentas por pagar | Ambas fichas | Expenses posee gasto/documento/pago futuro, sin escribir libro ni asumir aprobación por XML. | Accounting; políticas fiscales concretas requieren fuente/decisión vigente. |
| Costos y centros de costos | Ambas fichas | Costing posee centros/cálculos; Admin presenta alta mediante contrato; Accounting posee libro. | Accounting para imputación; no crear catálogo duplicado en Admin. |
| Reportes e inteligencia operativa | Ambas fichas | Lecturas autorizadas y filtros de tenant/alcance; sin mutaciones ni acceso SQL transversal implícito. | Module-boundaries para datasets cruzados. |
| Administración y configuración | Ambas fichas | Admin posee organización, membresías, permisos y entitlements; Firebase sólo identidad. | Accounting para Sociedad/División y module-boundaries para catálogo Costing. |
| Contabilidad | Ambas fichas reforzadas | Accounting posee libro por Sociedad; eventos idempotentes, balance, periodo y reversa. | Nueva `erclave-accounting`. |
| Sinergia modular | Ambas fichas | Contratos entre productor/consumidor, error parcial y compensación. | Nueva `erclave-module-boundaries`. |
| Diseño, experiencia y localización | Ambas fichas | ES/EN, accesibilidad, responsive por contenedor y captura preservada. | Form-contract, form-feedback y solution-manuals. |

## Hallazgos y tratamiento

1. Contabilidad tenía dos fichas, pero sin suficiente detalle sobre libro por Sociedad, idempotencia, concurrencia de cierre, historia y guardianes. Se amplían y se agrega una skill específica. Esto no implementa Accounting.
2. Mantenimiento figuraba en catálogo/fichas, pero faltaba en la lista obligatoria del validador. Se incorpora.
3. El validador contaba roles globalmente y podía pasar con un módulo sin ficha si otro repetía roles. Se exige negocio/técnico dentro de la sección de cada dominio y se contrasta el índice funcional.
4. La ausencia de skills por módulo no es por sí misma un riesgo: las skills existentes son transversales. Se agrega una ruta explícita para ownership/integraciones y se incluyen ambas nuevas skills en tooling.
5. Gastos, Costos, Reportes y Contabilidad siguen con capacidades planned según el estado vigente; sus fichas no prueban seguridad de runtime aún no construido.

## Riesgos de implementación que siguen abiertos

- CONT-03 implementa migración de semántica heredada sin Matriz ficticia ni ampliación de scopes restringidos. Conversión aplicada sólo al tenant Local autorizado; otros ambientes pendientes.
- CONT-04/05/07/08 deben llevar configuración, centros, maestros y documentos al alcance efectivo. No declarar separación operativa por tener catálogos.
- El programa contable posterior requiere eventos, libros y conciliación; no generar asientos desde botones o desde tablas de otros servicios.

La revisión de cobertura no es una auditoría exhaustiva de cada endpoint ni reemplaza pruebas conductuales. Los guardianes compartidos son Arquitectura, Datos/Custodio DB, API, Seguridad, Sinergia, QA/Release y UX/Manuales según impacto.

Backoffice y provisioning se revisan con Administración, Arquitectura/API y Seguridad; shell/shared con Arquitectura y Diseño/i18n. Billing e integraciones futuras no se consideran dominios implementados por tener carpetas: antes de habilitar una capacidad autónoma deben quedar su dueño funcional/técnico, contrato, permisos y evidencia en la matriz. Esta revisión no habilita módulos ni crea entitlements.

Riesgo adicional encontrado durante CONT-03: seed demo/onboarding sustituían metadata de membresías, lo que podía borrar un alcance ya versionado. Se conserva metadata y alcance existentes y se añade regresión PostgreSQL con rollback en el tenant permitido. No se ejecutan seeds QA por modificar el script compartido.
