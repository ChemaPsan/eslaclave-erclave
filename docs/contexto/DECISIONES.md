# Decisiones vigentes de ERClave

## CC-21 - costo estimado de cotizaciones - 2026-10-14

El usuario confirmo que una cotizacion puede aprobarse si falta costo confirmado en moneda base de Sociedad o tasa explicita hacia la moneda documental. En ese caso costo y margen estimados quedan nulos, nunca cero supuesto ni importe de moneda desconocida. Cuando existen, Sales conserva origen, tasa y convertido por partida y congela el resultado al aprobar; historia no se reinterpreta. [Revision y criterio](../arquitectura/cont_08_costo_estimado_cotizaciones.md).

## CC-18 - folios de movimientos internos - 2026-10-14

El usuario confirmo que, cuando `inventory.movement` este en modo manual, los movimientos automaticos sin formulario reciben un codigo estable derivado del documento y la operacion de origen. La autoridad de Admin valida y conserva ese codigo con clave idempotente; Inventario mantiene unicidad por tenant. Un movimiento manual capturado por una persona exige el codigo en el formulario. El modo administrado usa el siguiente numero de Admin. Los folios existentes no se renumeran.

## CC-17 - momento del snapshot - 2026-10-14

El usuario confirmo congelar plantilla e identidad al aprobar la cotizacion y al liberar la orden de produccion. Antes de aprobar, la cotizacion consulta la presentacion efectiva vigente; despues usa exclusivamente el snapshot del documento. La orden de produccion nace liberada y conserva el snapshot en su creacion. Los documentos anteriores sin snapshot no se reinterpretan con datos actuales. Administracion resuelve la jerarquia Corporativo > Sociedad > Division y la identidad del Emisor; cada dueno persiste su documento.

## Alcance y precedencia · conciliación 2026-10-07

Este documento conserva reglas vigentes y su justificación; [ESTADO_ACTUAL](ESTADO_ACTUAL.md) conserva implementación/ambiente y [PENDIENTES](PENDIENTES.md) las brechas. Una decisión no prueba runtime. El [snapshot previo a CHG-311](historico/DECISIONES_PRE_CHG311.md) conserva las formulaciones históricas, incluidas las sustituidas; [TRAZABILIDAD](../../TRAZABILIDAD.md) conserva evidencia de cada corte.

## Organización, capacidades y contabilidad

| Decisión vigente | Justificación y procedencia |
|---|---|
| Emisor 1:N Sociedad; cada Sociedad tiene un Emisor; División pertenece a Sociedad; centro pertenece a División; libros futuros por Sociedad. | Confirmación CHG-289; sustituye propuesta muchos-a-muchos. [CONT-01](../arquitectura/cont_01_estructura_organizacional.md). |
| Costos/tarifas de materiales, máquinas y mano de obra en moneda base de Sociedad; documento en otra moneda conserva original, tipo explícito y convertido; misma moneda = 1. | CHG-307 y confirmación transversal CHG-309. No volver a preguntar; no interpretar ni convertir historia sin moneda confirmada. Implementación parcial según CONTROL_CONTABLE. |
| Centro obligatorio sólo por flujo de imputación habilitado. Catálogo básico desde Admin sin activar analítica/Accounting. | CHG-296 sustituye obligatoriedad general de CHG-289 y la duda abierta CHG-294. Costing es dueño técnico; Admin orquesta por contrato. [Capacidades](../arquitectura/matriz_capacidades_organizacionales.md). |
| Organización y operación independientes de Accounting; analítica y libro se activan por separado. | CHG-294/296: no bloquear operación por módulo apagado; en fases futuras definir inicio, desactivación/reactivación, jobs e historia sin replay automático. [Fronteras](../arquitectura/contabilidad_opcional_y_capacidades.md). |
| Condiciones comerciales explícitas por División, sin herencia ni copia/restauración automática desde maestro. | CHG-302, opción 2 confirmada. Moneda/pago y crédito cliente o plazo proveedor; modificar ficha general no altera condiciones existentes. No sustituye herencia de plantillas Admin. [Contrato](../arquitectura/cont_07_commercial_condiciones.md). |
| Maestros compartidos con asignaciones por División; recursos físicos con División propia; usuarios con identidad corporativa y scope. | CHG-287 y cortes CONT-07. Evita duplicar maestros; cada dueño valida elegibilidad. [Plan CONT](../arquitectura/plan_preparacion_contabilidad.md). |
| Dimensión documental fija y snapshot de condiciones; refresco explícito permitido sólo donde el contrato lo habilita. | CHG-303/304/305. Cotización/pedido/servicio conservan historia; no recalcular documentos por cambio de maestro. Los bloqueos temporales de cortes antiguos se consultan en estado/control actuales. |

