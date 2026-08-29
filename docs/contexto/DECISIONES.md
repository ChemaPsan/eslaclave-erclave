# Decisiones vigentes de ERClave

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
- Liberar una orden reserva materiales por almacen y compromete minutos de mano de obra/maquinaria por fecha. La primera entrada a `in_progress` consume cada reserva mediante Inventory y registra una salida inmutable en el almacen que la otorgo; reanudar o cerrar no vuelve a consumir. Cancelar antes del inicio libera reservas y cancelar despues conserva las salidas fisicas. El cierre exige cantidades reales temporales y calcula el costo real desde snapshots verificables. Los comandos externos y locales son idempotentes y los bloqueos se ordenan por recurso para evitar sobreasignacion concurrente.
- En modo API, una receta solo selecciona articulos activos marcados `use_in_recipe`, puestos RH activos con `intervenes_in_production=true` y, como etapas, areas RH activas que tengan al menos uno de esos puestos productivos. La etapa conserva `labor_area_ref_id` y nombre snapshot, sin FK ni escritura cruzada.
- Las fases activas de una receta se numeran en orden consecutivo y sus porcentajes deben sumar exactamente 100. La orden copia numero, area y peso; su avance general es la suma ponderada del avance de cada fase, no un promedio simple.
- El costo manual de un articulo pertenece a Inventory y significa costo por una unidad base del articulo. Las conversiones solo se permiten entre unidades activas, compatibles y con factor estandar inequívoco; Compras sera la autoridad futura para recalcularlo desde recepciones u ordenes de compra.
- CHG-228 preparo Compras y CHG-229 implemento su primer corte supplier-to-receipt en Local, activable en Backoffice con dependencia obligatoria de Inventory. Admin conserva unidades, monedas, condiciones, folios y autorizacion. Compras es dueno de proveedor/requisicion/orden/recepcion comercial e Inventory del articulo/almacen/movimiento/saldo. Factura, pago, devolucion y contabilidad quedan fuera hasta definir sus owners y contratos.
- Desde CHG-230, todo proveedor nuevo exige perfil fiscal minimo y RFC unico por tenant. Los proveedores heredados incompletos permanecen legibles y solo deben completar el conjunto al editar datos fiscales. El maestro sigue siendo editable; cualquier factura fiscal futura conservara snapshots propios.
- Desde CHG-231, una requisicion de Compras agrupa multiples partidas y consolida cada articulo en una sola linea. La orden conserva precio por partida. Dividir una requisicion entre varios proveedores requiere un corte posterior con saldo adjudicable por linea y no se simula duplicando documentos.
- Desde CHG-232, una orden originada en requisicion debe coincidir exactamente en tipo, articulo, descripcion, cantidad y unidad; solo agrega precio. Requisiciones y ordenes se cancelan con motivo y actor. Cada recepcion reclama saldo bajo bloqueo, conserva una clave Inventory estable por linea y su conciliacion reintenta exclusivamente lineas no completadas.
- CHG-234 implementa Mantenimiento correctivo solo en Local, con RH e Inventory como dependencias duras y Production como integracion opcional. `maintenance-service` es dueno de ordenes, asignaciones, tiempos y solicitudes internas; RH de elegibilidad, Production de maquinas/ordenes y del hold `maintenance_order_ref_id`, e Inventory de refacciones, reservas, movimientos y costos. Resolver nunca reanuda Produccion automaticamente.
- Una orden de Mantenimiento apunta a una maquina de Production o a una descripcion/ubicacion libre de edificio u otro objetivo. Un articulo de Inventory no se convierte en activo. Solo una falla bloqueante puede permanecer activa por maquina.
- Una falla productiva deja la orden en `waiting_resources` si no inicio o la pasa a `paused` si estaba en proceso. Resolver libera la maquina, pero nunca reanuda Produccion automaticamente: el operador debe revalidar y reanudar.
- La primera entrega de Mantenimiento sera correctiva. Preventivos recurrentes, Activos, garantias, anexos y escalamiento automatico a Compras permanecen fuera hasta un corte propio.
- Los estados de orden y etapa son maquinas de estado backend; las etapas terminadas u omitidas son terminales y el cierre de orden requiere una transicion explicita desde validacion.
- Inventario incluye articulos sin movimientos con saldo cero cuando tienen almacen sugerido, sin fabricar movimientos ni existencias.
- El primer corte de Ventas es Local y comprende Clientes/Cotizaciones. Sales conserva ownership de sus documentos y snapshots; RH, Produccion y Administracion siguen siendo autoridades de responsables, productos/servicios y unidades.
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
