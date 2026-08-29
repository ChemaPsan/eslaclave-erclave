# ERClave - Modulo de Produccion

## Autorizacion operativa Local

Las autoridades de liberar, iniciar, pausar, reanudar, enviar a validacion, finalizar y cancelar una orden son permisos independientes. Actualizar avance no concede terminar una etapa. La matriz contractual vive en `docs/arquitectura/matriz_autorizacion_operativa.md`. La orden nueva vigente nace liberada, por lo que su alta exige `production.order.release`; el borrador previo a liberacion no esta implementado.

## 1. Objetivo

El modulo de Produccion es el primer modulo funcional de ERClave. Su objetivo es permitir que una empresa administre productos y servicios, configure recetas operativas, valide recursos, libere ordenes y controle el avance productivo con costos estimados y reales.

El modulo debe responder:

> Que producto o servicio se gestionara, que receta lo soporta, que recursos requiere, cuanto cuesta, si puede liberarse y en que estado se encuentra cada orden.

El enfoque del modulo debe ser agnostico a la industria. No debe asumir procesos textiles, alimenticios, manufactureros o de servicios especificos. Cada empresa debe poder definir sus propias etapas operativas.

---

## 2. Alcance por ambiente

El corte desplegado en QA persiste productos/servicios, recetas/versiones, maquinaria, ordenes y etapas. El codigo Local posterior agrega validacion autoritativa, reservas y consumo de materiales, capacidad comprometida y costo real; estas capacidades no se consideran disponibles en QA hasta su promocion gobernada.

El alcance funcional contempla:

- catalogo maestro de productos y servicios;
- alta, busqueda, edicion y cambio de estatus de productos/servicios;
- ficha maestra con SKU, unidad, categoria, responsable, precio objetivo, margen esperado y costo estandar;
- recetas conectadas al catalogo de productos/servicios;
- buscador de producto/servicio dentro del formulario de receta;
- recetas con recursos, version, etapas genericas, estado de aprobacion y motivo de cambio;
- validacion de recursos antes de liberar una orden;
- separacion entre almacenes, mano de obra y maquinaria;
- consulta de areas, puestos productivos y trabajadores elegibles gobernados por RH;
- catalogo de maquinaria con capacidad, costo y estatus;
- ordenes de produccion con estatus seleccionable desde catalogo;
- ordenes de produccion con snapshot de receta/version al momento de liberacion;
- costo planeado, costo real y variacion;
- seguimiento por etapas operativas genericas;
- guias visuales de flujo por apartado, colapsables y accesibles desde un riel lateral;
- trazabilidad funcional documentada en `TRAZABILIDAD.md`.

---

## 3. Flujo operativo general

El flujo base del modulo es:

1. Crear o editar producto/servicio en el catalogo maestro.
2. Crear o editar receta asociada al producto/servicio.
3. Configurar recursos requeridos: materiales, mano de obra y maquinaria.
4. Definir etapas operativas genericas de la receta.
5. Calcular costo estandar.
6. Aprobar receta vigente.
7. Validar recursos disponibles para una cantidad solicitada.
8. Liberar orden de produccion si no existen bloqueos.
9. Dar seguimiento a estatus general de la orden.
10. Dar seguimiento por etapas operativas.
11. Comparar costo planeado contra costo real.
12. Cerrar, cancelar o validar la orden segun corresponda.

---

## 4. Apartados del modulo

### 4.1 Productos y servicios

Este apartado administra el catalogo maestro. No debe construir recetas desde aqui; solo debe permitir ir a la receta correspondiente.

Funciones actuales:

- crear nuevo producto o servicio;
- buscar productos o servicios existentes;
- editar ficha maestra;
- cambiar estatus;
- consultar receta vigente;
- consultar historial de ordenes;
- ver costo estandar, precio objetivo y margen esperado;
- generar receta si no existe;
- editar receta si ya existe una receta vigente.

Campos principales:

| Campo | Descripcion |
|---|---|
| ID | Identificador interno del catalogo. |
| SKU / codigo interno | Clave operativa del producto o servicio. |
| Tipo | Producto o Servicio. |
| Nombre | Nombre comercial u operativo. |
| Unidad base | Codigo activo seleccionado del catalogo de unidades de Administracion. |
| Categoria | Agrupador del catalogo. |
| Centro de costos | Centro donde se acumula el costo. |
| Responsable | Area o persona dueña de la ficha. |
| Precio objetivo | Precio esperado o referencia comercial. |
| Margen esperado | Margen objetivo para control gerencial. |
| Costo estandar | Costo calculado desde la receta vigente. |
| Estatus | Activo, Inactivo o En espera de aprobacion. |

Regla clave:

- Si el producto/servicio ya tiene receta vigente, la accion debe ser **Editar receta**.
- Si no tiene receta vigente, la accion debe ser **Generar receta**.
- La vista inicial debe priorizar el catalogo y la ficha maestra; no debe incrustar el detalle de ordenes dentro de cada tarjeta.
- Cada producto/servicio debe ofrecer **Ver ordenes** para abrir el apartado de Ordenes filtrado por ese registro, con opcion de volver al catalogo o quitar el filtro.

---

### 4.2 Recetas

La receta define como se produce un producto o como se ejecuta un servicio.

Cada receta cuenta con un **codigo de receta** distinto del codigo comercial del producto. En modo administrado, Administracion asigna el consecutivo; en modo manual, el operador captura el codigo permitido por la politica del tenant. El codigo se muestra en listas y selectores para identificar la receta sin exponer su ID tecnico.

Funciones actuales:

- crear receta desde el apartado de Recetas;
- seleccionar producto/servicio desde catalogo buscable;
- mostrar en el buscador el nombre seguido del codigo de producto, manteniendo el ID tecnico oculto para relaciones internas;
- mostrar recetas guardadas, selectores y documentos con nombre/codigo del producto y version; el ID tecnico de receta permanece oculto;
- numerar las fases activas de forma consecutiva y asignar a cada area un porcentaje mayor que cero;
- exigir que los porcentajes de las fases sumen exactamente 100 antes de guardar o aprobar;
- buscar dentro del catalogo por clave, nombre o tipo;
- mostrar resultados con scroll para no empujar la pantalla;
- agregar recursos dados de alta previamente;
- separar la captura en materiales, mano de obra y maquinaria;
- capturar materiales en su unidad base de Almacenes, mano de obra en horas-persona y maquinaria en horas-maquina;
- aceptar fracciones decimales de hora sin restringirlas a bloques de 15 minutos; `0.5` horas equivale a 30 minutos;
- definir cantidad base;
- definir unidad;
- definir centro de costos;
- definir version;
- definir etapas operativas genericas;
- validar recursos;
- guardar receta;
- aprobar receta;
- editar receta existente;
- eliminar receta.

Campos principales:

| Campo | Descripcion |
|---|---|
| Producto/servicio | Se selecciona desde el catalogo maestro. |
| Version | Numero de version de receta. |
| Cantidad base | Cantidad sobre la que se calculan recursos. |
| Unidad | Codigo activo del catalogo de unidades; debe ser compatible con el producto y los recursos. |
| Centro de costos | Centro responsable del costo. |
| Recursos | Materiales, mano de obra y maquinaria. |
| Etapas operativas | Pasos genericos definidos por la empresa. |
| Estado de aprobacion | Borrador, Pendiente de aprobacion, Aprobada u Obsoleta. |
| Motivo de cambio | Razon del ajuste o version. |

Estados de aprobacion:

| Estado | Uso |
|---|---|
| Borrador | Receta en captura. |
| Pendiente de aprobacion | Receta lista para revision. |
| Aprobada | Receta vigente para liberar ordenes. |
| Obsoleta | Receta que ya no debe usarse en nuevas ordenes. |

Regla clave de versionamiento:

- Si una receta se actualiza o se genera una nueva version, las ordenes en curso deben conservar la receta/version con la que fueron liberadas.
- Los cambios de receta solo aplican para nuevas ordenes.

---

### 4.3 Validacion de recursos

Este apartado revisa si una receta puede convertirse en orden para una cantidad solicitada.

La validacion debe revisar:

- receta aprobada;
- materiales suficientes;
- mano de obra disponible;
- maquinaria disponible;
- costo planeado del lote;
- faltantes o bloqueos antes de liberar.