Admin es dueño de estructura normalizada; JSON es proyección de compatibilidad (CONT-02). Los comandos nuevos y adaptadores comparten reglas, locks, auditoría e idempotencia; permisos exactos según [CONT-02](../arquitectura/cont_02_administracion_organizacional.md). El scope v2 usa wildcard explícito para acceso total heredado, listas vacías deniegan y grants restringidos no crecen al crear Divisiones. La preferencia de División activa nunca autoriza ni concede bypass Owner; `admin.user.update` gobierna cambios de alcance. Reinvitar, onboarding o seed no lo reemplazan.

Migrar requiere origen/destino revisados, preview/hash, equivalencias y auditoría; no fusionar RFC, renumerar códigos ni asignar huérfanos silenciosamente. Preservar IDs/datos fiscales incompletos sin declararlos listos para CFDI. Los códigos `*-MIG-*` son exclusivamente migratorios. Expandir → migrar → exigir → retirar compatibilidad; el downgrade 0038 no procede con autoridad/datos fiscales nuevos. La estructura/mapeo real sigue pendiente y no se infiere del tenant.

La custodia del seguimiento corresponde al agente técnico contable con negocio y dueños de módulos: [CONTROL_CONTABLE](CONTROL_CONTABLE.md). Tener fichas/contratos no demuestra runtime. La continuación Local no concede promoción QA ni activación contable; CHG-291 sustituyó la preparación remota por Local.

## Ownership, contratos y autorización

- Cada servicio escribe sólo su schema; sin FKs entre schemas. El frontend consume HTTP mediante `frontend/api/`. Contratos, schemas, consumidores y pruebas cambian juntos; OpenAPI futuro usa `x-implementation-status: planned`.
- Firebase identifica; Admin resuelve tenant, membresías, permisos y entitlements. `X-Tenant-Id`, preferencia del navegador, rol Owner o control oculto no conceden autoridad.
- Permisos de lectura, alta, edición y transición son independientes. La acción exacta se autoriza antes de revelar precondiciones. Roles del tenant son configurables; no ampliar permisos retirados automáticamente.
- Manifiestos declaran `implementationStatus` y permisos puntuales con puntos. En implementados, enumeran capacidades del namespace dueño publicadas por OpenAPI; no permisos cruzados ni planned. Los planeados mantienen permisos vacíos.
- Integraciones consumen proyecciones mínimas: recepción Inventory no abre órdenes/productos completos, usa candidatos de terminado. Referencias crecientes requieren búsqueda acotada/identidad estable; nunca descargar todo para filtrar en navegador.
- Toda consulta restringe `tenant_id`. Operaciones distribuidas usan reclamo durable, claves estables y reconciliación; una llamada HTTP seguida de commit local no es atomicidad. No repetir efectos confirmados.

Fuentes normativas: [ownership](../arquitectura/ownership_datos_mvp.md), [APIs](../arquitectura/apis_mvp.md), [autorización operativa](../arquitectura/matriz_autorizacion_operativa.md) y [selección escalable](../arquitectura/seleccion_escalable_documentos.md).

## Catálogos, formularios y datos

Admin es autoridad de unidades de medida, monedas, condiciones de pago y folios. Cada dueño conserva unicidad/validación del documento; ID técnico no sustituye folio visible. Reserva de código atómica e idempotente, modo manual/managed según contrato. No inventar conversiones de empaque ni referencias.

Estados/tipos/prioridades/políticas de contrato permanecen enums cerrados. Catálogo implementado exige código válido del dueño; valores históricos inactivos se muestran sin reemplazo y altas requieren activos. PATCH puede conservar un valor histórico omitiéndolo. Purchasing expone su proyección de monedas/pago Admin con permisos comerciales, sin exigir permiso administrativo al comprador ni consumir Sales.

