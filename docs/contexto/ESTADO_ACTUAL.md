# Estado actual de ERClave

Ultima actualizacion: 2026-08-27.

## Ambiente local

- El arranque canonico Local aislado opera mediante `backend/scripts/start_local.ps1`: PostgreSQL `erclave_local`, Firebase Auth Emulator `demo-erclave`, frontend y APIs locales.
- Una ejecucion local conectada a cualquier recurso QA debe identificarse como `local conectado a QA` y requiere autorizacion explicita.

- Frontend estatico local esperado en `http://127.0.0.1:4173`.
- Admin API local esperada en `http://127.0.0.1:8000` contra PostgreSQL local. La conexion local a QA usada en una validacion autorizada anterior es evidencia historica, no el modo local canonico.
- Production API local esperada en `http://127.0.0.1:8002`.
- Inventory API local esperada en `http://127.0.0.1:8004`.
- HR API local esperada en `http://127.0.0.1:8006`.
- Sales API local esperada en `http://127.0.0.1:8008`; cubre Clientes, Cotizaciones, Pedidos, surtido y Entregas. El mismo servicio ya esta desplegado en QA como parte del candidato de cinco servicios.
- Purchasing API Local esperada en `http://127.0.0.1:8010`; cubre Proveedores, Requisiciones, Ordenes y Recepciones. No esta desplegada en QA ni Produccion.
- PostgreSQL portatil aislado para Inventory escucha en `127.0.0.1:5434`, base `erclave_local`.
- Firebase Auth Emulator escucha en `127.0.0.1:9099` y su UI en `127.0.0.1:4000`; el usuario local `admin.qa@erclave.local` resuelve el tenant demo sin consumir Firebase QA.
- Firebase autentica; `admin-service /v1/session/context` resuelve tenant, membresia, modulos, permisos y alcance.

## Cortes funcionales relevantes

### Feedback operativo

- CHG-251 normaliza en Local los errores de API y Firebase mediante un catálogo común ES/EN gobernado por `error.code`; `message` se conserva sólo como diagnóstico y ya no se presenta directamente.
- Las transiciones sensibles de Producción, Ventas, Compras y Mantenimiento distinguen éxito, warning y error; si una mutación falla, el selector o proyección vuelve al estado confirmado. Los errores inesperados pueden mostrar `correlation_id` como referencia de soporte.
- Formularios, toasts y errores de carga declaran semántica ARIA, permanecen visibles según severidad y escapan contenido antes de insertarlo en HTML. `validate:error-feedback` protege estas reglas.

### Compras

- CHG-229 implementa en Local el primer corte supplier-to-receipt mediante `purchasing-service` en `http://127.0.0.1:8010` y schema aislado `purchasing`.
- CHG-230 agrega perfil fiscal editable al maestro de proveedores. Las altas nuevas exigen razon social, RFC, regimen, correo de facturacion y codigo postal fiscal; RFC es unico por tenant y los registros heredados pueden completarse gradualmente.
- CHG-231 habilita en la UI Local requisiciones con multiples partidas buscables. Backend rechaza articulos repetidos en el mismo documento y la conversion a Orden solicita un precio independiente por partida.
- Compras es dueno de proveedores, requisiciones, ordenes, recepciones comerciales, idempotencia y auditoria. Inventory conserva la autoridad exclusiva de articulos, almacenes, movimientos, saldos y Kardex.
- La requisicion transita de borrador a enviada y aprobada/rechazada; una orden solo consume requisicion aprobada o exige motivo de compra directa. Emitir congela la orden para recibir.
- La recepcion rechaza duplicados y sobre-recepcion, admite parcialidad y solicita entradas idempotentes a Inventory. Si la autoridad fisica falla, conserva `needs_reconciliation` visible sin fingir una recepcion completada.
- CHG-232 cierra el flujo source-to-receipt: edita borradores, exige coincidencia exacta requisicion/orden, cancela con motivo, recibe varias partidas, reserva saldo concurrentemente y permite conciliar solo lineas fallidas con claves estables. Inventory expone lectura puntual tenant-safe de almacen para validar la recepcion.
- El catalogo Admin y manifiesto marcan `purchasing` como implementado, con dependencia obligatoria de `inventory`. La UI ofrece flujo bilingue real; reabastecimiento automatico, factura, CxP, pago, devolucion y asiento permanecen planeados.
- CHG-248 incorpora en los cinco submodulos el riel de ayuda transversal bilingue; resume cada recorrido sin alterar permisos, estados ni contratos.
- CHG-250 reemplaza los `prompt()` nativos de cancelacion por un modal ERClave bilingue que exige motivo, conserva los comandos y permisos puntuales existentes y presenta errores dentro del flujo.

### Mantenimiento

- CHG-252 corrige en Local la continuidad de carga del frontend: al terminar las consultas autoritativas, Mantenimiento vuelve a renderizar y deja el estado `Cargando Mantenimiento`; un guardrail evita reintroducir el bloqueo.
- CHG-234 implementa Mantenimiento correctivo en Local: API `8012`, schema `maintenance`, ordenes manuales o ligadas a maquina/Produccion, responsable RH elegible, tiempos y solicitudes multi-linea al almacen de refacciones.
- Solicitar una orden bloquea la maquina y pausa una orden productiva `in_progress`; resolver consume reservas y libera la maquina sin reanudar Produccion. Backoffice ya permite activar el modulo y el tenant demo Local lo tiene activo.
- CHG-235 endurece el flujo en Local con revision `20260824_0028`: conciliacion manual durable, compensacion de reservas al cancelar, rebloqueo al reabrir, revalidacion RH al iniciar, asignacion primaria unica e indices de consulta por orden.
- RH e Inventory son dependencias obligatorias. Production es integracion opcional y sigue siendo autoridad de maquinas y ordenes productivas.
- La UI tolera fallos de catalogos sin perder la lectura de ordenes, respeta permisos de mutacion y distingue exito de `needs_reconciliation`. QA y Produccion no fueron modificados.
- CHG-248 agrega el riel de ayuda transversal bilingue a Ordenes y Refacciones, conservando la regla de no reanudar Produccion automaticamente y la autoridad de Inventory sobre reservas y movimientos.

### Administracion y permisos