En el corte Local autoritativo, el navegador solo envia receta, cantidad, unidad y fecha. `production-service` consulta existencia/valuacion a `inventory-service`, capacidad laboral a `hr-service` y maquinaria a su propio catalogo; despues descuenta reservas y compromisos activos. Ningun costo o disponible enviado por el cliente se acepta como fuente de verdad.

Resultado esperado:

| Resultado | Descripcion |
|---|---|
| Lista para liberar | La receta esta aprobada y los recursos son suficientes. |
| Pendiente de liberacion | Existen faltantes o la receta no esta aprobada. |

---

### 4.4 Ordenes de produccion

Las ordenes se generan a partir de una receta aprobada y una cantidad solicitada.

La orden tiene su propio codigo de negocio. Al generarla copia la version de receta, las areas, el numero y el porcentaje de cada fase. El avance general se calcula como `suma(avance de fase * porcentaje / 100)`, de modo que una fase con mayor peso aporta mas al progreso real.

Funciones actuales:

- generar orden desde receta seleccionada;
- asignar codigo administrado o aceptar uno manual segun Administracion;
- validar orden antes de crearla;
- conservar snapshot de receta, version, recursos y etapas usadas al momento de generarla;
- asignar responsable general;
- asignar responsables por etapa operativa;
- elegir prioridad;
- definir fecha requerida;
- consultar costo planeado;
- consultar costo real;
- consultar variacion;
- registrar porcentaje real de avance por etapa; la captura de tiempo real de mano de obra y maquinaria se reserva para una fase futura de eficiencia;
- reservar materiales al liberar, consumirlos al iniciar por primera vez y liberarlos si se cancela antes de iniciar;
- cambiar estatus desde un catalogo directo;
- imprimir o generar vista de orden;
- avanzar etapas operativas.

Catalogo actual de estatus:

| Estatus | Descripcion |
|---|---|
| Liberada | Orden autorizada para iniciar. |
| En espera de recursos | Orden bloqueada por recursos, capacidad o confirmacion; solo puede iniciar si conserva todas sus reservas materiales. |
| En produccion | Orden en ejecucion; al entrar por primera vez consume las reservas y registra las salidas fisicas por almacen. |
| Pausada | Orden detenida temporalmente. |
| En validacion | Orden en revision antes de cierre. |
| Terminada | Orden completada; exige etapas concluidas y consolida el costo real sin duplicar las salidas registradas al iniciar. |
| Cancelada | Orden cancelada. |

Reglas clave:

- Una orden solo debe liberarse si la receta esta aprobada.
- Una orden solo debe liberarse si no hay faltantes de recursos.
- La orden debe conservar la version de receta usada al momento de liberacion.
- El estatus general de la orden se maneja separado del avance por etapa.
- La fecha compromete minutos de puestos y maquinas para impedir sobreasignacion concurrente.
- El cierre exige materiales consumidos y todas las etapas al 100%; en este corte no exige tiempos reales de recursos temporales.
- `En validacion` solo se alcanza con todas las etapas terminadas u omitidas; la ultima etapa concluida realiza el cambio automaticamente.
- La interfaz solo ofrece transiciones validas. Para cerrar, el operador captura el porcentaje de cada tarjeta de fase hasta que todas lleguen a 100% y despues selecciona `Terminada`.

---

### 4.5 Seguimiento por etapas operativas

El modulo no debe asumir etapas especificas de una industria. Las etapas vienen desde la receta.

**Entregables por area** consulta las etapas reales copiadas a cada orden. Cada tarjeta identifica el codigo de orden, numero de fase, area, peso y avance general; actualizar una etapa modifica el progreso de esa orden sin alterar la receta maestra ni otras ordenes.

Ejemplos genericos:

- Preparacion;
- Ejecucion;
- Validacion;
- Entrega.

Cada etapa puede tener:

- nombre;
- responsable;
- estatus;
- avance;
- porcentaje real completado;
- relacion con la orden.

Estados sugeridos por etapa:

| Estado | Descripcion |
|---|---|
| Pendiente | La etapa esta asignada pero no ha iniciado. |
| En proceso | La etapa esta en ejecucion. |
| Terminada | La etapa fue completada. |

---

