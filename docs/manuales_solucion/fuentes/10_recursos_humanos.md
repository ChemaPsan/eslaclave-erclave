# Manual funcional de Recursos Humanos

- Audiencia: responsables de RH, administradores de estructura y supervisores operativos
- Alcance por ambiente: Local y QA
- Última revisión: 2026-09-06
- Capacidades cubiertas: áreas, puestos, trabajadores, capacidad productiva y elegibilidad para Producción, Mantenimiento y servicios de Ventas

## Propósito

Recursos Humanos conserva la estructura organizacional y el expediente operativo mínimo de trabajadores. Otros módulos consultan proyecciones limitadas de elegibilidad y capacidad; no reciben datos personales innecesarios ni escriben las tablas de RH.

## Disponibilidad por ambiente

| Capacidad | Local | QA |
|---|---|---|
| Áreas, puestos y trabajadores | Disponible | Disponible |
| Elegibilidad y capacidad para Producción | Disponible | Disponible |
| Elegibilidad para Mantenimiento | Disponible | Disponible |
| Elegibilidad para órdenes de servicio de Ventas | Disponible | Servicio consumidor sólo Local |
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
| Elegible para ventas | Proyección mínima usada por órdenes de servicio en el corte Local. |
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
4. Mantenimiento validará nuevamente la elegibilidad al asignar e iniciar.

## Preparar responsables de servicio

En el corte Local, Ventas consulta una proyección mínima para asignar órdenes de servicio. El trabajador debe permanecer activo, con puesto y área vigentes. Sales conserva ID y nombre snapshot; no copia CURP, RFC, NSS ni contacto.

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

## Reportes estándar de portada (Local)

La portada ofrece reportes descargables de áreas y puestos, trabajadores, capacidad productiva configurada y elegibilidad por propósito. La capacidad muestra recursos, minutos configurados y plantilla activa de RH; no representa fechas ni compromisos de Producción. Abra la tarjeta, escriba para encontrar estatus, elegibilidad o propósito cuando aplique y pulse **Generar**.

Los archivos excluyen CURP, RFC, NSS, teléfono, correo y domicilio. Se requieren `hr.position.read` o `hr.worker.read`. La capacidad de descarga está disponible sólo en Local en este corte.

## Limitaciones vigentes

No incluye nómina, salario, reclutamiento, expedientes documentales, datos médicos, beneficiarios, calendarios, turnos, festivos, vacaciones o ausencias. La capacidad actual parte de minutos por trabajador y calendario base lunes-viernes del consumidor productivo.

## Soporte y protección de datos

Para soporte comparta número de empleado o nombre visible, puesto, área, estado y correlación. No copie CURP, RFC, NSS, teléfono o correo en tickets salvo canal y necesidad expresamente autorizados.