- CHG-236 implementa solo en Local autorizacion operativa granular: Produccion separa liberar, esperar recursos, iniciar, pausar, reanudar, enviar a validacion, finalizar y cancelar; cada resultado de etapa tiene permiso propio. Mantenimiento separa sus nueve transiciones y Almacenes separa leer de recibir producto terminado. Compras, Ventas y Recetas ya cumplian el patron y fueron auditados sin cambios de flujo.
- CHG-237 endurece ese corte solo en Local: la autorizacion exacta de Produccion ocurre antes de precondiciones sensibles; Almacenes consume una proyeccion minima de orden terminada en vez de lecturas generales; OpenAPI y runtime comparan tambien sus permisos; y el mapa maestro/manuales quedan sincronizados.
- El backend exige el permiso derivado de la accion solicitada aunque el usuario posea otra capacidad del mismo endpoint. El editor de Roles recibe los permisos desde OpenAPI y no depende de nombres fijos de puestos.

- En Local y QA, Administracion incluye catalogos tenant-safe de unidades, monedas y condiciones de pago. Cada tarjeta abre una vista dedicada; altas/ediciones son idempotentes, correlacionadas y auditadas. CHG-205 endurecio `document.template` con logo reemplazable/eliminable, colores, pie y numeracion compartidos por los PDF de Ventas y Produccion. La UI es bilingue y permission-aware; el backend verifica formato, Base64, firma binaria y limite decodificado de 1 MB del logo. Ambos generadores recuperan el registro API si falta en cache, informan fallos visibles y escapan el contenido operativo antes de insertarlo en el documento.
- Backoffice edita datos basicos del tenant y gobierna sus entitlements contractuales. El administrador del tenant solo cambia `tenant_enabled`; `session/context`, policy y permisos operativos exigen entitlement activo mas preferencia encendida. Los modulos planeados no pueden habilitarse y `admin` es obligatorio. La cabeza Alembic Local es `20260825_0029`; QA permanece en `20260821_0023`.
- En Local y QA, Administracion ofrece el catalogo de folios por tipo documental. Prefijo, separador, siguiente numero, longitud y modo administrado/manual son editables por tenant; la asignacion de un consecutivo es atomica, idempotente y auditada. Los formularios actuales de Produccion, Almacenes, RH y Ventas consumen esa autoridad antes de crear el registro.
- Los contratos OpenAPI parsean como YAML y un validador compara operaciones `implemented` con las rutas FastAPI. Capacidades futuras se marcan `x-implementation-status: planned`.
- Los manifiestos de microfrontend distinguen `implemented`/`planned` y usan permisos puntuales con puntos; en los implementados, `permissions` es el inventario exhaustivo de operaciones OpenAPI implementadas del namespace propietario. El runtime visual actual permanece centralizado en `frontend/app.js` hasta una extraccion modular posterior.
- El editor de permisos de roles trabaja con borrador explicito, busqueda, filtros, agrupacion por modulo/recurso, seleccion masiva visible y resumen de cambios; no incluye plantillas ni presets.
- Los nombres tecnicos se conservan como identificadores de policy, pero la interfaz usa nombres y descripciones ES/EN mantenidos en `admin.permissions`.
- El catalogo remoto requiere tenant y `admin.role.read`; solo expone permisos `tenant` asignables y marca disponibilidad segun el entitlement del modulo.
- Modificar permisos exige `admin.role.permissions.manage`, `expected_revision` e `Idempotency-Key`. El backend aplica diferencias, conserva scopes heredados sin permitir crear nuevos scopes arbitrarios y audita altas/bajas.
- Los grants historicos internos pueden conservarse como relacion para no perder trazabilidad, pero ya no ingresan a `session/context` ni producen autorizacion efectiva. El owner conserva un piso administrativo y no puede inactivarse.
- El payload anterior `permission_ids + scope` permanece compatible y esta deprecado; la interfaz nueva usa `assignments + expected_revision`.
- Mientras un ambiente no tenga `admin.role.permissions.manage`, Roles permite abrir `Ver permisos` en modo de solo lectura y explica por que la edicion permanece bloqueada; no aplica fallback de escritura inseguro.
- La revision vigente de Cloud SQL QA es `20260821_0023`. La promocion gobernada ejecuto la cadena `0013 -> 0023` sin copiar datos funcionales Local y publico el SHA inmutable `7aa5c674b605d8268b6bfe00e0812b6a300277cb` en los cinco servicios.

### Produccion

- En Local y QA, las ordenes nuevas ya no aceptan responsables libres: exigen trabajadores activos validados por `hr-service`, tanto para responsable general como por etapa, y conservan ID externo mas nombre snapshot.

