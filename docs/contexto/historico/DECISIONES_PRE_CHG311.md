# Archivo histórico de DECISIONES.md · corte previo a CHG-311

> **Evidencia histórica, no instrucciones vigentes.** Conserva las notas acumuladas hasta CHG-310, archivadas el 2026-10-07. Las afirmaciones de estado, pendientes y autorizaciones corresponden a sus fechas y pueden estar sustituidas. Volver a la [fuente viva](../DECISIONES.md) antes de planear o ejecutar. El cuerpo original se conserva; únicamente los enlaces relativos se ajustan a esta ubicación.

# Decisiones vigentes de ERClave

## CHG-309 · Decisión transversal confirmada · 2026-10-07

El usuario confirmó: «sí, en la moneda base de la Sociedad; esto aplica para todo». Regla transversal para costos y tarifas de toda la operación, incluidos materiales, máquinas y mano de obra. Cuando un documento use otra moneda, conservar original y convertido con tipo de cambio explícito. No reinterpretar ni convertir automáticamente historia sin moneda confirmada. Funciona con Accounting apagado. No volver a preguntar esta política; su aplicación completa sigue pendiente de implementación.


## Actualización CHG-307 · 2026-10-05

Confirmado por usuario: existencias en moneda base de Sociedad; tipo explícito entre monedas distintas, original y convertido conservados. Misma moneda=1. No conversión automática ni interpretación retroactiva. Implementado para stock en CHG-307, no para fabricación/otros flujos. Ver docs/arquitectura/cont_08_stock_contexto.md. Las notas de cortes anteriores son históricas.


**Política vigente:** costo en moneda de Sociedad y tipo explícito, implementada para stock en CHG-307. Mapeo real pendiente; no reinterpretar historia.

## Actualización CHG-306 · 2026-10-05

Solicitud vigente: terminar separación operativa antes de QA. No activar Accounting. Política monetaria confirmada: moneda base de Sociedad y tipo de cambio explícito, conservando importes. Estructura/mapeo reales aún sin respuesta.


## Actualización CHG-305 · 2026-10-05

Se conservan condiciones explícitas por División y Accounting opcional. El corte habilita servicios bajo contexto fijo; importa costos explícitos en moneda del pedido. Detener mediante wait/cancel no exige recursos activos; avanzar/capturar sí. Sin nueva política fiscal/contable ni mapeo automático.


## Actualización CHG-304 · 2026-10-05

Se mantiene decisión explícita sin herencia: pedido copia condiciones de cotización aprobada. Frontera técnica temporal: permitir pedido/consulta/cancelación y rechazar ejecución dimensionada todavía no propagada. No se asigna contexto a datos reales ni se activa Accounting.


## Actualización CHG-303 · 2026-10-05

Se conserva decisión del usuario: condiciones explícitas por División sin herencia. Corte técnico CONT-08: fijar División al asignarla, refresh sólo en borrador y bloquear conversión a pedido hasta soportar contexto. No se decide activación de Accounting ni asignación de datos reales.


## CHG-302 — Condiciones comerciales sin herencia (2026-09-28)

Decisión explícita del usuario: opción 2, condiciones por División. Moneda/pago y crédito del cliente o plazo del proveedor deben guardarse para cada División; sin herencia, copia automática ni restauración desde el maestro. Cambiar la ficha general no modifica condiciones existentes. No aplica esta excepción a la herencia de plantillas Admin. [Contrato vigente](../../arquitectura/cont_07_commercial_condiciones.md). Documentos y control de crédito continúan pendientes de integración propia.

## CHG-296 — disponibilidad de capacidades y política confirmada

El usuario confirma catálogo básico desde Administración sin activar analítica/Accounting, y Centro de costos obligatorio sólo por flujo de imputación habilitado. [Matriz vigente](../../arquitectura/matriz_capacidades_organizacionales.md). Sesión agrega contrato versionado de capacidades en código, con planned apagado aun ante flags/grants; disponibilidad no concede permisos ni prueba configuración lista. Sin cambios de DB, seeds, runtime levantado ni QA/Producción. CONT-04/05/07/08 siguen pendientes; siguiente corte configuración por alcance. No repetir la pregunta de obligatoriedad; estructura y asignación de datos existentes todavía pendientes.


## CHG-294 — Contabilidad opcional y fronteras de activación

Usuario solicita analizar módulos no siempre activos. [Criterio y recomendaciones](../../arquitectura/contabilidad_opcional_y_capacidades.md): organización/operación independientes de Accounting, catálogo básico de centros con dueño Costing y superficie Admin, analítica y contabilidad por activación propia. Skills accounting/module-boundaries y fichas actualizadas. Sin cambios de APIs, runtime, datos ni entitlements; CHG-293 sigue siendo el último corte funcional.

Antes de CONT-05/07/08 concretar autorización de la capacidad básica de centros y política de obligatoriedad cuando no se usan costos/contabilidad. No reinterpretar silenciosamente la obligación anterior ni bloquear operación con un módulo apagado. En futuros eventos/libros definir fecha de inicio, desactivación, jobs e historia sin replay automático. QA/Producción sin cambios.


## CHG-293 — ejecutar separación y fortalecer guardianes