Cada campo debe tener propósito de tarea, origen, obligatoriedad contextual y contrato alta/edición/lectura; considerar derivarlo o posponerlo antes de exigir captura. Categoría jerárquica y semántica de responsable/área se deciden con negocio. Catálogos fiscales requieren autoridad/vigencia y flujo fiscal, no listas parciales. Skills `erclave-form-contract` y `erclave-form-feedback`; [piloto](../auditorias/piloto_contrato_formularios_2026-09-20.md).

## Producción, RH e Inventarios

RH es dueño de áreas/puestos/trabajadores. Un trabajador tiene puesto vigente; Production exige trabajador/puesto/área activos y puesto que interviene en producción. Nuevos puestos no adquieren esa bandera por defecto. Producción consume RH, nunca escribe su schema.

La receta valida identidad/elegibilidad de producto, unidad, materiales, puestos, máquinas/áreas y proyecta cantidades/costo; no valida disponibilidad para fecha. Maquinaria en mantenimiento puede formar parte de receta, pero aporta cero capacidad a la orden; inactiva/inexistente no puede agregarse/aprobarse. Área recomendada no se infiere comparando nombres. La orden es la autoridad para existencias, capacidad y compromisos concurrentes.

La receta sugiere duración; orden decide inicio/días/fin. Minutos laborales/máquina se distribuyen por días productivos, materiales se reservan una vez y fecha requerida no precede fin. Calendario base lunes-viernes; turnos/festivos/ausencias son futuros. Bloqueo por recurso/fecha protege liberación. Etapas finalizadas/omitidas son terminales; cierre exige transición explícita.

Almacén confirma entrega física de materiales desde Movimientos antes de iniciar; liberar reserva y no consume, iniciar/reanudar revalida recursos/salida y no repite consumo. Sin materiales no se exige entrega. Cancelar conserva salidas ya emitidas; entrega parcial incierta bloquea cancelación hasta conciliar. Nuevas reservas productivas/refacciones sin vencimiento no caducan a 24 horas por defecto; no reactivar históricas.

Inventory es autoridad de movimientos inmutables, reservas, saldos/Kardex y valuación. Corrección mediante reversa o ajuste auditable. Disponible = máximo de físico menos reservado y cero; saldos sin movimientos pueden ser cero con almacén sugerido, nunca inventar existencias. Costos operativos requieren fuente trazable; costo estándar sigue estimado. Unidad base queda fija tras primer movimiento; inactivos no permiten movimientos/reservas y máximo no puede ser menor al mínimo.

Producción/Mantenimiento solicitan sobrantes de órdenes terminadas/canceladas; Almacén confirma y dueño registra ajuste de costo conservando salida original. Tránsito requiere recepción destino, permite parcial/retorno confirmado origen. No confundir sobrantes con merma ni devolución comercial.

Para servicios ejecutados con receta en Production, evidencia de recepción/inicio y cierre es obligatoria; texto, adjuntos, límites/retención y autorización según [contrato de evidencia](../auditorias/evidencia_servicios_2026-09-13.md). Esta evidencia histórica define el corte; estado de despliegue sólo en ESTADO_ACTUAL. Margen esperado representa utilidad sobre costo, finito y no negativo, sin tope 100 (CHG-273).

## Ventas, Compras y Mantenimiento

Sales conserva clientes/cotizaciones/pedidos/servicios/entregas y snapshots; requiere autoridades RH/Production efectivas. Alta de cliente exige contacto/responsable; perfil fiscal opcional con campos obligatorios conjuntos al iniciarse. Cotización usa referencias activas/unidad base, backend calcula importes. Sólo borrador editable; pedido desde cotización aprobada una vez.

Lecturas comerciales sobreviven a fallo de catálogos de mutación. Producto Inventory debe estar mapeado por Production: igual unidad no prueba identidad. Cada servicio de pedido genera una orden propia Sales, con planeación, responsable, tiempos, costos, evidencia y aceptación; no es Entrega física ni movimiento Inventory. CHG-314 adapta moneda sin alterar ese ciclo. Costo real productivo se concilia explícitamente desde evidencia autoritativa en CC-12 CHG-315; callback automático no es requisito y el costo no se inventa por snapshot.