- Productos y servicios se presentan como catalogo maestro antes de consultar ordenes relacionadas.
- En Local y QA, Productos/Servicios, Recetas/versiones, Maquinaria, Ordenes y etapas persisten mediante `production-service`; la UI recarga PostgreSQL y no degrada silenciosamente a `localStorage` cuando `apiMode=api`. La validacion autoritativa descrita a continuacion esta desplegada en ambos ambientes.
- La version vigente aprobada y el borrador/pendiente mas reciente se distinguen. Las ordenes siempre usan `current_version_id`, guardan snapshots de receta, recursos y costos autoritativos y conservan sus etapas aunque la receta cambie.
- El editor API de Recetas consume materiales activos con `use_in_recipe=true` desde Inventory y puestos productivos/areas activas desde HR. No carga seeds; las etapas nuevas conservan ID externo y nombre snapshot del area mediante la revision Local `20260805_0013`.
- El editor de Recetas separa materiales, mano de obra y maquinaria. Los materiales usan la unidad base de Almacenes; mano de obra y maquinaria se capturan como horas-persona y horas-maquina, con conversion transparente a minutos para el contrato vigente.
- Las horas-persona y horas-maquina aceptan cualquier fraccion decimal, sin saltos obligatorios de 15 minutos; la UI aclara que `0.5 h = 30 min`.
- El buscador de producto/servicio en Recetas presenta nombre y codigo comercial; los IDs tecnicos `prs_*` permanecen ocultos y se usan solo para la relacion interna.
- Las listas, selectores, mensajes y documentos de Recetas ocultan IDs `rec_*`; muestran nombre, codigo del producto y version mientras conservan el ID en relaciones y atributos internos.
- En Local y QA, la receta tiene folio de negocio propio, enumera sus fases y exige que sus pesos activos sumen 100%. La orden conserva ese snapshot y expone avance general ponderado. La seleccion de una version aprobada ya reconoce correctamente la version aprobada retornada por API aunque la proyeccion de cabecera no incluya `current_version_id`.
- El alta y edicion de Maquinaria consulta areas activas de `hr-service`; no permite capturar areas libres y dirige a Areas y puestos cuando el catalogo esta vacio.
- Las transiciones de orden y etapa se validan en backend, son idempotentes y auditadas. Una etapa terminal no vuelve a pendiente; completar todas las etapas lleva la orden a validacion y el cierre es explicito.
- En Local y QA, la validacion ya no acepta disponibilidad ni costos enviados por el navegador. Produccion consulta Inventarios y RH, descuenta reservas/capacidad comprometida por fecha, bloquea capacidad concurrentemente y crea reservas atomicas por almacen antes de liberar la orden.
- La primera entrada de una orden a `in_progress` consume sus reservas como salidas inmutables en los almacenes que las otorgaron y fija el costo real de materiales; reanudar o cerrar no duplica movimientos. En el corte vigente, cerrar exige todas las fases al 100%, pero no obliga a capturar minutos reales de mano de obra/maquinaria; esa medicion queda diferida hasta definir el modelo de eficiencia. `actual_cost` conserva el costo material consumido. Cancelar antes del inicio libera reservas; despues del inicio conserva las salidas fisicas y libera los compromisos de capacidad aplicables.
- Aprobar una receta revalida producto, materiales, unidades, puestos, areas y maquinaria existente no inactiva. Una maquina en mantenimiento puede definir el proceso, pero aporta cero capacidad y bloquea la orden hasta reactivarse. `area_ref_id` sigue recomendado para asignacion/reportes; nombres y costos son snapshots y no se infieren relaciones por texto.
- Areas y puestos pertenecen al modulo independiente Recursos Humanos, con microfrontend y `hr-service` propios.
- En Local y QA, RH administra expedientes minimos de trabajadores con un puesto vigente, identificadores CURP/RFC/NSS validados y datos complementarios opcionales. La cabeza Alembic comun es `20260821_0023`.
- El entitlement `hr` controla la disponibilidad por tenant; alta y edicion usan permisos separados `hr.area.*` y `hr.position.*`.
- El esquema `hr` incorpora aislamiento por tenant, FK compuesto area-puesto, idempotencia y auditoria. El 2026-07-31 se creo vacio en QA; posteriormente CHG-182 desplego `hr-service` y activo el entitlement estructural sin cargar areas ni puestos.
- El corte estructural CHG-182 dejo seis permisos `hr.*` activos y los permisos `production.labor.*` heredados inactivos. Los catalogos partieron vacios; su contenido actual depende exclusivamente de las capturas UAT autorizadas y no se documenta como constante.
- Produccion consume areas y puestos desde `hr-service`; no los persiste ni escribe su schema.
- Las recetas en modo API ya no usan el catalogo fijo de materiales: consumen articulos activos marcados `use_in_recipe` y balances reales de Almacenes.

### Almacenes e inventarios

- `inventory-service` es propietario de almacenes, articulos, movimientos, balances y Kardex.
- En modo API, el formulario de Movimientos persiste exclusivamente mediante `inventory-service`; al completar el comando invalida y recarga movimientos y balances. `localStorage` queda solo como fallback del modo maqueta y nunca representa un movimiento remoto registrado.
- El submodulo visible `Inventario` conserva el identificador tecnico `existencias`.
- Inventario consume balances enriquecidos con busqueda, filtros, orden y paginacion server-side.
- La vista usa container queries: colapsa el flujo por defecto, transforma la tabla en tarjetas cuando el panel central se estrecha y mueve Alertas debajo del contenido en viewports intermedios.
- Los movimientos registrados y no reversados son la fuente de verdad.
- En Local y QA, cada articulo expone `default_unit_cost_per_base_unit` con semantica explicita de costo por unidad base y un calculador HTTP para conversiones compatibles (por ejemplo kg/g o L/ml). No inventa equivalencias para empaques o unidades personalizadas.
- En Local y QA, `available_quantity = max(on_hand_quantity - reserved_quantity, 0)`. Las reservas activas y no vencidas se muestran por ubicacion y se protegen con bloqueos transaccionales por tenant/articulo/almacen.
- En Local y QA, cada articulo incorpora costo unitario predeterminado; los saldos calculan costo promedio e importe de inventario desde movimientos inmutables. Salidas, transferencias, reversiones y consumos preservan la valuacion y rechazan stock disponible insuficiente.
- La unidad base queda bloqueada despues del primer movimiento; articulos/almacenes inactivos no aceptan movimientos ni reservas y `maximum_stock` no puede ser menor que `minimum_stock`.
- La bandera `inventory.items.use_in_recipe` pertenece a la migracion `20260730_0009`. Los catalogos partieron vacios en QA; desde la promocion `0023`, su contenido depende de las capturas UAT autorizadas y no se documenta como constante.
- Inventario muestra con saldo cero los articulos sin movimientos que tengan almacen sugerido.

### Recursos Humanos

- Areas y puestos son catalogos generales de RH. La bandera `intervenes_in_production=true`, junto con estatus activo, es la unica que hace elegible un puesto y sus trabajadores para recetas y ordenes; crear un puesto nuevo no activa esa bandera por defecto.
- La validacion local cubrio 10,000 articulos y 10,000 movimientos; consultar `docs/operaciones/validacion_volumen_inventario_local.md`.

### Ventas

