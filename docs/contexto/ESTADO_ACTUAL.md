# Estado actual de ERClave

Ultima actualizacion: 2026-08-12.

## Ambiente local

- El arranque canonico Local aislado opera mediante `backend/scripts/start_local.ps1`: PostgreSQL `erclave_local`, Firebase Auth Emulator `demo-erclave`, frontend y APIs locales.
- Una ejecucion local conectada a cualquier recurso QA debe identificarse como `local conectado a QA` y requiere autorizacion explicita.

- Frontend estatico local esperado en `http://127.0.0.1:4173`.
- Admin API local esperada en `http://127.0.0.1:8000` contra PostgreSQL local. La conexion local a QA usada en una validacion autorizada anterior es evidencia historica, no el modo local canonico.
- Production API local esperada en `http://127.0.0.1:8002`.
- Inventory API local esperada en `http://127.0.0.1:8004`.
- PostgreSQL portatil aislado para Inventory escucha en `127.0.0.1:5434`, base `erclave_local`.
- Firebase Auth Emulator escucha en `127.0.0.1:9099` y su UI en `127.0.0.1:4000`; el usuario local `admin.qa@erclave.local` resuelve el tenant demo sin consumir Firebase QA.
- Firebase autentica; `admin-service /v1/session/context` resuelve tenant, membresia, modulos, permisos y alcance.

## Cortes funcionales relevantes

### Administracion y permisos

- El editor de permisos de roles trabaja con borrador explicito, busqueda, filtros, agrupacion por modulo/recurso, seleccion masiva visible y resumen de cambios; no incluye plantillas ni presets.
- Los nombres tecnicos se conservan como identificadores de policy, pero la interfaz usa nombres y descripciones ES/EN mantenidos en `admin.permissions`.
- El catalogo remoto requiere tenant y `admin.role.read`; solo expone permisos `tenant` asignables y marca disponibilidad segun el entitlement del modulo.
- Modificar permisos exige `admin.role.permissions.manage`, `expected_revision` e `Idempotency-Key`. El backend aplica diferencias, conserva scopes heredados sin permitir crear nuevos scopes arbitrarios y audita altas/bajas.
- Los grants historicos internos pueden conservarse como relacion para no perder trazabilidad, pero ya no ingresan a `session/context` ni producen autorizacion efectiva. El owner conserva un piso administrativo y no puede inactivarse.
- El payload anterior `permission_ids + scope` permanece compatible y esta deprecado; la interfaz nueva usa `assignments + expected_revision`.
- Mientras un ambiente no tenga `admin.role.permissions.manage`, Roles permite abrir `Ver permisos` en modo de solo lectura y explica por que la edicion permanece bloqueada; no aplica fallback de escritura inseguro.
- La revision vigente de Cloud SQL QA es `20260805_0013`; incluye metadata de permisos, revision por rol, comandos idempotentes, Inventory, RH y referencias externas de areas en Produccion. La promocion gobernada del 2026-08-12 repitio Alembic y la configuracion estructural de forma idempotente sin cargar datos funcionales.

### Produccion