Compras aprueba requisición, crea/emite orden y recibe mediante comandos independientes. Requisición del corte actual se convierte completa, líneas coinciden exactamente y OC agrega precio; adjudicación parcial entre proveedores es futura. Bienes requieren Inventory; servicios lo prohíben y permiten Compras sin Inventory. Compras prepara recepción, Almacén confirma bienes y solicitante original acepta servicios (comprador si directa). Claims/locks y claves por línea permiten recuperar faltantes sin repetir confirmados.

Maintenance correctivo es dueño de orden/técnicos/tiempos/solicitudes; RH de elegibilidad, Production de máquina/hold e Inventory de material/costo. Objetivo puede ser máquina o descripción/ubicación libre; artículo no se convierte en activo. Una falla bloqueante por máquina; detiene/pausa Production. Resolver libera máquina pero no reanuda orden. Solicitar refacción reserva; Almacén confirma solicitud completa y salida, resolver no consume. Rechazo audita motivo con estado cancelado; no rechazar entrega emitida/en conciliación. Reintento conserva claves y partidas.

Fuentes: [Producción](../../modulos/01_produccion.md), [Inventory](../../modulos/02_almacenes_inventarios.md), [Compras](../../modulos/03_compras_abastecimiento.md), [Ventas](../../modulos/04_ventas_clientes.md), [RH](../../modulos/10_recursos_humanos.md), [Mantenimiento](../../modulos/11_mantenimiento.md).

## Interfaz y evidencia

Container queries responden al ancho real de panel/modales; viewport se reserva al shell. Tablas declaran estrategia compacta, targets accesibles, ES/EN, teclado/zoom y datos legibles. El riel vertical compartido no cambia globalmente por corregir una pantalla. Solicitudes en Movimientos comienzan plegadas y su expansión es temporal; no sumar páginas como totales. [Responsive](../arquitectura/estandar_responsive_transversal.md).

`error.code` resuelve copy ES/EN, nunca diagnóstico `error.message`. Rutas estructuradas apuntan al control realmente serializado; campos desconocidos/inmutables usan resumen seguro. Conservar captura y restaurar estado rechazado, sin conservar contraseñas. Severidad distingue éxito, bloqueo, conciliación y técnico; correlación para soporte. [Feedback](../arquitectura/feedback_operativo_y_errores.md).

Una raíz operativa muestra reportes de sólo lectura; Admin es centro de configuración. Reportes cruzados pertenecen a Reporting futuro. Paginación visual de 25 no sustituye cursor contractual/búsqueda server-side. Smoke parcial y número de formularios cableados no son aceptación funcional. Usar `erclave-qa-evidence` y registrar ambiente/SHA/rol/pasos/evidencia.

## Ambientes, verificación y gobierno

Local usa Emulator, PostgreSQL y APIs locales; cualquier recurso QA vuelve la sesión `local conectado a QA` y requiere autorización explícita. `erclave.web.app` es QA; Produccion futura separa dominio/proyecto, RPO 15 minutos/RTO 2 horas. Pruebas/volumen locales se limpian y sólo usan [tenant autorizado](TENANTS.md).

Backend no carga `.env` implícitamente: Local recibe variables de arranque y QA de runtime/pipeline. Fuera de localhost, tenant se resuelve por membresías y vive en memoria; no fallback demo ni tokens persistidos. Admin runtime QA usa autoridad Firebase para gestión de identidades; no concede permisos ERClave.

Usuario aprueba releases/autodeploy después de pruebas locales. No migrar, seed, cargar datos ni desplegar QA/Produccion por inferencia. Usar skill de fronteras y, para release, `erclave-qa-release`, aprobaciones por recurso/gate y [flujo Local→QA](../operaciones/flujo_local_a_qa.md). Las autorizaciones históricas no son instrucciones actuales.

`verify:postgres` exige loopback `5434/erclave_local` y falla ante skips; `verify:local` agrega navegador con Emulator y URLs locales. Registrar pruebas realmente ejecutadas; no reutilizar resultados de otro corte.

El [gobierno_documentacion_viva.md](../arquitectura/gobierno_documentacion_viva.md) define fuentes vivas, evidencia histórica y planned; aplicar matriz y `npm.cmd run validate:documentation`. Estado mutable reside aquí únicamente por referencia a ESTADO_ACTUAL; decisiones nuevas o sustituidas quedan trazadas sin reescribir la historia.