### 4.6 Areas y puestos

> El catalogo fue trasladado al modulo independiente **Recursos Humanos**, cuyo propietario es `hr-service`. Produccion no crea ni modifica areas o puestos: solo consume puestos activos marcados para intervenir en produccion y conserva snapshots en sus recetas.

La configuracion de mano de obra se realiza en Recursos Humanos, no en Produccion ni en Almacenes. Produccion solo consulta el contrato propietario.

Funciones consumidas por Produccion:

- consultar areas activas y puestos productivos;
- seleccionar puestos por ID estable al configurar recursos de receta;
- seleccionar areas activas por ID estable para etapas y maquinaria;
- validar trabajadores activos y elegibles al asignar responsables;
- obtener capacidad diaria desde trabajadores activos por puesto;
- derivar costo por minuto desde el costo por hora del puesto;
- conservar IDs externos y nombres/costos snapshot para reproducibilidad historica.

Datos autoritativos de RH utilizados:

| Campo | Descripcion |
|---|---|
| Area | Area operativa. |
| Codigo de area | Identificador unico del area dentro del tenant. |
| Descripcion de area | Alcance operativo del area. |
| Puesto o rol | Rol requerido por la operacion. |
| Nombre para receta | Nombre visible al asignar el recurso en receta. |
| Trabajadores activos | Expedientes activos asignados al puesto; no es una cantidad capturada por Produccion. |
| Minutos por trabajador | Capacidad individual diaria definida por RH. |
| Capacidad total | Trabajadores activos por minutos disponibles, descontando compromisos de la fecha. |
| Costo por hora | Referencia maestra de RH; Produccion conserva el costo por minuto como snapshot. |
| Estatus | Activo o Inactivo. |

Permisos independientes:

| Operacion | Permiso |
|---|---|
| Consultar areas | `hr.area.read` |
| Crear area | `hr.area.create` |
| Editar area | `hr.area.update` |
| Consultar puestos | `hr.position.read` |
| Crear puesto | `hr.position.create` |
| Editar puesto y recursos | `hr.position.update` |

Las altas y ediciones de areas y puestos pertenecen al microfrontend y a la API de RH. `hr-service` debe rechazar un `area_id` inexistente o perteneciente a otro tenant. Renombrar un area conserva sus puestos mediante `labor_area_id`; el nombre mostrado no funciona como relacion ni crea registros implicitos.

---

### 4.7 Maquinaria

Este apartado configura maquinaria o recursos tecnicos. Tampoco debe tratarse como almacen.

Funciones actuales:

- crear maquina;
- seleccionar un area activa previamente registrada en Recursos Humanos; Maquinaria no permite crear ni capturar areas libres;
- consultar maquinaria existente;
- editar maquina;
- capturar area;
- capturar tipo de maquina;
- capturar minutos disponibles por dia;
- capturar costo por minuto/hora maquina;
- cambiar estatus.

Campos principales:

| Campo | Descripcion |
|---|---|
| Area | Area donde opera el equipo. |
| Tipo de maquina | Clasificacion tecnica. |
| Nombre de maquina | Nombre visible del recurso. |
| Minutos disponibles | Capacidad diaria. |
| Costo | Costo por unidad de tiempo. |
| Estatus | Activo, Inactivo o Mantenimiento. |

---

## 5. Entidades principales

| Entidad | Descripcion |
|---|---|
| Producto/servicio | Elemento maestro que se produce, transforma o ejecuta. |
| Ficha maestra | Datos administrativos, comerciales y de costeo del producto/servicio. |
| Receta | Estructura de recursos y etapas para producir o ejecutar. |
| Version de receta | Variante vigente o historica de una receta. |
| Recurso de almacen | Materia prima, consumible o herramienta. |
| Mano de obra | Rol operativo con capacidad y costo. |
| Maquinaria | Equipo o recurso tecnico con capacidad y costo. |
| Etapa operativa | Paso generico dentro de una receta u orden. |
| Orden de produccion | Documento operativo liberado desde una receta. |
| Centro de costos | Unidad donde se acumulan costos. |

---

## 6. Reglas de negocio vigentes