- En Local y QA, `sales-service` persiste Clientes, Cotizaciones, Pedidos y Entregas mediante las revisiones `20260818_0018`/`0019`/`0020`. CHG-204 cerro el plan correctivo de CHG-203: alta de Entregas, mapeo producto-articulo, sanitizacion, costo real por fuente y orquestacion durable/concurrente.
- Clientes exige codigo estable, contacto principal, moneda/condiciones controladas y responsable seleccionado de trabajadores activos de RH. El perfil fiscal es opcional, pero al iniciarse exige razon social, RFC/ID fiscal y correo de facturacion.
- Cotizaciones exige cliente activo, producto/servicio activo de Produccion y unidad activa de Administracion igual a la unidad base. Backend calcula subtotal, descuentos, total, costo snapshot y margen estimado.
- Los estados reales son borrador, cotizada, aprobada, vencida y cancelada; solo el borrador es editable y emitir/aprobar revalida referencias autoritativas.
- CHG-201 audito la sinergia modular: `sales` declara dependencias efectivas `hr`/`production`; Backoffice, onboarding y Administracion bloquean activaciones o apagados que dejen autoridades rotas, bajo bloqueo transaccional. La API sigue validando modulo y permiso aunque se oculte la UI.
- Los endpoints de lectura no requieren resolver maestros y la UI usa `Promise.allSettled`: una falla de catalogos o autoridades conserva documentos comerciales disponibles y bloquea solamente las mutaciones dependientes.
- El onboarding inserta entitlements antes de poblar permisos del owner. Seleccionar Ventas desde Backoffice incluye RH y Produccion, evitando un tenant activo sin autorizaciones comerciales.
- Pedidos nacen una sola vez de una cotizacion aprobada. Cada producto exige el articulo de Inventory mapeado por Production y puede usar reserva o solicitud de Production; servicios quedan listos. Surtido, cancelacion y confirmacion reclaman estado durable bajo locks, reanudan con claves estables y marcan `needs_reconciliation` tras una interrupcion externa. El costo de `stock` proviene del consumo y el de servicio de captura operativa; Production permanece sin costo real hasta su callback. Devoluciones y facturacion permanecen `planned`.
- QA ya tiene `sales-service` y la cadena de migraciones hasta `20260821_0023`; la habilitacion efectiva de Ventas continua dependiendo del entitlement del tenant y de RH/Produccion.
- CHG-250 alinea la verdad visible de Ventas: Pedidos se cuenta como capacidad implementada, se elimina copy planeado obsoleto y `Margen` queda como consulta de solo lectura derivada de Pedidos/Entregas, sin alta generica ni persistencia local de documentos.

### Interfaz transversal

- CHG-249 aplica una jerarquia visual mas sobria a botones y badges operativos: las acciones secundarias usan superficies neutras, las primarias conservan el acento morado y los estados activo/advertencia/error usan color semantico suave con borde y contraste para tema claro/oscuro. El bloque CSS esta aislado para rollback y conserva targets de 44 px.
- CHG-250 corrige la identidad de los submodulos RH; localiza su guia, resumen de capacidad y estados laborales provenientes de API; completa los nombres ingleses de Mantenimiento y las etiquetas/atributos accesibles del shell. Los nombres y descripciones capturados por el tenant permanecen como datos sin traduccion automatica.

- CHG-227, implementado solo en Local: toda mutacion HTTP iniciada desde el frontend principal o Backoffice muestra una capa de progreso bilingue, marca la pagina con `aria-busy` y bloquea botones, clics y activaciones por teclado mientras la operacion sigue pendiente. Un contador conserva el bloqueo cuando coinciden varias solicitudes y `finally` lo libera ante exito o error, reduciendo comandos duplicados por reintentos del usuario.

- El shell, los modulos activos, los catalogos, formularios y modales comparten reglas responsive basadas en el ancho real de su contenedor.
- La guia descriptiva conserva el patron compartido de riel vertical izquierdo y compresion; solo pasa a una columna en anchos estrechos o mediante una excepcion explicita de pantalla.
- En anchos intermedios las colecciones reducen columnas; en anchos estrechos formularios y acciones se apilan sin ocultar su significado.
- El backoffice transforma sus filas de tenants y consumo en tarjetas etiquetadas cuando su panel se estrecha.
- La navegacion movil conserva los submodulos activos, foco visible, salto al contenido y anuncios accesibles de notificaciones.
- `npm.cmd run validate:responsive` protege los contenedores, puntos de accesibilidad y referencias documentales obligatorias.

## Calidad

- La fuente normativa de ambientes es `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`; la skill `$erclave-environment-boundaries` aplica su preflight.

