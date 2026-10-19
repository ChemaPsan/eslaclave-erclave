---
name: erclave-accounting
description: Diseñar, implementar o revisar Contabilidad ERClave y contratos operativos que alimenten libros, pólizas, periodos, mapeos o dimensiones contables. Aplicar también al seguimiento de pendientes contables por submódulo y a cambios de Sociedad, División y Centro de costos que afecten imputación; no activa Accounting por existir estructura organizacional.
---

# Contabilidad y fronteras económicas ERClave

Leer desde la raíz `modulos/09_contabilidad.md`, `docs/arquitectura/plan_preparacion_contabilidad.md`, las decisiones vigentes y las fichas de Contabilidad y guardianes en `AGENTES.md`. Identificar el corte CONT y ambiente; una capacidad prevista no es runtime. Para ejecución vertical usar `erclave-feature`; para persistencia `erclave-db-migration` y para formularios las skills de contrato/feedback.

## Decisiones que no se vuelven a inferir

- Corporativo es tenant; libro por Sociedad; cada Sociedad tiene un Emisor; un Emisor puede servir a varias Sociedades del mismo tenant.
- División pertenece a Sociedad; Centro de costos pertenece a División. Admin gobierna organización, Costing gobierna centros y costos, Accounting gobierna libros, periodos, mapeos y pólizas. Alta de centros visible en Administración mediante contrato con Costing.
- Sociedad y Emisor se derivan de División. Backend valida pertenencia, vigencia, alcance autorizado y referencias relacionadas; no basta el selector ni una preferencia del navegador.
- Maestros compartidos conservan identidad y asignaciones por División; recursos físicos y documentos guardan División efectiva. No duplicar maestros ni reinterpretar historia al cambiar configuración.

## Revisión funcional y técnica

Para cada efecto definir documento/línea origen, momento económico, servicio productor, importe/moneda originales, regla de conversión/redondeo, dimensiones y evidencia. Distinguir compromiso, efecto operativo y contabilización. No inventar tasas, cuentas, tratamientos fiscales o momentos de reconocimiento. Si una regla normativa concreta es necesaria, verificar fuente oficial y vigencia/jurisdicción; registrar la política elegida y la decisión pendiente que materialmente bloquee ese corte.

Usar Decimal y moneda base configurable inicialmente MXN. Congelar importe original, tipo capturado, importe base y versión de regla al contabilizar. Balance exigido por asiento/libro/moneda base; nunca compensar desequilibrios entre Sociedades ni generar una cuenta puente silenciosa.

Mantener permisos puntuales para capturar, validar, contabilizar, reversar, cerrar y reabrir. Especificar segregación de funciones como política explícita, nunca por nombre de rol. Periodo cerrado rechaza contabilización ordinaria; reapertura auditada. Póliza contabilizada inmutable; corrección mediante reversa vinculada. Inactivación de cuenta/centro bloquea uso nuevo y conserva lectura histórica.

## Contratos y recuperación

El servicio operativo conserva sus documentos y publica eventos versionados con origen, tenant, Sociedad, División, Centro de costos, correlación e identidad idempotente. Accounting no escribe tablas operativas; tampoco Costing escribe el libro. Sin FK entre schemas de servicios. No implementar eventos/outbox antes de su corte autorizado.

Una ingesta repetida no duplica efectos; un mismo identificador con contenido diferente se rechaza. Mapeo ausente/ambiguo, referencia no válida o periodo cerrado queda pendiente visible, sin éxito ficticio. Diseñar concurrencia entre cierre y contabilización, reentrega, orden de eventos y recuperación parcial. Reconciliar documento → evento → póliza con importes y cantidades explicables.

## Evidencia exigible según el corte

Probar cruces de tenant/Sociedad/División, scopes vacíos/revocados, referencias inactivas, duplicados, fallos parciales, concurrencia, conservación histórica y permisos. Para núcleo contable añadir desbalance, redondeo, multimoneda, cierre concurrente, reversa y mapeo faltante. No atribuir estas pruebas a una skill escrita ni a un módulo aún planned.