- El usuario solicita aplicar el plan de Sociedad/División/Centro de costos y reforzar agentes/skills contables, con auditoría de cobertura del resto de módulos. Continuación Local autorizada; no implica promoción QA ni implementación inmediata de Accounting.
- CONT-03 conserva la semántica heredada de acceso total mediante wildcard explícito. En v2 las listas vacías deniegan Divisiones; nuevas invitaciones parten vacías. Las concesiones restringidas son IDs explícitos y no crecen por crear una División.
- El selector de contexto combina Sociedad/División en una etiqueta; la API deriva Sociedad y Emisor. La preferencia se aísla por tenant/usuario y nunca autoriza. El permiso existente `admin.user.update` gobierna cambios de alcance; no se agregan permisos ni bypass por Owner.
- Conversión de metadata mediante preview/hash, equivalencias y auditoría; sin cambio DDL. Reinvitar, repetir onboarding o seed no reemplaza el alcance. La migración operativa posterior requiere estructura/asignación explícita del usuario, solicitada y aún sin respuesta.
- Contabilidad mantiene pareja negocio/técnica senior y guardianes compartidos, con skills especializadas en contabilidad y fronteras. Tener fichas no certifica runtime ni pruebas. Mantenimiento pasa a ser exigido por el validador; cada dominio debe tener ambos roles en su propia sección.

## CHG-292 — autoridad y experiencia de CONT-02

- Admin conserva ownership de la estructura; activación revisada por tenant, snapshot anterior archivado si cambió el origen y verificación de proyección antes de cada comando. No se sobrescribe un destino alterado.
- Los comandos normalizados y los adaptadores deprecados comparten reglas, lock, auditoría e idempotencia. JSON es proyección de compatibilidad. El permiso amplio `admin.setting.update` de los adaptadores se mantiene documentado durante la transición; las rutas nuevas exigen permisos puntuales.
- Emisor/Sociedad/División tienen alta/edición/lectura/estado separados. Moneda activa de Admin, MXN inicial. Datos fiscales opcionales describen preparación, no readiness CFDI. Sin libros ni tipos de cambio en este corte.
- Se protege el borrado físico de tenants con organización/historial. Revisión 0038 sólo permite downgrade sin autoridad ni nuevos datos fiscales; después requiere corrección hacia adelante.
- Local es el único ambiente autorizado para este trabajo. Doce permisos nuevos y grants sólo al Owner del tenant demo autorizado; sin seeds globales sobre roles de otros tenants. Detalle: [CONT-02](../../arquitectura/cont_02_administracion_organizacional.md).

## CHG-291 — corrección explícita del ambiente

El usuario sustituyó su petición de levantar QA por levantar Local. Se utilizó el arranque canónico sobre el workspace original, no el candidato aislado de QA. El candidato local se conserva sin publicar; la corrección elimina la promoción como siguiente acción. La operación Local comprende los seeds canónicos del único tenant demo autorizado y Firebase Emulator, sin recursos QA/Producción.

## CHG-290 — separar el candidato solicitado

La promoción CONT-01 se prepara sobre main e57237f en worktree aislado, preservando y excluyendo los cambios funcionales previos. No se modifica el pipeline ni se ejecuta su configuración global por inferencia: revisar la limitación y autorizaciones del plan docs/operaciones/release_qa_20260923_cont01.md. Las decisiones funcionales CHG-289 siguen vigentes.

## CHG-289 — respuesta del usuario y CONT-01

- Emisor 1:N Sociedad; cada Sociedad tiene un solo Emisor. Se descarta el modelo muchos-a-muchos propuesto previamente.
- Los libros pertenecen a Sociedad. Su moneda base es configurable, inicialmente MXN; las transacciones permiten otra moneda con tipo capturado y conservación de importes originales/base.
- Centro de costos obligatorio, pertenece a División y por derivación a Sociedad. La alta estará claramente en Administración. Al crear un artículo/asignación operativa se selecciona un centro de la División activa del usuario; backend valida estado, tenant y alcance. Costing conserva el catálogo técnico y Admin lo orquesta por contrato.
- CONT-01 usa expansión: tablas nuevas y snapshot preparado, sin cambiar `organization.profile` ni las APIs actuales. El switch y reconciliación de cambios posteriores corresponden a CONT-02.
- La importación requiere hashes revisados; conserva campos/códigos/estados, usa equivalencias deterministas y rechaza duplicados fiscales o referencias huérfanas sin resolución explícita. Un reintento valida origen y destino; no sobrescribe diferencias. Códigos `*-MIG-*` son una regla exclusiva de migración, no folios normales.
- Moneda MXN se valida contra el catálogo Admin activo. Los datos fiscales heredados incompletos se conservan como tales; no se inventan ni se interpretan como listos para facturar.
- No hay cambios de API, permisos o frontend en este corte. CONT-00 queda cerrado; [CONT-01](../../arquitectura/cont_01_estructura_organizacional.md) documenta alcance y límites.

Las notas CHG-287/288 que siguen describen la preparación previa a la respuesta. Su condición de decisiones pendientes queda sustituida por CHG-289.

## CHG-288 — ejecución y diagnóstico sin inferir decisiones funcionales

- La instrucción del usuario de aplicar CHG-287 inicia la ejecución Local de sus cortes; no es necesario volver a solicitar permiso genérico para ese trabajo.
- Se separa calidad de datos de aprobación funcional: un preflight correcto no cierra CONT-00 ni habilita por sí solo una migración.
- Para diagnosticar el origen se usa el JSON original, sin la normalización que descarta filas malformadas. No fusionar RFC, renumerar códigos ni asignar sucursales huérfanas silenciosamente.
- Las propuestas Sociedad–Emisor/libro, Centro de costos y moneda/tipo de cambio/redondeo están concretadas en [CONT-00](../../arquitectura/cont_00_decisiones_y_preflight.md), pendientes de respuesta. No son reglas implementadas.
- El primer cambio de persistencia sigue siendo CONT-01, posterior al cierre funcional; JSON conserva autoridad operativa hasta definir el switch compatible.