- La fuente de verdad del resultado automatizado es la ultima ejecucion de `npm.cmd run verify`.
- En el corte CHG-195: `npm.cmd run verify` aprobo validadores, parseo/paridad OpenAPI, compilacion y `151 passed, 2 skipped`; las dos integraciones PostgreSQL omitidas por el comando general aprobaron aparte contra `erclave_local` con rollback. El smoke autenticado confirmo frontend, cuatro APIs, readiness, sesion y 50 unidades activas en Local.
- En el corte CHG-197: `npm.cmd run verify` aprobo validadores, parseo/paridad OpenAPI, compilacion y `161 passed, 3 skipped`; Alembic actualizo exclusivamente `127.0.0.1:5434/erclave_local` de `20260818_0016` a `20260818_0017`. No hubo QA ni Produccion.
- CHG-198 sincronizo fichas de agentes/modulos, ownership, modelo y diagramas con ese corte y agrego guardrails semanticos. No cambio runtime ni ambientes: las capacidades 0017 continúan exclusivas de Local y QA permanece en `20260805_0013`.
- CHG-199 formalizo el gobierno de documentacion viva y agrego `validate:documentation` al ciclo obligatorio. El control deriva automaticamente la cabeza Alembic, revision QA, ultimo CHG, indice modular y enlaces internos, y verifica que agentes e inicio de sesion mantengan estas reglas.
- CHG-200 implemento el primer corte real de Ventas solo en Local: Clientes/Cotizaciones y revision `20260818_0018`; su evidencia historica permanece en `TRAZABILIDAD.md`.
- CHG-201 audito Ventas y su gobierno modular sin agregar migracion: corrigio dependencias `sales -> hr/production`, permisos de owner en onboarding, lectura parcial por permiso, botones/transiciones, busqueda comercial e idempotencia concurrente. `npm.cmd run verify` aprobo `172 passed, 6 skipped`; las integraciones PostgreSQL adicionales aprobaron `6 passed` y el smoke Firebase valido ambos niveles con estado final restaurado. QA no cambio.
- CHG-202 extiende el runtime Local con la revision `20260818_0019`: Pedidos, surtido por servicio/Inventory/solicitud a Production, Entregas parciales o totales, catalogos comerciales administrables y plantilla documental tenant-safe. `npm.cmd run verify` aprobo `173 passed, 6 skipped`; la integracion PostgreSQL Sales aprobo `11 passed` y el smoke autenticado confirmo frontend/cinco APIs, catalogos, plantilla y lecturas nuevas. Devoluciones permanecen planeadas; QA no cambio.
- CHG-203 audito ese corte sin cambiar runtime: confirmo pruebas verdes y documento bloqueadores de UI, XSS, validaciones, identidad producto-articulo, costo real y consistencia distribuida. En ese punto el segundo corte quedo condicionado a cerrar la auditoria.
- CHG-204 aplico el plan de correccion CHG-203 solo en Local y agrego la revision `20260818_0020`, contratos, UI, pruebas y documentacion sincronizada. `npm.cmd run verify` aprobo `177 passed, 8 skipped` y la integracion PostgreSQL Sales `4 passed`. QA permanece sin Sales y en `20260805_0013`.
- En el corte CHG-164: `npm.cmd run verify` aprobo todos los validadores, compilacion y `121 passed, 1 skipped`; el smoke autenticado del stack local canonico con Firebase Emulator respondio correctamente en los seis modulos activos.
- En el corte CHG-166: `npm.cmd run verify` aprobo contratos, validadores, sintaxis y `126 passed, 1 skipped`; el smoke local creo y recargo producto, maquinaria, receta vigente, orden con snapshots y su ciclo completo de etapas.
- El repositorio puede contener cambios locales no confirmados; `session:context` debe mostrar el estado Git real de cada sesion.
- `npm.cmd run session:context` reconstruye la memoria operativa sin mostrar secretos: Git, trazabilidad, migraciones, estado, decisiones, tenants, pendientes y puertos locales.
- `validate-session-context.js` protege la presencia de los documentos y guardrails obligatorios.
- `validate-responsive-ui.js` protege el estandar transversal de interfaz para futuras sesiones.
- El candidato incorpora un pipeline QA manual en dos fases: construccion inmutable por SHA/digest y promocion con aprobaciones independientes para base, servicios, trafico y frontend.
- La configuracion backend de QA/Produccion rechaza URLs locales, CORS local, autenticacion demo, Firebase sin proyecto y base ausente antes de arrancar.
- El build QA del frontend elimina configuracion local, emulador, tenant y actor; `validate-qa-release-pipeline.js` protege estas fronteras.
- Fuera de localhost, modo API y URLs provienen del artefacto; Firebase identifica al actor y `/v1/session/tenants` resuelve el tenant activo en memoria. Los overrides de `localStorage` no pueden cambiar la frontera QA.
- En modo API, la representacion temporal de catalogos operativos vive solo en memoria y se repuebla desde Admin, Produccion, Inventory y RH. Los datos operativos del navegador no persisten entre sesiones ni se tratan como fuente de verdad.
- La configuracion estructural del tenant QA requiere confirmacion separada, sincroniza el catalogo de permisos y deja activos solamente `admin`, `production`, `inventory` y `hr`; no carga datos funcionales.
- GitHub Pages ya no se publica automaticamente desde `main`; permanece como maqueta manual.
- El 2026-08-08 se aprovisionaron en GCP QA las seis identidades dedicadas de `infra/qa/identity-plan.json`, Artifact Registry `erclave-qa` y Workload Identity Federation limitado a `ChemaPsan/eslaclave-erclave`; los accesos al secreto, Artifact Registry, Cloud SQL, Cloud Run y `actAs` quedaron delimitados por recurso o identidad.
- Los GitHub Environments `qa-build`, `qa-database`, `qa-services`, `qa-traffic` y `qa-frontend` exigen aprobacion de `ChemaPsan`; las variables QA del pipeline quedaron configuradas sin llaves JSON ni URL de base de datos.
- La identidad federada `erclave-github-deployer-qa` tiene `roles/firebasehosting.admin` en el proyecto QA `erclave`; el plan versionado y el validador del pipeline exigen ese permiso minimo para el gate `qa-frontend`.
- Cloud SQL QA exige conexiones cifradas (`ENCRYPTED_ONLY`), tiene PITR activo con siete dias de logs y conserva el backup manual exitoso `1786227437185`, creado antes del endurecimiento.
- El candidato CHG-182 fue construido una sola vez por digest y promovido en QA. Tras CHG-191, `admin-service-qa-bo-1-1` recibe 100% del trafico Admin; `inventory-service-qa-00003-zus`, `hr-service-qa-00003-gor` y `production-service-qa-00008-vuv` conservan 100% en sus servicios. Las cuatro URLs estables aprobaron health, readiness con Cloud SQL y version `4e9c6881dab61239f1abd5fff688019fdd697977`.
- Inventory y RH ya tienen servicio real desplegado en QA y entitlements estructurales activos para `ERClave Demo QA`; sus catalogos permanecen sin carga funcional o dummy. Ventas e Integraciones permanecen inactivos.
- El frontend sanitizado CHG-182 esta publicado en Firebase Hosting QA mediante el gate `qa-frontend` del run `31647661435`. `https://erclave.web.app` responde HTTP 200 y su configuracion runtime publicada referencia exclusivamente las cuatro APIs Cloud Run QA, Firebase QA y ningun tenant/actor local.
- CHG-191 configuro `QA_BACKOFFICE_ADMIN_EMAILS` y el run `31661213987` promovio `admin-service-qa-bo-1-1` mediante `qa-services` y `qa-traffic`. La revision reutiliza la imagen Admin certificada, conserva version CHG-182 y separa la allowlist interna de roles owner; rollback: `admin-service-qa-00017-dih`.
- El 2026-08-12 se repitio una verificacion publica read-only: Admin, Produccion, Inventory y RH respondieron ambiente `qa`, readiness con base configurada y la misma version CHG-182; `https://erclave.web.app/env.js` publica modo API/Firebase y las cuatro URLs QA.
- El candidato local posterior corrige dos huecos de paridad antes del siguiente release: Settings ya no carga silenciosamente `backend/.env`, Local rechaza bases/URLs/Firebase QA, y el frontend QA conserva en memoria el tenant resuelto desde `/v1/session/tenants` sin caer al tenant/actor demo. Estos cambios aun no estan desplegados en QA.
- En los cortes CHG-182 a CHG-190, `npm.cmd run verify` aprobo validadores, compilacion y `135 passed, 1 skipped`; el release QA `31647661435` completo migracion, configuracion, despliegue, smoke, promocion de trafico backend y publicacion del frontend. Los cuatro servicios publicos conservan health, readiness y version `4e9c6881dab61239f1abd5fff688019fdd697977`.