Entregar matriz de ownership y APIs afectadas, reglas confirmadas/pendientes, evidencia por ambiente y riesgos residuales. Consultar negocio/técnico Contabilidad más Arquitectura, Datos/Custodio DB, API, Seguridad, Sinergia y QA; UX/manuales cuando cambie experiencia. Las fichas orientan la revisión y no sustituyen pruebas ni autorizan despliegues.

## Contabilidad opcional por tenant

Consultar `docs/arquitectura/contabilidad_opcional_y_capacidades.md`. Organización y operación funcionan sin Accounting; un catálogo mostrado en Administración no habilita Contabilidad. Separar catálogo básico de Centros de costos, análisis de Costos y libro contable. No imponer cuentas/periodos/mapeos a operaciones de un tenant sin Accounting ni crear libros al dar de alta Sociedades.

Exigir runtime implementado, entitlement/activación efectiva, permiso y alcance en API y procesos automáticos. Apagado: sin nuevos efectos contables, sin dependencia síncrona desde operación, datos históricos conservados sin conceder acceso implícito. Activación con configuración y fecha de inicio; historia, saldos iniciales y replay requieren alcance explícito. Desactivación/reactivación deben cubrir jobs pendientes, concurrencia e idempotencia. Probar también Accounting apagado, no sólo el escenario con todos los módulos activos. La política condicional está confirmada en CHG-296; respetar la autorización puntual implementada en CONT-05 y concretar cada consumidor antes de exigirla en operación.

Política confirmada CHG-296: catálogo básico disponible desde Administración sin activar analítica/Accounting; Centro de costos obligatorio sólo en flujos de imputación habilitados. Consultar `docs/arquitectura/matriz_capacidades_organizacionales.md`. `capabilities.available` de sesión expresa disponibilidad, nunca autorización de una acción ni configuración lista. No habilitar capacidades planned por flags, roles o permisos.

## Catálogo básico implementado CHG-297

Consultar `docs/arquitectura/cont_05_catalogo_centros.md`. Sólo costing.cost_center.read/create/update/status usan disponibilidad Admin; nunca reclasificar todos los permisos Costing ni activar Accounting. Costing conserva tablas/auditoría; Admin asigna códigos por endpoint dedicado. Disponibilidad requiere runtime habilitado en ambos servicios, permiso y scope efectivo; revalidar elegibilidad en cada futuro consumidor. No afirmar separación de maestros/documentos ni atomicidad distribuida a partir del catálogo.

## Custodia del seguimiento por submódulo

El agente técnico de Contabilidad asume la función de Custodio de preparación e integración contable; negocio contable valida reglas y criterios, sin reemplazar a los dueños operativos. Para seguimiento o reanudación, leer [CONTROL_CONTABLE.md](../../../docs/contexto/CONTROL_CONTABLE.md) desde la raíz del repositorio (ruta canónica: `docs/contexto/CONTROL_CONTABLE.md`). Es el detalle enlazado desde PENDIENTES; ESTADO_ACTUAL sigue siendo autoridad por ambiente y TRAZABILIDAD conserva historia.

Antes de proponer trabajo, contrastar la fila con código/contratos/pruebas y separar: maestro/asignación, consumidor operativo, política monetaria, datos reales y aceptación/despliegue. Conservar lo implementado; registrar una adaptación monetaria como tal y no reabrir un ciclo completo. No usar una nota antigua ni una tabla de seguimiento como prueba suficiente de runtime.

Al cambiar el estado, mantener en la fila ID/corte CONT, dueño, capacidad comprobada, brecha concreta, dependencia, criterio de cierre, fuentes y ambiente/evidencia; actualizar enlaces/resumen en PENDIENTES/ESTADO y CHG cuando corresponda. Registrar incertidumbre o discrepancia sin inventar una decisión. Sólo cerrar con evidencia del delta; pruebas omitidas, APIs simuladas y UAT son categorías distintas. El control documental no autoriza implementación, backfill, activación contable ni release.

CHG-309: costos/tarifas de materiales, máquinas y mano de obra en moneda base de Sociedad; documento en otra moneda conserva original, tasa explícita y convertido. Decisión resuelta, aplicación transversal pendiente según matriz; historia sin moneda confirmada no se reinterpreta.
