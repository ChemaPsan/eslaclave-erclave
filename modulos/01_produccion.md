# ERClave - Modulo de Produccion

## 1. Objetivo

El modulo de Produccion es el primer modulo funcional de ERClave. Su objetivo es permitir que una empresa administre productos y servicios, configure recetas operativas, valide recursos, libere ordenes y controle el avance productivo con costos estimados y reales.

El modulo debe responder:

> Que producto o servicio se gestionara, que receta lo soporta, que recursos requiere, cuanto cuesta, si puede liberarse y en que estado se encuentra cada orden.

El enfoque del modulo debe ser agnostico a la industria. No debe asumir procesos textiles, alimenticios, manufactureros o de servicios especificos. Cada empresa debe poder definir sus propias etapas operativas.

---

## 2. Alcance actual de la maqueta

La maqueta actual contempla:

- catalogo maestro de productos y servicios;
- alta, busqueda, edicion y cambio de estatus de productos/servicios;
- ficha maestra con SKU, unidad, categoria, responsable, precio objetivo, margen esperado y costo estandar;
- recetas conectadas al catalogo de productos/servicios;
- buscador de producto/servicio dentro del formulario de receta;
- recetas con recursos, version, etapas genericas, estado de aprobacion y motivo de cambio;
- validacion de recursos antes de liberar una orden;
- separacion entre almacenes, mano de obra y maquinaria;
- catalogo de areas, puestos/roles y cantidad de recursos disponibles;
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
| Unidad base | Unidad de produccion o ejecucion. |
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

Funciones actuales:

- crear receta desde el apartado de Recetas;
- seleccionar producto/servicio desde catalogo buscable;
- buscar dentro del catalogo por clave, nombre o tipo;
- mostrar resultados con scroll para no empujar la pantalla;
- agregar recursos dados de alta previamente;
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
| Unidad | Unidad base de la receta. |
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

Resultado esperado:

| Resultado | Descripcion |
|---|---|
| Lista para liberar | La receta esta aprobada y los recursos son suficientes. |
| Pendiente de liberacion | Existen faltantes o la receta no esta aprobada. |

---

### 4.4 Ordenes de produccion

Las ordenes se generan a partir de una receta aprobada y una cantidad solicitada.

Funciones actuales:

- generar orden desde receta seleccionada;
- validar orden antes de crearla;
- conservar snapshot de receta, version, recursos y etapas usadas al momento de generarla;
- asignar responsable general;
- asignar responsables por etapa operativa;
- elegir prioridad;
- definir fecha requerida;
- consultar costo planeado;
- consultar costo real;
- consultar variacion;
- cambiar estatus desde un catalogo directo;
- imprimir o generar vista de orden;
- avanzar etapas operativas.

Catalogo actual de estatus:

| Estatus | Descripcion |
|---|---|
| Liberada | Orden autorizada para iniciar. |
| En espera de recursos | Orden bloqueada por recursos, capacidad o confirmacion. |
| En produccion | Orden en ejecucion. |
| Pausada | Orden detenida temporalmente. |
| En validacion | Orden en revision antes de cierre. |
| Terminada | Orden completada. |
| Cancelada | Orden cancelada. |

Reglas clave:

- Una orden solo debe liberarse si la receta esta aprobada.
- Una orden solo debe liberarse si no hay faltantes de recursos.
- La orden debe conservar la version de receta usada al momento de liberacion.
- El estatus general de la orden se maneja separado del avance por etapa.

---

### 4.5 Seguimiento por etapas operativas

El modulo no debe asumir etapas especificas de una industria. Las etapas vienen desde la receta.

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
- costo real estimado o factor de variacion;
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

Este apartado configura la mano de obra. No debe tratarse como almacen.

Funciones actuales:

- consultar listado de areas;
- buscar por area, puesto o rol;
- crear un area mediante un formulario independiente con codigo, nombre, descripcion y estatus;
- editar un area sin capturar ni duplicar puestos;
- entrar al detalle de un area;
- ver roles/puestos dentro del area;
- crear un puesto mediante un formulario independiente;
- seleccionar el area desde el catalogo previamente creado; el puesto nunca crea areas por texto libre;
- editar un puesto existente y actualizar su cantidad, capacidad, costo y estatus;
- capturar cantidad de recursos;
- capturar minutos disponibles por recurso;
- calcular capacidad total;
- capturar costo por minuto;
- cambiar estatus.

Campos principales:

| Campo | Descripcion |
|---|---|
| Area | Area operativa. |
| Codigo de area | Identificador unico del area dentro del tenant. |
| Descripcion de area | Alcance operativo del area. |
| Puesto o rol | Rol requerido por la operacion. |
| Nombre para receta | Nombre visible al asignar el recurso en receta. |
| Cantidad de recursos | Numero de personas o recursos del mismo rol. |
| Minutos por recurso | Capacidad individual diaria. |
| Capacidad total | Cantidad por minutos disponibles. |
| Costo por minuto | Costo unitario de mano de obra. |
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

`hr-service` debe rechazar un `area_id` inexistente o perteneciente a otro tenant. Renombrar un area conserva sus puestos mediante `labor_area_id`; el nombre mostrado no funciona como relacion ni crea registros implicitos.

---

### 4.7 Maquinaria

Este apartado configura maquinaria o recursos tecnicos. Tampoco debe tratarse como almacen.

Funciones actuales:

- crear maquina;
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
| Costo real | Costo resultante o simulado durante la ejecucion. |
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
- Registrar aprobador y fecha.

### Al generar orden

- Validar receta aprobada.
- Validar disponibilidad de recursos.
- Calcular costo planeado.
- Registrar version de receta usada.
- Generar etapas desde la receta.

### Durante la ejecucion

- Actualizar estatus general de orden.
- Actualizar avance por etapa.
- Registrar costo real.
- Registrar pausas, cancelaciones o cierre.

---

## 9. Integraciones futuras

| Modulo | Relacion |
|---|---|
| Almacenes | Disponibilidad, reserva y consumo de materias primas/consumibles. |
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

- Definir modelo de datos definitivo para backend.
- Definir permisos por rol.
- Definir aprobaciones formales por usuario.
- Definir versionamiento real de recetas.
- Definir consumo real de recursos.
- Definir mermas, rechazos y retrabajos.
- Definir cierre parcial de orden.
- Definir integracion con almacenes reales.
- Definir reportes gerenciales.
- Definir auditoria y bitacora de cambios.