Este archivo debe describir hechos comprobados, no planes ni aspiraciones.
# Actualizacion CHG-206 (2026-08-20)

En Local quedó implementada la vinculación guiada de producto terminado entre Almacenes, Producción y Ventas. Producción conserva la referencia autoritativa 1:1; el alta crea un artículo `finishedGood` con la misma unidad y admite identidad logística distinta de la comercial. No hubo migración ni promoción a QA/Producción.
# Actualizacion CHG-207 (2026-08-20)

En Local existe el Custodio de manuales funcionales de la solucion y la skill `$erclave-solution-manuals`. La biblioteca `docs/manuales_solucion/` separa fuentes Markdown revisables de documentos Word generados y registra cobertura, ambiente y dudas funcionales por modulo. Los manuales permanecen por elaborar progresivamente; esta capacidad no implica que ya exista un manual completo de cada modulo.
# Actualizacion CHG-208 (2026-08-20)

En Local, Entregas de Ventas vuelve a mostrar la fecha programada requerida en modo API. Los vinculos Cotizacion -> Pedido y Pedido -> Entrega sustituyen listas extensas por busqueda acotada sobre folio, cliente, producto/servicio, importe o estado, conservando solo documentos elegibles. No cambia API ni persistencia; la paginacion server-side para volumen mayor a 200 permanece pendiente.

# Actualizacion CHG-209 (2026-08-20)

En Local, las referencias crecientes implementadas en Administracion, Produccion, Almacenes, Ventas y Recursos Humanos usan búsqueda acotada con identidad visible e ID estable. Estatus, tipos, prioridades y otros catálogos cerrados conservan selectores directos. El patrón es accesible por teclado, reacciona a catálogos actualizados y cuenta con un validador transversal; no cambia APIs ni persistencia y la paginación server-side para más de 200 candidatos sigue pendiente.

# Actualizacion CHG-210 (2026-08-20)

En Local, la raíz de cada módulo es un centro de reportes estándar de solo lectura. Producción, Almacenes, Recursos Humanos, Ventas y Administración muestran sus catálogos/reportes propios sin botones de alta, captura rápida ni acciones de negocio; el patrón y catálogo mínimo también quedaron definidos para Compras, Gastos, Costos y Contabilidad antes de su activación. Las mutaciones permanecen en submódulos. Reportes continúa inactivo y se reserva para cruces, tableros configurables y análisis especializados. No cambia APIs ni persistencia.

# Actualizacion CHG-212 (2026-08-21)

En Local, Administracion gobierna folios y consecutivos por tenant; Produccion identifica recetas y ordenes con codigos de negocio, exige fases ponderadas al 100% y calcula avance general ponderado; Entregables por area conserva numero, peso y area de la fase. Almacenes expone costo por unidad base y conversiones estandar compatibles. RH mantiene areas y puestos generales y solo comparte con Produccion los marcados explicitamente. Las revisiones `20260821_0021` y `20260821_0022` estan aplicadas solo en PostgreSQL Local; QA permanece en `20260805_0013`.

# Actualizacion CHG-241 (2026-08-25)

En Local, Produccion ya no exige concentrar todos los minutos de mano de obra y maquinaria en una sola fecha. Recetas guardan una duracion sugerida y las ordenes capturan inicio, dias productivos y fecha requerida. Production distribuye capacidad de lunes a viernes, descuenta compromisos activos por dia, devuelve el desglose autoritativo y persiste compromisos diarios bajo bloqueo transaccional. Los materiales se validan y reservan una sola vez. La revision `20260825_0029` esta aplicada solo en `127.0.0.1:5434/erclave_local`; QA y Produccion permanecen sin cambios. Calendarios tenant, turnos, festivos, ausencias y afectacion automatica por mantenimiento siguen pendientes.

# Actualizacion CHG-242 (2026-08-25)

En Local, el editor de Recetas ofrece maquinaria activa y en mantenimiento, incluso si su area RH sigue pendiente. La receta define que equipo requiere el proceso; el estatus operativo se evalua al validar/liberar la orden. Por ello una maquina en mantenimiento puede guardarse en la receta, pero sigue aportando cero minutos y bloquea la orden hasta volver a activa. Maquinaria inactiva o inexistente permanece rechazada. No hubo migracion ni cambios de maestros; QA y Produccion permanecen sin cambios.

# Actualizacion CHG-243 (2026-08-25)

En Local, **Validar definicion** dentro de Recetas comprueba exclusivamente que cada recurso exista y sea elegible y proyecta cantidades/costo; no compara inventario ni horas disponibles. La duracion sugerida solo precarga la futura orden. **Validar orden** conserva la comprobacion autoritativa de materiales, minutos de puestos y maquinas, compromisos existentes y horizonte multi-dia. No hubo migracion ni cambios de datos; QA y Produccion permanecen sin cambios.

# Actualizacion CHG-244 (2026-08-25)

El frontend Local compacta el shell y elimina la identidad generica **Centro operativo** y los badges tecnicos de persistencia. Los indicadores transversales viven ahora encima de **Alertas operativas** y responden al ancho del panel lateral. Los modales adaptan validaciones de recursos y partidas de Compras por su propio contenedor; Mantenimiento y Compras usan tarjetas operativas que apilan identidad, responsable, estados, partidas y acciones sin comprimir palabras. Los controles operativos pequenos conservan un target minimo de 44 px. La cobertura ES/EN activa incluye tambien Compras, Mantenimiento y Recursos Humanos. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-245 (2026-08-25)

El frontend Local aprovecha mejor la zona superior en todos los modulos y submodulos. Contexto de sesion, sucursal, busqueda y accion contextual comparten una topbar adaptable en escritorio; en ancho intermedio se compactan antes de apilarse. La cabecera blanca previa al hero funciona solo como breadcrumb y retorno, sin repetir el titulo principal; heroes, workspace y paneles reducen su altura y espaciado compartidos. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-246 (2026-08-25)

En Local, Resolver y Cancelar ordenes de Mantenimiento ya no usan cuadros `prompt()` del navegador. Ambas acciones abren formularios dentro del modal ERClave; Resolver captura diagnostico, causa raiz opcional, trabajo realizado y verificacion, mientras Cancelar solicita el motivo auditable. Validaciones y errores permanecen dentro del formulario. No hubo cambio de API, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-247 (2026-08-25)

