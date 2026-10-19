# Manual funcional de Recursos Humanos

- Audiencia: responsables de RH, administradores de estructura y supervisores operativos
- Alcance por ambiente: Local y QA; las capacidades futuras se indican expresamente
- Última revisión: 2026-10-14 (folios CC-18 implementados sólo Local; sin promoción QA)
- Versión funcional de referencia: QA e57237f
- Capacidades cubiertas: áreas, puestos, trabajadores, capacidad productiva y elegibilidad para Producción, Mantenimiento y servicios de Ventas; preparación por División sólo Local

## Propósito

Recursos Humanos conserva la estructura organizacional y el expediente operativo mínimo de trabajadores. Otros módulos consultan proyecciones limitadas de elegibilidad y capacidad; no reciben datos personales innecesarios ni escriben las tablas de RH.

## Corregir errores de captura

**Disponible en Local y QA.** Si un dato es inválido, el formulario muestra una explicación junto al campo y un resumen desde el que puede ir al control correspondiente. Corrija el dato indicado y vuelva a guardar; la captura se conserva mientras el formulario permanezca abierto. En partidas, revise la fila señalada y seleccione nuevamente el registro del catálogo si corresponde.

Los errores de permisos, conexión o reglas generales se muestran como un aviso de la operación. Si no aparece un campo señalado, no cambie datos al azar: revise el aviso y conserve la referencia de correlación para soporte. Corregir un campo no elimina los avisos de los demás. Cerrar el formulario o recargar no garantiza conservar cambios sin guardar.


## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Áreas, puestos y trabajadores | Disponible | Disponible |
| Elegibilidad y capacidad para Producción | Disponible | Disponible |
| Elegibilidad para Mantenimiento | Disponible | Disponible |
| Elegibilidad para órdenes de servicio de Ventas | Disponible | Disponible |
| Reportes estándar descargables | Disponible | Disponible |
| Elegibilidad por División para validar/liberar/iniciar/reanudar producción manual | Implementado; validación Local | No promovido |
| Nómina, reclutamiento, ausencias y documentos | No disponible | No disponible |

## Mapa del módulo

- **Áreas y puestos:** estructura, capacidad por trabajador, costo por hora y banderas operativas.
- **Trabajadores:** expediente, puesto vigente y estado.
- **Portada:** reportes estándar de sólo lectura.

## Conceptos principales

| Concepto | Significado |
|---|---|
| Área | Agrupación organizacional general; no pertenece a Producción por existir. |
| Puesto | Función dentro de un área activa. |
| Puesto vigente | Única asignación operativa actual del trabajador. |
| Interviene en producción | Hace elegible el puesto para recetas, responsables y capacidad. |
| Interviene en mantenimiento | Hace elegible al trabajador para órdenes correctivas. |
| Elegible para ventas | Consulta de trabajadores activos con puesto y área vigentes para asignar órdenes de servicio. |
| Capacidad laboral | Trabajadores activos por minutos disponibles por trabajador y fecha. |

## Acceso y permisos

Las altas y cambios requieren permisos `hr.area.*`, `hr.position.*` y `hr.worker.*` según el recurso. El entitlement `hr` y la membresía activa se validan además del permiso. Activar RH no concede acceso a roles existentes.

## Crear áreas y puestos

1. Abra **RH > Áreas y puestos**.
2. Cree el área con código, nombre y estado.
3. Cree el puesto dentro de un área activa; no capture el área como texto libre.
4. Defina nombre visible, minutos disponibles por trabajador y costo por hora.
5. Active exclusivamente las banderas que correspondan a la operación real.

La capacidad autoritativa no usa una cantidad manual de plazas. Se calcula con trabajadores activos asignados al puesto. Un puesto inactivo nunca es elegible, aunque conserve una bandera operativa.

## Registrar un trabajador

1. Abra **Trabajadores** y cree el expediente.
2. Capture número de empleado, nombre, primer apellido, CURP, RFC, NSS y fecha de ingreso.
3. Seleccione un puesto vigente mediante el buscador; el área se deriva de esa relación.
4. Guarde y confirme estado activo.

Para expedientes nuevos, CURP requiere 18 caracteres, RFC de persona física 13 y NSS 11 dígitos con verificador válido. Los errores identifican el campo sin repetir el dato personal rechazado. Número de empleado, CURP, RFC y NSS son únicos por tenant.

## Preparar personal para Producción

1. Active el área, puesto y trabajador.
2. Marque **Interviene en producción** en el puesto.
3. Confirme minutos disponibles por trabajador y costo por hora.
4. Producción consultará la capacidad diaria y comprometerá minutos en su propio esquema.