## CHG-287 — estrategia de ejecución para preparación contable

- El programa se ejecuta mediante cortes verticales `CONT-00` a `CONT-18`; cada implementación futura recibe su propio CHG y no hereda estado de terminado por aparecer en el plan.
- Los cambios persistentes siguen expandir → migrar → exigir → retirar compatibilidad. El JSON `organization.profile` no se elimina en el primer despliegue.
- Maestros compartidos usan asignaciones por División; recursos físicos pertenecen a una División; usuarios conservan identidad corporativa y scope.
- La definición de Sociedad, el dueño del libro, la regla de Centro de costos y los momentos contables permanecen como gates de `CONT-00`, no como reglas implementadas.
- Plan vigente: [estructura organizacional, costos y contabilidad](../../arquitectura/plan_preparacion_contabilidad.md).

## CHG-285 — catálogo configurable sólo cuando existe autoridad funcional

- Estados, tipos, prioridades y políticas que forman parte del contrato permanecen como enums cerrados.
- Entidades crecientes y referencias compartidas provienen de su servicio dueño.
- Un código histórico inactivo se muestra sin sustituirse; PATCH puede conservarlo omitiendo el campo y las altas exigen una opción activa.
- Régimen fiscal, país y uso CFDI se diseñarán con el flujo fiscal completo, su vigencia y autoridad. No se completan con listas parciales por apariencia.

## CHG-284 — Purchasing expone sus referencias comerciales

- El frontend de Compras consume referencias desde Purchasing, no directamente desde Admin ni desde Sales.
- Admin conserva ownership de `currencies` y `payment_terms`; Purchasing reexpone la proyección mínima necesaria y valida los mismos códigos al guardar.
- Los permisos de negocio de proveedor y orden son consumidores autorizados de lectura/validación del catálogo; no se exige `admin.catalog.read` al comprador.
- Un fallo de referencias impide abrir la captura de proveedor, conserva operativa la lista y evita ofrecer valores inventados o listas fijas desactualizadas.

## Coherencia de formularios y evidencia CHG-283

Toda propuesta de campo operativo identifica la tarea o decisión que resuelve, su origen, obligatoriedad contextual y contrato de alta, edición y lectura. Antes de añadir captura se considera si el dato puede derivarse, heredarse de un catálogo o completarse después. Los códigos de catálogos implementados proceden del servicio dueño y se revalidan en backend; las opciones fijas no sustituyen un catálogo administrable vigente. Una observación de código o smoke parcial no se registra como aceptación funcional. Guía de ejecución: `$erclave-form-contract` y `$erclave-qa-evidence`. Hallazgos piloto y decisiones pendientes: [auditoría](../../auditorias/piloto_contrato_formularios_2026-09-20.md).

Las decisiones CHG históricas que siguen conservan su contexto original. Para capacidades actualmente desplegadas y pendientes usar `ESTADO_ACTUAL.md` y `PENDIENTES.md`.

## Evidencia de servicios CHG-274 — solo Local

CHG-274 implementa evidencia de recepción/inicio y cierre solo en órdenes de Producción cuya receta proviene de un servicio. Texto obligatorio; hasta3 adjuntos opcionales por momento. Fotos JPEG/PNG/WebP/HEIC/HEIF/BMP/TIFF de hasta5MiB se reorientan y convierten en WebP sin metadatos, lado máximo1600px y archivo <=300KiB. PDF/TXT/DOCX/XLSX hasta2MiB; sin archivos ejecutables o macros. Todos los adjuntos vencen a365 días desde carga; texto/orden/metadatos permanecen. Backend impide esperar recursos/iniciar sin recepción y completar100% total/enviar a validación/terminar sin cierre. Productos conservan su recorrido. Local head `20260913_0036`; QA `20260908_0034` sin cambios. Detalle: `docs/auditorias/evidencia_servicios_2026-09-13.md`.


## Margen esperado sin tope CHG-273

CHG-273 permite `expected_margin` mayor a 100 en productos y servicios: porcentaje de utilidad esperada sobre costo, finito y no negativo, sin tope porcentual de negocio. Se retira max HTML y le=100 Pydantic; PostgreSQL usa NUMERIC sin precisión fija y constraint no negativo/finito. Tarjeta muestra el porcentaje guardado sin sustituirlo por margen sobre venta. Ayuda ES/EN. Migración Local `20260913_0035` aplicada; QA conserva `20260908_0034` y release b63cdad. Valores existentes conservados; rollback bloquea datos que no caben en el esquema anterior. Detalle: `docs/auditorias/margen_esperado_2026-09-13.md`.


## Autoridad de salida antes del inicio CHG-264

CHG-264 implementa solo en Local la salida completa de materiales desde Movimientos antes de iniciar `in_progress`. Liberar conserva reservas; Almacen confirma entrega con `inventory.movement.create`; Produccion valida cantidades/costos confirmados al iniciar y no consume al iniciar/reanudar. Aplica a productos y servicios con receta, sin agregar materiales a las ordenes comerciales de servicio de Sales. Detalle y matriz API: `docs/auditorias/materiales_produccion_movimientos_2026-09-08.md`.