En Local, la captura requerida de tiempo de Mantenimiento ya es visible desde cada tarjeta de orden activa mediante **Registrar tiempo**. Resolver muestra el total acumulado y, cuando la orden tiene cero minutos, integra Inicio, Fin y Notas antes de ejecutar la transicion; si el rol carece de `maintenance.time.create`, explica la autoridad faltante. No hubo cambio de contrato, base de datos, datos ni ambientes remotos.

# Actualizacion CHG-211 (2026-08-20)

En Local se revirtió únicamente la portada de Administración: vuelve a mostrar su centro de configuración de organización, usuarios, roles, permisos, módulos activos y catálogos base. Los módulos operativos conservan las portadas de reportes estándar de CHG-210 y Reportes continúa inactivo. La excepción de Administración quedó documentada y protegida por el validador transversal; no cambia APIs ni persistencia.

# Actualizacion CHG-213 (2026-08-21)

En Local se corrigio la apertura de los selectores buscables para mostrar el catalogo completo antes de filtrar. RH devuelve validaciones de expediente accionables sin repetir CURP, RFC o NSS y el formulario declara sus longitudes. Produccion impide elegir materiales con unidades fuera del catalogo activo y explica faltantes autoritativos por recurso antes de asignar el folio de orden. Una orden en espera puede iniciar solo si conserva reservas materiales; liberar reserva, iniciar no descuenta y completar consume las reservas como salidas de Inventario. Los datos demo heredados `LTS`/`MT` y la falta de trabajadores `Fundidor A` no fueron corregidos automaticamente porque son incidencias operativas de maestros. No hubo migracion, despliegue ni escritura en QA/Produccion.

# Actualizacion CHG-214 (2026-08-21)

En Local, la revision `20260821_0023` normalizo de forma transaccional los alias heredados e inequivocos `LTS -> LTR` y `MT -> MTR` en Inventario, Produccion y snapshots de Ventas. Cada fila corregida conserva evidencia en `admin.audit_events`; el downgrade restaura solo las filas registradas que no hayan cambiado despues. La proteccion que impide cambiar realmente la unidad base de un articulo con movimientos o reservas permanece vigente y ahora se explica en espanol/ingles desde la interfaz. `cera_01` conserva identidad, cantidades, costo e historia y ahora usa `LTR`. QA y Produccion permanecen sin cambios en `20260805_0013`.

# Actualizacion CHG-215 (2026-08-21)

En Local, crear o versionar una receta ya no produce `500` cuando incluye maquinaria activa sin referencia estable a un area de RH. Production responde `422 machine_resource_invalid` con una causa operativa segura; la UI excluye esa maquinaria del selector y muestra que debe abrirse en Maquinaria para vincular un area activa. Se conserva la regla de no relacionar maestros automaticamente por nombre. El dato Local `h_002` sigue sin modificarse: su texto de area existe, pero `area_ref_id` permanece vacio hasta confirmacion del operador.

# Actualizacion CHG-216 (2026-08-21)

En codigo Local, la primera transicion de una orden liberada o en espera hacia **En produccion** consume sus reservas por medio de Inventory. Cada reserva genera una salida inmutable en el almacen que la otorgo y devuelve cantidad/costo para el real de materiales. Reanudar, volver desde validacion o completar no genera otra salida; cancelar antes de iniciar libera reservas y cancelar despues conserva los movimientos fisicos. Iniciar una etapa ya no puede saltarse el comando de estatus. No hubo migracion ni mutacion de ordenes, reservas o movimientos existentes; QA/Produccion permanecen sin cambios.

# Actualizacion CHG-217 (2026-08-21)

En Local, el formulario de nueva orden ya no mezcla faltantes calculados por la maqueta con datos reales. En modo API valida localmente solo campos y responsables, y delega existencia disponible, reservas, capacidad laboral y maquinaria a `POST /v1/production/resource-validations`. El modo mock conserva su calculadora local. No cambia contratos, persistencia ni datos; QA/Produccion permanecen sin cambios.

# Actualizacion CHG-218 (2026-08-21)

En Local, **Validar orden** usa la receta maestra recargada y su `currentVersionId` aprobado, no el snapshot transitorio del formulario. Los snapshots historicos permanecen para ordenes creadas y documentos. `rec-000004` ya estaba correctamente activa/aprobada en PostgreSQL; no se modificaron sus datos. No cambia contratos ni persistencia y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-219 (2026-08-21)

En Local se corrigio el cierre de una reserva al consumirla totalmente: Inventory conserva su ultima cantidad positiva como snapshot historico, cambia el estatus a `consumed` y reporta saldo operativo cero. El intento fallido de iniciar `OP-000003` fue revertido completamente por PostgreSQL; la orden sigue en espera, las reservas siguen activas y no existen salidas parciales. No cambia schema ni contrato y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-220 (2026-08-21)

En Local, una orden solo entra a **En validacion** cuando todas sus fases estan terminadas u omitidas; la ultima fase realiza el cambio automaticamente. El selector solo ofrece transiciones validas y muestra **Terminada** cuando tambien se guardo el uso real de mano de obra y maquinaria desde **Cierre/consumos**. `OP-000003` permanece sin mutacion, en validacion con sus dos fases pendientes, y puede recuperarse volviendo a **En produccion**. No cambia schema y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-221 (2026-08-21)

En Local, el avance de una fase se captura como porcentaje: 0% pendiente, 1-99% en proceso y 100% terminada. Todas las fases deben estar al 100% para validar y cerrar; los minutos y el uso real de mano de obra/maquinaria ya no bloquean este corte y quedan diferidos hasta definir el modelo de eficiencia. `OP-000003` ya conserva sus dos fases al 100% y esta lista para terminar despues de recargar. No hubo mutacion de datos, cambio de schema ni escritura en QA/Produccion.

# Actualizacion CHG-222 (2026-08-21)

En Local, **Almacenes > Movimientos** muestra las ordenes de Produccion terminadas con cantidad pendiente. El almacenista confirma almacen, cantidad, fecha y observaciones; Inventory valida la orden y el vinculo por ID, deriva articulo/unidad/costo, registra una entrada trazable y permite parciales sin exceder lo producido. No se recibieron ordenes automaticamente, no hubo migracion y QA/Produccion permanecen sin cambios.