Ser responsable general de una orden no aporta capacidad a otro puesto. La receta debe pedir el puesto exacto y existir al menos un trabajador activo en él.

## Preparar personal para Mantenimiento

1. Cree o active un área y puesto de mantenimiento.
2. Marque **Interviene en mantenimiento**.
3. Asigne trabajadores activos al puesto.
4. Mantenimiento validará nuevamente la elegibilidad al asignar, iniciar y reanudar.

## Preparar responsables de servicio

Ventas consulta una proyección mínima para asignar órdenes de servicio, tanto en Local como en QA. El trabajador debe permanecer activo, con puesto y área vigentes. Ventas conserva una referencia y el nombre registrado al asignar; no copia CURP, RFC, NSS ni contacto.

Producción, Mantenimiento y las órdenes de servicio de Ventas vuelven a comprobar la elegibilidad al iniciar o reanudar. Si RH inactiva al trabajador, su puesto o su área, el responsable operativo debe seleccionar a otra persona elegible o solicitar a RH la corrección correspondiente. Después debe reintentar la misma transición. Haber asignado al trabajador anteriormente no permite saltar esta revisión.

## Estados y efectos

| Estado | Efecto |
|---|---|
| Activo | Puede ser elegible si puesto, área y bandera también son válidos. |
| Inactivo | Conserva historia y deja de aparecer en nuevas asignaciones. |
| Baja | Ya no participa en capacidad o nuevas operaciones. |

Inactivar un maestro no borra snapshots históricos. Las operaciones nuevas deben resolver otro responsable; las ya registradas conservan la identidad visible que tenían.

## Mensajes frecuentes

- **No hay responsables elegibles:** revise trabajador, puesto, área, estado y bandera.
- **El puesto no aparece en receta:** active **Interviene en producción** sólo si corresponde.
- **Capacidad laboral insuficiente:** agregue trabajadores activos o amplíe el horizonte; no cambie evidencia histórica.
- **El NSS debe contener exactamente 11 dígitos:** valide el documento fuente y su verificador.
- **Identificador duplicado:** localice el expediente existente del mismo tenant.
- **Trabajador ya no elegible:** asigne otro responsable o regularice su estructura antes de iniciar.

## Integraciones y privacidad

Administración gobierna folios, permisos y entitlement. Producción consume capacidad y elegibilidad; Mantenimiento consume elegibilidad técnica; Ventas consume una proyección de responsables de servicio. Cada consumidor guarda sólo referencia y snapshot necesarios. Los listados de RH minimizan identificadores personales.

## Reportes estándar de portada

La portada ofrece reportes descargables de áreas y puestos, trabajadores, capacidad productiva configurada y elegibilidad por propósito. La capacidad muestra recursos, minutos configurados y plantilla activa de RH; no representa fechas ni compromisos de Producción. Abra la tarjeta, escriba para encontrar estatus, elegibilidad o propósito cuando aplique y pulse **Generar**.

Los archivos excluyen CURP, RFC, NSS, teléfono, correo y domicilio. Se requieren `hr.position.read` o `hr.worker.read`, según el reporte. La descarga está disponible en Local y QA; no crea ni modifica expedientes.

## Limitaciones vigentes

No incluye nómina, salario, reclutamiento, expedientes documentales, datos médicos, beneficiarios, calendarios, turnos, festivos, vacaciones o ausencias. La capacidad actual parte de minutos por trabajador y calendario base lunes-viernes del consumidor productivo.

## Soporte y protección de datos

Para soporte comparta número de empleado o nombre visible, puesto, área, estado y correlación. No copie CURP, RFC, NSS, teléfono o correo en tickets salvo canal y necesidad expresamente autorizados.


## Demoras de comunicación en Local

Mejora disponible solo en Local, pendiente de QA: la espera de cada petición incluye la descarga de la respuesta. Un fallo conserva la captura mientras permanezca abierto el formulario; no realiza un nuevo envío automáticamente. Consulte el estado del registro antes de repetir una operación cuyo resultado no se confirmó.

## Preparar puestos y trabajadores por División

Disponible sólo en Local. Estas asignaciones preparan la separación; todavía no cambian recetas, órdenes, disponibilidad comprometida o nómina. El maestro del puesto y el expediente siguen siendo únicos.

En Recursos Humanos → Áreas y puestos, abra el área y pulse **Asignación por División** en el puesto. En Trabajadores, use la misma acción en la tarjeta del expediente. Se requiere lectura del catálogo correspondiente; guardar necesita el permiso de actualización de puesto o trabajador.