La orden permanece Liberada/En espera de recursos despues de entregar; iniciar sigue siendo un comando propio de Produccion. Sin materiales no exige entrega. Cancelar antes de entregar libera reservas; despues de entregar conserva los movimientos. Una entrega iniciada e incompleta bloquea cancelacion hasta conciliar. El lock por tenant/orden cubre entrega y cambios de estado durante HTTP; la intencion se persiste antes de consumir. Reintentos usan la identidad estable por orden/reserva y conservan movimientos confirmados. Nuevas reservas productivas sin fecha explicita no vencen a las 24 horas; no se reactivan reservas historicas.

## Refacciones y entrega fisica Local CHG-263

- Solicitar aparta material; Almacen confirma la entrega completa desde Movimientos y ese es el momento de registrar la salida. Resolver la reparacion no consume.
- La confirmacion combina autorizacion y entrega; no se agrega una aprobacion previa independiente ni una entrega parcial editable. El tecnico asignado es el receptor y queda en la auditoria de la confirmacion.
- Se reutilizan `inventory.movement.read|create` para consulta y registro/rechazo de esta salida interna; los permisos de Mantenimiento no conceden entrega. Inventory valida ademas el origen de la reserva, de modo que esa capacidad no consume/libera reservas de Produccion o Ventas.
- Las nuevas reservas de Mantenimiento sin vencimiento explicito permanecen hasta entrega/cancelacion. No se reactivan reservas historicas vencidas ni se reinterpretan movimientos previos.
- El rechazo usa `cancelled` con motivo auditado; no crea un estado persistente adicional. Solicitudes ya emitidas o con entrega en conciliacion no se rechazan.

## Coherencia frontend/backend

- CHG-262 aplica los contratos existentes a campos inmutables, valores iniciales y ramas condicionales. No se agrega un campo al backend solo para sostener una captura heredada de la maqueta.
- Los permisos de lectura son independientes por recurso y se validan antes de componer consultas; un comando compuesto comprueba todas sus autoridades antes de la primera mutacion.
- Un saldo parcial del navegador no autoriza ni bloquea salidas API; Inventory es la autoridad de existencia y reservas.

## Autorizacion operativa por capacidad

- Cada aprobacion, aceptacion, liberacion, finalizacion, cancelacion o recepcion implementada usa un permiso puntual derivado del contrato.
- El backend resuelve el permiso exacto a partir de la accion solicitada; ocultar el control en frontend no sustituye autorizacion.
- Gerente de Produccion, Almacenista o Tecnico son roles configurables del tenant, no nombres codificados en la politica. Los usuarios heredan capacidades por sus membresias de rol.
- Los permisos genericos retirados no se convierten automaticamente en todas las capacidades nuevas, porque eso ampliaria autoridad sin aprobacion del administrador.
- La matriz vigente vive en `docs/arquitectura/matriz_autorizacion_operativa.md`.
- Una integracion entre modulos recibe una proyeccion minima para su tarea. Desde CHG-237, los permisos de recepcion Inventory no abren ordenes ni productos completos de Produccion; consumen exclusivamente `finished-goods-candidates`.
- La autorizacion exacta se evalua antes de precondiciones que puedan revelar estado interno. OpenAPI y runtime deben coincidir tanto en rutas como en conjuntos de permisos estaticos.

## Arquitectura y ownership

- El frontend consume HTTP exclusivamente mediante `frontend/api/`.
- Cada microservicio escribe solamente su schema y datos propios.
- No se crean FKs entre schemas de servicios distintos.
- Los movimientos de inventario son inmutables: se corrigen con reversa o nuevo ajuste auditable.
- Balances y Kardex son consultas calculadas; no tienen captura directa.
- Los contratos OpenAPI, schemas, consumidores y pruebas cambian en el mismo corte.
- Los OpenAPI deben parsear como YAML y coincidir con cada ruta FastAPI implementada. Una operacion futura lleva `x-implementation-status: planned`; un contrato o manifiesto no convierte por si solo un modulo en real.
- Los manifiestos de microfrontend declaran `implementationStatus` y solo usan permisos puntuales con puntos, nunca alias historicos con `:`.
- En manifiestos `implemented`, `permissions` enumera exhaustivamente las capacidades implementadas del namespace propietario publicadas por operaciones OpenAPI cuyo `x-required-module` corresponde al modulo. No incorpora permisos cruzados ni operaciones `planned`; los manifiestos planeados conservan la lista vacia. `validate-architecture` bloquea faltantes y sobrantes.

## Identidad y autorizacion

- Firebase es proveedor de identidad, no fuente de permisos ni membresias.
- En QA, la cuenta runtime de Admin conserva `roles/firebaseauth.admin` porque Backoffice crea, actualiza y elimina identidades Firebase durante el ciclo de tenants. El rol no concede permisos ERClave ni sustituye `session/context`; no se entrega a los otros servicios ni a operadores humanos.
- ERClave autoriza mediante `admin-service /v1/session/context`.
- `X-Tenant-Id` selecciona contexto, pero nunca concede autoridad.
- Las APIs aplican permisos y aislamiento aunque el frontend o sus filtros sean manipulados.

## Datos y escalamiento