# Actualizacion CHG-223 (2026-08-21)

El reinicio individual de Inventory Local ahora carga y valida explicitamente la base `127.0.0.1:5434/erclave_local`, Firebase Emulator y dependencias loopback antes de iniciar. Se corrigio el `500` causado por un proceso con health activo pero sin URL efectiva de base. El GET autenticado de almacenes devuelve `200`; no se modificaron datos ni QA/Produccion.

# Actualizacion CHG-224 (2026-08-21)

El repositorio queda preparado, pero no autorizado ni desplegado, para un candidato QA de cinco servicios: Admin, Produccion, Inventory, RH y Ventas. El pipeline construye/promueve las cinco imagenes por digest, entrega a Inventory la URL autoritativa de Produccion para recepciones y publica la URL de Ventas en el frontend sanitizado. QA vigente conserva cuatro servicios, version `4e9c6881dab61239f1abd5fff688019fdd697977` y revision documentada `20260805_0013`. Antes de ejecutar se requieren PR/SHA inmutable, identidad `erclave-sales-qa`, variables Sales y aprobaciones separadas de cada gate. No hubo escritura externa.

# Actualizacion CHG-225 (2026-08-21)

El corte CHG-224 ya esta fusionado en `main` con SHA inmutable `adb134f7ac8b33b4a842d07db10c9b5f88525f2f` y su validacion CI concluyo correctamente. En QA se creo la identidad dedicada `erclave-sales-qa@erclave.iam.gserviceaccount.com` sin llaves administradas por usuario; conserva solo `roles/cloudsql.client`, acceso al secreto `erclave-database-url-qa` y `roles/run.invoker` sobre Admin, RH, Produccion e Inventory. GitHub Actions ya contiene las variables no secretas `QA_SALES_RUNTIME_SERVICE_ACCOUNT` y `QA_SALES_API_URL`. No se construyo candidato, no se leyo el secreto, no se ejecuto migracion/configuracion de tenant, no se desplego Cloud Run, no se movio trafico y no se publico frontend.

# Actualizacion CHG-226 (2026-08-23)

El workflow gobernado `32621200718` promovio a QA el SHA inmutable `7aa5c674b605d8268b6bfe00e0812b6a300277cb`, ejecuto Alembic hasta `20260821_0023`, llevo a 100% las revisiones certificadas de cinco servicios y publico el frontend sanitizado en `https://erclave.web.app`. Despues del ajuste de configuracion CHG-226, el trafico actual de Admin apunta a `admin-service-qa-00021-669`; Inventory permanece en `inventory-service-qa-00006-ceb`, RH en `hr-service-qa-00006-xey`, Produccion en `production-service-qa-00011-naj` y Ventas en `sales-service-qa-00001-gez`. Todos conservan el mismo SHA certificado.

Durante UAT, crear y eliminar tenants devolvio `500`. Cloud Logging demostro `INSUFFICIENT_PERMISSION` del Admin SDK de Firebase en la identidad runtime `erclave-admin-qa@erclave.iam.gserviceaccount.com`; no fue un error operativo. Con autorizacion explicita se concedio solamente `roles/firebaseauth.admin` a esa cuenta. El tenant que se intento eliminar ya habia sido borrado en PostgreSQL antes del fallo de limpieza; la identidad Firebase asociada tampoco existia, comprobado con un job efimero sobre la misma imagen, eliminado al terminar. No se cargaron datos ni se modificaron otros tenants.

El primer onboarding posterior respondio `201`, pero no envio correo porque la clave web publica solo llegaba al frontend. Con autorizacion explicita se agrego `ERCLAVE_FIREBASE_WEB_API_KEY` al runtime Admin, se valido la revision `admin-service-qa-00021-669` por URL etiquetada y se promovio al 100% conservando imagen y SHA. El workflow ahora deriva siempre esa variable desde `QA_FIREBASE_API_KEY`; los siguientes onboardings solicitan el correo de restablecimiento a Firebase en vez de devolver solo un enlace manual.

En la rama CHG-226, aun pendiente de una nueva promocion gobernada, Admin traduce fallos Firebase a errores seguros y separa el resultado principal del seguimiento de invitacion/limpieza. El onboarding puede responder `invitation.delivery=pending` si el tenant ya persistio pero la invitacion fallo; el borrado responde `firebase_identity_cleanup.status=completed|pending` sin exponer correos internos ni presentar una limpieza secundaria como fracaso total.

# Actualizacion CHG-238 (2026-08-24)

En Local, Compras expone de forma continua el ciclo ya implementado por API: aprobar una requisicion abre la creacion de orden con la requisicion precargada; crear conserva la orden en borrador; emitir abre la recepcion con la orden seleccionada. Las tarjetas conservan accesos explicitos para retomar el siguiente paso. Formularios y comandos de proveedor, requisicion, orden y recepcion se muestran solo con su permiso puntual. No hubo migracion, cambio de contrato, escritura operativa ni modificacion en QA/Produccion.

# Actualizacion CHG-239 (2026-08-24)

En Local, Mantenimiento hace visible el tecnico asignado y conserva su seleccion al reasignar. Las ordenes elegibles enlazan directamente a **Solicitar refacciones** con el folio precargado; las solicitudes muestran sus partidas y estados. El diagnostico Local confirma que la base vigente no contiene un almacen `spare_parts`, por lo que la UI ahora ofrece abrir su alta en Inventario, preseleccionada correctamente y sujeta a `inventory.warehouse.create`, en vez de ocultar el recorrido. No se crearon maestros automaticamente, no hubo migracion ni cambios en QA/Produccion.

# Actualizacion CHG-240 (2026-08-24)

En Local, **Compras > Ordenes de compra** muestra primero el historial completo sin filtrar estatus y solo presenta el alta cuando hay requisiciones aprobadas pendientes de conversion. El diagnostico autenticado encontro dos OC emitidas (`OC_0001`, `OC_0002`) y ninguna requisicion elegible: `REQ_001`/`REQ_003` ya estan convertidas y `REQ_002` cancelada. **Reabastecimiento** queda visual y semánticamente separado como capacidad planeada; no contiene OC. No hubo escritura operativa, migracion ni cambios en QA/Produccion.
