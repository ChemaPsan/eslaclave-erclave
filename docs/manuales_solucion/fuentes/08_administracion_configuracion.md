# Manual funcional de Administracion y Backoffice

- Audiencia: administradores del tenant y operadores internos autorizados de Backoffice
- Alcance por ambiente: catalogos, Roles y Backoffice en Local y QA; permisos operativos granulares CHG-236 solo en Local
- Ultima revision: 2026-08-24
- Capacidades cubiertas: catalogo de codigos por tipo documental; Roles y permisos; alta, suspension y eliminacion de tenants; owner e invitacion Firebase

## Proposito

Administracion controla configuraciones propias de cada tenant. El catalogo evita que cada operador invente codigos; Backoffice permite al equipo interno crear clientes, asignar su owner inicial y gobernar modulos contratados sin conceder permisos operativos por fuera de ERClave.

## Acceso

Consultar folios requiere `admin.setting.read`; editar requiere `admin.setting.update`. Reservar un folio desde otro modulo requiere el permiso de alta de ese documento.

### Roles y permisos

El administrador abre **Administracion > Roles > Ver/Editar permisos**. El catalogo agrupa capacidades por modulo y recurso; permite buscar, seleccionar y guardar un borrador explicito. `admin.role.read` permite consultar y `admin.role.permissions.manage` permite cambiar asignaciones.

En Local, las aprobaciones y cambios operativos ya aparecen como capacidades separadas. Por ejemplo, `production.order.complete` puede asignarse al gerente, `production.order_stage.complete` a responsables de etapa e `inventory.finished_goods_receipt.receive` al personal de almacen. No es necesario que el rol se llame de una forma especifica. Conceder iniciar no concede finalizar y crear un movimiento no concede recibir producto terminado.

Backoffice es una aplicacion interna. Solo admite correos incluidos en la lista administrativa del ambiente; ser owner de un tenant no concede acceso a Backoffice.

## Campos

| Campo | Efecto |
|---|---|
| Prefijo | Texto inicial, por ejemplo REC, OP, ART o COT. |
| Separador | Caracter entre prefijo y numero. |
| Siguiente numero | Proxima reserva; no puede disminuir. |
| Longitud | Digitos con ceros a la izquierda. |
| Administrado | ERClave reserva el siguiente codigo de forma atomica e idempotente. |
| Manual | El operador captura; el modulo valida formato y unicidad. |
| Estatus | Inactivo impide nuevas asignaciones. |

## Procedimiento

Abra **Administracion > Catalogos base > Folios y consecutivos**, localice el tipo, cambie los campos y guarde. Solo afecta altas nuevas; nunca renombra documentos existentes.

Ejemplo: `OP`, separador `-`, siguiente `25` y longitud `6` produce `OP-000025`.

## Catalogos iniciales

Productos/servicios, recetas, ordenes de produccion, maquinaria, almacenes, articulos, movimientos, areas, puestos, empleados, clientes, cotizaciones, pedidos y entregas.

## Validaciones frecuentes

- **No se puede retroceder:** elija un siguiente numero igual o mayor al actual.
- **Codigo manual obligatorio:** capturelo en el formulario origen.
- **Secuencia inactiva/no encontrada:** active o revise la configuracion.

Los reintentos con la misma clave devuelven el mismo resultado. Un folio reservado puede quedar sin documento si la operacion posterior falla; no se reutiliza silenciosamente.

## Alta de tenant desde Backoffice

1. Abra **Alta de tenant** y capture nombre comercial, slug, razon social, plan y datos del owner.
2. Capture la entidad fiscal, sucursal inicial y modulos contratados. Ventas requiere tambien RH y Produccion.
3. Guarde una sola vez. El resultado muestra tenant, owner, modulos e invitacion.
4. En QA, **Correo enviado** significa que Firebase acepto la solicitud de recuperacion para que el owner defina su contrasena. Revise spam o promociones. Si el correo no llega, el owner puede usar **Recuperar contrasena** desde el acceso de ERClave.

El alta crea la identidad Firebase para autenticacion, pero las membresias, roles, permisos y modulos los conserva Admin Service. Firebase no decide que puede hacer el usuario dentro del tenant.

## Suspender o eliminar un tenant

- **Suspender** bloquea el acceso sin destruir la configuracion administrativa.
- **Eliminar** retira configuracion, roles, membresias, modulos y datos administrativos del tenant. Es una accion destructiva y requiere confirmacion.
- La identidad Firebase solo se elimina cuando el usuario ya no pertenece a otro tenant. Nunca se debe eliminar una identidad compartida por coincidencia de nombre.
- Despues de eliminar, actualice la lista para confirmar que el tenant desaparecio. Una referencia visual anterior no demuestra que la operacion siga pendiente.

## Mensajes frecuentes de Backoffice

- **Correo no recibido:** revise spam y use **Recuperar contrasena** con el correo exacto del owner.
- **Modulo con dependencias:** active primero las autoridades indicadas; Ventas depende de RH y Produccion.
- **Acceso denegado:** confirme que se usa el correo interno autorizado, no solamente un owner ordinario.
- **Tenant suspendido:** rehabilitelo desde Backoffice antes de intentar ingresar como usuario del cliente.

## Cobertura

Catalogo, consumidores UI y ciclo de tenants de Backoffice implementados en Local y QA. Clientes API externos deben integrar la reserva central o usar compatibilidad manual autorizada. La reconciliacion automatica persistente de invitaciones o limpiezas Firebase pendientes permanece como mejora futura.