- PostgreSQL es la fuente transaccional del MVP.
- Toda consulta operativa multi-tenant comienza restringida por `tenant_id`.
- Las listas grandes usan filtros server-side, limites y paginacion estable; no se descargan colecciones completas para filtrarlas en el navegador.
- Categoria de articulos sigue siendo texto libre. Un catalogo jerarquico requiere una decision funcional y migracion posteriores.
- Reservas, bloqueos, transito y cuarentena no deben mostrarse como reales hasta que exista su modelo operativo.
- Las areas laborales son catalogos independientes con ID estable. Los puestos solo pueden vincularse a un `labor_area_id` existente del mismo tenant; nunca crean areas desde texto libre.
- Cada trabajador tiene un unico puesto vigente y expediente RH. Los responsables operativos referencian trabajadores activos; Produccion exige ademas que su puesto y area esten activos y que el puesto intervenga en produccion.
- Administracion es fuente de verdad tenant-safe de unidades de medida. Produccion e Inventarios guardan el codigo estable y validan que siga activo; las altas/ediciones del catalogo son idempotentes, correlacionadas y auditadas.
- Administracion es tambien la autoridad tenant-safe de folios de negocio. Cada tipo documental define prefijo, separador, siguiente consecutivo, longitud y modo `managed` o `manual`; reservar un folio es atomico e idempotente. Los servicios propietarios conservan su validacion y unicidad, y nunca usan el ID tecnico como folio visible.
- Crear/editar areas y crear/editar puestos usan permisos distintos para que los roles de usuario deleguen cada responsabilidad por separado.
- Areas y puestos pertenecen a `hr-service`, usan permisos `hr.area.*` y `hr.position.*` y requieren el entitlement `hr` activo. Produccion y Costos solo consumen el contrato; no escriben el esquema `hr`.
- Maquinaria pertenece a Produccion, pero su area se selecciona exclusivamente entre areas activas de RH. El formulario de Maquinaria no crea areas ni acepta nombres libres; conserva `area_name` como snapshot compatible con el contrato vigente.
- Produccion conserva snapshots de los datos laborales utilizados por una receta para que cambios posteriores de costo, capacidad o estatus no alteren historia aprobada.
- El editor de permisos no usa plantillas ni presets: cada rol conserva personalizacion individual. La UI ofrece busqueda, filtros y selecciones masivas explicitas, pero nunca concede permisos por nombre de rol.
- Los codigos de permiso permanecen como contrato; la UI muestra etiquetas/descripciones ES/EN versionadas. Solo permisos clasificados `tenant` y marcados asignables pueden concederse a roles humanos.
- Editar permisos usa draft, diff, guardado unico, revision optimista e idempotencia. Los filtros no limitan el payload ni eliminan asignaciones ocultas; scopes existentes se preservan.
- Un articulo solo es candidato de receta cuando esta activo y tiene `use_in_recipe=true`; la disponibilidad se calcula desde movimientos de todos los almacenes del tenant.
- Una orden de Produccion solo se crea desde una version aprobada vigente. Produccion orquesta, pero Inventarios es autoridad de existencia, reservas, movimientos y valuacion; RH es autoridad de trabajadores, puestos y capacidad laboral; Produccion es autoridad de maquinaria y compromisos de capacidad. El navegador no puede declarar disponibilidad ni costo.
- Liberar una orden reserva materiales por almacen y compromete minutos de mano de obra/maquinaria por fecha. Almacen confirma la entrega desde Movimientos y registra salidas inmutables antes de `in_progress`; iniciar, reanudar o cerrar no consume. Cancelar antes de entregar libera reservas y cancelar despues conserva salidas. El cierre exige materiales entregados y etapas completas; tiempos reales temporales permanecen diferidos. Los comandos externos y locales son idempotentes y los bloqueos se ordenan por recurso para evitar sobreasignacion concurrente.
- En modo API, una receta solo selecciona articulos activos marcados `use_in_recipe`, puestos RH activos con `intervenes_in_production=true` y, como etapas, areas RH activas que tengan al menos uno de esos puestos productivos. La etapa conserva `labor_area_ref_id` y nombre snapshot, sin FK ni escritura cruzada.
- Las fases activas de una receta se numeran en orden consecutivo y sus porcentajes deben sumar exactamente 100. La orden copia numero, area y peso; su avance general es la suma ponderada del avance de cada fase, no un promedio simple.
- El costo manual de un articulo pertenece a Inventory y significa costo por una unidad base del articulo. Las conversiones solo se permiten entre unidades activas, compatibles y con factor estandar inequívoco; Compras sera la autoridad futura para recalcularlo desde recepciones u ordenes de compra.
- CHG-228 preparo Compras y CHG-229 implemento su primer corte supplier-to-receipt, hoy desplegado en Local y QA. Admin conserva unidades, monedas, condiciones, folios y autorizacion. Compras es dueno de proveedor/requisicion/orden/recepcion comercial e Inventory del articulo/almacen/movimiento/saldo. CHG-255 mantiene Inventory como dependencia condicional solo para partidas inventariables; factura, pago, devolucion y contabilidad quedan fuera hasta definir sus owners y contratos.
- Desde CHG-230, todo proveedor nuevo exige perfil fiscal minimo y RFC unico por tenant. Los proveedores heredados incompletos permanecen legibles y solo deben completar el conjunto al editar datos fiscales. El maestro sigue siendo editable; cualquier factura fiscal futura conservara snapshots propios.
- Desde CHG-231, una requisicion de Compras agrupa multiples partidas y consolida cada articulo en una sola linea. La orden conserva precio por partida. Dividir una requisicion entre varios proveedores requiere un corte posterior con saldo adjudicable por linea y no se simula duplicando documentos.
- Desde CHG-232, una orden originada en requisicion debe coincidir exactamente en tipo, articulo, descripcion, cantidad y unidad; solo agrega precio. Requisiciones y ordenes se cancelan con motivo y actor. Cada recepcion reclama saldo bajo bloqueo, conserva una clave Inventory estable por linea y su conciliacion reintenta exclusivamente lineas no completadas.
- CHG-234 implementa Mantenimiento correctivo y CHG-235 endurece su conciliacion; el corte acumulado esta desplegado en Local y QA. RH e Inventory son dependencias duras y Production es integracion opcional. `maintenance-service` es dueno de ordenes, asignaciones, tiempos y solicitudes internas; RH de elegibilidad, Production de maquinas/ordenes y del hold `maintenance_order_ref_id`, e Inventory de refacciones, reservas, movimientos y costos. Resolver nunca reanuda Produccion automaticamente.
- Una orden de Mantenimiento apunta a una maquina de Production o a una descripcion/ubicacion libre de edificio u otro objetivo. Un articulo de Inventory no se convierte en activo. Solo una falla bloqueante puede permanecer activa por maquina.
- Una falla productiva deja la orden en `waiting_resources` si no inicio o la pasa a `paused` si estaba en proceso. Resolver libera la maquina, pero nunca reanuda Produccion automaticamente: el operador debe revalidar y reanudar.
- La primera entrega de Mantenimiento sera correctiva. Preventivos recurrentes, Activos, garantias, anexos y escalamiento automatico a Compras permanecen fuera hasta un corte propio.
- Los estados de orden y etapa son maquinas de estado backend; las etapas terminadas u omitidas son terminales y el cierre de orden requiere una transicion explicita desde validacion.
- Inventario incluye articulos sin movimientos con saldo cero cuando tienen almacen sugerido, sin fabricar movimientos ni existencias.
- El corte certificado de Ventas esta desplegado en Local y QA para Clientes, Cotizaciones, Pedidos y Entregas. CHG-255 agrega Ordenes de servicio solo en Local hasta una promocion posterior. Sales conserva ownership de sus documentos y snapshots; RH, Produccion y Administracion siguen siendo autoridades de responsables, productos/servicios y unidades.
- La activacion de `sales` exige `hr` y `production` efectivos en los dos niveles de gobierno. Las transiciones de entitlements bloquean todas las filas modulares del tenant y no permiten apagar una autoridad mientras Ventas permanezca activa. Onboarding crea entitlements antes de asignar permisos al owner.
- La UI comercial carga documentos y catalogos de mutacion por separado. La indisponibilidad o falta de permisos sobre responsables, productos o unidades no debe ocultar Clientes/Cotizaciones a un usuario de solo lectura.
- Un cliente exige contacto principal y responsable RH activo. El perfil fiscal es opcional, pero razon social, RFC/ID fiscal y correo de facturacion se vuelven obligatorios juntos al iniciarlo.
- Una cotizacion solo usa cliente activo, productos/servicios activos y la unidad base activa. Importes, costo snapshot y margen estimado se calculan en backend.
- El segundo corte Local convierte una cotizacion aprobada una sola vez en Pedido. Sales orquesta referencias a reservas de Inventory o solicitudes de Production sin escribir sus schemas; confirmar Entregas consume parcial o totalmente reservas y calcula costo/margen real. Devoluciones y facturacion permanecen `planned`.
- Monedas y condiciones de pago son catalogos tenant-safe de Admin. Estados comerciales son maquinas de estado y no catalogos editables.
- `document.template` es configuracion unica por tenant para logo/colores de todos los PDF. Local admite el logo como data URL validado; QA/Produccion requeriran object storage.
- Toda operacion de Ventas que produzca efectos en Inventory o Production usa un reclamo local durable antes de la llamada, claves derivadas estables y estado `needs_reconciliation` reanudable; una llamada HTTP seguida de una transaccion local nunca se considera atomicidad.
- Una unidad coincidente no demuestra que un articulo de Inventory corresponde al producto vendido. Production es dueno del mapeo por ID, valida el articulo por API de Inventory y Sales vuelve a validarlo al surtir.
- Un costo solo se etiqueta como real cuando proviene de consumo o captura operativa trazable. Sales conserva `actual_cost_source`; el costo estandar permanece exclusivamente estimado.
- Una partida `service` confirmada en un Pedido genera exactamente una orden de servicio propiedad de Sales. Su planeacion, asignacion, ejecucion, tiempos, costos, evidencia y aceptacion usan permisos puntuales, idempotencia, auditoria y snapshots; no se representan como Entrega ni generan movimientos de Inventory.
- Compras puede operar para un tenant de servicios sin habilitar Inventory. Admin sigue siendo dependencia transversal; Inventory se exige y consulta solo cuando una partida es `inventory_item`. Una partida `service` prohibe articulo y almacen, pero conserva recepcion comercial parcial o total en Compras.