- Productos y servicios se administran desde el catalogo maestro.
- Las recetas se administran desde el apartado de Recetas.
- No se deben duplicar flujos de receta dentro del catalogo maestro.
- Una receta debe estar conectada a un producto o servicio existente.
- El selector de producto/servicio en recetas debe permitir buscar por texto o mostrar todos los registros si no hay busqueda.
- El listado de resultados debe tener scroll para no empujar la pantalla.
- Si un producto/servicio tiene receta vigente, debe abrirse la edicion de receta.
- Si no tiene receta vigente, debe permitir generar receta.
- Mano de obra y maquinaria no pertenecen a almacenes.
- El area de una maquina se selecciona del catalogo activo de Recursos Humanos; si no existe, debe darse de alta primero en RH.
- La interfaz expresa los tiempos de receta en horas-persona y horas-maquina; el contrato vigente los conserva en minutos para validar capacidad y costo sin perder precision.
- Almacenes queda para materias primas, consumibles y herramientas.
- Una orden solo debe liberarse con receta aprobada.
- Una orden debe validar disponibilidad de recursos antes de liberarse.
- Las ordenes en curso deben conservar la version de receta con la que fueron liberadas.
- Los cambios de receta solo aplican para nuevas ordenes.
- El estatus de orden debe seleccionarse desde catalogo, no por boton ciclico.
- Las etapas operativas deben ser genericas y configurables por receta.
- Las guias de flujo deben poder ocultarse/mostrarse sin bloquear el trabajo principal.

---

## 7. Costeo

El modulo debe diferenciar:

| Concepto | Descripcion |
|---|---|
| Costo estandar | Costo calculado desde receta aprobada. |
| Costo planeado | Costo estimado para una orden y cantidad especifica. |
| Costo real | Suma de materiales consumidos y cantidades reales de recursos temporales valuados con el snapshot de la orden. |
| Variacion | Diferencia entre costo planeado y real. |
| Margen esperado | Margen objetivo de la ficha maestra. |

El costo debe considerar:

- materiales;
- consumibles;
- herramientas si aplican al costo;
- mano de obra;
- maquinaria;
- cantidad solicitada;
- cantidad base de receta.

---

## 8. Validaciones automaticas esperadas

### Al crear o editar producto/servicio

- Validar nombre, SKU, unidad, categoria, centro de costos y responsable.
- Evitar duplicidad de claves cuando exista backend.
- Mantener relacion con recetas existentes.

### Al crear o editar receta

- Validar producto/servicio existente.
- Validar recursos existentes.
- Validar cantidades mayores a cero.
- Validar al menos una etapa operativa.
- Calcular costo estandar.
- Registrar motivo de cambio.

### Al aprobar receta

- Validar que tenga recursos.
- Validar que tenga etapas.
- Validar que el producto/servicio siga activo.
- Revalidar articulos/unidades, puestos/areas y maquinaria contra sus catalogos propietarios.
- Registrar aprobador y fecha.

### Al generar orden

- Validar receta aprobada.
- Validar disponibilidad de recursos.
- Mostrar el recurso insuficiente con requerido, disponible y unidad antes de asignar el folio.
- Calcular costo planeado.
- Reservar materiales y comprometer capacidad por cada fecha productiva bajo bloqueo transaccional por recurso/dia.
- Registrar version de receta usada.
- Generar etapas desde la receta.

### Durante la ejecucion

- Actualizar estatus general de orden.
- Actualizar avance por etapa.
- Registrar porcentaje real por etapa; las reservas ya consumidas al iniciar aportan el costo real de materiales. La medicion de tiempos y eficiencia se incorporara cuando exista su modelo operativo.
- Registrar pausas, cancelaciones o cierre.

La reserva al liberar y la salida al iniciar representan hechos distintos. La primera entrada a **En produccion** solicita a Almacenes consumir cada reserva y crear una salida inmutable en el almacen que la otorgo. Reanudar una orden pausada o cerrarla no vuelve a descontar. Cancelar antes del inicio libera la reserva; cancelar despues conserva las salidas fisicas ya registradas. El frontend debe impedir materiales cuya UOM no pertenezca al catalogo activo de Administracion y conservar visibles, pero bloqueados, los recursos invalidos de versiones heredadas.

---

## 9. Integraciones