1. Busque y seleccione una División autorizada por nombre o código.
2. Para un puesto, revise el **Costo por hora en esta División**: tarifa de costeo para la empresa, no salario. Admite cero y hasta seis decimales. Compruebe la **Moneda base de la Sociedad**, derivada de la División y de sólo lectura; marque **Confirmo este importe en la moneda indicada para operaciones futuras** antes de guardar la asignación activa. La casilla no viene seleccionada. Un importe propuesto o histórico no acredita moneda confirmada. Cambiar la tarifa general después no actualiza esta asignación.
3. Puede elegir un centro activo de esa División o dejar **Sin centro**. Preparar el sistema no vuelve obligatorio el centro ni activa Contabilidad. Cambiar División limpia la selección anterior.
4. Para un trabajador, el puesto vigente y su área deben estar activos y el puesto debe tener una asignación activa en esa División. No capture de nuevo el puesto ni datos personales en este formulario.
5. Guarde y revise **Asignaciones existentes**. Puede habilitar el mismo maestro en varias Divisiones sin duplicarlo.
6. Para retirar disponibilidad, abra la asignación y cambie su estado a inactiva. Se conservan el centro, tarifa, moneda y puesto históricos; desactivar no exige confirmar de nuevo la moneda. Reactivar revalida las referencias y exige confirmación explícita de tarifa en moneda vigente.

Si el trabajador cambia de puesto, sus asignaciones anteriores dejan de dar elegibilidad para el nuevo puesto: revise la asignación de ese puesto y vuelva a guardar la del trabajador para confirmarla. Dar de baja al trabajador o inactivar el área/puesto también lo excluye de la consulta elegible. Las banderas **Interviene en producción/mantenimiento** siguen siendo necesarias para esos usos.

Un rechazo conserva la captura y señala el costo por hora cuando es corregible. Conflicto de revisión: vuelva a abrir la asignación para revisar la versión guardada. Puesto no disponible: revise su estado y asignación en esa División. Área inactiva: revise su estado en RH. Ninguno de estos cambios crea por sí solo disponibilidad adicional en órdenes ni permite sumar dos veces la capacidad de una persona habilitada en varias Divisiones.

## Consultar capacidad nominal por División

En **Recursos Humanos → Áreas y puestos → Ver área → Asignación por División** de un puesto, seleccione la División y pulse **Consultar capacidad de esta División**. La consulta requiere permiso de lectura de puestos y alcance sobre esa División. Muestra trabajadores elegibles y capacidad declarada de la División, usando las tarifas confirmadas vigentes.

Es capacidad nominal: no descuenta compromisos de Producción ni reserva tiempo. Una persona habilitada en varias Divisiones sigue siendo la misma persona; no sume las consultas para prometer más horas disponibles. Las órdenes manuales Local ya combinan esos IDs con compromisos globales por persona/día dentro de Producción. Una persona habilitada en dos Divisiones no aporta dos jornadas. Al iniciar o reanudar, Producción vuelve a verificar los responsables, trabajadores comprometidos y sus puestos vigentes. La ocupación histórica sin persona identificada exige revisión y puede bloquear el solapamiento; RH no inventa asignaciones ni libera compromisos productivos.

Una tarifa histórica sin moneda permanece sin confirmar y no se considera un costo vigente por aparecer en la ficha. Si cambia la Sociedad o su moneda, revise el importe y confirme de nuevo antes de utilizarla. No convierta importes anteriores por inferencia. El rechazo de moneda, alcance o elegibilidad conserva captura y requiere corregir el dato o renovar el contexto autorizado, no duplicar el puesto.

## Documentos relacionados

[Registro de esta fuente y su Word](../REGISTRO.md) · [Ficha funcional](../../../modulos/10_recursos_humanos.md) · [Estado por ambiente](../../contexto/ESTADO_ACTUAL.md) · [Control de integración por submódulo](../../contexto/CONTROL_CONTABLE.md).

## Folio de puesto · sólo Local (CC-18)

Al crear un puesto, Administración asigna su código visible. Si la secuencia `hr.position` está en modo manual, capture el código solicitado; RH conserva el mismo código. En modo administrado, el sistema lo asigna al guardar. Los puestos anteriores conservan su identidad y pueden aparecer sin código nuevo. El código queda visible en la consulta de puestos y en las proyecciones de elegibilidad de trabajadores. Reintentar el alta con la misma clave de operación recupera el mismo folio.