## Ambientes

- Local usa Firebase Emulator, PostgreSQL local y APIs locales; no consume recursos QA por defecto.
- Una ejecucion local que consume cualquier recurso QA se clasifica como `local conectado a QA` y requiere autorizacion explicita.
- `erclave.web.app` permanece como dominio QA; Produccion usara un dominio adquirido y un proyecto GCP separado.
- El primer release incluye Administracion, Backoffice, Produccion, Almacenes/Inventario, Recursos Humanos y Ventas, todos certificados previamente en QA.
- El usuario propietario aprueba directamente releases y autodeploys despues de pruebas locales.
- Produccion tendra RPO de 15 minutos y RTO de 2 horas; su infraestructura no se implementa antes de autorizar la fase productiva.

- Local, QA y Produccion no comparten bases de datos de prueba.
- No se despliega, migra, ejecuta seed ni escribe en QA/Produccion sin autorizacion explicita.
- Las pruebas de volumen y datos dummy se ejecutan solamente en recursos locales aislados y se limpian al terminar.
- `backend/shared/erclave_common/config.py` no carga `.env` automaticamente. Local canonico recibe variables explicitas de `start_local.ps1`; QA/Produccion las reciben del runtime/pipeline. Esto impide que un archivo hibrido cambie silenciosamente la frontera.
- En dominios no locales, el tenant activo se resuelve desde `/v1/session/tenants` y se conserva solo en memoria para enviar `X-Tenant-Id`; no existe fallback al tenant o actor demo.
- `docs/contexto/ESTADO_ACTUAL.md` es la unica fuente de estado operativo mutable. Agentes, skills y documentos modulares deben referenciarlo, no duplicar revisiones o despliegues que envejecen.
- La documentacion viva y los agentes se gobiernan por `docs/arquitectura/gobierno_documentacion_viva.md`. Cada cambio aplica su matriz de actualizacion y `npm.cmd run validate:documentation`; evidencia historica, estado vigente y objetivos `planned` nunca se mezclan.
- Toda liberacion Local→QA usa `$erclave-qa-release`, registra `Agentes consultados` y conserva aprobaciones independientes para build, base/configuracion, servicios, trafico, frontend, IAM y datos.

