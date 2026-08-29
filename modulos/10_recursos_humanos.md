# ERClave — Recursos Humanos

## Alcance MVP

Recursos Humanos administra áreas, puestos y expedientes de trabajadores. Un área se crea y edita sin puestos; un puesto sólo puede crearse dentro de un área activa y existente del mismo tenant. Cada trabajador mantiene un solo puesto vigente y un puesto puede agrupar cualquier cantidad de trabajadores.

Cada puesto registra nombre operativo, nombre visible en receta, minutos disponibles por trabajador, costo por hora para la empresa, estatus y la bandera **Interviene en producción**. La capacidad autoritativa se obtiene contando trabajadores activos asignados al puesto: `trabajadores_activos * minutos_por_trabajador`; el campo historico de cantidad configurada no sustituye expedientes reales. Producción sólo puede ofrecer puestos activos con esa bandera habilitada y deriva el costo por minuto como `costo_por_hora / 60`.

Areas y puestos son generales para toda la organizacion: Administracion, Ventas, Almacenes o cualquier otra funcion puede existir en RH. Crear un puesto nuevo deja **Interviene en produccion** desmarcado; solo debe activarse cuando ese puesto participa realmente en recetas y ordenes.

El propietario funcional y técnico es `hr-service`, con esquema PostgreSQL `hr`, contrato `contracts/api/hr-service.openapi.yaml` y microfrontend `recursos-humanos`. El módulo se contrata por tenant mediante el entitlement `hr`; si está inactivo o suspendido, el backend rechaza las operaciones aunque la ruta se invoque directamente.

Los permisos asignables son `hr.area.read/create/update` y `hr.position.read/create/update`. Firebase autentica la identidad, pero `admin-service` conserva la fuente de verdad de membresía, estado del tenant, entitlement y permisos efectivos.

Administración presenta estos seis permisos bajo la sección **Recursos Humanos** del catálogo y dentro de un grupo propio al asignarlos a roles. Activar el módulo no concede permisos automáticamente a roles existentes; entitlement y autorización del usuario siguen siendo controles independientes.

El seed de permisos reconcilia de forma idempotente los contratos: conserva los registros históricos y sus asignaciones, pero marca como inactivos `production.labor.*`, `production.labor_area.*` y `production.labor_role.*`. De esta forma dejan de mostrarse y de otorgar acceso sin borrar evidencia.

## Reglas

- No se crean áreas desde texto libre al capturar un puesto.
- El vínculo se conserva mediante `labor_area_id`, no mediante el nombre del área.
- Editar un área no crea, elimina ni duplica puestos.
- La bandera productiva controla visibilidad en recetas; el estatus inactivo siempre excluye al puesto.
- Áreas y puestos conservan formularios y permisos independientes.
- Cada lectura y escritura se filtra por `tenant_id`; el FK compuesto impide asociar un puesto con un área de otro tenant.
- Altas y modificaciones requieren `Idempotency-Key`; reutilizarla con otro payload se rechaza.
- Las mutaciones generan auditoría con actor, acción, entidad y estado anterior/posterior.
- El expediente exige número de empleado, nombre, primer apellido, CURP, RFC, NSS, fecha de ingreso y puesto; segundo apellido y contacto son opcionales.
- CURP, RFC y NSS se normalizan y validan por formato: CURP 18 caracteres, RFC de persona fisica 13 y NSS 11 digitos; NSS ademas valida su digito verificador. La validacion local no sustituye la certificacion de la autoridad.
- Los errores 422 identifican campo y causa sin repetir el valor personal rechazado en la respuesta.
- CURP, RFC, NSS y número de empleado son únicos por tenant. Los listados deben minimizar identificadores personales.
- El expediente no incluye en este corte nómina, salario, documentos adjuntos, datos médicos ni beneficiarios.
- Producción solo puede asignar trabajadores activos cuyo puesto y área estén activos y cuyo puesto tenga `intervenes_in_production=true`.
- El codigo de area y el numero de empleado se obtienen del catalogo de folios de Administracion cuando esta en modo administrado; el cambio de prefijo no modifica expedientes existentes.

## Integraciones

- Administración activa, inactiva o suspende `hr` por tenant y asigna permisos de RH a roles.
- Producción consulta puestos elegibles y `GET /v1/hr/production-capacity`; guarda snapshots de costo y compromete capacidad por fecha en su propio schema, sin escribir el catálogo de RH.
- Costos puede consumir el costo por hora como referencia, sin apropiarse del dato maestro.

## Operación segura

El schema base de RH nacio en `20260730_0010`; expedientes de trabajadores se agregaron en `20260817_0014` y la capacidad autoritativa forma parte del corte acumulado `20260818_0017`, hoy desplegado en Local y QA dentro de la cabeza `20260821_0023`. Siempre se ejecuta la cadena Alembic completa hasta la cabeza autorizada del ambiente, nunca una revision aislada como procedimiento operativo. Ninguna migracion, seed, activacion o dato de prueba se aplica a QA sin autorizacion explicita; consultar `docs/contexto/ESTADO_ACTUAL.md` para las cabezas vigentes de Local y QA.

## CHG-209: seleccion escalable

Áreas y puestos se consultan mediante búsqueda por código, nombre, puesto o área y se relacionan por ID estable. Estatus laboral permanece como una lista cerrada gobernada por el flujo.

## CHG-250: identidad y localizacion

- Las pantallas `Areas y puestos` y `Trabajadores` conservan la identidad de Recursos Humanos en su breadcrumb, aunque reutilicen componentes operativos compartidos con Produccion.
- Los estados API `active`, `inactive` y `terminated` se presentan como `Activo`, `Inactivo` y `Baja` en espanol, con sus equivalentes ingleses.
- La guia de configuracion, busqueda, etiquetas, resumen de capacidad y estatus de areas/puestos cambian con el idioma; nombres y descripciones capturados por el tenant permanecen como datos, sin traduccion automatica.
- La navegacion, contexto de sesion y acciones globales del shell exponen etiquetas y atributos accesibles en ambos idiomas.
