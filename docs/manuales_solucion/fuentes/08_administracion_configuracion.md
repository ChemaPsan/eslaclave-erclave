# Manual funcional de Administración y Backoffice

- Audiencia: administradores del tenant y operadores internos autorizados
- Alcance por ambiente: Local y QA
- Última revisión: 2026-09-02
- Capacidades cubiertas: contexto de sesión, organización, usuarios, roles, permisos, módulos, unidades, folios, catálogos, plantilla documental y ciclo de tenants en Backoffice

## Propósito

Administración gobierna quién puede entrar, qué módulos tiene contratados y qué configuración comparte cada tenant. Firebase autentica la identidad; Admin Service decide membresía, tenant activo, permisos, entitlements y alcance.

Backoffice es una aplicación interna separada para alta, configuración, suspensión y eliminación de tenants. Ser owner de una empresa no concede acceso al Backoffice.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Usuarios, roles y permisos | Disponible | Disponible |
| Entitlements y módulos activos | Disponible | Disponible |
| Unidades, folios y catálogos comerciales | Disponible | Disponible |
| Entidades legales, sucursales y perfil organizacional | Disponible | Disponible |
| Alta, edición, suspensión y eliminación de tenants | Disponible | Disponible |
| Onboarding automático por checkout/pago | No disponible | No disponible |

## Mapa de Administración

- **Organización:** perfil, entidades legales y sucursales.
- **Usuarios:** invitaciones, estado y membresía.
- **Roles:** definición y matriz de permisos.
- **Módulos activos:** entitlements contratados por tenant.
- **Catálogos base:** unidades, folios, monedas, condiciones, impuestos y otros catálogos implementados.
- **Plantilla documental:** configuración compartida de encabezado, pie y marca.
- **Backoffice:** operación interna sobre tenants.

Administración es la excepción a la portada de reportes: su primera vista es un centro de configuración, no un centro operativo.

## Contexto de sesión y tenant

Al iniciar sesión, ERClave obtiene los tenants donde el usuario tiene membresía. El selector de tenant cambia el contexto completo y obliga a recargar permisos, módulos y datos. El header de tenant es un selector, no una autorización: el backend comprueba que la identidad pertenezca al tenant solicitado.

Un módulo visible requiere tres condiciones: tenant activo, entitlement activo y permiso efectivo. Activar el módulo no concede permisos a roles existentes.

## Usuarios

1. Abra **Administración > Usuarios**.
2. Invite con correo, rol y alcance permitidos.
3. El usuario establece su contraseña mediante Firebase; nunca se envía una contraseña por correo.
4. Actualice rol, sucursal o estado cuando sea necesario.
5. Use **Deshabilitar** para bloquear acceso conservando evidencia o **Eliminar** cuando corresponda retirar la membresía.

La identidad Firebase sólo se elimina si ya no está compartida con otro tenant. Una respuesta de invitación o limpieza pendiente debe conservarse; el reintento automático durable permanece como mejora futura.

## Roles y matriz de permisos

1. Abra **Roles** y cree o seleccione un rol.
2. Use **Ver/Editar permisos**.
3. Busque por módulo, recurso o acción.
4. Seleccione exclusivamente las capacidades necesarias y guarde el borrador explícito.

`admin.role.read` permite consultar y `admin.role.permissions.manage` permite reemplazar asignaciones. El sistema rechaza permisos inactivos o grants prohibidos. Las transiciones críticas son independientes: iniciar, completar, cancelar, aprobar, recibir o conciliar no se heredan unas de otras por el nombre del rol.

## Módulos y dependencias

Backoffice y Administración muestran Admin, Producción, Inventario, RH, Ventas, Compras y Mantenimiento como servicios reales del release QA vigente.

- Producción usa RH e Inventario para capacidad y materiales.
- Ventas usa Producción, RH e Inventario según la partida.
- Mantenimiento requiere RH e Inventario; Producción es integración opcional.
- Compras puede activarse sin Inventario para servicios en el corte Local; las partidas físicas sí requieren Inventario.

No active una dependencia sólo para superar una pantalla: confirme el modelo operativo del tenant y asigne permisos coherentes.

## Unidades de medida

Las unidades tienen código estable, nombre ES/EN, categoría, factor y estado. Los campos operativos guardan el código, no texto libre. La unidad `E48` representa **Unidad de servicio / Service unit** en el corte Local vigente.

Cambiar o inactivar una unidad afecta nuevas capturas, no reescribe documentos históricos. Inventario protege la unidad de artículos con movimientos o reservas.

## Folios y consecutivos

| Campo | Efecto |
|---|---|
| Prefijo | Texto inicial del folio. |
| Separador | Carácter entre prefijo y número. |
| Siguiente número | Próxima reserva; no puede disminuir. |
| Longitud | Dígitos con ceros a la izquierda. |
| Administrado | ERClave reserva de forma atómica e idempotente. |
| Manual | El operador captura y el módulo valida formato/unicidad. |
| Estado | Inactivo impide nuevas asignaciones. |

Abra **Catálogos base > Folios y consecutivos**, edite y guarde. El cambio sólo afecta altas nuevas. El corte Local incluye folio `sales.service_order` para órdenes de servicio.

## Alta de tenant desde Backoffice

1. Ingrese con un correo interno permitido.
2. Capture nombre comercial, slug, razón social, plan, datos del owner, entidad fiscal y sucursal inicial.
3. Seleccione módulos contratados y revise dependencias.
4. Confirme una sola vez. El alta crea tenant, owner, rol, membresía, entitlements y perfil organizacional.
5. En QA, confirme que Firebase aceptó el correo para que el owner establezca su contraseña; revise spam y recuperación de contraseña.
6. Acceda como owner y confirme tenant, módulos y permisos sin conservar tokens o contraseñas.

## Suspender, reactivar o eliminar

- **Suspender:** bloquea el acceso y conserva configuración.
- **Reactivar:** devuelve acceso cuando el estado y la suscripción lo permiten.
- **Eliminar:** retira configuración administrativa, roles, membresías y entitlements; exige confirmación destructiva.

Después de una eliminación recargue la lista y confirme que el tenant ya no aparezca. La limpieza de datos propiedad de otros servicios debe respetar su ownership y no se sustituye por borrar filas desde Admin.

## Mensajes frecuentes

- **Acceso denegado a Backoffice:** use un correo interno allowlisted; owner no es suficiente.
- **Módulo con dependencias:** revise autoridades requeridas para el flujo real.
- **Permiso no efectivo:** confirme tenant activo, rol, entitlement y sesión renovada.
- **No se puede retroceder la secuencia:** conserve un siguiente número igual o mayor.
- **Secuencia inactiva o no encontrada:** active o configure el tipo documental.
- **Correo no recibido:** revise spam y use recuperación con el correo exacto.
- **Tenant suspendido:** reactívelo antes de probar acceso operativo.

## Limitaciones vigentes

No existe checkout/billing operativo, provisioning service-to-service endurecido, reintento durable de invitaciones/limpiezas Firebase ni sincronización automática con clientes API externos. Gastos, Costos, Reportes avanzados y Contabilidad siguen definidos pero no implementados como servicios operativos.

## Soporte y seguridad

Conserve tenant visible, correo, módulo, rol, acción y referencia de correlación. Nunca comparta tokens, enlaces vigentes de invitación o contraseñas. Para pruebas use sólo datos ficticios y el tenant autorizado para el ambiente.