| Modulo | Relacion |
|---|---|
| Almacenes | Disponibilidad, reserva, valuacion y consumo de materias primas/consumibles implementados en codigo Local. |
| Recursos Humanos | Trabajadores elegibles, areas, puestos y capacidad diaria autoritativa implementados en codigo Local. |
| Compras | Solicitudes por faltantes. |
| Ventas | Produccion bajo pedido o demanda. |
| Finanzas/Costos | Costo estandar, real y variaciones. |
| Contabilidad | Asientos por consumo, WIP, merma y producto terminado si aplica. |
| Reportes | Productividad, capacidad, costo, cumplimiento y margen. |
| Usuarios/Permisos | Control de altas, aprobaciones y cierres. |

---

## 10. Metricas sugeridas

- productos activos sin receta aprobada;
- recetas pendientes de aprobacion;
- ordenes liberadas;
- ordenes en espera de recursos;
- ordenes en produccion;
- ordenes en validacion;
- ordenes terminadas;
- ordenes canceladas;
- costo planeado vs costo real;
- variacion de costo;
- uso de capacidad de mano de obra;
- uso de maquinaria;
- cumplimiento de fechas;
- avance promedio por etapa.

---

## 11. Pendientes funcionales

- Definir mermas, rechazos y retrabajos.
- Definir cierre parcial de orden.
- Implementar recepcion de merma y reglas de rechazo/retrabajo en Almacenes.
- Sustituir el calendario productivo base lunes-viernes por calendarios tenant con turnos, festivos, ausencias y excepciones de mantenimiento; la distribucion y los compromisos multi-dia ya estan implementados en Local.
- Definir reportes gerenciales.
- Promover y certificar en QA el corte Local autoritativo antes de presentarlo como desplegado.
# CHG-206: vínculo con producto terminado

Producción es dueña de `product_services.inventory_item_ref_id`. Un producto activo puede vincularse por ID con un único artículo activo de tipo `finishedGood` y la misma unidad base. El nombre/código de Producción son comerciales; los de Inventario son logísticos y pueden ser distintos.

## CHG-209: seleccion escalable

Productos, recetas, artículos vinculables, recursos, áreas y responsables usan búsqueda por identidad visible y conservan su ID técnico. Estatus y prioridad continúan como listas cerradas. Al superar 200 candidatos, la búsqueda deberá paginarse desde el servicio propietario.

## CHG-222: recepcion fisica posterior al cierre

Una orden **Terminada** queda disponible para recepcion en Almacenes. El almacenista confirma almacen, cantidad, fecha y observaciones; Inventory valida la orden y el vinculo, permite parciales y registra la entrada. El cierre de Produccion no incrementa existencias por si solo.

## CHG-214: consistencia de unidades heredadas

La revision `20260821_0023`, desplegada en Local y QA, normaliza de forma auditada los alias inequivocos `LTS -> LTR` y `MT -> MTR` tanto en los articulos y movimientos de Inventory como en los recursos y snapshots de Produccion. Esto permite que una receta historica siga refiriendo la misma magnitud sin alterar cantidades ni costos. Produccion no infiere otras equivalencias y continua rechazando unidades ausentes o inactivas del catalogo del tenant.

## CHG-215: maquinaria elegible para recetas

CHG-242 reemplaza la restriccion operativa de CHG-215: una maquina activa o en mantenimiento puede formar parte de una receta aunque su `area_ref_id` siga pendiente. La receta define el proceso; la disponibilidad se decide al validar/liberar la orden, donde una maquina en mantenimiento aporta cero capacidad y bloquea correctamente. Una maquina inactiva o inexistente sigue rechazandose con `422 machine_resource_invalid`. El area RH permanece como dato recomendado para asignacion y reportes y nunca se infiere automaticamente por nombre.

## CHG-243: validacion de definicion frente a disponibilidad

El editor de Recetas valida que los recursos seleccionados sigan existiendo en sus catalogos elegibles y calcula cantidades/costo para el lote simulado. No usa existencias actuales ni compara horas-persona u horas-maquina; la duracion sugerida tampoco altera ese resultado. La orden de produccion realiza la validacion operativa autoritativa con inventario, capacidad diaria, compromisos e intervalo multi-dia.