## Responsive y accesibilidad visual

- Los componentes contenidos en paneles se adaptan mediante CSS Container Queries; los media queries de viewport se reservan para el shell global.
- Cada tabla declara una estrategia compacta: tarjetas con etiquetas, scroll horizontal interno o vista reducida justificada.
- Ningun layout depende de cortar textos traducibles, identificadores, cantidades, errores o acciones esenciales.
- Formularios, flujos, filtros y alertas deben seguir operables cuando sidebar y paneles laterales reduzcan el ancho real del contenido.
- Los breakpoints se eligen donde el contenido se rompe, usando como referencia los estados documentados en `docs/arquitectura/estandar_responsive_transversal.md`.
- QA verifica ancho de contenedor, zoom 200%, teclado, ES/EN y estados carga/vacio/error; probar solo resoluciones de viewport no es suficiente.
- La guia de flujo compartida mantiene el riel vertical izquierdo y su estado comprimido. Las correcciones de una pantalla no pueden modificar globalmente su formato; cualquier excepcion se delimita con una clase especifica.
- El shell muestra una sola identidad principal por pantalla. Los indicadores transversales pertenecen al panel de Alertas operativas y las leyendas internas de API, base de datos, mock, QA o persistencia no se presentan como estados de negocio.
- Modales y tarjetas operativas compuestas son contenedores responsive propios; no pueden depender exclusivamente del ancho del panel padre ni comprimir texto humano para conservar columnas.

Una decision nueva o reemplazada debe registrarse tambien en `TRAZABILIDAD.md` y actualizar las fuentes funcionales correspondientes.

## Feedback operativo y localización de errores

- `error.code` es la fuente estable para resolver copy ES/EN; `error.message` es diagnóstico y no se presenta directamente al usuario.
- Un error de mutación nunca confirma ni conserva visualmente un estado no aceptado. La UI restaura o recarga la proyección autoritativa y explica el siguiente paso.
- La severidad visible distingue éxito, bloqueo funcional, conciliación y fallo técnico; sólo los casos inesperados o inciertos muestran `correlation_id` como referencia de soporte.
- El contrato y la taxonomía completos viven en `docs/arquitectura/feedback_operativo_y_errores.md`.
- Desde CHG-259, toda presentacion de errores del shell usa `frontend/features/error-feedback.js`; `frontend/app.js` no puede leer `error.message` ni `reason.message` para mostrarlo. El validador transversal bloquea regresiones.

## Verificacion y paginacion Local

- La verificacion PostgreSQL completa es un comando explicito y reproducible: `npm run verify:postgres`. Solo admite `erclave_local` en loopback `5434` y convierte cualquier prueba omitida en fallo.
- `npm run verify:local` compone la integracion PostgreSQL estricta con Playwright. El E2E usa Chrome instalado, Firebase Emulator y URLs loopback; una dependencia Local ausente o una base remota detiene el recorrido.
- La primera paginacion transversal es de presentacion: pagina en bloques de 25 los registros que la pantalla ya cargo, sin perder acciones ni filtros. No sustituye la busqueda/paginacion server-side obligatoria para maestros y documentos de alto volumen.

## Continuidad del flujo de Compras

- Aprobar, crear, emitir y recibir permanecen como comandos independientes; la navegacion guiada no los fusiona ni hereda permisos entre ellos.
- La seleccion de requisicion u orden se transporta solo en estado transitorio del frontend. El backend vuelve a validar tenant, estado, lineas, proveedor, saldos y permiso en cada comando.
- Crear una orden consume la requisicion completa del primer corte y la cambia a `converted`; dividir partidas entre proveedores sigue fuera del alcance vigente.

## Planeacion multi-dia de Produccion