- Productos y servicios se presentan como catalogo maestro antes de consultar ordenes relacionadas.
- En Local y QA, Productos/Servicios, Recetas/versiones, Maquinaria, validacion observada, Ordenes y etapas persisten mediante `production-service`; la UI recarga PostgreSQL y no degrada silenciosamente a `localStorage` cuando `apiMode=api`.
- La version vigente aprobada y el borrador/pendiente mas reciente se distinguen. Las ordenes siempre usan `current_version_id`, guardan snapshots de receta y disponibilidad/costo observados y conservan sus etapas aunque la receta cambie.
- El editor API de Recetas consume materiales activos con `use_in_recipe=true` desde Inventory y puestos productivos/areas activas desde HR. No carga seeds; las etapas nuevas conservan ID externo y nombre snapshot del area mediante la revision Local `20260805_0013`.
- El editor de Recetas separa materiales, mano de obra y maquinaria. Los materiales usan la unidad base de Almacenes; mano de obra y maquinaria se capturan como horas-persona y horas-maquina, con conversion transparente a minutos para el contrato vigente.
- Las horas-persona y horas-maquina aceptan cualquier fraccion decimal, sin saltos obligatorios de 15 minutos; la UI aclara que `0.5 h = 30 min`.
- El buscador de producto/servicio en Recetas presenta nombre y codigo comercial; los IDs tecnicos `prs_*` permanecen ocultos y se usan solo para la relacion interna.
- Las listas, selectores, mensajes y documentos de Recetas ocultan IDs `rec_*`; muestran nombre, codigo del producto y version mientras conservan el ID en relaciones y atributos internos.
- El alta y edicion de Maquinaria consulta areas activas de `hr-service`; no permite capturar areas libres y dirige a Areas y puestos cuando el catalogo esta vacio.
- Las transiciones de orden y etapa se validan en backend, son idempotentes y auditadas. Una etapa terminal no vuelve a pendiente; completar todas las etapas lleva la orden a validacion y el cierre es explicito.
- La validacion de recursos y costos es backend y se repite al liberar. Es una fotografia observada, no una reserva: todavia no consume ni aparta Inventario.
- Areas y puestos pertenecen al modulo independiente Recursos Humanos, con microfrontend y `hr-service` propios.
- El entitlement `hr` controla la disponibilidad por tenant; alta y edicion usan permisos separados `hr.area.*` y `hr.position.*`.
- El esquema `hr` incorpora aislamiento por tenant, FK compuesto area-puesto, idempotencia y auditoria. El 2026-07-31 se creo vacio en QA; posteriormente CHG-182 desplego `hr-service` y activo el entitlement estructural sin cargar areas ni puestos.
- PostgreSQL QA conserva seis permisos `hr.*` activos y los permisos `production.labor.*` heredados inactivos. Los catalogos `hr.labor_areas` y `hr.labor_roles` quedaron en cero registros.
- Produccion consume areas y puestos desde `hr-service`; no los persiste ni escribe su schema.
- Las recetas en modo API ya no usan el catalogo fijo de materiales: consumen articulos activos marcados `use_in_recipe` y balances reales de Almacenes.

### Almacenes e inventarios

- `inventory-service` es propietario de almacenes, articulos, movimientos, balances y Kardex.
- En modo API, el formulario de Movimientos persiste exclusivamente mediante `inventory-service`; al completar el comando invalida y recarga movimientos y balances. `localStorage` queda solo como fallback del modo maqueta y nunca representa un movimiento remoto registrado.
- El submodulo visible `Inventario` conserva el identificador tecnico `existencias`.
- Inventario consume balances enriquecidos con busqueda, filtros, orden y paginacion server-side.
- La vista usa container queries: colapsa el flujo por defecto, transforma la tabla en tarjetas cuando el panel central se estrecha y mueve Alertas debajo del contenido en viewports intermedios.
- Los movimientos registrados y no reversados son la fuente de verdad.
- `available_quantity = on_hand_quantity` y `reserved_quantity = 0` hasta implementar Reservas.
- La bandera `inventory.items.use_in_recipe` pertenece a la migracion `20260730_0009`; la cabeza acumulada `20260730_0011` fue aplicada en QA el 2026-07-31 con autorizacion explicita. Los catalogos `inventory.warehouses`, `inventory.items` e `inventory.movements` permanecieron en cero registros.
- Inventario muestra con saldo cero los articulos sin movimientos que tengan almacen sugerido.
- La validacion local cubrio 10,000 articulos y 10,000 movimientos; consultar `docs/operaciones/validacion_volumen_inventario_local.md`.

### Interfaz transversal

- El shell, los modulos activos, los catalogos, formularios y modales comparten reglas responsive basadas en el ancho real de su contenedor.
- La guia descriptiva conserva el patron compartido de riel vertical izquierdo y compresion; solo pasa a una columna en anchos estrechos o mediante una excepcion explicita de pantalla.
- En anchos intermedios las colecciones reducen columnas; en anchos estrechos formularios y acciones se apilan sin ocultar su significado.
- El backoffice transforma sus filas de tenants y consumo en tarjetas etiquetadas cuando su panel se estrecha.
- La navegacion movil conserva los submodulos activos, foco visible, salto al contenido y anuncios accesibles de notificaciones.
- `npm.cmd run validate:responsive` protege los contenedores, puntos de accesibilidad y referencias documentales obligatorias.

## Calidad

- La fuente normativa de ambientes es `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`; la skill `$erclave-environment-boundaries` aplica su preflight.

- La fuente de verdad del resultado automatizado es la ultima ejecucion de `npm.cmd run verify`.
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
