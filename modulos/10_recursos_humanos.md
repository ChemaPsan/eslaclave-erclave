# ERClave — Recursos Humanos

## Alcance MVP

Recursos Humanos administra dos catálogos independientes: áreas y puestos. Un área se crea y edita sin puestos; un puesto sólo puede crearse dentro de un área activa y existente del mismo tenant.

Cada puesto registra nombre operativo, nombre visible en receta, cantidad de recursos, minutos disponibles por recurso, costo por hora para la empresa, estatus y la bandera **Interviene en producción**. Producción sólo puede ofrecer en recetas puestos activos con esa bandera habilitada; el costo por minuto se deriva como `costo_por_hora / 60`.

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
- No se almacenan nómina, expedientes ni datos personales en este alcance.

## Integraciones

- Administración activa, inactiva o suspende `hr` por tenant y asigna permisos de RH a roles.
- Producción consulta puestos elegibles (`production_only=true`) y guarda snapshots de costo/capacidad en la receta; no escribe el catálogo de RH.
- Costos puede consumir el costo por hora como referencia, sin apropiarse del dato maestro.

## Operación segura

La migración `20260730_0010` y el seed de permisos deben ejecutarse primero en PostgreSQL local aislado. Ninguna migración, seed, activación o dato de prueba se aplica a QA sin autorización explícita.