- La receta propone `suggested_duration_days`; la orden conserva la decision operativa definitiva con inicio, duracion y fin planeados.
- Mano de obra y maquinaria se miden en minutos diarios, descuentan compromisos activos por recurso/fecha y se asignan secuencialmente sobre dias productivos. Materiales se validan y reservan una sola vez.
- El calendario base del corte Local es lunes-viernes. Turnos, festivos, ausencias y excepciones por mantenimiento requieren un calendario tenant posterior y no se simulan con datos inventados.
- La fecha requerida es un limite de negocio y no puede quedar antes del fin planeado. Crear/liberar conserva el bloqueo transaccional por cada combinacion recurso/fecha.

## Maquinaria de receta frente a disponibilidad operativa

- La receta puede referir maquinaria activa o en mantenimiento porque define el proceso esperado, no confirma disponibilidad para una fecha concreta.
- La validacion/liberacion de la orden es la autoridad operativa: una maquina en mantenimiento aporta cero capacidad y bloquea el inicio del ciclo hasta reactivarse.
- `area_ref_id` mejora asignacion y reportes, pero su ausencia no invalida la definicion de receta. No se infiere ni escribe automaticamente comparando nombres.
- Maquinaria inactiva o inexistente no puede agregarse ni aprobarse en una receta.

## Frontera entre validar receta y validar orden

- La validacion de receta confirma identidad y elegibilidad de producto, unidad, materiales, puestos, maquinaria y areas; tambien proyecta cantidades y costo. No evalua existencias ni minutos disponibles.
- La duracion sugerida de receta es solo un valor inicial para planeacion y no participa en la elegibilidad de sus recursos.
- La orden de produccion es el unico punto que valida disponibilidad material, capacidad laboral/maquinaria, compromisos concurrentes, inicio y numero de dias productivos.
- Un faltante operativo nunca invalida historicamente la definicion de una receta; impide liberar la orden concreta hasta resolverlo o cambiar su horizonte.


## 2026-09-08 — Responsabilidades CHG-265

El usuario confirmó: solicitante acepta servicios comprados, destino confirma transferencias y Almacén confirma devoluciones. La preparación comercial no implica movimiento físico. No se agregan permisos nuevos ni escrituras entre schemas. CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.


## Ajustes UAT Local CHG-266

Mantener listado como entrada de Proveedores y separar captura en modal. Corregir la compresión con clases y container queries acotadas, sin alterar globalmente el riel. Explicar transiciones de cotización según permiso efectivo; conservar el ciclo backend y restaurar únicamente el baseline Owner del tenant demo Local con los cuatro permisos ya declarados en OpenAPI.

Evidencia y APIs: `docs/auditorias/uat_responsive_compras_ventas_2026-09-08.md`.


## Solicitudes compactas Local CHG-267

Agrupar todas las bandejas operativas de Movimientos en un desplegable inicial cerrado, antes del historial. Mostrar existencia de pendientes sin sumar páginas como totales. Mantener consultas y comandos existentes; distinguir errores y carga. La expansión es temporal de la pantalla, no preferencia persistente global.

Evidencia y APIs: `docs/auditorias/almacen_solicitudes_desplegables_2026-09-08.md`.


## Recuperación de refacciones Local CHG-268

CHG-268 recupera reservas/cancelaciones de refacciones interrumpidas bajo locks por tenant/orden/solicitud y conserva claves Inventory. Corrige serialización Decimal; Mantenimiento ofrece reintento ES/EN con permiso propio, Almacén confirma la entrega por separado. MTO-000001 recuperada en Local: una reserva de 1 H87, existencia física 2, disponible 1, sin salida ni duplicados. Sin migraciones ni permisos nuevos. Detalle: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Candidato de continuidad CHG-269

CHG-269 prepara la promoción solicitada de todos los cambios Local CHG-255–268 a QA. Base pública verificada: a119ddf en las siete APIs; destino Alembic 20260908_0034 mediante pipeline protegido. Añade dependencia Inventory→Maintenance y rollback compensatorio de tráfico con evidencia. Ejecución y pendientes en `docs/operaciones/release_qa_20260908.md`. QA no se declara actualizado hasta verificar el release.


## Release QA verificado CHG-270

CHG-270 cierra el release QA solicitado y la publicación para otra computadora. PR #14 fusionado; código QA `b63cdad2fbac423c24460e55582ccfc0003e9924` en siete servicios al 100% y Hosting verificado contra su artefacto. Alembic QA `20260908_0034`; candidato `34389669031`, release `34390476667`. Handoff vigente: `docs/contexto/REANUDACION_CHG269.md`. Evidencia, digests, revisiones y rollback: `docs/operaciones/release_qa_20260908.md`. UAT autenticada permanece pendiente para el tester; no se copiaron datos Local ni se modificó Producción.


## Errores de formulario corregibles CHG-272

La respuesta estructurada de API debe llegar completa al resolvedor de formulario. La propiedad del request se captura antes de awaits; las rutas de payload se vinculan a controles exactos y a la identidad/orden realmente serializados, incluso al filtrar partidas. Los lookups se marcan en su control visible. Campos no editables o rutas desconocidas usan resumen seguro; ningun mensaje generico promete marcas inexistentes.

El sistema conserva captura y distingue validacion, bloqueo de negocio, permisos y fallo tecnico. No muestra diagnosticos del servidor ni guarda contrasenas para restaurarlas. La skill `erclave-form-feedback`, exigida en AGENTS/AGENTES, obliga a evidencia conductual por consumidor presente o futuro. Registro de 54 variantes y 22 casos MAIN no equivale a certificacion funcional exhaustiva. Evidencia y alcance Local: `docs/auditorias/formularios_feedback_2026-09-13.md`. Sin cambio de ownership, contratos ni reglas backend; sin promocion QA.
