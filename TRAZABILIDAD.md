# Trazabilidad de cambios

Este archivo registra cada ajuste hecho en el repo con nivel de detalle suficiente para auditar qué se cambió, cuándo, por qué, en qué secciones y con qué validacion.

## Regla de uso

Cada cambio relevante debe quedar registrado aqui con:

- fecha y hora local;
- identificador del cambio;
- autor o agente que hizo el ajuste;
- archivos tocados;
- secciones exactas afectadas;
- descripcion precisa del cambio;
- motivo o contexto;
- impacto esperado;
- validacion realizada;
- observaciones o pendientes.

## Formato sugerido por entrada

| Campo | Contenido |
|---|---|
| Fecha | AAAA-MM-DD HH:MM |
| Cambio | ID corto, por ejemplo `CHG-001` |
| Autor | Nombre de la persona o agente |
| Archivos | Lista de archivos modificados |
| Secciones | Titulos, bloques o lineas afectadas |
| Descripcion | Que se cambio exactamente |
| Motivo | Por que se hizo el ajuste |
| Impacto | Efecto esperado en el repo o producto |
| Validacion | Comprobacion realizada despues del cambio |
| Observaciones | Riesgos, notas o pendientes |

## Registro

### CHG-001

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Creacion inicial del archivo de trazabilidad |
| Autor | GitHub Copilot |
| Archivos | `TRAZABILIDAD.md`, `README.md` |
| Secciones | Contenido actual, estructura del proyecto |
| Descripcion | Se agrego este archivo para llevar un historial detallado de cada cambio futuro y se enlazo desde el README para que sea visible desde la portada del proyecto. |
| Motivo | Tener una fuente unica y ordenada para auditar cambios, contexto, alcance y validacion de cada ajuste. |
| Impacto | Facilita seguimiento fino del trabajo y reduce ambiguedad sobre que se toco en cada iteracion. |
| Validacion | Revision manual del contenido y confirmacion de que el README referencia el nuevo archivo. |
| Observaciones | A partir de ahora, cada cambio relevante deberia sumar una nueva fila en este documento. |

### CHG-002

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Separacion de productos/servicios y recetas en Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Productos y servicios, submodulo Recetas, mock DB local, estilos de catalogo |
| Descripcion | Se agrego un catalogo independiente de productos y servicios con alta y busqueda. El boton Generar receta ahora navega al apartado Recetas con el producto seleccionado como contexto, sin crear recetas desde Productos y servicios. |
| Motivo | Delimitar responsabilidades por submodulo para evitar duplicar funcionalidades y facilitar permisos futuros por rol. |
| Impacto | Productos y servicios queda como catalogo maestro; Recetas conserva la configuracion de recursos, etapas y tiempos. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La persistencia sigue siendo mock en `localStorage`; queda pendiente prueba visual manual en navegador. |

### CHG-003

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Gestion de estatus e historial en productos y servicios |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Catalogo de Productos y servicios, mock DB local, estilos de tarjetas |
| Descripcion | Se agrego cambio de estatus por producto o servicio con opciones Activo, Inactivo y En espera de aprobacion. Cada tarjeta muestra historial de ordenes relacionadas y se elimino el boton duplicado Dar de alta dentro del apartado. |
| Motivo | Completar la gestion del catalogo maestro sin mezclar alta de recetas y permitir seguimiento operativo por producto o servicio. |
| Impacto | El submodulo ahora permite administrar disponibilidad funcional del producto/servicio y consultar su historial de uso en ordenes. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El historial se calcula contra ordenes mock existentes por nombre de producto o receta asociada. |

### CHG-004

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Selector de catalogo en formulario de recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, construccion y validacion de recetas, historial de productos/servicios |
| Descripcion | El campo Producto o servicio del formulario de receta dejo de ser texto libre y ahora es un selector conectado al catalogo de Productos y servicios. Al cambiar la seleccion se prellenan unidad y centro de costos, y la receta guarda `productServiceId`. |
| Motivo | Asegurar que las recetas solo se creen sobre productos o servicios existentes y mantener separadas las responsabilidades de catalogo y receta. |
| Impacto | Mejora la trazabilidad entre productos/servicios, recetas y ordenes; evita duplicidad o errores por captura manual del nombre. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Las recetas existentes sin `productServiceId` siguen resolviendose por nombre para conservar compatibilidad del mock actual. |

### CHG-005

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Buscador de producto o servicio en recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, selector de producto o servicio |
| Descripcion | El selector de Producto o servicio en recetas se cambio a un campo buscable con `datalist`, permitiendo escribir clave, nombre o tipo para encontrar coincidencias del catalogo de Productos y servicios. |
| Motivo | Facilitar la seleccion cuando existan muchos productos o servicios sin perder la relacion tecnica con el catalogo maestro. |
| Impacto | El usuario puede buscar rapidamente y la receta sigue guardando `productServiceId` solo cuando el producto o servicio coincide con el catalogo. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Si el texto no coincide con una opcion del catalogo, la validacion impide guardar la receta. |

### CHG-006

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Despliegue completo del catalogo buscable en recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, buscador de Producto o servicio, estilos de lookup |
| Descripcion | Se reemplazo el `datalist` nativo por un dropdown propio. Al enfocar el campo vacio muestra todos los productos y servicios; al escribir filtra por clave, nombre, tipo, categoria o centro. |
| Motivo | Permitir seleccion eficiente incluso con cientos de productos y asegurar que el usuario pueda abrir el catalogo completo sin escribir primero. |
| Impacto | El formulario de recetas conserva `productServiceId`, prellena unidad y centro al seleccionar, y mejora la experiencia de busqueda. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El dropdown es local al mock frontend y no requiere dependencias externas. |

### CHG-007

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Scroll interno en buscador de producto o servicio |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Modal Nueva receta, dropdown de Producto o servicio |
| Descripcion | El dropdown del buscador de Producto o servicio ahora flota sobre el formulario, no empuja la pagina hacia abajo y limita la altura visible a aproximadamente cinco registros con scroll interno para el resto. |
| Motivo | Evitar que catalogos grandes deformen el formulario o hagan crecer la pagina al desplegar resultados. |
| Impacto | Mejora la usabilidad del buscador con muchos productos o servicios manteniendo seleccion y filtrado dentro del modal. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El alto visible se controla por CSS con `max-height` y `overflow: auto`. |

### CHG-008

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Separacion de mano de obra y maquinaria fuera de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/utils/production.js`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Areas y puestos, Maquinaria, catalogo de recursos de recetas |
| Descripcion | Se agregaron subapartados de Areas y puestos y Maquinaria dentro de Produccion. Mano de obra y maquinaria se movieron a catalogos operativos independientes con alta desde modal, mientras Almacenes queda para materias primas, consumibles y herramientas. Las recetas ahora toman recursos desde el catalogo combinado de almacenes, puestos y maquinaria. |
| Motivo | Evitar tratar mano de obra y maquinaria como inventario fisico, y permitir configurar capacidad operativa por area, puesto y equipo. |
| Impacto | Las recetas pueden asignar materias primas, puestos de mano de obra y maquinas desde fuentes separadas; el costeo estimado sigue funcionando con los recursos existentes. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/utils/production.js`, `node --check frontend/data/mockDb.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | La disponibilidad de puestos y maquinas se maneja como minutos disponibles por dia dentro del mock local. |

### CHG-009

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Reorden visual de submodulos de Produccion |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `TRAZABILIDAD.md` |
| Secciones | Lista de submodulos de Produccion |
| Descripcion | Se movieron Areas y puestos y Maquinaria al final de la lista visual de Produccion, manteniendo intacta la logica funcional. |
| Motivo | Mantener primero el flujo operativo principal y dejar los catalogos de configuracion al final. |
| Impacto | La navegacion queda mas clara: Productos y servicios, Recetas, Ordenes, Entregables, Validacion, Areas y puestos, Maquinaria. |
| Validacion | `node --check frontend/data/modules.js` ejecutado sin errores de sintaxis. |
| Observaciones | Cambio solo visual/de orden, sin modificaciones de comportamiento. |

### CHG-010

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Gestion completa de areas, puestos y cantidad de recursos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, modal de puesto, catalogo de mano de obra |
| Descripcion | Se agrego resumen por area, edicion de puestos existentes, captura de cantidad de recursos por rol y minutos disponibles por recurso. La capacidad total se calcula como cantidad por minutos por recurso. |
| Motivo | Permitir gestionar varios recursos del mismo puesto y area, por ejemplo 20 costureros en Costura, sin duplicar registros individuales. |
| Impacto | El catalogo de mano de obra ahora representa capacidad real por area/puesto y las recetas validan contra esa capacidad total. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/data/mockDb.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | Los roles antiguos sin `quantity` usan fallback visual de 1 recurso para compatibilidad con datos previos en `localStorage`. |

### CHG-011

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Navegacion por areas y detalle de puestos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos |
| Descripcion | La pantalla de Areas y puestos ahora muestra primero un listado de areas con buscador por area, puesto o rol. Al entrar a un area se muestran sus puestos/roles y desde cada rol se abre el formulario de edicion de cantidad, minutos, costo y estatus. |
| Motivo | Facilitar la consulta cuando existan muchas areas y puestos, manteniendo una navegacion jerarquica clara. |
| Impacto | El usuario puede encontrar areas por descripcion o por roles contenidos, entrar al area y editar la capacidad de cada puesto. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El area seleccionada se conserva temporalmente en `localStorage` para mantener el contexto al editar o crear puestos. |

### CHG-012

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-12 |
| Cambio | Flecha global de retorno entre pantallas |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Topbar, navegacion principal, navegacion interna de modulos |
| Descripcion | Se agrego un boton global de volver en el encabezado y un historial interno de pantallas para retornar a la vista anterior en la navegacion del prototipo. |
| Motivo | Dar una forma consistente de regresar desde cualquier pantalla o subpantalla sin depender solo de botones contextuales. |
| Impacto | La navegacion entre modulos, submodulos, detalle de areas, tarjetas internas y redirecciones despues de guardar ahora queda integrada con una flecha de retorno. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El historial es local al frontend mock y no persiste entre recargas. |

### CHG-013

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Alta contextual de roles desde detalle de area |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, detalle de area, modal de puesto |
| Descripcion | Se agrego un boton en el detalle de cada area para crear un nuevo rol o recurso dentro de esa misma area. El formulario de alta abre con el area precargada y mantiene la edicion existente de roles. |
| Motivo | Permitir agregar puestos o recursos desde el punto donde se consulta el area, sin regresar al listado general ni capturar de nuevo el area manualmente. |
| Impacto | El flujo de Areas y puestos queda mas directo: se entra a un area, se revisan sus roles y desde ahi se agregan nuevos recursos asociados a esa area. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El boton general de Nueva area/puesto se conserva para crear registros desde cero. |

### CHG-014

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Bloqueo de area en alta contextual de rol |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, modal de puesto |
| Descripcion | Cuando se crea un nuevo rol o recurso desde el detalle de un area, el campo Area se muestra precargado y en modo solo lectura. |
| Motivo | Evitar que el usuario cambie el area cuando el alta ya nace dentro de una area especifica. |
| Impacto | El flujo contextual queda mas consistente: desde el detalle de area solo se agregan roles a esa misma area, mientras el alta general conserva el campo editable. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La edicion de roles existentes mantiene el comportamiento previo. |

### CHG-015

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Estilo global para campos no editables y bloqueo de area al editar rol |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Areas y puestos, formularios del sistema |
| Descripcion | Al abrir un rol desde el detalle de un area, el campo Area queda en modo solo lectura tambien durante la edicion. Se agrego un estilo visual global para campos `readonly` y `disabled` dentro de formularios. |
| Motivo | Evitar cambios accidentales de area cuando el usuario ya esta trabajando dentro de un area especifica, y hacer evidente que un campo no se puede modificar. |
| Impacto | Los campos bloqueados ahora se distinguen visualmente por color, borde y patron de fondo. El alta general de Nueva area/puesto conserva el area editable. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | La regla visual aplica a inputs, selects y textareas no editables dentro de `.preview-field`. |

### CHG-016

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Edicion de registros de maquinaria |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Maquinaria, modal de maquina, persistencia mock |
| Descripcion | Se agrego la accion Abrir maquina en cada tarjeta de maquinaria y el modal ahora permite editar area, tipo, nombre, minutos disponibles, costo y estatus de una maquina existente. |
| Motivo | Permitir actualizar horas maquina, costos o datos operativos sin duplicar registros. |
| Impacto | El catalogo de maquinaria puede mantenerse desde la interfaz y conserva el mismo identificador de maquina al editar, evitando romper referencias existentes en recetas. |
| Validacion | `node --check frontend/app.js` y `node --check frontend/data/mockDb.js` ejecutados sin errores de sintaxis. |
| Observaciones | El alta de nueva maquina mantiene el mismo flujo y la edicion reutiliza el formulario existente. |

### CHG-017

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Fortalecimiento gerencial del modulo de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/resources.js`, `frontend/utils/production.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Validacion, Ordenes, Entregables |
| Descripcion | Se aplicaron cinco mejoras prioritarias: ficha maestra enriquecida de producto/servicio, receta versionada con aprobacion, validacion de liberacion contra receta aprobada y recursos, costo estandar contra costo real, y seguimiento de orden por etapas operativas genericas. |
| Motivo | Convertir Produccion en un flujo mas cercano a gestion ERP: catalogo maestro, receta controlada, liberacion previa, costeo y control de avance sin depender de una industria especifica. |
| Impacto | Las ordenes se liberan solo con receta aprobada y recursos suficientes; los productos muestran costo, margen y receta vigente; las recetas manejan aprobacion; las ordenes muestran avance por etapa y variacion de costo. |
| Validacion | `node --check frontend/app.js`, `node --check frontend/utils/production.js` y `node --check frontend/data/resources.js` ejecutados sin errores de sintaxis. |
| Observaciones | Las etapas se nombran como operativas genericas para mantener el sistema agnostico al producto o industria. |

### CHG-018

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Edicion de productos y servicios existentes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, ficha maestra, recetas relacionadas |
| Descripcion | Se agrego la accion Editar ficha en cada producto/servicio y el modal de catalogo ahora funciona para alta y edicion, precargando tipo, nombre, SKU, unidad, categoria, centro, responsable, precio objetivo, margen, estatus y descripcion. |
| Motivo | Permitir mantener la ficha maestra de productos y servicios sin crear registros duplicados. |
| Impacto | Al editar se conserva el identificador del producto/servicio para no romper recetas u ordenes relacionadas; las recetas vinculadas se sincronizan con nombre, unidad y centro actualizados. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El costo estandar se conserva desde la receta vigente y no se captura manualmente desde la ficha. |

### CHG-019

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Accion contextual de receta vigente y regla de versionamiento para ordenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Ordenes |
| Descripcion | En Productos y servicios, si el producto o servicio ya tiene una receta vigente, la accion ahora muestra Editar receta; si no tiene receta, mantiene Generar receta. |
| Motivo | Evitar duplicidad conceptual: cuando ya existe receta vigente, el flujo correcto es editar/versionar esa receta, no generar otra desde cero. |
| Impacto | El usuario puede ir directo a la receta existente desde la ficha maestra del producto/servicio. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Regla de negocio documentada para implementacion posterior: cuando una receta se actualice o se genere una nueva version, las ordenes en curso deben conservar la receta/version con la que fueron liberadas; los cambios de receta solo aplican para nuevas ordenes. |

### CHG-020

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Catalogo directo de estatus para ordenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Ordenes de produccion |
| Descripcion | Se reemplazo el cambio ciclico de estatus por un selector de catalogo en cada orden. El usuario puede elegir directamente Liberada, En espera de recursos, En produccion, Pausada, En validacion, Terminada o Cancelada. |
| Motivo | Evitar que el usuario tenga que presionar varias veces un boton para llegar al estatus deseado. |
| Impacto | El cambio de estatus de orden es mas rapido y controlado; el avance por etapas operativas se mantiene separado. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El catalogo queda centralizado en frontend para facilitar su futura migracion a configuracion o backend. |

### CHG-021

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Guias visuales de flujo en apartados de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Productos y servicios, Recetas, Areas y puestos, Maquinaria, Ordenes, Entregables, Validacion |
| Descripcion | Se agrego un componente visual de flujo con pasos numerados para que cada apartado con proceso operativo muestre la secuencia que debe seguirse. |
| Motivo | Ayudar a que cualquier usuario entienda que hacer primero, que sigue y como se conectan catalogos, recetas, validacion, ordenes y seguimiento. |
| Impacto | Los apartados ahora muestran cuadros de flujo para catalogo maestro, receta, configuracion de mano de obra, configuracion de maquinaria, estatus de orden, seguimiento por etapa y liberacion. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | Las guias usan lenguaje generico de ERP para no depender de una industria especifica. |

### CHG-022

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Guias de flujo laterales y colapsables |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo |
| Descripcion | Las guias visuales de flujo dejaron de mostrarse como bloque horizontal principal y ahora se presentan como panel lateral izquierdo colapsable mediante mostrar/ocultar. |
| Motivo | Evitar que usuarios que ya conocen el flujo vean la guia ocupando el primer renglon de trabajo, manteniendola disponible para consulta. |
| Impacto | Los apartados con flujo operativo conservan la guia, pero el contenido principal queda priorizado a la derecha y la guia puede ocultarse cuando no se necesite. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | En pantallas pequenas el layout vuelve a una sola columna para mantener legibilidad. |

### CHG-023

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Colapso vertical real de guias de flujo |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | Cuando una guia de flujo se oculta, el layout deja de reservar la columna lateral y la guia se contrae verticalmente como barra compacta superior. |
| Motivo | Evitar que una guia cerrada siga ocupando espacio horizontal util en pantalla. |
| Impacto | El contenido principal recupera el ancho completo al ocultar la guia, mientras la opcion de mostrarla queda disponible. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El cambio se implemento con reglas CSS basadas en el estado cerrado de `details`. |

### CHG-024

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Colapso horizontal de guias de flujo |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | Las guias de flujo cerradas ahora se contraen horizontalmente como un riel lateral angosto en lugar de convertirse en una barra superior. |
| Motivo | Mantener la guia siempre accesible sin quitar ancho util al contenido principal. |
| Impacto | Al ocultar la guia, el contenido usa casi todo el ancho y la guia queda como tira lateral para volver a abrirla. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El riel lateral usa el estado cerrado de `details` y conserva el comportamiento responsive existente. |

### CHG-025

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Mejora visual del riel colapsado de flujo |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Produccion, guias de flujo colapsables |
| Descripcion | El riel cerrado de las guias de flujo ahora se muestra como una pestana lateral con icono, texto corto Abrir flujo y estilo visual integrado al panel. |
| Motivo | Evitar que el titulo largo se vea como texto fuera de contexto cuando la guia esta cerrada. |
| Impacto | La guia cerrada se entiende como una pestaña accionable y ocupa poco espacio sin perder contexto visual. |
| Validacion | `node --check frontend/app.js` ejecutado sin errores de sintaxis. |
| Observaciones | El titulo completo solo se muestra cuando la guia esta abierta. |

### CHG-026

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Actualizacion documental del modulo de Produccion |
| Autor | Codex |
| Archivos | `modulos/01_produccion.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion funcional de Produccion |
| Descripcion | Se actualizo el documento del modulo de Produccion para reflejar la maqueta actual: catalogo maestro, recetas aprobables, validacion de liberacion, ordenes, costos, etapas genericas, areas y puestos, maquinaria y reglas de negocio vigentes. |
| Motivo | Mantener alineada la documentacion funcional con lo implementado en la maqueta. |
| Impacto | El documento ahora describe el flujo ERP agnostico y separa claramente catalogos, recetas, recursos, ordenes y seguimiento operativo. |
| Validacion | Revision documental local del archivo `modulos/01_produccion.md`. |
| Observaciones | Se uso texto ASCII para evitar problemas de codificacion en el repositorio. |

### CHG-027

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:14 |
| Cambio | Lista inicial de agentes especializados por modulo |
| Autor | Codex |
| Archivos | `AGENTES.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Nueva matriz de agentes, contenido actual del README, registro de trazabilidad |
| Descripcion | Se agrego una lista de agentes por modulo con dos perfiles por area: agente de negocio y agente tecnico. Cada perfil incluye responsabilidades, preguntas que responde, dependencias y entregables esperados. |
| Motivo | Preparar una estructura de trabajo donde cada modulo tenga especialistas funcionales y tecnicos para revisar cambios, dependencias y pendientes de integracion antes de evolucionar el producto. |
| Impacto | El repo ahora cuenta con una guia clara para consultar agentes por modulo y reducir riesgos al modificar flujos, frontend, datos, API futura o integraciones. |
| Validacion | Revision documental local de `AGENTES.md` y enlace desde `README.md`. |
| Observaciones | Queda pendiente convertir la matriz en prompts o fichas individuales para agentes reales. |

### CHG-028

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:21 |
| Cambio | Entrenamiento conceptual de agentes por modulo |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Base de conocimiento comun, entrenamiento por modulo, fuentes de referencia |
| Descripcion | Se enriquecio la lista de agentes con modelos de referencia y conocimiento especifico por area. Se agregaron criterios de dominio para negocio y tecnica en sinergia modular, produccion, almacenes, compras, ventas, gastos, costos, reportes, administracion y contabilidad. |
| Motivo | Convertir la lista de agentes en una guia de aprendizaje operativo y tecnico basada en mejores practicas documentadas, para que cada agente pueda evaluar cambios con mayor criterio. |
| Impacto | Los agentes ahora tienen una base comun de razonamiento y una ruta de especializacion por modulo, facilitando revisiones futuras de flujos, datos, seguridad, API, reportes e integraciones. |
| Validacion | Revision documental local de `AGENTES.md` y confirmacion de estructura por encabezados. |
| Observaciones | Las fuentes se agregaron como referencias conceptuales; queda pendiente convertir cada perfil en prompt ejecutable o ficha individual. |

### CHG-029

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:28 |
| Cambio | Agente transversal de diseno y experiencia |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Matriz general, base de conocimiento comun, entrenamiento por modulo, agentes transversales |
| Descripcion | Se agrego un agente transversal de Diseno y experiencia con perfil de negocio UX/UI y perfil tecnico de frontend/sistema visual. El agente documenta identidad de marca, paleta, tokens CSS, componentes existentes, responsive, accesibilidad, localizacion y criterios para revisar pantallas de todos los modulos. |
| Motivo | Centralizar el conocimiento visual de ERClave para que cualquier cambio de modulo conserve la identidad de marca, consistencia de componentes y calidad de experiencia operativa. |
| Impacto | Los futuros cambios de interfaz podran revisarse contra un criterio de diseno comun, evitando estilos duplicados, pantallas inconsistentes o rupturas de responsive/tema. |
| Validacion | Revision documental local de `AGENTES.md`, manual de identidad y estilos actuales del frontend. |
| Observaciones | Queda pendiente convertir este agente en checklist ejecutable para revisiones visuales antes de publicar. |

### CHG-030

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Arquitectura objetivo de microservicios y microfrontends |
| Autor | Codex |
| Archivos | `docs/arquitectura/microservicios_microfrontends.md`, `frontend/shell/README.md`, `frontend/microfrontends/README.md`, `frontend/microfrontends/*/manifest.js`, `frontend/microfrontends/registry.js`, `backend/services/README.md`, `backend/services/*/README.md`, `contracts/README.md`, `contracts/api/README.md`, `contracts/events.md`, `contracts/microfrontend.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, frontend shell, microfrontends, microservicios, contratos, eventos, README |
| Descripcion | Se documento la separacion objetivo del sistema en shell frontend, microfrontends por modulo, microservicios por dominio, contratos API/eventos/UI y estrategia progresiva de migracion desde el prototipo actual. Tambien se agregaron manifests iniciales de microfrontends y carpetas base por microservicio. |
| Motivo | Evitar que cambios pequenos en un boton, submodulo o regla afecten todo el sistema, estableciendo ownership, contratos y fronteras claras por modulo. |
| Impacto | El repo ahora tiene una ruta arquitectonica para aislar cambios visuales, funcionales y tecnicos por modulo antes de iniciar la extraccion de codigo desde `frontend/app.js`. |
| Validacion | Revision documental local y confirmacion de que la arquitectura identifica a Produccion como primer candidato de migracion. |
| Observaciones | Queda pendiente ejecutar la fase 2: convertir `frontend/app.js` en shell y mover Produccion a `frontend/microfrontends/produccion/`. |

### CHG-031

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:36 |
| Cambio | Regla de segmentacion obligatoria para agentes |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Base de conocimiento comun, regla obligatoria de segmentacion, entrenamiento de Sinergia y Diseno, checklist antes de actualizar un modulo, fuentes de referencia |
| Descripcion | Se actualizo la guia de agentes para que todos consideren la arquitectura de microservicios y microfrontends antes de validar o ejecutar cambios. Se agregaron preguntas obligatorias sobre modulo dueno, microfrontend, microservicio, contratos, eventos, shell, shared, blast radius y trazabilidad. |
| Motivo | Asegurar que los agentes entiendan la importancia de mantener el sistema segmentado y eviten aprobar cambios que mezclen responsabilidades o afecten otros modulos por acoplamiento. |
| Impacto | Las futuras validaciones de agentes deberan revisar ownership, fronteras, contratos y riesgo de impacto antes de modificar botones, formularios, estados, APIs o eventos. |
| Validacion | Revision documental local de `AGENTES.md` y verificacion de referencias a microfrontends, microservicios, contratos y checklist de segmentacion. |
| Observaciones | Queda pendiente convertir esta regla en checklist automatizable para revisiones de PR o cambios locales. |

### CHG-032

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 10:41 |
| Cambio | Agente de localizacion Espanol/Ingles |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Matriz general, base de conocimiento comun, entrenamiento de Diseno, agente transversal de Diseno, checklist antes de actualizar un modulo, fuentes de referencia |
| Descripcion | Se amplio el agente transversal de Diseno y experiencia para incluir localizacion bilingue Espanol/Ingles. Se agregaron responsabilidades de lenguaje bilingue, paridad de claves i18n, variables dinamicas, glosario funcional y deteccion de textos hardcodeados. |
| Motivo | Asegurar que todo el sistema pueda traducirse correctamente entre Espanol e Ingles sin romper tono, contexto operativo, botones, tabs, modales, tablas o componentes responsivos. |
| Impacto | Cada cambio de UI debera revisar textos visibles, claves en `frontend/i18n/translations.js`, paridad entre `es` y `en`, variables dinamicas y longitud de traducciones antes de aprobarse. |
| Validacion | Revision documental local de `AGENTES.md` y confirmacion de que `frontend/i18n/translations.js` contiene estructura bilingue `es` y `en`. |
| Observaciones | Queda pendiente automatizar una validacion que compare claves y placeholders entre ambos idiomas. |

### CHG-033

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Validadores automaticos iniciales |
| Autor | Codex |
| Archivos | `package.json`, `tools/validators/shared.js`, `tools/validators/validate-i18n.js`, `tools/validators/validate-architecture.js`, `tools/validators/validate-traceability.js`, `tools/validators/validate-syntax.js`, `tools/validators/validate-all.js`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Scripts npm, validadores, validaciones automaticas en README, registro de trazabilidad |
| Descripcion | Se agrego una primera suite de validadores automaticos sin dependencias externas. Incluye validacion i18n Espanol/Ingles, arquitectura de microfrontends/microservicios, trazabilidad secuencial y sintaxis JavaScript. |
| Motivo | Convertir reglas de `AGENTES.md` en checks ejecutables para detectar problemas antes de aprobar cambios. |
| Impacto | El repo ahora puede ejecutar `npm run validate` y validar reglas basicas de agentes, segmentacion, localizacion, trazabilidad y sintaxis. |
| Validacion | `npm run validate`, `npm run validate:i18n`, `npm run validate:architecture` y `npm run validate:syntax` ejecutados correctamente. |
| Observaciones | Los validadores son una primera capa; despues pueden conectarse a GitHub Actions o ampliarse para revisar diffs por modulo. |

### CHG-034

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 |
| Cambio | Workflow de GitHub Actions para validadores |
| Autor | Codex |
| Archivos | `.github/workflows/validate.yml`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | GitHub Actions, validaciones automaticas, README, trazabilidad |
| Descripcion | Se agrego un workflow independiente de GitHub Actions que ejecuta `npm run validate` en pushes a `main`, pull requests a `main` y ejecucion manual. |
| Motivo | Automatizar las validaciones de agentes, segmentacion, i18n, trazabilidad y sintaxis cada vez que se suban cambios relevantes al repo. |
| Impacto | GitHub podra marcar en verde o rojo los cambios segun pasen los validadores automaticos, reduciendo el riesgo de subir cambios que rompan reglas del repo. |
| Validacion | Revision local del YAML y `npm run validate` ejecutado correctamente antes de agregar el workflow. |
| Observaciones | El workflow usa Node 20 y no requiere instalacion de dependencias porque los validadores no usan paquetes externos. |

### CHG-035

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 11:48 |
| Cambio | MVP de formularios genericos para modulos no Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Render generico de modulos, formularios genericos, persistencia local por modulo/submodulo, traducciones Espanol/Ingles |
| Descripcion | Se agrego una captura funcional generica para los modulos distintos de Produccion. El boton principal del modulo, el boton superior y las pantallas de submodulo abren un formulario reutilizable, guardan registros en `localStorage` por modulo/submodulo y muestran los registros guardados en tablas y listas. |
| Motivo | Avanzar hacia un MVP funcional del resto de modulos usando Produccion como referencia, sin duplicar logica compleja ni agregar alcance excesivo para el nivel actual del sistema. |
| Impacto | Almacenes, Compras, Ventas, Gastos, Costos, Reportes y Contabilidad ya pueden capturar registros basicos y verlos reflejados en la interfaz, manteniendo idioma Espanol/Ingles y estilo visual existente. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Produccion no recibio ajustes funcionales; se mantiene como referencia. La captura generica es intencionalmente simple y queda lista para especializarse modulo por modulo en fases posteriores. |

### CHG-036

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 11:56 |
| Cambio | Alta especializada de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Submodulo Almacenes, modal de alta de almacen, tabla de registros, traducciones Espanol/Ingles |
| Descripcion | Se especializo la primera seccion del modulo Almacenes para dar de alta fichas de almacen con codigo, nombre, tipo, estatus, centro de negocio, ubicacion fisica, responsable, capacidad, politica de inventario, permiso de reservas y descripcion. Los registros se guardan en `localStorage` y se muestran en la tabla/lista del submodulo. |
| Motivo | Iniciar el flujo funcional de Almacenes con una ficha maestro de almacen alineada a la documentacion del modulo y a practicas basicas de control de inventario. |
| Impacto | El submodulo Almacenes deja de usar captura generica y ya cuenta con una ficha funcional inicial, manteniendo el diseno de marca, soporte Espanol/Ingles y sin tocar el flujo de Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Los submodulos Ubicaciones, Movimientos, Reservas y Kardex conservan por ahora el MVP generico para especializarse en pasos posteriores. |

### CHG-037

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:03 |
| Cambio | Catalogo consultable y flujo colapsable en Almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Modulo Almacenes, submodulo Almacenes, guias de flujo colapsables, catalogo de almacenes |
| Descripcion | Se aplico la logica de guia de flujo colapsable al modulo Almacenes. La primera seccion del modulo ahora muestra un catalogo consultable de almacenes dados de alta, con tarjetas que presentan codigo, tipo, centro, ubicacion, responsable, capacidad, politica, reservas y estatus. |
| Motivo | Alinear Almacenes con el patron visual de Produccion y establecer que la primera seccion funcional de cada modulo permita alta y consulta de registros existentes. |
| Impacto | El usuario puede dar de alta almacenes y consultarlos visualmente desde la misma seccion, mientras los demas submodulos de Almacenes ya muestran guia de flujo colapsable para orientar su operacion futura. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Ubicaciones, Movimientos, Reservas y Kardex siguen usando captura generica; quedan listos para especializacion posterior. |

### CHG-038

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:10 |
| Cambio | Ubicaciones fisicas integradas en ficha de almacen |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Modulo Almacenes, submodulos, modal de alta de almacen, documentacion funcional |
| Descripcion | Se elimino Ubicaciones como submodulo independiente de Almacenes y se integro como configuracion opcional dentro de la ficha de almacen. El alta de almacen ahora permite capturar zona, pasillo, rack, nivel y posicion como ubicacion fisica inicial opcional. |
| Motivo | Simplificar el MVP y evitar una seccion separada para una configuracion que puede vivir dentro del alta del almacen hasta que el producto requiera un catalogo avanzado de ubicaciones. |
| Impacto | El flujo queda mas simple: primero se crea el almacen y, si aplica, se configura su espacio fisico interno. Movimientos, Reservas y Kardex permanecen como submodulos separados. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Si en una fase posterior se requiere administrar muchas posiciones por almacen, se podra separar Ubicaciones fisicas como catalogo propio. |

### CHG-039

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:15 |
| Cambio | Busqueda y edicion de almacenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/i18n/translations.js`, `TRAZABILIDAD.md` |
| Secciones | Catalogo de almacenes, modal de almacen, mock DB generico, traducciones Espanol/Ingles |
| Descripcion | Se agrego buscador al catalogo de almacenes para filtrar por codigo, nombre, tipo, ubicacion, responsable, capacidad, espacio fisico y descripcion. Cada tarjeta de almacen ahora incluye accion Editar y el modal de almacen puede precargar datos existentes para actualizar la ficha. |
| Motivo | Permitir consultar rapidamente almacenes cuando el catalogo crezca y mantener fichas existentes sin duplicar registros. |
| Impacto | El submodulo Almacenes permite alta, consulta, busqueda y edicion de almacenes con persistencia local, manteniendo soporte ES/EN y sin afectar Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La edicion conserva `createdAt` y agrega `updatedAt`; queda pendiente auditoria visual o historial de cambios por registro en fases futuras. |

### CHG-040

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:18 |
| Cambio | Registro manual de movimientos de inventario |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Movimientos, modal de movimiento, tabla de movimientos, documentacion funcional |
| Descripcion | Se especializo el submodulo Movimientos para registrar entradas, salidas, transferencias, ajustes positivos y ajustes negativos manuales. El formulario captura documento origen, articulo, cantidad, unidad, almacen, ubicacion fisica opcional, fecha y motivo. |
| Motivo | Permitir operacion manual elemental de inventario mientras las integraciones automaticas con Produccion, Compras y Ventas se implementan en fases posteriores. |
| Impacto | El usuario puede registrar movimientos manuales y consultarlos en tabla/lista dentro de Almacenes, conservando trazabilidad basica y soporte Espanol/Ingles. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Esta version aun no recalcula existencias; el siguiente paso natural es conectar movimientos con disponibilidad, reservas y kardex. |

### CHG-041

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:23 |
| Cambio | Documentacion de catalogos base de Administracion |
| Autor | Codex |
| Archivos | `docs/catalogos_base.md`, `modulos/08_administracion_configuracion.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Catalogos base, Administracion y Configuracion, backlog de configuracion |
| Descripcion | Se agrego un documento dedicado para concentrar los catalogos base que deberan configurarse a nivel Administracion, incluyendo principios, modelo minimo, catalogos transversales, catalogos por modulo, opciones fijas actuales que deberan migrarse y permisos sugeridos. |
| Motivo | Evitar perder contexto sobre los valores configurables que el MVP puede manejar temporalmente como opciones fijas, pero que deberan centralizarse cuando el sistema crezca. |
| Impacto | El equipo cuenta con un mapa claro para implementar despues la pantalla de Catalogos base y migrar configuraciones compartidas sin duplicarlas en cada modulo. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El cambio es documental; no modifica funcionalidad del frontend ni comportamiento de los modulos existentes. |

### CHG-042

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:29 |
| Cambio | Catalogo de articulos en Almacenes |
| Autor | Codex |
| Archivos | `frontend/data/modules.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Articulos, Almacenes > Movimientos, documentacion funcional |
| Descripcion | Se agrego el submodulo Articulos dentro de Almacenes con alta, consulta, busqueda y edicion de articulos inventariables. El formulario captura codigo, nombre, tipo, categoria, unidad, minimos, maximos, politica de inventario, almacen sugerido, estatus y descripcion. Movimientos ahora usa selector de articulos cuando ya existen articulos registrados, conservando captura manual solo como apoyo temporal. |
| Motivo | Reducir errores de captura en movimientos y preparar el flujo para que, cuando existan usuarios y permisos, solo perfiles autorizados puedan crear o editar articulos. |
| Impacto | Almacenes queda con un catalogo maestro inicial de articulos conectado al registro manual de movimientos, sin recalcular existencias todavia y sin afectar Produccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El catalogo de articulos usa persistencia local del mock DB; en fases posteriores debera conectarse con permisos, lotes/series, existencias y kardex. |

### CHG-043

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:33 |
| Cambio | Busqueda rapida de articulos en movimientos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Movimientos, seleccion de articulos, documentacion funcional |
| Descripcion | Se reemplazo la lista desplegable de articulos en el formulario de movimientos por un campo de busqueda con resultados filtrables por codigo, nombre, tipo, categoria, unidad o almacen sugerido. Al seleccionar un articulo, se guarda su identificador real y se autocompleta la unidad de movimiento. |
| Motivo | Evitar scroll pesado y errores de captura cuando el catalogo tenga cientos de articulos, replicando el patron de seleccion usado en Produccion para asociar productos/servicios a recetas. |
| Impacto | Los operadores pueden encontrar articulos rapidamente y los movimientos quedan ligados a registros autorizados del catalogo cuando este exista. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La captura manual se conserva solo cuando todavia no hay articulos registrados en el MVP. |

### CHG-044

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:36 |
| Cambio | Reservas deshabilitado para MVP |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Reservas, documentacion funcional |
| Descripcion | Se dejo el submodulo Reservas como pantalla informativa de proximamente. La accion principal queda deshabilitada y no abre formularios ni permite crear registros durante el MVP. |
| Motivo | Evitar apartados de inventario incompletos mientras no existe recalculo real de existencias, consumo de reservas ni conexion con kardex. |
| Impacto | El usuario entiende que Reservas forma parte del alcance futuro, pero no puede operar reservas en esta version. Almacenes, Articulos y Movimientos permanecen funcionales. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | Reservas debera activarse en una fase posterior cuando existan existencias calculadas, permisos y consumo/liberacion contra movimientos reales. |

### CHG-045

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:40 |
| Cambio | Kardex como consulta funcional |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/02_almacenes_inventarios.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes > Kardex, filtros de consulta, documentacion funcional |
| Descripcion | Se habilito Kardex como pantalla de consulta derivada de Movimientos. La vista permite filtrar por articulo y almacen, buscar por documento, articulo, almacen, tipo de movimiento o motivo, y muestra fecha, documento, movimiento, articulo, almacen, entradas, salidas y saldo calculado por articulo/unidad. |
| Motivo | Kardex debe funcionar como historial auditable, no como formulario. La captura operativa debe ocurrir en Movimientos y Kardex debe reflejarla. |
| Impacto | El usuario puede consultar el historial de inventario sin crear registros desde Kardex. El boton de accion queda como solo consulta y el boton global muestra aviso si se intenta crear desde esa seccion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El saldo se calcula a partir de movimientos locales del MVP; transferencias se registran como movimiento auditable sin impacto neto en saldo hasta modelar origen/destino completo. |

### CHG-046

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:47 |
| Cambio | Alta y administracion de clientes en Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Clientes, perfil comercial, perfil de facturacion |
| Descripcion | Se especializo el submodulo Clientes para crear, consultar, buscar y editar clientes. La ficha separa perfil comercial y perfil de facturacion, permitiendo manejar nombre comercial distinto de razon social o nombre fiscal, RFC/ID fiscal, regimen, uso CFDI, email de facturacion y direccion fiscal. |
| Motivo | Iniciar el modulo de Ventas con un maestro de clientes suficientemente controlado para cotizaciones, pedidos y futura facturacion. |
| Impacto | Ventas > Clientes deja de usar captura generica y cuenta con un flujo funcional de alta, consulta, busqueda y edicion de clientes con soporte Espanol/Ingles. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | La informacion fiscal se captura en el MVP, pero aun no emite facturas ni valida RFC contra un servicio fiscal externo. |

### CHG-047

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:53 |
| Cambio | Cotizaciones ligadas a clientes y productos existentes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Cotizaciones, busqueda de clientes, busqueda de productos/servicios |
| Descripcion | Se especializo el submodulo Cotizaciones para crear, consultar, buscar y editar cotizaciones. El formulario exige seleccionar un cliente dado de alta y un producto o servicio existente del catalogo de Produccion mediante busquedas tipo lookup. Tambien captura cantidad, unidad, precio unitario, descuento, vigencia, promesa de entrega, condiciones, moneda y notas. |
| Motivo | Evitar cotizaciones desconectadas de los maestros comerciales y operativos, asegurando que solo se coticen clientes y productos/servicios previamente registrados. |
| Impacto | Ventas > Cotizaciones deja de usar captura generica y ya valida dependencias con Clientes y Produccion. Si no hay clientes registrados, no permite crear cotizacion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El MVP maneja una partida por cotizacion; multiples partidas quedan documentadas como fase posterior. |

### CHG-048

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 12:55 |
| Cambio | Guias de flujo colapsables para Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Clientes, Cotizaciones, Pedidos, Entregas y Margen |
| Descripcion | Se agregaron guias de flujo colapsables al modulo de Ventas. Clientes y Cotizaciones muestran su flujo dentro de sus pantallas especializadas, y las secciones restantes de Ventas usan la guia de flujo en la vista generica. |
| Motivo | Mantener consistencia visual y funcional con Produccion y Almacenes, dejando claro el orden operativo esperado por submodulo. |
| Impacto | El usuario puede consultar el flujo recomendado de cada seccion de Ventas sin abrir formularios ni perder espacio de trabajo. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El cambio es visual/documental dentro del frontend; no modifica persistencia ni reglas de negocio. |

### CHG-049

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 13:01 |
| Cambio | Cotizaciones multipartida y PDF generico |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Cotizaciones, partidas, PDF generico |
| Descripcion | Se actualizo el formulario de cotizaciones para permitir multiples partidas, cada una ligada a un producto o servicio dado de alta. El sistema calcula subtotal y total sumando partidas, conserva compatibilidad con cotizaciones anteriores de una sola partida y agrega accion PDF para abrir una vista imprimible/guardable como PDF desde el navegador. |
| Motivo | Permitir cotizaciones comerciales mas realistas sin romper la restriccion de usar catalogos maestros para clientes y productos/servicios. |
| Impacto | Las cotizaciones pueden incluir varias partidas, consultarse, editarse y generarse como documento PDF generico. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | El PDF es generico y usa la funcion de imprimir/guardar como PDF del navegador; plantillas por tenant quedan para una fase posterior. |

### CHG-050

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-13 13:44 |
| Cambio | Resumen de estado MVP en documentacion de modulos |
| Autor | Codex |
| Archivos | `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion por modulos, estado MVP funcional |
| Descripcion | Se agrego un resumen del estado funcional actual por modulo para identificar rapidamente que ya esta implementado en Produccion, Almacenes, Ventas y Administracion, y que modulos conservan MVP generico. |
| Motivo | Mantener contexto documental antes de subir cambios al repositorio y facilitar continuidad de trabajo por modulo. |
| Impacto | La carpeta `modulos/` queda con una vista rapida del avance funcional y de las areas pendientes de especializacion. |
| Validacion | `npm run validate` ejecutado correctamente. |
| Observaciones | No modifica comportamiento del frontend. |

### CHG-051

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:25 |
| Cambio | Cierre MVP Produccion, Almacenes y Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/01_produccion.md`, `modulos/02_almacenes_inventarios.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion > Ordenes, Almacenes > Existencias y Movimientos, Ventas > Cotizaciones y Pedidos, documentacion de estado MVP |
| Descripcion | Se agrego snapshot de receta/version al generar ordenes de produccion y se bloqueo eliminar recetas con ordenes relacionadas. En Almacenes se agrego el submodulo Existencias como consulta calculada desde Movimientos, con busqueda, filtro por almacen y bloqueo de salidas o ajustes negativos que excedan saldo. En Ventas se especializo Pedidos para crear pedidos desde cotizaciones aprobadas, evitando duplicados y calculando costo/margen estimado desde las partidas. |
| Motivo | Cerrar huecos MVP detectados en los tres modulos ya trabajados sin activar todavia reservas, entregas ni microservicios reales. |
| Impacto | Produccion conserva historia de ordenes aunque cambien recetas; Almacenes gana disponibilidad calculada basica; Ventas pasa de preventa a pedido comercial inicial conectado con cotizaciones. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Entregas, reservas reales, transferencias origen/destino y consumo real de recursos quedan para fases posteriores por requerir contratos con inventario, produccion y ventas. |

### CHG-052

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:40 |
| Cambio | Entregas MVP en Ventas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, busqueda de pedidos, registro de entrega, estatus de entrega, documentacion MVP |
| Descripcion | Se especializo el submodulo Entregas para buscar pedidos, ver estatus del pedido y registrar entregas con estatus Pendiente de entrega, En ruta, Entrega parcial, Entregado, No entregado, Reprogramado o Cancelado. El formulario guarda fecha, receptor, referencia, nueva fecha cuando aplica y notas; las entregas parciales o no entregadas exigen notas, y las reprogramadas exigen nueva fecha. |
| Motivo | Completar el flujo comercial MVP despues de cotizacion y pedido, permitiendo seguimiento operativo de entrega sin activar todavia inventario/reservas reales. |
| Impacto | Ventas ahora permite dar seguimiento a pedidos desde Entregas, actualizar el estatus comercial del pedido y conservar historial de intentos o entregas registradas. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La entrega no descuenta inventario ni libera reservas; ese impacto queda para la fase de integracion con Almacenes. Los estatus se simplificaron tomando como referencia patrones de fulfillment/logistica usados por sistemas como Shopify y ERPs operativos. |

### CHG-053

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:52 |
| Cambio | Edicion de pedidos con bitacora de ajustes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/README.md`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Pedidos, edicion de pedido, historial de ajustes, documentacion MVP |
| Descripcion | Se agrego accion Editar en tarjetas de pedido. El formulario permite ajustar codigo, estatus, promesa de entrega, modo de surtido, responsable y notas, exigiendo motivo de ajuste. Cada guardado registra una bitacora dentro del pedido con fecha, usuario, motivo y cambios campo por campo con valor anterior y nuevo. |
| Motivo | Permitir correcciones operativas controladas en pedidos sin perder trazabilidad comercial ni modificar partidas/importes heredados de la cotizacion origen. |
| Impacto | Los pedidos pueden mantenerse actualizados durante el MVP y cada ajuste queda visible desde la tarjeta y el historial de edicion. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Cliente, partidas, subtotal y total permanecen controlados por la cotizacion origen; cambios comerciales de alcance o precio deberan resolverse en fases posteriores con versionamiento formal de pedido/cotizacion. |

### CHG-054

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 19:59 |
| Cambio | Entregas como vista de gestion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, filtros de estatus, consulta de entregas, documentacion MVP |
| Descripcion | Se ajusto el submodulo Entregas para funcionar unicamente como vista de gestion y consulta. Ahora lista entregas registradas, permite buscar por pedido, cliente, cotizacion, estatus, receptor, referencia o notas, y agrega filtro por estatus. Se removio la accion de alta desde esta seccion y la accion global muestra aviso de vista de gestion. |
| Motivo | Mantener Entregas como tablero operativo de seguimiento, evitando mezclar captura o cambios de flujo dentro de una vista que debe servir para controlar estatus y revisar historial. |
| Impacto | El usuario puede ver todas las entregas y sus estatus sin abrir formularios desde Entregas; el registro operativo queda reservado al flujo del pedido o a futuras integraciones. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La funcion de registro de entrega permanece disponible en codigo para integrarse despues desde flujos operativos, pero el apartado Entregas ya no la expone como accion principal. |

### CHG-055

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:06 |
| Cambio | Consulta de cotizacion desde entregas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/04_ventas_clientes.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas > Entregas, tarjetas de entrega, consulta de cotizacion relacionada |
| Descripcion | Se agrego accion Ver cotizacion en cada tarjeta de entrega y se habilito click sobre la tarjeta para abrir la vista imprimible de la cotizacion relacionada. La relacion se resuelve por el pedido ligado a la entrega o, como compatibilidad, por codigo de cotizacion guardado en la entrega. |
| Motivo | Permitir que la gestion de entregas consulte rapidamente el documento comercial origen sin convertir Entregas en una pantalla de captura. |
| Impacto | El usuario puede revisar la cotizacion asociada desde el tablero de Entregas, conservando el apartado como vista de gestion/consulta. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Si una entrega no tiene pedido/cotizacion resoluble, se muestra aviso de cotizacion no encontrada. |

### CHG-056

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:09 |
| Cambio | Modulos fuera del MVP como Proximamente |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Navegacion lateral, modulos activos MVP, estado visual de modulos pendientes |
| Descripcion | Se limitaron como activos los modulos Produccion, Almacenes y Ventas. Los demas modulos quedan sombreados en la navegacion, no despliegan submodulos ni navegan al hacer click, y al pasar el cursor muestran Proximamente. |
| Motivo | Concentrar el trabajo en los modulos ya avanzados para cerrar un MVP funcional y escalable sin distraer con apartados genericos pendientes. |
| Impacto | La experiencia del prototipo comunica con claridad el alcance actual del MVP y evita que usuarios entren a modulos no trabajados. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | La documentacion y estructura tecnica de los modulos pendientes se conserva para retomarlos en fases posteriores. |

### CHG-057

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:11 |
| Cambio | Orden de navegacion MVP |
| Autor | Codex |
| Archivos | `frontend/app.js`, `modulos/README.md`, `TRAZABILIDAD.md` |
| Secciones | Navegacion lateral, orden visual de modulos activos MVP |
| Descripcion | Se ordeno la navegacion para mostrar primero Produccion, Almacenes y Ventas, dejando Compras y el resto de modulos despues como Proximamente. El arreglo base de modulos se conserva y el orden se resuelve al renderizar el sidebar. |
| Motivo | Agrupar al inicio los modulos habilitados y enfocar el prototipo en las areas ya trabajadas para el MVP. |
| Impacto | Ventas aparece antes de Compras en la navegacion, junto con Produccion y Almacenes como modulos activos. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Cambio visual de navegacion; no modifica datos, contratos ni comportamiento interno de modulos. |

### CHG-058

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-14 21:17 |
| Cambio | Paridad de localizacion para modulos MVP activos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/modules.js`, `tools/validators/validate-active-module-localization.js`, `tools/validators/validate-all.js`, `package.json`, `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Almacenes, Ventas, panel principal de modulo, validadores, agente de diseno/localizacion |
| Descripcion | Se agregaron campos visibles en Ingles para los metadatos principales de Produccion, Almacenes y Ventas, incluyendo resumen, accion primaria, estatus, KPIs, flujo, tabla, validaciones, captura rapida y registros. El render principal ahora consume los campos localizados cuando el idioma activo es Ingles. |
| Motivo | Evitar que etiquetas y textos visibles de los tres modulos activos queden unicamente en Espanol y se ignoren en futuras revisiones del MVP. |
| Impacto | El panel principal de los modulos MVP cambia correctamente entre Espanol e Ingles en sus metadatos visibles, y el pipeline bloquea faltantes de paridad en esos campos. |
| Validacion | `npm run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | Los datos operativos creados por usuario o cargados desde simulaciones se mantienen como datos de negocio; la nueva validacion se enfoca en copy visible controlado por `frontend/data/modules.js`. |

### CHG-059

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Compatibilidad Windows en validador de arquitectura |
| Autor | Codex |
| Archivos | `tools/validators/validate-architecture.js`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Validadores, arquitectura de microfrontends |
| Descripcion | Se normalizo la ruta de `registry.js` dentro del validador de arquitectura para que se excluya correctamente tambien en Windows, donde las rutas llegan con separadores `\\`. Tambien se aclaro en README como ejecutar validaciones desde la raiz del repo y que usar en PowerShell. |
| Motivo | Permitir ejecutar `npm.cmd run validate` localmente en PowerShell sin falsos positivos de imports cruzados del propio registro de microfrontends. |
| Impacto | La validacion de arquitectura sigue bloqueando imports cruzados entre microfrontends, pero ya no falla por el archivo `frontend/microfrontends/registry.js` en Windows. |
| Validacion | `npm.cmd run validate` ejecutado correctamente antes de registrar la entrada; se repite despues del registro. |
| Observaciones | En Linux/macOS se conserva `npm run validate`; en PowerShell se recomienda `npm.cmd run validate` si `npm.ps1` esta bloqueado. |

### CHG-060

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Agente transversal de arquitectura SaaS |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes, arquitectura, multi-tenant, QA/Prod |
| Descripcion | Se agrego el Arquitecto senior de plataforma SaaS como agente transversal prioritario, separado de la matriz por modulo, para gobernar decisiones de arquitectura, ambientes, tecnologia, multi-tenancy, seguridad, contratos, CI/CD y migracion desde maqueta a plataforma real. |
| Motivo | Facilitar su consulta frecuente durante la etapa de llevar los modulos MVP a ambientes reales de QA y Produccion. |
| Impacto | Las decisiones tecnicas transversales ahora tienen un agente de referencia visible antes de la matriz modular, con responsabilidades, criterios de rechazo y entregables esperados. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El agente no reemplaza a los agentes tecnicos por modulo; los gobierna cuando una decision afecta plataforma, ambientes, contratos o escalabilidad. |

### CHG-061

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Documentacion y diagrama QA/Prod |
| Autor | Codex |
| Archivos | `docs/arquitectura/qa_prod.md`, `docs/arquitectura/diagramas/arquitectura_qa_prod.drawio`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, QA, Produccion, multi-tenant, CI/CD |
| Descripcion | Se agrego el documento inicial de arquitectura QA/Prod con diagramas Mermaid, principios, ambientes, stack recomendado, estrategia multi-tenant, CI/CD, modulos MVP, contratos, criterios minimos y riesgos. Tambien se agrego un diagrama editable `.drawio` para diagrams.net. |
| Motivo | Dar al arquitecto SaaS una base visual y documental para planear la salida de la maqueta hacia ambientes reales de QA y Produccion. |
| Impacto | El repo ahora contiene documentacion viva en Markdown y un diagrama editable para comunicar la arquitectura inicial de despliegue y operacion. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los diagramas Mermaid viven en Markdown y el archivo `.drawio` puede abrirse desde https://app.diagrams.net/. |

### CHG-062

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Documentacion de onboarding comercial SaaS |
| Autor | Codex |
| Archivos | `docs/arquitectura/onboarding_comercial_saas.md`, `docs/arquitectura/diagramas/onboarding_comercial_saas.drawio`, `docs/arquitectura/qa_prod.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, onboarding comercial, billing, provisioning, tenants, APIs |
| Descripcion | Se documento el flujo de contratacion desde la web de EsLaClave: seleccion de plan, pago en linea, webhook, provisioning idempotente, creacion de tenant, invitacion segura del administrador, wizard inicial, portal de desarrollador, credenciales API, scopes, cuotas y metering. Se agrego diagrama editable `.drawio` y se actualizo `qa_prod.md` para incluir billing/provisioning. |
| Motivo | Formalizar el flujo requerido para comprar ERClave en linea y activar tenants reales sin depender de procesos manuales ni enviar contrasenas por correo. |
| Impacto | La arquitectura QA/Prod ahora contempla servicios comerciales transversales y el repo tiene una base para discutir planes, API comercial, monetizacion y alta automatica de clientes. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diseno propone iniciar con bajo costo y evolucionar a Apigee/monetizacion avanzada cuando el volumen de integraciones lo justifique. |

### CHG-063

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-15 |
| Cambio | Decision de dominio, DNS y costo operativo inicial |
| Autor | Codex |
| Archivos | `docs/arquitectura/onboarding_comercial_saas.md`, `TRAZABILIDAD.md` |
| Secciones | Dominio, DNS y entrada publica; Decisiones pendientes |
| Descripcion | Se documento la recomendacion de comprar dominio fuera de Google, usar Cloudflare Registrar y Cloudflare DNS para el arranque, mantener la plataforma en Google Cloud, definir subdominios base, acceso por tenant, cobro hibrido y rango mensual estimado para un lanzamiento publico limitado. |
| Motivo | Aterrizar la estrategia comercial y tecnica para publicar ERClave con costos controlados, sin depender de Google Domains/Cloud Domains como ruta principal de registro. |
| Impacto | El roadmap SaaS ahora incluye decisiones iniciales de dominio, DNS, entrada publica, activacion manual o por pago en linea, y presupuesto operativo esperado para hasta 20 tenants iniciales. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los precios reales dependeran del registrador, extension de dominio, proveedor de pagos, trafico, logs, almacenamiento y uso de correo transaccional. |

### CHG-064

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Guia del siguiente paso tecnico para backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura backend MVP, ownership de datos, modelo conceptual, APIs, eventos |
| Descripcion | Se agrego una guia tecnica que define que el siguiente paso recomendado no es iniciar directo con base de datos ni listado de APIs, sino documentar primero ownership de datos, entidades canonicas, reglas backend, contratos entre modulos y despues derivar modelo de datos y APIs. |
| Motivo | Evitar acoplamiento prematuro entre Produccion, Almacenes, Ventas, Administracion, Billing y Provisioning al pasar de maqueta a backend real multi-tenant. |
| Impacto | El proyecto cuenta con una ruta clara para avanzar hacia `ownership_datos_mvp.md`, `modelo_datos_mvp.md` y `apis_mvp.md` sin romper la separacion modular. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El documento se basa en los modulos actualmente trabajados y en el agente Arquitecto senior de plataforma SaaS. |

### CHG-065

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Ownership de datos y contratos MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Ownership de entidades, contratos entre servicios, reglas multi-tenant, eventos MVP |
| Descripcion | Se agrego el documento de ownership de datos y contratos del MVP, definiendo servicios duenos, entidades por dominio, reglas multi-tenant, contratos HTTP/eventos entre Administracion, Produccion, Almacenes, Ventas, Billing, Provisioning e Integraciones, y reglas anti-acoplamiento. Tambien se marco en la guia del siguiente paso que el documento ya fue definido. |
| Motivo | Preparar el diseno de modelo de datos y APIs sobre limites claros de responsabilidad, evitando que los modulos escriban datos ajenos o dependan de reglas solo en frontend. |
| Impacto | El proyecto ya cuenta con la base arquitectonica para derivar `modelo_datos_mvp.md` y `apis_mvp.md` sin romper la separacion modular ni el aislamiento por tenant. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los contratos son iniciales y deberan convertirse despues en especificaciones OpenAPI y eventos versionados. |

### CHG-066

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-16 |
| Cambio | Modelo de datos MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Modelo PostgreSQL MVP, schemas por servicio, entidades, indices, auditoria, outbox, referencias cruzadas |
| Descripcion | Se agrego el modelo de datos MVP para PostgreSQL con estrategia inicial de schemas por servicio, columnas comunes, tablas por dominio, indices multi-tenant, referencias internas y externas, estados iniciales, reglas de integridad backend, auditoria y patron outbox. Tambien se marcaron como definidos los enlaces al modelo desde los documentos de ownership y siguiente paso backend. |
| Motivo | Convertir el ownership y contratos del MVP en una base tecnica concreta para implementar migraciones, modelos backend y APIs sin acoplar servicios ni romper aislamiento por tenant. |
| Impacto | El proyecto ya cuenta con una guia de datos para iniciar Alembic/SQLModel y derivar el documento `apis_mvp.md` con claridad sobre tablas, reglas, snapshots, idempotencia e indices. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El modelo es conceptual-operativo; aun no crea migraciones ni codigo backend. |

### CHG-067

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Agente senior de datos y persistencia |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agente transversal prioritario, arquitectura de datos, persistencia, migraciones, seguridad |
| Descripcion | Se agrego el Arquitecto senior de datos y persistencia como agente transversal especializado en modelado de datos, relaciones, PostgreSQL, Cloud SQL, SQLAlchemy/SQLModel, Alembic, multi-tenancy, auditoria, outbox, indices, migraciones seguras, seguridad y evaluacion de tecnologias de datos. |
| Motivo | Contar con un agente experto que revise la construccion de bases de datos y relaciones con la misma linea etica del proyecto: no inventar, validar fuente de verdad, proteger seguridad, trazabilidad e integridad. |
| Impacto | Las decisiones de base de datos ahora tienen un responsable transversal con criterios de rechazo, preguntas obligatorias y fuentes de verdad documentales antes de aprobar modelos o migraciones. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El agente queda junto al Arquitecto senior de plataforma SaaS porque sus decisiones afectan a todos los modulos. |

### CHG-068

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Contratos API MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | APIs por servicio, errores, paginacion, filtros, permisos, idempotencia, contratos cruzados, OpenAPI |
| Descripcion | Se agrego el documento de APIs MVP con contratos iniciales para `admin-service`, `production-service`, `inventory-service`, `sales-service`, `billing-service`, `provisioning-service` e `integration-service`. Incluye headers, paginacion, filtros, errores, permisos, endpoints por servicio, requests ejemplo, reglas backend, eventos, idempotencia y criterios para generar OpenAPI. |
| Motivo | Convertir el modelo de datos y ownership en contratos API iniciales para construir backend real con FastAPI/OpenAPI sin mezclar responsabilidades entre servicios. |
| Impacto | El proyecto ya cuenta con una base para crear especificaciones OpenAPI, modelos Pydantic, rutas FastAPI y pruebas de contrato por servicio. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El documento define contratos MVP de arquitectura; aun no crea archivos OpenAPI YAML ni codigo backend. |

### CHG-069

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Diagrama draw.io de APIs MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/apis_mvp_relaciones.drawio`, `docs/arquitectura/apis_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | APIs MVP, relaciones entre servicios, contratos cruzados, eventos y datos |
| Descripcion | Se agrego un diagrama editable `.drawio` con el flujo de entrada por frontend, apps externas y proveedor de pago, API Gateway, servicios MVP, relaciones entre Ventas, Produccion, Almacenes, Billing, Provisioning, Administracion e Integraciones, ademas de Cloud SQL, outbox, Pub/Sub y auditoria. Se enlazo el diagrama desde `apis_mvp.md`. |
| Motivo | Facilitar la revision visual de contratos API y relaciones entre servicios antes de generar especificaciones OpenAPI o implementar backend real. |
| Impacto | El equipo puede abrir el diagrama en diagrams.net para analizar flujos, fronteras de ownership, eventos y dependencias entre servicios. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diagrama es de arquitectura MVP; no representa aun infraestructura detallada por ambiente ni despliegue real. |

### CHG-070

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Diagrama draw.io de flujo de negocio de adquisicion y uso |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/flujo_negocio_adquisicion_uso.drawio`, `docs/arquitectura/onboarding_comercial_saas.md`, `TRAZABILIDAD.md` |
| Secciones | Onboarding comercial SaaS, flujo de negocio, adquisicion, activacion y uso |
| Descripcion | Se agrego un diagrama editable `.drawio` no tecnico que muestra el flujo de negocio desde descubrimiento del cliente, contratacion en linea o asesorada, confirmacion de pago o activacion manual, creacion del espacio de empresa, invitacion segura del administrador, configuracion inicial y operacion continua en Produccion, Almacenes y Ventas. Se enlazo desde el documento de onboarding comercial SaaS. |
| Motivo | Facilitar la explicacion visual del recorrido del cliente y la usabilidad del producto sin entrar en detalles tecnicos de APIs, infraestructura o servicios. |
| Impacto | El proyecto cuenta con una vista ejecutiva del flujo comercial y de adopcion para revisiones de negocio, ventas y producto. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El diagrama complementa los diagramas tecnicos existentes; no reemplaza arquitectura, APIs ni modelo de datos. |

### CHG-071

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Plan de implementacion backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/plan_implementacion_backend_mvp.md`, `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/siguiente_paso_backend_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Fases de backend MVP, admin-service, production-service, inventory-service, sales-service, billing/provisioning, integration-service, criterios QA |
| Descripcion | Se agrego el plan de implementacion backend MVP con fases recomendadas para scaffolding FastAPI, admin-service, auditoria/idempotencia, production-service, inventory-service, sales-service, integracion frontend, billing/provisioning e integration-service. Tambien se documentaron mocks temporales, validadores recomendados, criterios para QA real, criterios para modulo real, riesgos y primer sprint sugerido. |
| Motivo | Convertir la arquitectura, ownership, modelo de datos y APIs en una ruta ejecutable para construir el backend real sin sobredimensionar ni mezclar responsabilidades. |
| Impacto | El proyecto ya tiene un plan de trabajo para pasar de maqueta a QA real iniciando por plataforma minima y `admin-service`, antes de automatizar venta publica y provisioning. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | El plan no crea codigo backend todavia; sirve como guia para el siguiente sprint tecnico. |

### CHG-072

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Agentes transversales de APIs y QA |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agente transversal prioritario, APIs, contratos backend, QA, validadores, release |
| Descripcion | Se agregaron dos agentes transversales: Arquitecto senior de APIs y contratos backend, enfocado en OpenAPI, FastAPI, permisos, idempotencia, errores y contratos; e Ingeniero senior de QA, validadores y release, enfocado en automatizar reglas objetivas, pruebas, CI/CD, compatibilidad Windows/Linux y criterios de QA/Produccion. |
| Motivo | Completar los agentes necesarios antes de pasar de documentacion a contratos OpenAPI, validadores y scaffolding backend real. |
| Impacto | El proyecto cuenta con criterios explicitos para disenar APIs seguras y para convertir reglas de agentes/documentos en validadores repetibles antes de implementar servicios. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Estos agentes complementan al Arquitecto SaaS y al Arquitecto de datos; no reemplazan a los agentes tecnicos por modulo. |

### CHG-073

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Contratos OpenAPI MVP iniciales |
| Autor | Codex |
| Archivos | `.gitignore`, `contracts/api/README.md`, `contracts/api/admin-service.openapi.yaml`, `contracts/api/production-service.openapi.yaml`, `contracts/api/inventory-service.openapi.yaml`, `contracts/api/sales-service.openapi.yaml`, `contracts/api/billing-service.openapi.yaml`, `contracts/api/provisioning-service.openapi.yaml`, `contracts/api/integration-service.openapi.yaml`, `docs/arquitectura/apis_mvp.md`, `package.json`, `tools/validators/validate-all.js`, `tools/validators/validate-openapi-contracts.js`, `TRAZABILIDAD.md` |
| Secciones | Contratos API, OpenAPI, validadores, API MVP |
| Descripcion | Se crearon los contratos OpenAPI iniciales para los siete servicios MVP: Administracion, Produccion, Almacenes, Ventas, Billing, Provisioning e Integraciones. Tambien se agrego un validador `validate-openapi-contracts.js` que verifica existencia de contratos y metadatos minimos como `operationId`, `x-required-module`, `x-permissions` e `Idempotency-Key`; se conecto al comando general `npm run validate` y se actualizo el README de contratos API. |
| Motivo | Iniciar la implementacion API-first con contratos versionados antes de crear codigo FastAPI, evitando inventar endpoints durante el desarrollo backend. |
| Impacto | El proyecto ya cuenta con una primera version contractual para generar rutas, modelos Pydantic, pruebas de contrato y scaffolding backend por servicio. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Los contratos son MVP iniciales y deberan enriquecerse durante la implementacion de cada servicio. |

### CHG-074

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Scaffolding backend base con FastAPI |
| Autor | Codex |
| Archivos | `.gitignore`, `README.md`, `backend/README.md`, `backend/.env.example`, `backend/pyproject.toml`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/.gitkeep`, `backend/shared/erclave_common/*`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/*`, `backend/services/admin-service/tests/test_health.py`, `backend/services/admin_service_adapter.py`, `docs/arquitectura/apis_mvp.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `package.json`, `tools/validators/validate-all.js`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Backend FastAPI, admin-service, configuracion por ambiente, Alembic, health checks, validadores |
| Descripcion | Se creo el scaffolding backend base con FastAPI para `admin-service`, incluyendo estructura de proyecto Python, configuracion por ambiente, variable configurable `ERCLAVE_API_PUBLIC_BASE_URL` para no amarrar el dominio aun no comprado, health checks, manejo comun de errores, middleware de `correlation_id`, placeholder de tenant, Alembic inicial, tests de health y validador `validate-backend-scaffold.js` conectado a `npm run validate`. |
| Motivo | Iniciar la implementacion real del backend siguiendo el plan MVP, sin depender de dominio definitivo y preparando la base tecnica para implementar `admin-service` antes de los modulos operativos. |
| Impacto | El repo ya puede validar que existe el esqueleto backend minimo y cuenta con comandos documentados para levantar FastAPI localmente cuando se instalen dependencias. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro; `python -m py_compile` ejecutado correctamente sobre los archivos Python del scaffolding. |
| Observaciones | Aun no se implementan endpoints funcionales de `admin-service`; solo endpoints tecnicos `/health`, `/ready` y `/version`. |

### CHG-075

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Modelo fisico inicial de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/models.py`, `backend/alembic/env.py`, `backend/alembic/versions/20260617_0001_admin_service_initial.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, modelo fisico, SQLAlchemy, Alembic, multi-tenant, auditoria |
| Descripcion | Se definio el modelo fisico inicial de `admin-service` con SQLAlchemy y migracion Alembic para `admin.tenants`, `admin.users`, `admin.roles`, `admin.permissions`, `admin.role_permissions`, `admin.memberships`, `admin.membership_roles`, `admin.tenant_modules` y `admin.audit_events`. Se documento la decision de usar usuarios globales y membresias por tenant para soportar SaaS multi-tenant sin duplicar identidades. |
| Motivo | Crear la base de datos real de Administracion antes de implementar endpoints, manteniendo ownership claro de tenants, usuarios, permisos, modulos activos y auditoria. |
| Impacto | `admin-service` ya cuenta con una fuente tecnica de verdad para el schema `admin` y Alembic puede apuntar al metadata del servicio. |
| Validacion | `python -m py_compile` ejecutado correctamente sobre los archivos Python nuevos; `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Se agregaron tablas puente `role_permissions` y `membership_roles` porque son necesarias para resolver permisos efectivos por tenant. |

### CHG-076

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-17 |
| Cambio | Catalogo seed inicial de modulos MVP |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/seeds/__init__.py`, `backend/services/admin-service/app/seeds/catalog.py`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/plan_implementacion_backend_mvp.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, seeds, modulos MVP, validadores |
| Descripcion | Se creo el catalogo seed versionado de modulos MVP con `admin`, `production`, `inventory`, `sales`, `billing`, `provisioning` e `integrations`, incluyendo servicio duenio, estatus, visibilidad comercial y orden sugerido. El validador backend ahora verifica que el catalogo exista y contenga los siete modulos esperados. |
| Motivo | Definir la fuente inicial de verdad para codigos de modulo antes de crear permisos, entitlements o scripts de carga a base de datos. |
| Impacto | Los siguientes pasos pueden extraer permisos desde OpenAPI y aplicar seeds idempotentes sin inventar codigos de modulo en cada endpoint. |
| Validacion | `python -m py_compile` ejecutado correctamente sobre el catalogo seed; `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Este cambio no inserta datos en PostgreSQL; prepara el catalogo para el siguiente script seed idempotente. |

### CHG-077

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-22 |
| Cambio | Guias operativas para Cloud SQL PostgreSQL QA |
| Autor | Codex |
| Archivos | `docs/operaciones/README.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Documentacion operativa, base PostgreSQL QA, Cloud SQL Auth Proxy, migraciones Alembic |
| Descripcion | Se creo una carpeta de documentacion operativa con una guia paso a paso para crear una base PostgreSQL QA en Google Cloud SQL, conectarse desde Windows, Linux o macOS con Cloud SQL Auth Proxy, configurar `ERCLAVE_DATABASE_URL`, ejecutar Alembic y levantar `admin-service`. |
| Motivo | Facilitar que el ambiente de base de datos en nube pueda configurarse de forma repetible y entendible sin depender de conocimiento previo avanzado de operaciones cloud. |
| Impacto | El proyecto cuenta con una ruta documentada para crear la base QA compartida antes de ejecutar migraciones reales y preparar seeds idempotentes. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | La guia no crea recursos automaticamente ni guarda secretos; usa placeholders para contrasenas, proyecto GCP y connection name. |

### CHG-078

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Seed idempotente de permisos MVP |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/seeds/permissions.py`, `backend/scripts/seed_admin_mvp.py`, `backend/services/admin-service/tests/test_permission_seeds.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, seeds, permisos MVP, OpenAPI, PostgreSQL QA |
| Descripcion | Se creo un extractor de permisos MVP desde `contracts/api/*.openapi.yaml` usando `x-permissions`, junto con un runner idempotente que aplica los permisos sobre `admin.permissions` mediante `INSERT ... ON CONFLICT (code) DO UPDATE`. Tambien se agrego una prueba del extractor y documentacion de ejecucion. |
| Motivo | Poblar la base QA con el catalogo inicial de permisos reales despues de ejecutar la migracion Alembic, sin duplicar registros al reintentar el proceso. |
| Impacto | `admin-service` ya cuenta con un camino repetible para cargar permisos globales MVP en PostgreSQL y preparar roles, policy evaluation y entitlements reales. |
| Validacion | `python -m py_compile` sobre el runner y extractor; `pytest services/admin-service/tests/test_permission_seeds.py`; `python scripts/seed_admin_mvp.py --dry-run`; `npm.cmd run validate`. |
| Observaciones | El seed aplica `admin.permissions`; no crea tenants, roles, membresias ni entitlements. El catalogo de modulos sigue versionado en codigo porque el modelo fisico inicial aun no tiene tabla global `admin.modules`. |

### CHG-079

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Agente custodio de la base de datos ERClave |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, base de datos ERClave, migraciones, validadores, impacto entre schemas |
| Descripcion | Se agrego un agente transversal especializado en la base de datos real de ERClave. Su rol es conocer y proteger schemas, migraciones Alembic, seeds, dependencias entre servicios, drift entre docs/modelos/base, impacto entre schemas y reglas automatizables para evitar que el proyecto crezca rompiendo datos o ownership. |
| Motivo | Cubrir una necesidad mas especifica que el diseno general de datos: vigilancia continua de la base ERClave concreta y automatizacion de alertas cuando un cambio pueda afectar otros schemas, servicios, reportes, permisos o ambientes. |
| Impacto | Los cambios futuros que toquen modelos, migraciones, seeds, contratos persistentes o base QA/Prod deberan considerar a este agente junto con el Arquitecto de datos y el Ingeniero QA. |
| Validacion | `npm.cmd run validate` ejecutado correctamente despues del registro. |
| Observaciones | Este cambio define el rol; los validadores concretos del custodio se implementaran progresivamente conforme existan mas schemas y migraciones. |

### CHG-080

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Validadores de agentes y guardrails de base de datos |
| Autor | Codex |
| Archivos | `.gitignore`, `tools/validators/validate-agents.js`, `tools/validators/validate-db-guardrails.js`, `tools/validators/validate-all.js`, `package.json`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes, validadores, custodio de base de datos, migraciones Alembic, seeds idempotentes |
| Descripcion | Se agregaron validadores automaticos para confirmar que los agentes transversales y por modulo siguen presentes y para revisar guardrails estaticos de base de datos: migraciones Alembic con revision unica, ausencia de operaciones destructivas en `upgrade`, `tenant_id` en tablas administrativas tenant-scoped, ausencia de FK cruzadas, extractor de permisos y seed idempotente con `ON CONFLICT`. |
| Motivo | Convertir al nuevo custodio de base de datos ERClave y las reglas de agentes en checks ejecutables antes de seguir creciendo el backend. |
| Impacto | `npm run validate` ahora falla si se pierde cobertura de agentes o si una migracion/seed rompe reglas basicas de seguridad estructural de la base. |
| Validacion | `npm.cmd run validate:agents`, `npm.cmd run validate:db-guardrails` y `npm.cmd run validate` ejecutados correctamente. |
| Observaciones | Los guardrails actuales son estaticos y no requieren conexion a Cloud SQL. Mas adelante pueden ampliarse con comparacion contra schema real de QA/Prod cuando exista un flujo seguro con credenciales. |

### CHG-081

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Validador de compatibilidad multiplataforma |
| Autor | Codex |
| Archivos | `tools/validators/validate-cross-platform.js`, `tools/validators/validate-all.js`, `package.json`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Validadores, compatibilidad Windows/Linux/macOS, automatizacion, operaciones Cloud SQL |
| Descripcion | Se agrego un validador estatico para proteger la portabilidad del proyecto: revisa que scripts npm, validadores Node y scripts backend no dependan de comandos Windows-only, que la guia Cloud SQL mantenga instrucciones para Windows, Linux y macOS, y que el workflow de GitHub Actions ejecute `npm run validate` sobre Ubuntu. |
| Motivo | Confirmar que lo construido para seeds, validadores y operacion QA pueda mantenerse usable desde Linux, Windows y macOS conforme crezca el equipo o se mueva a CI. |
| Impacto | `npm run validate` ahora alerta si se introduce una dependencia operativa de sistema operativo en scripts compartidos o si se pierde documentacion multiplataforma esencial. |
| Validacion | `npm.cmd run validate:cross-platform` y `npm.cmd run validate` ejecutados correctamente. |
| Observaciones | Los comandos de usuario para activar `.venv`, descargar Cloud SQL Proxy o usar PowerShell siguen documentados por sistema operativo; el validador se enfoca en automatizacion compartida y documentacion minima. |

### CHG-082

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Seed idempotente de tenant demo QA |
| Autor | Codex |
| Archivos | `backend/scripts/seed_admin_qa_demo.py`, `backend/services/admin-service/tests/test_qa_demo_seed.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `docs/operaciones/cloud_sql_postgres_qa.md`, `tools/validators/validate-backend-scaffold.js`, `tools/validators/validate-db-guardrails.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, QA demo, tenants, usuarios, roles, permisos, modulos activos |
| Descripcion | Se creo un script idempotente para poblar QA con el tenant `demo-qa`, usuario `admin.qa@erclave.local`, rol `owner`, membresia activa, modulos activos de QA y asignacion del rol owner a todos los permisos activos. Tambien se agregaron pruebas y guardrails para confirmar que el seed use `ON CONFLICT` en las tablas afectadas. |
| Motivo | Tener un primer tenant real de QA para validar permisos, membresias, roles y modulos activos antes de implementar endpoints funcionales de `admin-service`. |
| Impacto | La base QA puede pasar de estructura y catalogo de permisos a un contexto SaaS minimo operable para pruebas de policy evaluation y futuros endpoints. |
| Validacion | `python -m py_compile` sobre el script; `pytest services/admin-service/tests`; `python scripts/seed_admin_qa_demo.py --dry-run`; `npm.cmd run validate`. |
| Observaciones | El seed demo no crea contrasenas ni credenciales de autenticacion; solo crea identidad, membresia y autorizaciones internas para QA. |

### CHG-083

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Endpoints MVP de lectura de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/app/main.py`, `backend/services/admin_service_adapter.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, FastAPI, PostgreSQL, tenants, entitlements, policy evaluation, usuarios, roles |
| Descripcion | Se implemento el primer corte funcional de endpoints reales de `admin-service`: `GET /v1/tenants/{tenant_id}`, `GET /v1/tenants/{tenant_id}/entitlements`, `POST /v1/policy/evaluate`, `GET /v1/users` y `GET /v1/roles`. Se agrego repositorio SQL para leer PostgreSQL, schemas Pydantic y pruebas con repositorio falso para validar el contrato sin depender de Cloud SQL en CI. |
| Motivo | Crear la primera API real que el frontend podra consumir antes de migrar pantallas operativas fuera de `mockDb` y `localStorage`. |
| Impacto | `admin-service` deja de ser solo health checks y puede leer tenants, modulos activos, usuarios, roles y evaluar permisos sobre los datos seed de QA. |
| Validacion | `python -m py_compile` sobre los nuevos modulos y adapter; `pytest services/admin-service/tests`; `uvicorn services.admin_service_adapter:app --port 8001` carga correctamente; `npm.cmd run validate`. |
| Observaciones | Los endpoints mutables siguen pendientes. La autenticacion real aun no esta implementada; `X-Tenant-Id` es header operativo temporal para lecturas de usuarios y roles. |

### CHG-084

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Capa frontend API para admin-service |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/api/client.js`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/data/modules.js`, `backend/services/admin-service/app/main.py`, `README.md`, `backend/README.md`, `tools/validators/validate-active-module-localization.js`, `tools/validators/validate-architecture.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, admin-service, API client, CORS local, Administracion, validadores de arquitectura |
| Descripcion | Se agrego una capa `frontend/api/` para centralizar consumo HTTP, con cliente base, configuracion local y funciones de `admin-service`. Se habilito el modulo visual `Administracion` en la navegacion MVP con un panel hibrido mock/API para tenant, modulos activos, usuarios, roles y policy evaluation. Tambien se habilito CORS local en `admin-service` para permitir llamadas desde el frontend local. |
| Motivo | Conectar el primer bloque real de APIs sin romper la maqueta ni permitir `fetch` dispersos en pantallas. |
| Impacto | El frontend puede empezar a leer datos reales de Cloud SQL QA mediante `admin-service`, conservando fallback mock. La arquitectura ahora exige que nuevas llamadas HTTP pasen por `frontend/api/`. |
| Validacion | `python -m py_compile services/admin-service/app/main.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate:active-localization`; `npm.cmd run validate`. |
| Observaciones | La conexion API usa el tenant demo QA por defecto. Autenticacion real, manejo de token y despliegue de frontend QA quedan pendientes para siguientes cambios. |

### CHG-085

| Campo | Contenido |
|---|---|
| Fecha | 2026-06-29 |
| Cambio | Acceso a Administracion desde engrane |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, navegacion, Administracion, shell |
| Descripcion | Se movio el acceso visual de `Administracion` fuera de la lista principal de modulos y se conecto al boton de engrane del footer lateral. El engrane navega al panel de Administracion y queda marcado como activo cuando esa vista esta seleccionada. |
| Motivo | Mantener la barra principal enfocada en modulos operativos y dejar Administracion como configuracion/plataforma accesible desde el icono esperado. |
| Impacto | El panel hibrido mock/API de Administracion sigue disponible, pero ya no aparece como modulo operativo principal. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate:active-localization`; `npm.cmd run validate`. |
| Observaciones | Administracion sigue incluida en validaciones de localizacion activa porque es una vista real conectada al admin-service. |

### CHG-086

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Entitlements operables en admin-service y frontend |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, entitlements, Administracion, API QA, frontend |
| Descripcion | Se implemento `PUT /v1/tenants/{tenant_id}/entitlements/{module_code}` para activar, inactivar o suspender modulos de un tenant usando PostgreSQL. El panel de Administracion ahora muestra acciones por modulo en modo API QA y refresca los datos reales tras cada cambio. |
| Motivo | Pasar el primer bloque de Administracion de lectura real a operacion real, empezando por modulos activos del tenant porque impactan directamente la disponibilidad SaaS y la evaluacion de politicas. |
| Impacto | El tenant demo QA puede administrar entitlements desde el backend y desde la maqueta local sin tocar manualmente Cloud SQL. El frontend conserva modo mock y solo habilita acciones cuando la API QA esta lista. |
| Validacion | `pytest`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; prueba real contra Cloud SQL QA cambiando `integrations` a `inactive` y restaurandolo a `active`; `/ready` respondio `ready`. |
| Observaciones | Al cierre de este cambio quedaban pendientes los endpoints mutables de tenants, usuarios y roles. No se agrego migracion porque `admin.tenant_modules` ya incluia `status`, `source` y `limits`. |

### CHG-087

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Usuarios operables en admin-service y panel de Administracion |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, usuarios, membresias, roles de membresia, Administracion, API QA |
| Descripcion | Se implementaron `POST /v1/users/invitations`, `PATCH /v1/users/{user_id}` y `POST /v1/users/{user_id}/disable`. La invitacion crea o actualiza identidad global, crea o reactiva la membresia del tenant y asigna roles de membresia. El panel de Administracion agrega formulario de invitacion y accion de desactivar usuario en modo API QA. |
| Motivo | Continuar la secuencia arquitectonica despues de entitlements: administrar usuarios y membresias antes de avanzar a roles/permisos finos o autenticacion real. |
| Impacto | QA ya puede operar usuarios del tenant demo desde API y frontend local sin introducir contrasenas ni proveedor de identidad. El actor demo queda protegido en UI para evitar desactivar el usuario usado en pruebas de policy evaluation. |
| Validacion | `pytest services/admin-service/tests/test_admin_api.py`; `pytest`; `npm.cmd run validate:syntax`; prueba real contra Cloud SQL QA invitando, editando y desactivando un usuario temporal; `/ready` respondio `ready`. |
| Observaciones | La desactivacion afecta la membresia del tenant, no elimina la identidad global. Quedan pendientes auditoria/idempotencia formal y endpoints mutables de roles. |

### CHG-088

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Auditoria e idempotencia base para mutaciones de admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, auditoria, idempotencia, contratos OpenAPI, Administracion |
| Descripcion | Se agrego validacion obligatoria de `Idempotency-Key` en las mutaciones actuales de entitlements y usuarios. Cada comando registra un evento en `admin.audit_events` dentro de la misma transaccion, con accion, recurso, estado anterior, estado posterior, `correlation_id` e `idempotency_key`. El cliente frontend genera headers por comando y el contrato OpenAPI quedo alineado para `PATCH /v1/users/{user_id}`. |
| Motivo | Cerrar la recomendacion arquitectonica previa antes de avanzar a roles/permisos mutables o migrar modulos operativos, asegurando trazabilidad minima de acciones criticas. |
| Impacto | Las operaciones reales de Administracion quedan auditadas y los reintentos empiezan a portar una clave idempotente verificable. Todavia no existe tabla dedicada de comandos procesados ni respuesta cacheada por idempotency key. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py services/admin_service_adapter.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate`. `python -m pytest services/admin-service/tests/test_admin_api.py` no se pudo ejecutar porque el ambiente local no tiene instalado `pytest`. |
| Observaciones | La auditoria usa `actor_type='system'` de forma temporal hasta integrar autenticacion real y actor autenticado. |

### CHG-089

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Roles y permisos operables en admin-service |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `backend/README.md`, `backend/services/admin-service/README.md`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, roles, permisos, policy, auditoria, Administracion |
| Descripcion | Se implementaron `POST /v1/roles`, `PATCH /v1/roles/{role_id}`, `PUT /v1/roles/{role_id}/permissions` y `GET /v1/permissions`. Las mutaciones de roles exigen `Idempotency-Key`, aceptan `X-Correlation-Id` y registran auditoria en `admin.audit_events`. El panel de Administracion permite crear roles, activar/inactivar roles y asignar permisos disponibles desde API QA. |
| Motivo | Completar el nucleo SaaS minimo de Administracion antes de iniciar la migracion de modulos operativos reales. |
| Impacto | QA puede operar roles y permisos sin tocar manualmente Cloud SQL. `POST /v1/policy/evaluate` puede reflejar cambios de permisos hechos desde el propio `admin-service`. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py services/admin_service_adapter.py`; `python -m pytest services/admin-service/tests/test_admin_api.py` con 20 tests correctos; `python -m pytest` con 25 tests correctos; `npm.cmd run validate:syntax`; `npm.cmd run validate`. |
| Observaciones | La UI permite agregar permisos al rol; la remocion fina de permisos queda para un refinamiento posterior junto con actor autenticado real. |

### CHG-090

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Rediseño del panel operativo de Administracion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, panel API QA, UX |
| Descripcion | Se rediseñaron las secciones de modulos activos, usuarios y roles del panel de Administracion para usar un tablero compacto con secciones delimitadas, registros escaneables, badges de estado, formularios integrados y layout responsive. |
| Motivo | Mejorar la legibilidad y operabilidad del panel conectado a `admin-service`, evitando listas extendidas y formularios demasiado dispersos. |
| Impacto | La Administracion en modo API QA conserva las mismas acciones pero se presenta con una interfaz mas clara para probar entitlements, usuarios, roles y permisos. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`. |
| Observaciones | No cambia contratos ni comportamiento backend. |

### CHG-091

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Reacomodo espacial del panel de Administracion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, distribucion, UX |
| Descripcion | Se reemplazo el hero alto por un encabezado operativo mas compacto con KPIs integrados. El cuerpo de Administracion se reacomodo en una grilla de 12 columnas: modulos activos como franja superior, usuarios y roles como paneles balanceados, con listas contenidas y formularios mas compactos. |
| Motivo | Mejorar la distribucion, reducir espacios vacios y aprovechar mejor el ancho disponible durante pruebas de API QA. |
| Impacto | El panel conserva las mismas acciones, pero ahora prioriza lectura rapida y operacion repetida sin crecer verticalmente de forma innecesaria. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`. |
| Observaciones | Cambio visual sin impacto en contratos ni backend. |

### CHG-092

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Correccion responsive del panel de Administracion |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, responsive, UX |
| Descripcion | Se reemplazaron las grillas fijas del panel de Administracion por un flujo fluido de una columna con subgrids `auto-fit`, se redujeron anchos minimos rigidos, se ajustaron KPIs, formularios, registros y acciones para evitar desbordes al cambiar el tamaño de pantalla. |
| Motivo | Evitar que el modulo de Administracion se desordene en ventanas medianas, tablets o pantallas moviles. |
| Impacto | El panel conserva el diseño operativo, pero ahora se mantiene ordenado por defecto: header en una columna, modulos arriba, usuarios y roles apilados, subgrids fluidos y controles a ancho completo en movil. |
| Validacion | `npm.cmd run validate:syntax`; `npm.cmd run validate:architecture`; `npm.cmd run validate`. |
| Observaciones | Cambio visual sin impacto en contratos ni backend. |

### CHG-093

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Prueba API QA real de Administracion |
| Autor | Codex |
| Archivos | `TRAZABILIDAD.md` |
| Secciones | Admin-service, QA real, entitlements, usuarios, roles, permisos, auditoria |
| Descripcion | Se ejecuto un flujo real contra `admin-service` en `http://127.0.0.1:8000` conectado a Cloud SQL QA mediante proxy local. Se valido lectura de tenant, lectura de entitlements, inactivacion/restauracion de `inventory`, lectura de usuarios, invitacion y desactivacion de usuario temporal, lectura de roles, creacion/inactivacion/activacion/inactivacion final de rol temporal, lectura de permisos, asignacion de permiso a rol temporal y `POST /v1/policy/evaluate`. |
| Motivo | Confirmar que el nucleo MVP de Administracion opera contra QA real y no solo mediante tests unitarios o maqueta local. |
| Impacto | Se confirmo persistencia real en Cloud SQL QA, restauracion del modulo `inventory` a `active`, usuario temporal desactivado y rol temporal `codex_qa_1782963345` inactivo. |
| Validacion | Flujo API completo exitoso; `policy.evaluate` respondio `allowed=True`; consulta directa a `admin.audit_events` encontro 9 eventos con `Idempotency-Key` de la corrida `1782963345`. |
| Observaciones | Quedaron datos temporales auditables en QA: usuario `codex.qa.1782963345@erclave.local` desactivado y rol `codex_qa_1782963345` inactivo. |

### CHG-094

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-01 |
| Cambio | Primer corte backend real de production-service |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260701_0002_production_service_initial.py`, `backend/services/production-service/app/*`, `backend/services/production-service/tests/test_production_api.py`, `backend/services/production_service_adapter.py`, `backend/pyproject.toml`, `backend/README.md`, `backend/services/production-service/README.md`, `tools/validators/validate-backend-scaffold.js`, `TRAZABILIDAD.md` |
| Secciones | Production-service, FastAPI, PostgreSQL, productos/servicios, backend MVP |
| Descripcion | Se creo el primer scaffold funcional de `production-service` con FastAPI, health checks compartidos, repositorio SQL, schemas Pydantic, adapter para Uvicorn, pruebas con repositorio falso y migracion inicial para `production.product_services`. El primer corte implementa `GET/POST /v1/production/product-services`, `GET/PATCH /v1/production/product-services/{product_service_id}` y `PATCH /v1/production/product-services/{product_service_id}/status`. |
| Motivo | Iniciar el primer modulo operativo real despues de validar `admin-service` en QA, empezando por el catalogo de productos/servicios como base para recetas y ordenes. |
| Impacto | El backend ya tiene una frontera real para Produccion sin escribir inventario, costos ni contabilidad. La suite de backend ahora cubre admin-service y production-service. |
| Validacion | `python -m py_compile` sobre los nuevos modulos y migracion; `python -m pytest services/production-service/tests/test_production_api.py` con 8 tests correctos; `python -m pytest` con 33 tests correctos; `npm.cmd run validate`; `alembic upgrade head` aplicado en Cloud SQL QA; prueba API real en `production-service` local puerto `8002` creando, leyendo, actualizando, inactivando, restaurando y buscando `codex_prod_1782964372`. |
| Observaciones | Quedo dato temporal QA `codex_prod_1782964372` activo para validar persistencia. Recetas, versiones, ordenes, areas laborales y maquinaria quedan para cortes posteriores. |

### CHG-095

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Diagramas de estado real backend MVP |
| Autor | Codex |
| Archivos | `docs/arquitectura/diagramas/apis_mvp_relaciones.drawio`, `docs/arquitectura/diagramas/estado_actual_backend_mvp.drawio`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura, diagramas, backend MVP, QA real |
| Descripcion | Se ajusto el diagrama de APIs MVP y relaciones para distinguir servicios ya operables en QA de servicios objetivo. `admin-service` queda marcado como real para entitlements, usuarios, roles, permisos, policy y auditoria; `production-service` queda marcado como real parcial para `product_services`. Tambien se creo un diagrama nuevo del estado actual backend MVP mostrando frontend local, servicios FastAPI locales, Cloud SQL Auth Proxy, Cloud SQL QA, schemas reales, migraciones, pruebas y validadores. |
| Motivo | Evitar que los diagramas mezclen roadmap objetivo con estado implementado, despues de validar Administracion y el primer corte de Produccion contra QA real. |
| Impacto | El arquitecto puede revisar visualmente que ya existe un nucleo QA real y que recetas, ordenes, inventario, ventas, billing, provisioning e integraciones siguen como fases posteriores. |
| Validacion | `npm.cmd run validate:traceability`; `npm.cmd run validate:architecture`. |
| Observaciones | No cambia contratos, backend ni frontend; es actualizacion documental editable en diagrams.net. |

### CHG-096

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Session Context MVP previo al login |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/admin.js`, `frontend/app.js`, `backend/README.md`, `backend/services/admin-service/README.md`, `TRAZABILIDAD.md` |
| Secciones | Admin-service, session context, permisos, entitlements, frontend, navegacion |
| Descripcion | Se agrego `GET /v1/session/context` para devolver tenant, usuario, entitlements, permisos efectivos y modulos activos usando `X-Tenant-Id` y `X-Actor-Id` como contexto temporal. El frontend en modo API QA carga ese contexto, bloquea modulos inactivos o no contratados y refresca la sesion despues de cambios de entitlements desde Administracion. |
| Motivo | Dar el paso recomendado antes del login completo: eliminar dependencias de navegacion fija y hacer que la app use el contexto real de tenant, usuario, permisos y modulos activos desde `admin-service`. |
| Impacto | Si un modulo se desactiva para el tenant QA, la navegacion del frontend deja de permitir entrada a ese modulo en modo API. Este contrato queda listo para reemplazar `X-Actor-Id` por el subject de un token OIDC/JWT en la fase de login real. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:syntax`; `npm.cmd run validate:openapi`. |
| Observaciones | No implementa login ni proveedor de identidad todavia; establece la frontera de sesion que usara el login posterior. |

### CHG-097

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Publicacion QA en Firebase Hosting y Cloud Run |
| Autor | Codex |
| Archivos | `.firebaserc`, `firebase.json`, `backend/Dockerfile`, `backend/services/admin-service/app/main.py`, `backend/services/production-service/app/main.py`, `frontend/env.js`, `frontend/index.html`, `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Deploy QA, Firebase Hosting, Cloud Run, Cloud SQL QA, CORS |
| Descripcion | Se preparo el repo para despliegue QA: Firebase Hosting sirve la maqueta desde `frontend`, Cloud Run publica `admin-service-qa` y `production-service-qa`, y el frontend online arranca en modo API apuntando a `admin-service-qa`. Se agrego configuracion runtime `frontend/env.js`, Dockerfile comun para servicios FastAPI y CORS para dominios Firebase `erclave.web.app` / `erclave.firebaseapp.com`. |
| Motivo | Permitir que negocio, arquitectura y comercial revisen la maqueta QA en linea usando el backend QA real sin depender de levantar servicios locales. |
| Impacto | La maqueta queda disponible en `https://erclave.web.app` y consume `admin-service-qa` en Cloud Run conectado a Cloud SQL QA. `production-service-qa` queda publicado para el primer corte real de productos/servicios. |
| Validacion | Deploy exitoso de Cloud Run para `admin-service-qa` y `production-service-qa`; deploy exitoso de Firebase Hosting; smoke test `GET /ready`, `GET /v1/session/context`, `GET /v1/production/product-services`, `curl -I https://erclave.web.app`, CORS preflight desde `https://erclave.web.app`. |
| Observaciones | Los servicios QA estan expuestos sin autenticacion final para facilitar revision temprana. Antes de compartir masivamente conviene agregar control de acceso, login o proteccion temporal. |

### CHG-098

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Login QA con Firebase Auth |
| Autor | Codex |
| Archivos | `backend/pyproject.toml`, `backend/shared/erclave_common/config.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/scripts/seed_admin_qa_demo.py`, `backend/README.md`, `contracts/api/admin-service.openapi.yaml`, `frontend/auth.js`, `frontend/api/client.js`, `frontend/api/admin.js`, `frontend/api/config.js`, `frontend/app.js`, `frontend/env.js`, `frontend/index.html`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, admin-service, session context, frontend QA, Cloud Run, Firebase Hosting |
| Descripcion | Se conecto la maqueta QA con Firebase Auth Web usando Google Sign-In en el frontend y verificacion de Firebase ID tokens en `admin-service`. En `ERCLAVE_AUTH_MODE=firebase`, `GET /v1/session/context` resuelve el usuario por email autenticado y tenant, dejando `X-Actor-Id` como fallback local/demo. El frontend envia `Authorization: Bearer <idToken>`, muestra una puerta de acceso Google en modo API y conserva el modo mock para revision sin backend. |
| Motivo | Pasar del contexto temporal por header a una primera autenticacion real reutilizable para QA, sin perder velocidad de desarrollo local. |
| Impacto | `admin-service-qa` ya rechaza `session/context` sin token, el tenant QA tiene owner corporativo `eslaclavecaf@gmail.com` sembrado como usuario activo, y la maqueta publicada en `https://erclave.web.app` pide login antes de consumir APIs reales. |
| Validacion | `python -m pytest`; `node --check frontend/app.js`; `node --check frontend/auth.js`; `node --check frontend/api/client.js`; deploy Cloud Run `admin-service-qa` revision `admin-service-qa-00002-xmr`; seed QA aplicado via Cloud SQL Auth Proxy; deploy Firebase Hosting; smoke tests `curl -I https://erclave.web.app`, `GET /ready`, `GET /v1/session/context` sin token devuelve 401 `auth_required`, preflight CORS con `Authorization` devuelve 200. |
| Observaciones | Falta inicializar Firebase Authentication y habilitar el proveedor Google en Firebase Console; el intento por API devolvio `CONFIGURATION_NOT_FOUND` porque Auth aun no tiene configuracion inicial en el proyecto. |

### CHG-099

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Modelo multitenant e identidad SaaS |
| Autor | Codex |
| Archivos | `docs/arquitectura/modelo_multitenant.md`, `docs/arquitectura/qa_prod.md`, `docs/arquitectura/ownership_datos_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Multitenant, Firebase Auth, roles, permisos, entitlements, billing, provisioning, contratacion en linea |
| Descripcion | Se documento el modelo multitenant objetivo: Firebase Auth solo resuelve identidad, mientras ERClave gobierna tenant, membresias, roles, permisos efectivos, modulos contratados, limites, estados comerciales y policy. Tambien se aterrizo el flujo de `session/context`, seleccion de tenant, estados de tenant, reglas de contratacion en linea, provisioning idempotente, implicaciones para APIs, datos, frontend y soporte interno. |
| Motivo | Evitar que la incorporacion de Firebase Auth desplace reglas de negocio hacia el proveedor de identidad y dejar claro como escalar a usuarios multiempresa, roles por tenant y compra en linea. |
| Impacto | Arquitectura queda alineada para implementar login real, selector de tenant, autorizacion backend, billing/provisioning y pruebas de aislamiento sin redisenar la base conceptual. |
| Validacion | Documento revisado contra `ownership_datos_mvp.md`, `onboarding_comercial_saas.md`, `modelo_datos_mvp.md` y estado actual de `session/context`. |
| Observaciones | No cambia codigo ni contratos; es definicion arquitectonica para guiar siguientes fases. |

### CHG-100

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-02 |
| Cambio | Actualizacion de agentes con contexto multitenant |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, plataforma SaaS, datos, APIs, QA, reglas comunes, Administracion |
| Descripcion | Se actualizaron los agentes necesarios para incorporar el modelo multitenant definido: Firebase/Auth solo identifica, mientras ERClave resuelve tenant, membresias, roles, permisos, entitlements, limites, billing/provisioning y policy. Se agregaron preguntas, rechazos y fuentes obligatorias para Arquitectura SaaS, Datos/Persistencia, APIs/Contratos, QA/Release, reglas comunes y Administracion. |
| Motivo | Asegurar que futuras decisiones tecnicas y funcionales no coloquen permisos, modulos contratados o estado comercial en Firebase, frontend o localStorage, y que los agentes protejan usuarios multiempresa y aislamiento por tenant. |
| Impacto | Las revisiones futuras deberan validar `session/context`, membresia activa, rol por tenant, modulo contratado, permiso efectivo, estados comerciales e idempotencia de billing/provisioning antes de aprobar cambios relacionados. |
| Validacion | Revision documental de `AGENTES.md` contra `docs/arquitectura/modelo_multitenant.md`; `npm.cmd run validate:traceability`; `npm.cmd run validate`. |
| Observaciones | No cambia codigo de ejecucion; fortalece criterios de revision y decision. |

### CHG-101

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-03 |
| Cambio | Cierre login local y autorizacion backend comun |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/env.js`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, local demo, admin-service, permisos efectivos, mutaciones, QA |
| Descripcion | Se ajusto la configuracion frontend para que `localhost`/`127.0.0.1` usen backend local y modo demo sin quedar bloqueados por Firebase Auth, mientras `erclave.web.app` conserva `authMode=firebase`. Se agrego una dependencia comun de autorizacion en `admin-service` que, en `ERCLAVE_AUTH_MODE=firebase`, valida token, membresia activa y permiso efectivo antes de ejecutar mutaciones de entitlements, usuarios y roles. |
| Motivo | Cerrar el paso minimo de login QA/local sin bloquear desarrollo, y avanzar al guard backend recomendado para que las acciones criticas no dependan solo de UI o de token autenticado sin permiso. |
| Impacto | Local vuelve a cargar con `http://127.0.0.1:8000` y `X-Actor-Id` demo; QA mantiene Firebase obligatorio. Las mutaciones en QA quedan protegidas por permisos como `admin.entitlement.manage`, `admin.user.invite`, `admin.user.update`, `admin.user.disable`, `admin.role.create` y `admin.role.update`. |
| Validacion | `python -m pytest`; `npm.cmd run validate`; deploy Cloud Run `admin-service-qa` revision `admin-service-qa-00003-cwf`; deploy Firebase Hosting; smoke local `GET /v1/session/context` con `X-Actor-Id`; smoke QA `GET /ready`; `GET /v1/session/context` sin token devuelve 401 `auth_required`; mutacion `PUT /v1/tenants/{tenant_id}/entitlements/inventory` sin token devuelve 401 `auth_required`; intento por API de inicializar Firebase Auth devolvio `CONFIGURATION_NOT_FOUND`, confirmando que falta el paso manual de Firebase Console. |
| Observaciones | Para cerrar login real en QA falta iniciar Firebase Authentication en consola y habilitar Google provider; la automatizacion por API no puede crear la config inicial si Auth no fue inicializado. |

### CHG-102

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Administracion como centro de configuracion inicial |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Administracion, usuarios, roles, permisos, organizacion, configuracion base, Firebase Auth |
| Descripcion | Se rediseño Administracion como hub de configuracion con tarjetas clicables para Usuarios, Roles, Permisos, Organizacion y Configuracion base. Los paneles internos solo se abren al seleccionarlos. Usuarios ahora permite invitar/reactivar enviando correo de activacion, inactivar membresia y eliminar acceso; el backend agrega `DELETE /v1/users/{user_id}`, asegura identidad Firebase al invitar y elimina identidad Firebase por email al borrar. `session/context` activa membresias invitadas cuando el usuario entra con token Firebase valido. |
| Motivo | Convertir Administracion en el modulo de bienvenida/configuracion inicial del sistema, evitando usar espacio en metricas generales y cerrando el flujo operativo de alta, baja y reingreso por invitacion. |
| Impacto | El tenant puede administrar accesos de forma mas clara y preparar organizacion/catalogos base antes de operar otros modulos. La eliminacion de usuario queda protegida por permiso `admin.user.delete`, contrato OpenAPI e idempotencia. En un usuario sin otras membresias, ERClave elimina tambien la identidad global local; en modo Firebase elimina la identidad del proveedor. |
| Validacion | `node --check frontend/app.js`; `node --check frontend/api/admin.js`; `npm.cmd run validate:syntax`; `npm.cmd run validate:openapi`; `npm.cmd run validate`; `ERCLAVE_AUTH_MODE=demo python -m pytest services/admin-service/tests/test_admin_api.py`; `ERCLAVE_AUTH_MODE=demo python -m pytest`; seed local QA `scripts/seed_admin_mvp.py` y `scripts/seed_admin_qa_demo.py` aplicado correctamente con 94 permisos. |
| Observaciones | Los paneles Organizacion y Configuracion base quedan como estructura funcional inicial; sus formularios persistentes se implementaran cuando existan endpoints de tenant settings, razones sociales, sucursales y catalogos base. El seed de permisos y asignaciones del owner se reejecuto en la base QA local para incluir `admin.user.delete`. |

### CHG-103

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Organizacion configurable desde tenant settings |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260705_0003_admin_tenant_settings.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Administracion, Organizacion, Settings, corporativo, razones sociales, sucursales |
| Descripcion | Se implemento persistencia generica de configuraciones por tenant con `admin.tenant_settings` y endpoints `GET /v1/settings` y `PUT /v1/settings/{key}`. El frontend ahora guarda `organization.profile` con formulario editable de corporativo, altas de razones sociales y altas de sucursales. El contacto dejo de ser una seccion independiente y se movio como campos de corporativo y razon social. Se reordeno el hub de Administracion para mostrar primero Organizacion, despues Configuracion base y luego Usuarios, Roles y Permisos. |
| Motivo | Convertir Administracion en la bienvenida real de configuracion del tenant, permitiendo capturar datos corporativos y fiscales antes de operar los demas modulos. |
| Impacto | Los cambios de organizacion quedan persistidos por tenant, auditados por `admin.setting.upsert` y consumidos por el panel al refrescar. En modo mock se mantiene persistencia local para pruebas sin API. |
| Validacion | `node --check frontend/app.js`; `node --check frontend/api/admin.js`; `python -m py_compile` de admin-service y migracion; `ERCLAVE_AUTH_MODE=demo python -m pytest services/admin-service/tests/test_admin_api.py`. |
| Observaciones | Las razones sociales y sucursales se guardan inicialmente dentro de `organization.profile` en JSONB; cuando el modelo fiscal requiera relaciones transaccionales o integracion de facturacion se podran promover a tablas dedicadas. |

### CHG-104

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Agentes y alta de tenants alineados a estructura corporativa |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/scripts/seed_admin_qa_demo.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/models.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/services/admin-service/tests/test_qa_demo_seed.py`, `backend/README.md`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/admin_service_modelo_fisico.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/modelo_multitenant.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, Administracion, tenant settings, OpenAPI, seed QA, alta de tenants |
| Descripcion | Se actualizaron los agentes para tratar la estructura corporativa como dato central del tenant: corporativo, razones sociales, sucursales y contactos viven en `organization.profile` dentro de `admin.tenant_settings`. Se agrego modelo SQLAlchemy `TenantSetting`, se reforzo el seed QA para inicializar `organization.profile`, se documento el schema en OpenAPI y se agrego `POST /v1/tenants` como primer corte idempotente de provisioning que crea tenant e inicializa el perfil organizacional. |
| Motivo | Evitar que futuras iteraciones pasen por alto la estructura corporativa, la guarden en Firebase/localStorage/metadatos ambiguos o creen tenants sin configuracion base administrativa. |
| Impacto | Los agentes, contratos, docs, seeds, API y base quedan alineados para que cada tenant soporte configuracion organizacional desde su creacion. |
| Validacion | `python -m py_compile` de admin-service, modelos y seed; `npm.cmd run validate:openapi`; `npm.cmd run validate:agents`; `ERCLAVE_AUTH_MODE=demo python -m pytest`. |
| Observaciones | `POST /v1/tenants` conserva pendiente el endurecimiento de autenticacion service-to-service para `internal.provisioning.tenant.create` antes de Produccion. |

### CHG-105

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige base URL local de admin API |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, configuracion runtime |
| Descripcion | Se corrigio `getApiBaseUrl()` para que en localhost respete `window.ERCLAVE_CONFIG.apiBaseUrl` y use `http://127.0.0.1:8010` como default local. Tambien se ignora el valor legado `http://127.0.0.1:8000` si quedo persistido en `localStorage`, evitando que el panel de Administracion consuma un admin-service viejo sin endpoints de settings. |
| Motivo | El boton API QA mostraba 404 porque el frontend apuntaba al puerto local anterior `8000`, donde `/v1/settings` no existe, aunque el admin-service vigente esta en `8010`. |
| Impacto | La Administracion local en modo API QA debe cargar contra el admin-service correcto y dejar de mostrar 404 por rutas nuevas. |
| Validacion | `node --check frontend/api/config.js`; smoke `GET http://127.0.0.1:8010/ready`; comparacion manual: `8010/v1/settings` responde 401 por auth, `8000/v1/settings` responde 404 por servicio viejo. |
| Observaciones | Si el navegador conserva modulo JS cacheado, hacer hard refresh. Hay un listener viejo en `8000` reportado por Windows, pero la app local ya no deberia usarlo con esta configuracion. |

### CHG-106

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Administracion sin tablero operativo |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, modulo Administracion, topbar, KPIs, notificaciones |
| Descripcion | Se agrego modo visual `admin-focus` cuando el modulo activo es Administracion. En ese modo se ocultan buscador global, boton Nuevo registro, KPIs superiores y panel lateral de notificaciones/resumen operativo. Tambien se evita renderizar notificaciones mientras Administracion esta activa. |
| Motivo | Administracion debe funcionar como centro de configuracion del sistema, no como tablero operativo de Produccion, Inventario, Ventas o Contabilidad. |
| Impacto | El modulo de Administracion queda enfocado en configuracion: Organizacion, Configuracion base, Usuarios, Roles y Permisos. Los elementos operativos permanecen disponibles en los demas modulos. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Cambio visual/frontend sin impacto en APIs ni base de datos. |

### CHG-107

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Barra global de usuario y sucursal |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, contexto de sesion, sucursal activa, usuario autenticado |
| Descripcion | Se agrego una barra superior discreta global visible en todas las pantallas y modulos. La barra muestra el usuario logueado o usuario de sesion local y la sucursal activa. Si hay mas de una sucursal configurada en `organization.profile`, muestra selector para cambiar la sucursal activa; si hay una sola o ninguna configurada, usa `Matriz` como valor por default. |
| Motivo | Dar contexto operativo constante al usuario sobre con que identidad y sucursal esta trabajando, preparando navegacion futura por sucursal y alcances por usuario. |
| Impacto | Todos los modulos comparten contexto visible de usuario/sucursal sin duplicar controles por pantalla. La seleccion de sucursal se persiste localmente en `erclave-active-branch-id`. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Por ahora el selector toma todas las sucursales configuradas en Organizacion; cuando existan alcances por usuario/sucursal en backend, debe filtrarse desde `session/context` o policy. |

### CHG-108

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Logout discreto en barra de contexto |
| Autor | Codex |
| Archivos | `frontend/index.html`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Shell frontend, barra global de contexto, sesion |
| Descripcion | Se movio el boton de cerrar sesion desde el topbar principal hacia la barra global de contexto de usuario/sucursal y se ajusto su estilo para que sea un control discreto tipo chip. |
| Motivo | Cerrar sesion pertenece al contexto de usuario y no debe competir visualmente con acciones operativas o de configuracion del modulo activo. |
| Impacto | La barra superior muestra usuario, sucursal y cierre de sesion en un mismo lugar, con menor peso visual. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | Cambio visual/frontend sin impacto en APIs ni base de datos. |

### CHG-109

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Normaliza Admin API local a localhost |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/api/config.js`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, fetch diagnostics |
| Descripcion | Se cambio la URL local de Admin API a `http://localhost:8010` cuando la app corre en `localhost`, normalizando overrides que usen `127.0.0.1`. Tambien se mejoro el mensaje de error de `fetch` para mostrar la URL base real y orientar sobre servicio local/cache. |
| Motivo | El navegador mostraba `Failed to fetch` al intentar conectar con la API QA local desde `localhost:4173`, aunque el backend respondia por curl. Alinear host de pagina y API reduce bloqueos/rarezas de navegador y facilita diagnostico. |
| Impacto | El boton API QA debe conectar contra `localhost:8010` y, si falla, mostrar un mensaje accionable en lugar de un error generico. |
| Validacion | `node --check frontend/api/config.js`; `node --check frontend/api/client.js`; `npm.cmd run validate`. |
| Observaciones | `localhost:8010/ready` y preflight CORS desde `localhost:4173` responden correctamente. |

### CHG-110

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Permite Private Network Access en Admin API local |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Backend Admin API, CORS, API QA local, fetch diagnostics |
| Descripcion | Se habilito `allow_private_network=True` en el CORS del Admin API y se agrego `DELETE` a los metodos permitidos para operaciones administrativas. En el cliente API se agrego fallback local entre `localhost` y `127.0.0.1` cuando `fetch` falla por red, conservando un mensaje diagnostico con URL base y fallback. |
| Motivo | Chrome enviaba un preflight con `Access-Control-Request-Private-Network: true` desde `localhost:4173` hacia `localhost:8010` y Starlette lo rechazaba con `400 Disallowed CORS private-network`, provocando `Failed to fetch` en API QA. |
| Impacto | La Administracion local puede consumir Admin API QA desde el navegador sin bloqueo PNA/CORS y mantiene compatibilidad si el host local se resuelve distinto. |
| Validacion | `python -m py_compile backend/services/admin-service/app/main.py`; `node --check frontend/api/client.js`; `curl -i http://localhost:8010/ready`; preflight `OPTIONS /v1/session/context` desde `Origin: http://localhost:4173` con `Access-Control-Request-Private-Network: true`; `npm.cmd run validate`. |
| Observaciones | Se reinicio el Admin API local en `127.0.0.1:8010`; si el navegador conserva cache de modulos, hacer hard refresh. |

### CHG-111

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Fuerza Admin API local por IPv4 |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/api/config.js`, `frontend/api/client.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, API QA local, diagnostico de red |
| Descripcion | Se cambio la URL base local del Admin API a `http://127.0.0.1:8010` y se dejo la normalizacion local para convertir overrides `localhost` a IPv4. Tambien se amplio el mensaje de error para indicar la URL fallback intentada. |
| Motivo | El navegador continuaba mostrando `Failed to fetch` contra `localhost:8010` aunque los preflights y endpoints respondian por curl. Usar IPv4 explicito evita diferencias de resolucion local entre `localhost`, `::1` y `127.0.0.1`. |
| Impacto | API QA local debe intentar primero `127.0.0.1:8010`, manteniendo fallback hacia `localhost:8010` solo si hiciera falta. |
| Validacion | `node --check frontend/api/config.js`; `node --check frontend/api/client.js`; `curl http://localhost:4173/env.js`; `curl http://localhost:4173/api/config.js`; `npm.cmd run validate`. |
| Observaciones | El Admin API local se dejo escuchando en `0.0.0.0:8010` para aceptar conexiones IPv4 locales. |

### CHG-112

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Serializa carga de Administracion y fija controles laterales |
| Autor | Codex |
| Archivos | `frontend/api/admin.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Administracion, API QA local, navegacion lateral |
| Descripcion | Se cambio la carga inicial del dashboard de Administracion de `Promise.all` a requests secuenciales para evitar fallos intermitentes de fetch contra el Admin API local cuando Chrome abre varias conexiones simultaneas. Tambien se hizo sticky el sidebar y su footer para que los controles de tema, idioma y acceso a Administracion permanezcan visibles en escritorio. |
| Motivo | En local el navegador seguia reportando `Failed to fetch` en `/v1/settings` aunque los endpoints y preflights respondian individualmente. Ademas, los controles inferiores del sidebar quedaban accesibles solo al llegar al final de paginas largas. |
| Impacto | API QA local carga de forma mas estable y la navegacion auxiliar del shell queda siempre a mano en pantallas de escritorio. |
| Validacion | `node --check frontend/api/admin.js`; `curl http://localhost:4173/api/admin.js`; `npm.cmd run validate`; smoke `GET http://127.0.0.1:8010/ready`. |
| Observaciones | El Admin API local quedo reiniciado y escuchando en `0.0.0.0:8010`. |

### CHG-113

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige consulta de settings por modulo |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `backend/services/admin-service/app/repositories.py`, `TRAZABILIDAD.md` |
| Secciones | Backend Admin API, settings, PostgreSQL, Administracion |
| Descripcion | Se separo la consulta de `AdminRepository.list_settings()` en dos variantes: una sin filtro de modulo y otra con `module_code = :module_code`. Tambien se dejo el registro de routers antes de middlewares en el bootstrap del Admin API. |
| Motivo | PostgreSQL/psycopg no podia inferir el tipo del parametro en `(:module_code is null or module_code = :module_code)`, causando `500 Internal Server Error` al cargar `/v1/settings?module_code=admin` desde API QA. |
| Impacto | El endpoint de settings de Administracion ya puede devolver `organization.profile` para el tenant QA sin romper la carga del panel. |
| Validacion | `python -m py_compile services/admin-service/app/repositories.py services/admin-service/app/main.py`; ejecucion directa de `repo.list_settings('ten_739ee59d765d5e14818674800d', module_code='admin')`; `curl http://127.0.0.1:8010/ready`; `npm.cmd run validate`. |
| Observaciones | El Admin API local se reinicio despues del cambio y quedo escuchando en `0.0.0.0:8010`. |

### CHG-114

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | APIs finas para razones sociales y sucursales |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/admin.js`, `frontend/app.js`, `contracts/api/admin-service.openapi.yaml`, `backend/services/admin-service/README.md`, `docs/arquitectura/modelo_multitenant.md`, `docs/arquitectura/admin_service_modelo_fisico.md`, `TRAZABILIDAD.md` |
| Secciones | Admin API, Administracion, organizacion, razones sociales, sucursales, OpenAPI |
| Descripcion | Se agregaron endpoints para crear, actualizar, activar e inactivar razones sociales y sucursales: `/v1/organization/legal-entities` y `/v1/organization/branches`. Por ahora persisten en `admin.tenant_settings` key `organization.profile`, pero cada accion tiene endpoint propio, idempotencia y auditoria. El frontend usa estas APIs para altas y cambios de estado cuando corre en API QA; en mock conserva persistencia local. |
| Motivo | Administracion necesitaba operaciones reales de alta/actualizacion/activacion/inactivacion para estructura corporativa sin reescribir manualmente todo el JSON desde la UI. |
| Impacto | El tenant QA puede administrar razones sociales y sucursales desde API QA con acciones auditables, manteniendo compatibilidad con el modelo JSONB inicial. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py`; `node --check frontend/api/admin.js`; `node --check frontend/app.js`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate`. |
| Observaciones | Los endpoints usan `admin.setting.update` como permiso vigente. Si mas adelante se requieren permisos granulares, crear `admin.legal_entity.*` y `admin.branch.*` en seed/migracion de permisos. |

### CHG-115

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Actualiza agentes para endpoints finos de organizacion |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, Administracion, estructura corporativa |
| Descripcion | Se actualizaron los agentes para exigir que razones sociales y sucursales se creen, actualicen, activen e inactiven mediante los endpoints finos de `admin-service` (`/v1/organization/legal-entities` y `/v1/organization/branches`) mientras persistan en `organization.profile`. Tambien se agregaron preguntas de revision sobre idempotencia, auditoria, contrato OpenAPI, frontend y tests. |
| Motivo | Evitar que futuros cambios vuelvan a tratar razones sociales y sucursales como reemplazos opacos del JSON completo o como datos locales del frontend. |
| Impacto | Los agentes tecnicos y transversales ahora alinean sus revisiones con el modelo actual: `organization.profile` como almacenamiento inicial y endpoints finos como superficie de mutacion. |
| Validacion | `npm.cmd run validate:agents`; `npm.cmd run validate`. |
| Observaciones | No cambia runtime; es una actualizacion documental/operativa para guiar futuros cambios. |

### CHG-116

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Fortalece session/context con roles, limites y sucursales |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/services/admin-service/app/main.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/services/admin-service/README.md`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Admin API, session/context, roles, entitlements, alcance de sucursales, shell frontend |
| Descripcion | Se extendio `GET /v1/session/context` para devolver roles activos detallados, `entitlement_limits` por modulo y `scope` con sucursales disponibles para la membresia. El alcance de sucursal se calcula desde `membership.metadata.scope.branch_ids` cuando exista y, si no esta configurado, permite todas las sucursales activas de `organization.profile`. El frontend ahora prioriza `session.scope.branches` para la barra global de sucursal y conserva fallback a la organizacion local/mock. |
| Motivo | Convertir `session/context` en la fuente real para usuario, permisos, modulos, limites y sucursal activa, evitando que el shell infiera alcance operativo desde datos locales o desde todo el perfil organizacional. |
| Impacto | La barra global de contexto queda preparada para usuarios con alcance por sucursal. Los servicios y microfrontends pueden consumir limites por modulo y roles explicitos sin recalcularlos en frontend. |
| Validacion | `python -m py_compile services/admin-service/app/main.py services/admin-service/app/schemas.py services/admin-service/app/repositories.py`; `node --check frontend/app.js`; `pytest services/admin-service/tests/test_admin_api.py`. |
| Observaciones | Se reemplazo el parametro directo `allow_private_network` de CORS por un middleware compatible que agrega `Access-Control-Allow-Private-Network` cuando Chrome lo solicita; esto conserva el soporte local sin depender de una version especifica de Starlette. |

### CHG-117

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Endpoint interno de onboarding tenant + owner |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `TRAZABILIDAD.md` |
| Secciones | Provisioning, Admin API, tenants, owner inicial, organization.profile, modulos activos, Firebase Auth |
| Descripcion | Se agrego `POST /v1/provisioning/tenant-onboarding` como comando idempotente para crear o actualizar tenant por slug, inicializar `organization.profile`, crear o enlazar el usuario owner, crear rol `owner`, asignar permisos activos, crear membresia con alcance de sucursal, habilitar modulos solicitados y auditar la operacion. El request pide datos del tenant, `source`, owner inicial, perfil organizacional y modulos. |
| Motivo | Evitar altas manuales incompletas donde se cree tenant sin usuario owner, sin perfil organizacional, sin modulos o sin roles/permisos. |
| Impacto | El alta de cliente nuevo puede resolverse con un unico comando interno de provisioning y queda preparada para enlazarse a flujos comerciales/billing. El usuario owner queda autenticable en Firebase por email y autorizado en ERClave por membresia/rol. |
| Validacion | `python -m py_compile services/admin-service/app/api.py services/admin-service/app/repositories.py services/admin-service/app/schemas.py`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:openapi`. |
| Observaciones | En este corte el endpoint conserva pendiente autenticacion service-to-service fuerte antes de Produccion; `ensure_firebase_user` ocurre antes de la transaccion de base, por lo que errores posteriores podrian dejar una identidad Firebase sin membresia y deberan compensarse en la fase de provisioning robusto. |

### CHG-118

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Invitacion Firebase para owner inicial |
| Autor | Codex |
| Archivos | `backend/README.md`, `backend/shared/erclave_common/config.py`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `TRAZABILIDAD.md` |
| Secciones | Firebase Auth, provisioning, tenant onboarding, invitacion owner, configuracion |
| Descripcion | Se agrego soporte para preparar la invitacion de contrasena del owner inicial dentro de `POST /v1/provisioning/tenant-onboarding`. Si `ERCLAVE_FIREBASE_WEB_API_KEY` esta configurado, el backend llama Identity Toolkit para que Firebase envie el correo de recuperacion/activacion; si no existe esa key, genera un `reset_link` con Firebase Admin y lo devuelve en `data.invitation`. |
| Motivo | Completar el flujo de alta tenant + owner para que el usuario no solo exista en Firebase y ERClave, sino que tenga un camino de acceso inicial para definir contrasena. |
| Impacto | El onboarding ahora devuelve `invitation.provider`, `email`, `email_sent`, `delivery` y opcionalmente `reset_link`. QA/Prod pueden mandar correo real configurando `ERCLAVE_FIREBASE_WEB_API_KEY`; local/demo conserva respuesta `disabled`. |
| Validacion | `python -m py_compile services/admin-service/app/auth.py services/admin-service/app/api.py shared/erclave_common/config.py`; `pytest services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate:openapi`. |
| Observaciones | El envio real usa las plantillas SMTP/configuracion de Firebase Authentication. Sigue pendiente un `notification-service` dedicado si se requiere branding, auditoria y reintentos avanzados de correo transaccional. |

### CHG-119

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Front Backoffice interno para alta de tenants |
| Autor | Codex |
| Archivos | `AGENTES.md`, `backend/README.md`, `backend/services/admin-service/README.md`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/auth.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/shared/erclave_common/config.py`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/modelo_multitenant.md`, `frontend/api/backoffice.js`, `frontend/backoffice/README.md`, `frontend/backoffice/app.js`, `frontend/backoffice/env.js`, `frontend/backoffice/index.html`, `frontend/backoffice/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Backoffice interno, Firebase Auth, provisioning, tenant onboarding, seguridad |
| Descripcion | Se creo `frontend/backoffice/` como front separado para administradores internos de EsLaClave. Incluye login con Firebase, formulario de alta de tenant, owner inicial, datos fiscales, sucursal inicial, modulos contratados y panel de resultado con invitacion. Se agrego `frontend/api/backoffice.js` como frontera API hacia `POST /v1/provisioning/tenant-onboarding`. El backend ahora protege ese endpoint en modo Firebase con allowlist `ERCLAVE_BACKOFFICE_ADMIN_EMAILS`. |
| Motivo | Crear tenants es una operacion de plataforma SaaS y no debe vivir dentro del modulo Administracion del cliente. El backoffice sera tambien la superficie futura para billing/provisioning y soporte interno. |
| Impacto | El equipo interno puede usar una interfaz separada para crear clientes sin entrar a un tenant existente. En QA/Prod el endpoint requiere token Firebase de un correo autorizado; en demo/local conserva flujo de desarrollo. |
| Validacion | `python -m py_compile services/admin-service/app/auth.py services/admin-service/app/api.py shared/erclave_common/config.py`; `pytest services/admin-service/tests/test_admin_api.py`; `node --check frontend/backoffice/app.js`; `node --check frontend/api/backoffice.js`. |
| Observaciones | Para uso local se sirve en `http://localhost:4173/backoffice/`. En Firebase mode configurar `ERCLAVE_BACKOFFICE_ADMIN_EMAILS` y, para correo real del owner, `ERCLAVE_FIREBASE_WEB_API_KEY`. |

### CHG-120

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Configuracion runtime online para Firebase Hosting |
| Autor | Codex |
| Archivos | `frontend/env.js`, `frontend/backoffice/env.js`, `frontend/api/config.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, backoffice, despliegue QA |
| Descripcion | Se actualizo la configuracion runtime del frontend para que Firebase Hosting apunte a `admin-service-qa` y `production-service-qa` en Cloud Run, conservando `localApiBaseUrl` para desarrollo local. `getApiBaseUrl()` ahora prioriza `localApiBaseUrl` cuando se ejecuta en `localhost` o `127.0.0.1`, evitando que la configuracion online rompa pruebas locales. |
| Motivo | Subir el front y backoffice en linea sin que el navegador intente llamar a `localhost` como API QA. |
| Impacto | `https://erclave.web.app/` y `/backoffice/` quedan listos para consumir los servicios QA publicados, mientras que el entorno local mantiene `http://127.0.0.1:8010` por defecto. |
| Validacion | `npm.cmd run validate`; `python -m pytest services/admin-service/tests/test_admin_api.py`; `node --check frontend/api/config.js`. |
| Observaciones | `productionApiBaseUrl` queda configurado para el servicio QA aunque el modulo de Produccion todavia conserva consumo mayormente local/mock en frontend. |

### CHG-121

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Ajusta copy de producto en login |
| Autor | Codex |
| Archivos | `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, autenticacion, experiencia de entrada |
| Descripcion | Se reemplazo el texto descriptivo del mecanismo de login por un mensaje de producto: ERClave como plataforma SaaS modular para centralizar procesos, usuarios, sucursales y modulos de negocio. |
| Motivo | La pantalla de acceso debe presentar brevemente que es ERClave y reforzar marca/eslogan, no explicar la implementacion de autenticacion. |
| Impacto | El panel izquierdo del login comunica valor de negocio antes del formulario de acceso. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate:traceability`. |
| Observaciones | No cambia comportamiento de autenticacion ni permisos. |

### CHG-122

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige preflight private-network de backoffice online |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/main.py`, `backend/services/admin-service/tests/test_admin_api.py`, `TRAZABILIDAD.md` |
| Secciones | Admin API, CORS, backoffice online |
| Descripcion | Se agrego una respuesta explicita para preflight CORS con `Access-Control-Request-Private-Network: true` cuando el origen pertenece a Firebase Hosting autorizado. Esto evita que `CORSMiddleware` rechace la solicitud con `400 Disallowed CORS private-network` antes de que el navegador ejecute `POST /v1/provisioning/tenant-onboarding`. |
| Motivo | Edge/Chrome puede enviar la cabecera private-network en preflight y bloquear el alta de tenant online con `Failed to fetch` aunque la API este disponible. |
| Impacto | El backoffice publicado en `https://erclave.web.app/backoffice/` puede completar el preflight y conectar con `admin-service-qa` para crear tenants. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `python -m py_compile services/admin-service/app/main.py`; `npm.cmd run validate:traceability`; validacion online del `OPTIONS` private-network posterior al deploy. |
| Observaciones | El cambio se acota a `admin-service`, que es la API consumida por el backoffice interno. |

### CHG-123

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Corrige tipo ambiguo al crear membresia owner |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/repositories.py`, `TRAZABILIDAD.md` |
| Secciones | Admin API, provisioning, tenant onboarding, PostgreSQL |
| Descripcion | Se casteo explicitamente `:status` como `varchar` en el insert de `admin.memberships` usado por `POST /v1/provisioning/tenant-onboarding`. Esto evita el error `psycopg.errors.AmbiguousParameter: inconsistent types deduced for parameter` al calcular `activated_at` con `case when :status = 'active'`. |
| Motivo | El backoffice online ya pasaba CORS, pero el alta de tenant terminaba en `500 Internal Server Error` al crear la membresia inicial del owner. |
| Impacto | El onboarding puede crear la membresia owner con estado `invited` o `active` sin error de tipos en PostgreSQL. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `python -m py_compile services/admin-service/app/repositories.py`; `npm.cmd run validate:traceability`; deploy y health online de `admin-service-qa`. |
| Observaciones | El intento fallido pudo haber creado o actualizado la identidad Firebase del owner antes de la transaccion de base; el flujo es idempotente y el siguiente intento reutiliza/actualiza esa identidad. |

### CHG-124

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Resuelve tenant activo del usuario autenticado |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/admin.js`, `frontend/api/config.js`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Session context, multitenant, frontend shell, backoffice onboarding |
| Descripcion | Se agrego `GET /v1/session/tenants` para listar tenants activos/invitados del correo autenticado por Firebase. El frontend ahora resuelve el tenant del usuario antes de pedir `session/context`, persiste el tenant activo y manda al usuario a Administracion cuando inicia sesion o cambia de tenant. |
| Motivo | Un usuario owner creado por backoffice entraba al shell con el tenant demo hardcodeado, provocando `session_context_not_found` y dejando ver navegacion operativa sin contexto real. |
| Impacto | El shell deja de usar el fallback de modulos MVP en modo API sin sesion; los modulos operativos solo se habilitan cuando `session/context` devuelve entitlements del tenant real. |
| Validacion | `python -m pytest services/admin-service/tests/test_admin_api.py`; `node --check frontend/app.js`; `node --check frontend/api/admin.js`; `node --check frontend/api/config.js`; `npm.cmd run validate:traceability`; `npm.cmd run validate`. |
| Observaciones | En esta fase se selecciona automaticamente el tenant guardado si pertenece al usuario o, en su defecto, el mas reciente disponible. Un selector multi-tenant explicito queda como mejora posterior. |

### CHG-125

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Pantalla de carga para tenant real |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend shell, session context, administracion |
| Descripcion | Se agrego una vista temporal de carga para Administracion mientras se resuelve el tenant, session context o dashboard real. La pantalla muestra un skeleton desenfocado y evita renderizar datos mock del cliente piloto durante la transicion. |
| Motivo | Al iniciar sesion con un usuario nuevo se alcanzaban a ver datos del piloto antes de cargar el tenant real, generando confusion y riesgo visual de mezclar contexto. |
| Impacto | En modo API, la barra de sucursal y el modulo Administracion usan mensajes neutrales de carga hasta tener contexto real del tenant. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate:traceability`; `npm.cmd run validate`. |
| Observaciones | No cambia permisos ni contratos backend; es una mejora de experiencia para no mostrar fallback mock mientras cargan datos reales. |

### CHG-126

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Tenants nuevos sin datos operativos demo |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/data/mockDb.js`, `frontend/utils/production.js`, `frontend/app.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, mock DB local, Produccion, submodulos operativos |
| Descripcion | Se separo el uso de datos semilla para que solo aplique en modo mock o en el tenant demo configurado. En modo API con tenants reales, recetas, ordenes, productos/servicios, areas, maquinaria y registros genericos arrancan vacios y usan llaves de `localStorage` separadas por tenant. Produccion ya no toma `defaultRecipes[0]` cuando no hay recetas reales y muestra estados vacios en listas y validacion. |
| Motivo | Los tenants creados desde backoffice deben iniciar desde cero, sin datos piloto de produccion, ordenes o catalogos que puedan confundirse con informacion real del cliente. |
| Impacto | Un nuevo tenant autenticado entra limpio a sus modulos; solo ve informacion cuando la capture o cuando la API la devuelva para su tenant. El tenant demo conserva datos semilla para pruebas. |
| Validacion | `node --check frontend/app.js`; `node --check frontend/utils/production.js`; `node --check frontend/data/mockDb.js`; `node --check frontend/api/config.js`; `npm.cmd run validate`. |
| Observaciones | La separacion es de frontend/localStorage; cuando haya persistencia operativa por API, debe conservarse la misma regla de no sembrar datos demo para tenants reales. |

### CHG-127

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Limpia metricas y alertas demo en tenants reales |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Frontend shell, status strip, notificaciones operativas |
| Descripcion | La fila superior de metricas dejo de usar valores hardcodeados de demo cuando el frontend corre en modo API con un tenant real. Para tenants nuevos calcula ceros desde los datos locales/API disponibles y muestra etiquetas neutrales. Las notificaciones ya no agregan una alerta falsa de operacion estable cuando no existen productos, recetas ni ordenes. |
| Motivo | Evitar que un tenant recien creado vea datos piloto como produccion activa, inventario critico, margen estimado o pendientes contables. |
| Impacto | La experiencia inicial de un nuevo tenant queda limpia y coherente con un arranque desde cero; el tenant demo conserva metricas semilla. |
| Validacion | `node --check frontend/app.js`; `npm.cmd run validate`. |
| Observaciones | El estado neutral se aplica en CSS con la clase `.neutral` para chips/trends sin datos. |

### CHG-128

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Administracion de tenants en backoffice |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `frontend/api/backoffice.js`, `frontend/backoffice/app.js`, `frontend/backoffice/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Backoffice, provisioning, tenant lifecycle, admin-service |
| Descripcion | Se agrego una pestaña de Administracion de tenants al backoffice con busqueda por nombre comercial, slug y razon social. El admin-service expone rutas internas protegidas para listar tenants, suspender/reactivar y eliminar tenants. Suspender cambia el estado del tenant y deshabilita membresias para impedir acceso; eliminar borra roles, permisos asignados, membresias, modulos, settings y el tenant, y solo elimina identidad Firebase de usuarios que ya no pertenecen a ningun otro tenant. |
| Motivo | El equipo interno necesita operar el ciclo de vida de tenants desde el portal de backoffice, no solo crear altas nuevas. |
| Impacto | Backoffice puede bloquear acceso temporalmente o remover un tenant completo desde una pantalla dedicada. La busqueda permite ubicar tenants por datos comerciales o fiscales antes de actuar. |
| Validacion | `python -m pytest backend/services/admin-service/tests/test_admin_api.py`; `python -m py_compile backend/services/admin-service/app/api.py backend/services/admin-service/app/repositories.py backend/services/admin-service/app/schemas.py`; `node --check frontend/backoffice/app.js`; `node --check frontend/api/backoffice.js`; `npm.cmd run validate`. |
| Observaciones | La eliminacion es permanente y esta pensada para backoffice interno; antes de produccion conviene agregar doble confirmacion textual y auditoria externa si se requiere conservar evidencia fuera del tenant eliminado. |

### CHG-129

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-05 |
| Cambio | Gate visual de autorizacion para backoffice |
| Autor | Codex |
| Archivos | `frontend/api/backoffice.js`, `frontend/backoffice/app.js`, `frontend/backoffice/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Backoffice, autenticacion, autorizacion interna |
| Descripcion | El front de backoffice ahora valida autorizacion contra `GET /v1/backoffice/tenants?limit=1` antes de mostrar cualquier pestaña o formulario interno. Si la API responde rechazo, muestra una pantalla de acceso restringido y no renderiza alta de tenant ni administracion de tenants. |
| Motivo | Un usuario owner creado por onboarding podia ver la interfaz del backoffice aunque el backend lo bloqueara con `403`, generando la percepcion de que tenia acceso interno. |
| Impacto | Solo correos incluidos en `ERCLAVE_BACKOFFICE_ADMIN_EMAILS` ven herramientas de backoffice; los usuarios de tenants quedan fuera incluso si autenticaron correctamente en Firebase. |
| Validacion | `node --check frontend/backoffice/app.js`; `node --check frontend/api/backoffice.js`; `npm.cmd run validate`. |
| Observaciones | El backend ya era la barrera de seguridad efectiva; este cambio agrega la compuerta visual para evitar exposicion de pantallas internas. |

### CHG-130

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-07 14:09 |
| Cambio | Primer modulo de uso y costos por tenant |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260707_0004_admin_tenant_usage_daily.py`, `backend/services/admin-service/app/api.py`, `backend/services/admin-service/app/repositories.py`, `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/backoffice.js`, `frontend/backoffice/app.js`, `frontend/backoffice/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Backoffice interno, Admin API, medicion SaaS, migraciones admin, contrato OpenAPI |
| Descripcion | Se agrego la tabla `admin.tenant_usage_daily` para metricas diarias por tenant con usuarios activos, requests API, storage MB y costo estimado MXN. El admin-service expone `GET /v1/backoffice/usage` protegido por `require_backoffice_admin`, con filtros por rango, tenant y limite, devolviendo filas y resumen agregado. El backoffice incorpora la pestaña `Uso y costos` con filtros, resumen y tabla de consulta. |
| Motivo | Dar al equipo interno una primera base auditable para observar consumo y costos por tenant sin mezclar datos operativos de modulos cliente ni exponer ingestion publica. |
| Impacto | Backoffice puede consultar uso diario por tenant desde una tabla propia del schema `admin`; la eliminacion interna de tenants limpia sus metricas antes de borrar el tenant. La ingesta de metricas queda reservada para jobs internos futuros. |
| Validacion | `python -m py_compile backend/services/admin-service/app/api.py backend/services/admin-service/app/repositories.py backend/services/admin-service/app/schemas.py backend/alembic/versions/20260707_0004_admin_tenant_usage_daily.py`; `node --check frontend/backoffice/app.js`; `node --check frontend/api/backoffice.js`; `python -m pytest backend/services/admin-service/tests/test_admin_api.py`; `npm.cmd run validate`; `python -m pytest` desde `backend`. |
| Observaciones | Primer corte de lectura; no calcula costos reales de proveedor cloud ni abre endpoints mutables de metricas. |

### CHG-131

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-08 |
| Cambio | Politica de aislamiento tenant |
| Autor | Codex |
| Archivos | `docs/arquitectura/politica_aislamiento_tenant.md`, `docs/arquitectura/modelo_multitenant.md`, `tools/validators/validate-tenant-isolation.js`, `tools/validators/validate-all.js`, `backend/services/production-service/tests/test_production_api.py`, `TRAZABILIDAD.md` |
| Secciones | Arquitectura multitenant, seguridad SaaS, guardrails, pruebas anti-fuga |
| Descripcion | Se agrego una politica normativa para el modelo pooled multi-tenant de ERClave. La politica define tablas globales permitidas, tablas tenant-scoped con `tenant_id` obligatorio, excepcion controlada para auditoria, reglas para base de datos, APIs, repositorios, frontend, backoffice y pruebas anti-fuga. Se agrego un validador automatico que revisa migraciones tenant-scoped, repositorio/API de Produccion y presencia de cobertura anti-fuga. |
| Motivo | El producto apunta a volumen con multi-tenancy logico; se necesitaba convertir la intencion arquitectonica en reglas verificables para evitar fugas entre tenants al iniciar funcionalidades ERP cliente. |
| Impacto | Nuevas funcionalidades ERP deben nacer con `tenant_id`, contexto de tenant y pruebas de aislamiento. El suite `npm run validate` ahora falla si se crean tablas tenant-scoped sin `tenant_id` o si Produccion pierde filtros basicos de tenant. |
| Validacion | `node tools/validators/validate-tenant-isolation.js`; `python -m pytest backend/services/production-service/tests/test_production_api.py`. |
| Observaciones | El validador es un primer guardrail estatico; no sustituye revision de codigo ni futuras pruebas de integracion con PostgreSQL Row-Level Security. |

### CHG-132

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-13 |
| Cambio | Quality gate CI para pruebas backend |
| Autor | Codex |
| Archivos | `.github/workflows/validate.yml`, `.github/workflows/pages.yml`, `TRAZABILIDAD.md` |
| Secciones | CI/CD, pruebas automaticas, despliegue frontend |
| Descripcion | El workflow de validacion ahora ejecuta en paralelo los validadores del repositorio y la suite Pytest completa con Python 3.11. El workflow de GitHub Pages incorpora el mismo quality gate y declara que el despliegue depende de su resultado exitoso. |
| Motivo | Las 67 pruebas backend existentes no se ejecutaban en CI, por lo que una regresion podia aprobar validadores estructurales y llegar a `main` o a un despliegue de frontend. |
| Impacto | Los pull requests y pushes cubiertos por el workflow muestran checks separados para validadores y backend; Pages no despliega cuando falla cualquiera de las validaciones o pruebas. |
| Validacion | `npm.cmd run validate` con 11 validadores correctos; `python -m pytest -q` desde `backend` con 67 pruebas correctas. |
| Observaciones | Para impedir merges desde la configuracion de GitHub se deben marcar `Agent rule validators` y `Backend tests (Python 3.11)` como required status checks de la rama `main`. |

### CHG-133

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-21 |
| Cambio | Recetas y versiones reales en production-service |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260721_0005_production_recipes.py`, `backend/services/production-service/app/api.py`, `backend/services/production-service/app/repositories.py`, `backend/services/production-service/app/schemas.py`, `backend/services/production-service/tests/test_production_api.py`, `backend/services/production-service/README.md`, `tools/validators/validate-db-guardrails.js`, `TRAZABILIDAD.md` |
| Secciones | Produccion, recetas, versionado, persistencia multi-tenant, API |
| Descripcion | Se agregaron las tablas `production.recipes`, `recipe_versions`, `recipe_resources` y `recipe_stages`, junto con endpoints para crear, consultar, versionar, editar borradores y ejecutar las transiciones submit, approve y obsolete. La aprobacion exige recursos y etapas, actualiza la version vigente y el costo estandar del producto. |
| Motivo | Continuar la Fase 4 del plan del arquitecto convirtiendo recetas en datos backend reales antes de implementar ordenes, Inventarios o Ventas. |
| Impacto | Cada receta y sus componentes quedan aislados por `tenant_id`; las versiones aprobadas son inmutables y una nueva aprobacion vuelve obsoleta la anterior. El validador de FKs ahora distingue relaciones internas del mismo schema de relaciones cruzadas prohibidas. |
| Validacion | `python -m py_compile`; `python -m pytest -q` con 72 pruebas; `npm.cmd run validate`. |
| Observaciones | Este corte no incluye todavia ordenes de produccion, integracion con inventario ni conexion del frontend de recetas. |

### CHG-134

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-21 |
| Cambio | Prueba directa de API de recetas contra Cloud SQL QA |
| Autor | Codex + agentes QA y seguridad |
| Archivos | `backend/services/production-service/app/repositories.py`, `TRAZABILIDAD.md` |
| Secciones | Produccion, API QA, recetas, aislamiento tenant, aprobacion |
| Descripcion | Se ejecuto el flujo real crear-leer-listar-submit-approve contra `production-service` local conectado a Cloud SQL QA. La prueba encontro y corrigio una asignacion duplicada de `updated_at` que provocaba `500` al enviar una version a aprobacion. Tambien se endurecio la aprobacion para exigir al menos una etapa activa. |
| Motivo | Verificar que el segundo corte de Produccion persiste y recupera datos reales antes de conectarlo al frontend o desplegarlo publicamente. |
| Impacto | El flujo funcional completo queda comprobado en PostgreSQL QA; lectura cruzada y creacion de version desde otro tenant fueron rechazadas. Se confirmo que receta y producto apuntan a la version aprobada y que el snapshot contiene recursos y etapas. |
| Validacion | API real: create `201`, read/list `200`, cross-tenant `404`, submit `200`, approve `200`; consulta SQL de snapshot y versiones vigentes; 72 pruebas Pytest; todos los validadores automaticos aprobados. |
| Observaciones | La idempotencia real, autenticacion/autorizacion, `approved_by` confiable, FKs tenant-aware/RLS y concurrencia de versionado siguen pendientes; no debe desplegarse publicamente este corte hasta resolver al menos autenticacion e idempotencia. |

### CHG-135

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-21 |
| Cambio | Autorizacion e idempotencia real para production-service |
| Autor | Codex + agentes de seguridad y persistencia |
| Archivos | `backend/alembic/versions/20260721_0006_production_idempotency.py`, `backend/shared/erclave_common/config.py`, `backend/services/production-service/app/authorization.py`, `backend/services/production-service/app/api.py`, `backend/services/production-service/app/repositories.py`, `backend/services/production-service/app/schemas.py`, `backend/services/production-service/tests/test_production_api.py`, `contracts/api/production-service.openapi.yaml`, `backend/.env.example`, `backend/README.md`, `tools/validators/validate-backend-scaffold.js`, `tools/validators/validate-tenant-isolation.js`, `TRAZABILIDAD.md` |
| Secciones | Seguridad, Firebase Auth, RBAC, multi-tenancy, idempotencia, Produccion |
| Descripcion | Cada ruta de Produccion valida el Bearer token indirectamente mediante `admin-service /v1/session/context`, comprueba tenant activo, modulo contratado y permiso exacto. El aprobador se deriva de la sesion. Los comandos sensibles registran llave, hash, actor y respuesta en `production.idempotency_records` dentro de la misma transaccion, permitiendo replay y rechazando reutilizacion con otro payload. |
| Motivo | Eliminar la confianza en `X-Tenant-Id` como autoridad y hacer seguros los reintentos antes de desplegar publicamente o conectar el frontend. |
| Impacto | `X-Tenant-Id` queda como selector; Administracion conserva ownership de membresias/permisos. Las versiones se bloquean al numerarlas para evitar carreras. PATCH de borrador ahora tambien exige `Idempotency-Key`. |
| Validacion | 76 pruebas Pytest; validadores completos; migracion QA `20260721_0006`; replay real devuelve el mismo ID, payload distinto devuelve `409`, y PostgreSQL confirma una receta y un registro completed. |
| Observaciones | La prueba con token Firebase real se ejecutara durante el despliegue QA; local/demo conserva `X-Actor-Id` exclusivamente para pruebas controladas. RLS y FKs compuestas por tenant permanecen como endurecimiento posterior. |

### CHG-136

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-21 |
| Cambio | Despliegue seguro de production-service en Cloud Run QA |
| Autor | Codex |
| Archivos | `TRAZABILIDAD.md` |
| Secciones | Cloud Run QA, Produccion, autenticacion entre servicios |
| Descripcion | Se desplego el backend actualizado de Produccion y se configuro `ERCLAVE_AUTH_MODE=firebase`, proyecto Firebase, Cloud SQL, secreto de base y URL canonica de `admin-service`. La revision final `production-service-qa-00005-bmp` recibe el 100% del trafico. |
| Motivo | Publicar en QA el corte de recetas con autorizacion e idempotencia antes de conectar el frontend. |
| Impacto | Health y OpenAPI responden; recetas sin token reciben `401 auth_required` y un token invalido es rechazado por la integracion real con Administracion como `401 invalid_token`. |
| Validacion | `/health` 200; `/openapi.json` 200; ruta protegida sin token 401; ruta protegida con token invalido 401; lectura positiva de recetas con token Firebase y permiso `production.recipe.read`; revision lista y 100% de trafico. |
| Observaciones | El servicio QA quedo disponible en `https://production-service-qa-370105017372.us-central1.run.app`; el token usado para la comprobacion positiva no se almaceno en el repositorio. |

### CHG-137

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-21 |
| Cambio | Conexion del frontend de recetas con Production API QA |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/api/client.js`, `frontend/api/production.js`, `frontend/app.js`, `frontend/utils/production.js`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Produccion, recetas, Firebase Auth, QA |
| Descripcion | El modulo de Produccion carga productos y recetas desde la API usando la sesion Firebase y el tenant activo. Crear y editar receta persiste en QA; editar una receta no borrador genera una nueva version y las acciones de envio y aprobacion usan las transiciones auditables del backend. |
| Motivo | Sustituir la persistencia local del flujo de recetas una vez comprobada la autorizacion positiva de un usuario QA. |
| Impacto | Las recetas visibles en modo API reflejan PostgreSQL QA. Se preservan costos y metadatos de recursos externos al catalogo simulado, se generan llaves de idempotencia por comando y se impide la eliminacion fisica desde el frontend. |
| Validacion | Sintaxis JavaScript y suite completa de validadores automaticos aprobadas; Firebase Hosting version `e3ab27b1b2f047d8` publicada; cliente servido verificado y preflight CORS de Production API respondio `200`. |
| Observaciones | QA esta disponible en `https://erclave.web.app`. Ordenes y otros submodulos de Produccion conservan su comportamiento previo; este corte conecta el catalogo y ciclo de versiones de recetas. |

### CHG-138

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-24 |
| Cambio | Capa operativa de Codex para desarrollo verificable |
| Autor | Codex |
| Archivos | `AGENTS.md`, `.agents/skills/erclave-feature/`, `.agents/skills/erclave-db-migration/`, `tools/verify.js`, `tools/traceability-draft.js`, `tools/validators/validate-codex-tooling.js`, `tools/validators/validate-all.js`, `tools/validators/validate-cross-platform.js`, `package.json`, `.github/workflows/validate.yml`, `.github/workflows/pages.yml`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | Desarrollo asistido, calidad, CI/CD, skills, trazabilidad |
| Descripcion | Se agregaron instrucciones persistentes para Codex, dos skills de proyecto para entrega funcional y migraciones seguras, un comando unificado que ejecuta guardrails, compilacion y Pytest, un generador de borradores CHG basado en Git y un validador que protege esta capa. Los workflows de validacion y Pages usan ahora el mismo criterio completo. |
| Motivo | Reducir explicaciones repetidas, homogeneizar la implementacion entre modulos y asegurar que los cambios asistidos terminen con contratos, pruebas y trazabilidad alineados. |
| Impacto | Codex dispone de un flujo versionado y descubrible dentro del repositorio. Desarrollo local y CI comparten `npm run verify`; los borradores de trazabilidad siguen requiriendo revision humana antes de considerarse completos. |
| Validacion | Validacion oficial de ambas skills con `quick_validate.py`; `npm.cmd run verify`. |
| Observaciones | El generador incluye todos los cambios visibles en Git para que el autor decida cuales pertenecen al corte. Se preservaron sin modificar el diagrama Draw.io y su archivo temporal preexistentes. |

### CHG-139

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-24 |
| Cambio | Correccion de redireccion posterior a invitacion Firebase |
| Autor | Codex |
| Archivos | `backend/shared/erclave_common/config.py`, `backend/services/admin-service/tests/test_config.py`, `backend/.env.example`, `backend/README.md`, `TRAZABILIDAD.md` |
| Secciones | Onboarding, Firebase Auth, configuracion QA, seguridad operativa |
| Descripcion | Se configuro `ERCLAVE_APP_PUBLIC_BASE_URL=https://erclave.web.app` en `admin-service-qa` para que Firebase redirija al frontend publico despues de establecer la contrasena. La configuracion ahora rechaza URLs locales, invalidas o sin HTTPS cuando el ambiente es QA o Produccion. |
| Motivo | Las invitaciones completaban el cambio de contrasena pero redirigian al valor local por defecto `http://localhost:4173`, provocando que Safari no pudiera conectarse al servidor. |
| Impacto | Las invitaciones generadas a partir de la correccion regresan al frontend QA. Una configuracion futura insegura impide que el servicio arranque en QA/Produccion en lugar de generar ligas defectuosas. |
| Validacion | Revision Cloud Run `admin-service-qa-00011-bd5` lista con 100% de trafico; variable publica verificada; `/health` HTTP 200; `npm.cmd run verify`. |
| Observaciones | Las ligas emitidas antes del cambio conservan el `continueUrl` anterior; para comprobar el flujo completo se debe usar una invitacion o recuperacion de contrasena nueva. |

### CHG-140

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-24 |
| Cambio | Guia manual de pruebas QA del MVP |
| Autor | Codex + especialistas funcionales, tecnicos y QA |
| Archivos | `docs/qa/guia_pruebas_qa_mvp.md`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | QA, onboarding, Administracion, Produccion, modulos prototipo, regresion |
| Descripcion | Se documento el alcance comprobable por una persona de QA con contexto de negocio, prioridades P0/P1/P2, precondiciones, smoke diario, pasos, resultados esperados, motivo de cada prueba, evidencia minima y plantilla de defectos. La guia separa funciones reales en QA, prototipos locales y modulos todavia no disponibles. |
| Motivo | Dar al equipo QA una referencia operativa basada en lo realmente implementado y evitar certificar como backend real una maqueta o reportar como defecto una integracion futura. |
| Impacto | QA puede priorizar acceso, aislamiento, Administracion y recetas reales; evaluar Almacenes/Ventas como prototipos; y registrar resultados y defectos con contexto suficiente para desarrollo. |
| Validacion | Revision cruzada de `AGENTES.md`, documentos funcionales, frontend, APIs, tests y `TRAZABILIDAD.md`; `npm.cmd run verify`. |
| Observaciones | La guia no contiene credenciales ni datos reales. Debe actualizarse cuando un submodulo cambie de local/mock a API persistente o se habilite un nuevo servicio. |

### CHG-141

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-24 |
| Cambio | Documento Word de pruebas QA |
| Autor | Codex |
| Archivos | `docs/qa/guia_pruebas_qa_mvp.docx`, `tools/generate-qa-document.py`, `package.json`, `README.md`, `TRAZABILIDAD.md` |
| Secciones | QA, Word, casos de prueba, contexto de negocio |
| Descripcion | La guia Markdown se transformo en un documento Word profesional con portada, metadatos del ambiente, indice actualizable, encabezados, pie de pagina, listas y tablas formateadas para alcance, casos, evidencia y defectos. |
| Motivo | Entregar al equipo QA una guia legible y compartible en Word que explique que probar, como hacerlo y por que importa para el negocio. |
| Impacto | QA puede consultar, imprimir o compartir el documento y regenerarlo desde la fuente Markdown con `npm run qa:document`. |
| Validacion | Generacion y reapertura con python-docx 1.2.0; contenido clave, tablas y tamano comprobados; `npm.cmd run verify`. |
| Observaciones | El Markdown sigue siendo la fuente de verdad; regenerar el Word despues de modificar los casos. No capturar secretos, tokens o ligas vigentes. |

### CHG-142

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-24 |
| Cambio | Promocion del guardrail de invitaciones a Admin QA |
| Autor | Codex |
| Archivos | `TRAZABILIDAD.md` |
| Secciones | Cloud Run QA, configuracion publica, onboarding |
| Descripcion | Se construyo y desplego `backend/` en `admin-service-qa` para activar la validacion que rechaza URLs locales o sin HTTPS en QA/Produccion. Tambien se configuro `ERCLAVE_API_PUBLIC_BASE_URL` con la URL publica del servicio para que `/version` no anuncie localhost. |
| Motivo | La revision que corrigio la redireccion Firebase solo habia actualizado variables sobre una imagen anterior; faltaba promover el guardrail de codigo y corregir la metadata publica del servicio. |
| Impacto | QA queda protegido contra futuras invitaciones con `continueUrl` local y reporta sus URLs publicas correctas. |
| Validacion | Revision final `admin-service-qa-00013-xmz` lista con 100% de trafico; `ERCLAVE_APP_PUBLIC_BASE_URL=https://erclave.web.app`; health y readiness HTTP 200; `/version` con URL publica; GitHub Actions aprobado. |
| Observaciones | La guia QA y su documento Word no requieren despliegue de frontend; se publican como artefactos del repositorio. |

### CHG-143

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-26 |
| Cambio | Guardrail del tenant autorizado para desarrollo |
| Autor | Codex |
| Archivos | `AGENTS.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `docs/qa/guia_pruebas_qa_mvp.docx`, `TRAZABILIDAD.md` |
| Secciones | Desarrollo local, QA, aislamiento multitenant, datos dummy |
| Descripcion | Se establecio `ERClave Demo QA` (`ten_739ee59d765d5e14818674800d`) como el unico tenant autorizado para desarrollo local, pruebas manuales y datos dummy. Se exige confirmar el tenant antes de toda escritura y detenerse si no coincide. |
| Motivo | Proteger el tenant separado del equipo de QA y evitar que seeds, cargas ficticias o mutaciones de ensayo contaminen sus datos. |
| Impacto | Las futuras sesiones de Codex y la ejecucion manual de QA tienen una regla persistente y verificable para seleccionar el tenant de trabajo. Cualquier uso de otro tenant requiere autorizacion explicita. |
| Validacion | Regla operativa revisada en `AGENTS.md`; guia Markdown y documento Word regenerado; `npm.cmd run verify`. |
| Observaciones | No se documentan identificadores ni credenciales del tenant reservado del equipo de QA; la proteccion se expresa mediante una lista permitida de un solo tenant. |

### CHG-144

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-26 |
| Cambio | Catalogo enfocado de productos y servicios |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `modulos/01_produccion.md`, `TRAZABILIDAD.md` |
| Secciones | Frontend, Produccion, productos y servicios, ordenes |
| Descripcion | Se reorganizo la vista inicial de Productos y servicios como un catalogo a ancho completo con resumen, buscador, datos maestros, costos, receta vigente y acciones por ficha. El historial de ordenes dejo de mostrarse dentro de la tarjeta y se sustituyo por una accion `Ver ordenes` con contador que abre Ordenes filtradas por el producto seleccionado. |
| Motivo | Mantener la primera pantalla enfocada en consultar y administrar el catalogo, evitando mezclar el detalle operativo de ordenes y corrigiendo la distribucion estrecha causada por el riel lateral. |
| Impacto | Cada producto o servicio conserva acceso a su ficha y receta, y ahora permite consultar sus ordenes en una vista especializada con regreso al catalogo o eliminacion del filtro. La relacion se resuelve por producto y recetas asociadas sin cambiar APIs ni persistencia. |
| Validacion | Paridad i18n ES/EN, sintaxis JavaScript, validadores del repositorio y pruebas backend mediante `npm.cmd run verify`. |
| Observaciones | El cambio es exclusivamente de frontend y documentacion funcional. No se desplego ni se escribieron datos en QA. |

### CHG-145

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-26 |
| Cambio | MVP real local de Almacenes e Inventarios |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260726_0007_inventory_service_initial.py`, `backend/services/inventory-service/`, `backend/services/inventory_service_adapter.py`, `backend/pyproject.toml`, `backend/README.md`, `contracts/api/inventory-service.openapi.yaml`, `frontend/api/inventory.js`, `frontend/api/config.js`, `frontend/app.js`, `frontend/env.js`, `TRAZABILIDAD.md` |
| Secciones | Almacenes, articulos, movimientos, existencias, Kardex, autorizacion, auditoria |
| Descripcion | Se implemento el corte vertical de inventory-service con schema propio, almacenes y articulos por tenant, movimientos inmutables, transferencias y reversas atomicas, bloqueo de saldos negativos, existencias y Kardex calculados, idempotencia, auditoria, autorizacion contra Admin y cliente frontend. |
| Motivo | Proveer una fuente de verdad de materiales antes de continuar la integracion real del flujo de Produccion. |
| Impacto | El frontend consume inventory-service local en el puerto 8004 contra PostgreSQL portatil aislado en 5434. Las escrituras requieren tenant, permiso e Idempotency-Key; no se modificaron datos ni infraestructura de QA. |
| Validacion | `npm.cmd run verify` con 91 pruebas; 7 pruebas nuevas de API Inventory; ciclo Alembic real `upgrade -> downgrade -> upgrade` en `erclave_local`; smoke persistente con 2 almacenes, 1 articulo, entrada, salida, saldo 17, Kardex, auditoria, idempotencia y lectura negativa de aislamiento. |
| Observaciones | PostgreSQL 17.10 portatil vive en `C:\tmp\erclave-postgresql17`, escucha solo en `127.0.0.1:5434` con SCRAM y puede iniciarse junto con Inventory API usando el script documentado con bypass por proceso, sin cambiar la politica global. Cloud SQL QA no recibio migraciones ni escrituras. Reservas quedan fuera de este corte. |

### CHG-146

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-27 |
| Cambio | Especificacion escalable y validacion local de volumen de Inventario |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/api/inventory.js`, `frontend/data/modules.js`, `frontend/i18n/translations.js`, `backend/services/inventory-service/app/`, `backend/services/inventory-service/tests/`, `backend/alembic/versions/20260727_0008_inventory_search_indexes.py`, `contracts/api/inventory-service.openapi.yaml`, `docs/arquitectura/inventario_consulta_escalable.md`, `docs/operaciones/validacion_volumen_inventario_local.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `modulos/02_almacenes_inventarios.md`, `tools/benchmarks/inventory-volume.js`, `TRAZABILIDAD.md` |
| Secciones | Inventario, Existencias, busqueda, filtros, paginacion, volumen local |
| Descripcion | Se renombro visualmente el submodulo Existencias a Inventario conservando el modulo Almacenes y los identificadores tecnicos `almacenes` y `existencias`. Se implementaron filtros y paginacion server-side, la igualdad temporal entre disponible y existencia fisica hasta implementar Reservas, y validaciones locales con 10,000 articulos por tenant. |
| Motivo | Preparar una consulta operativa que pueda crecer sin descargar catalogos completos al navegador y verificar desde ahora su semantica de aislamiento, filtros y recorrido por cursor. |
| Impacto | La consulta de Inventario consume balances enriquecidos y paginados desde `inventory-service`; incorpora busqueda parcial, filtros, orden y controles multitenant sin cambiar rutas tecnicas. |
| Validacion | 19 pruebas de inventory-service; 103 pruebas backend totales; benchmark en memoria de 10,000 articulos/20,000 filas en 59.1 ms; PostgreSQL local con 10,000 articulos y 10,000 movimientos, busqueda sin acento y pagina de 50 en 30.896 ms tras `ANALYZE`; migracion `0008`; `npm.cmd run verify`. |
| Observaciones | No se desplego, migro, cargo ni escribio informacion en QA. El umbral local de 2 segundos detecta regresiones gruesas y no constituye un SLO de produccion. |

### CHG-147

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-27 |
| Cambio | Memoria operativa persistente entre sesiones |
| Autor | Codex |
| Archivos | `AGENTS.md`, `package.json`, `docs/contexto/`, `tools/session-context.js`, `tools/validators/validate-session-context.js`, `tools/validators/validate-all.js`, `tools/validators/validate-codex-tooling.js`, `TRAZABILIDAD.md` |
| Secciones | Inicio de sesion, estado actual, decisiones, tenants, pendientes, automatizacion Codex |
| Descripcion | Se agrego `npm.cmd run session:context` para recuperar en modo solo lectura la rama, cambios locales, ultima migracion, ultima trazabilidad, memoria operativa y estado de servicios. Se incorporaron documentos persistentes y un validador obligatorio. |
| Motivo | Reducir la perdida de contexto y asegurar que nuevas sesiones recuperen validaciones, decisiones de arquitectura, limites de agentes, tenant autorizado y siguiente prioridad desde el repositorio. |
| Impacto | Las nuevas sesiones cuentan con un bootstrap reproducible y sin secretos. El flujo de inicio y cierre de `AGENTS.md` obliga a consultar y mantener esta memoria. |
| Validacion | `npm.cmd run session:context`, `npm.cmd run validate:session-context`, `npm.cmd run verify`. |
| Observaciones | El comando es solo lectura y no inicia servicios, modifica datos ni contacta QA. El contenido sigue requiriendo mantenimiento al cerrar cada corte. |

### CHG-148

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-27 |
| Cambio | Responsividad de la vista Inventario |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/index.html`, `frontend/styles.css`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Inventario, flujo guiado, filtros, tabla, alertas, responsive |
| Descripcion | Se colapso el flujo de Inventario por defecto, se agregaron container queries para adaptar filtros y filas al ancho real del panel, etiquetas en modo tarjeta, hero flexible y reubicacion de Alertas en viewports intermedios. |
| Motivo | Evitar encabezados encimados, textos cortados y compresion excesiva cuando conviven sidebar, flujo y panel de alertas. |
| Impacto | Inventario conserva la tabla completa en paneles amplios y cambia a tarjetas de dos o una columna cuando el contenedor se estrecha, sin depender solo del ancho total de la ventana. |
| Validacion | `npm.cmd run validate:syntax`, `npm.cmd run validate:i18n`, `npm.cmd run validate:active-localization`, comprobacion HTTP del copy Inventario y `npm.cmd run verify`. |
| Observaciones | Se agrego version al entrypoint del frontend para evitar que el navegador conserve el copy anterior. No hubo despliegues ni escrituras sobre QA. |

### CHG-149

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-27 |
| Cambio | Estandar responsive transversal para agentes y QA |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `frontend/index.html`, `frontend/backoffice/styles.css`, `frontend/backoffice/app.js`, `frontend/backoffice/index.html`, `tools/validators/validate-responsive-ui.js`, `tools/validators/validate-all.js`, `package.json`, `docs/arquitectura/estandar_responsive_transversal.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `AGENTS.md`, `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Responsive, container queries, tablas, formularios, flujos, alertas, QA |
| Descripcion | Se implemento y documento un estandar transversal con container queries para el panel operativo, modales y backoffice; layouts flexibles para catalogos, formularios, guias y acciones; filas etiquetadas en Inventario y backoffice; navegacion movil accesible, foco visible, salto al contenido y soporte de movimiento reducido. Un validador automatico protege sus puntos estructurales. |
| Motivo | Evitar que cada modulo resuelva responsive de forma aislada o dependa solo del viewport cuando sidebar y paneles laterales determinan el ancho operativo real. |
| Impacto | Los modulos y secciones existentes responden al ancho util que dejan sidebar, flujo y alertas; todos los agentes cuentan con criterios comunes y QA dispone de una matriz reproducible para detectar bloqueos, truncamientos, superposiciones y perdida de operabilidad. |
| Validacion | `npm.cmd run validate:responsive`, revision cruzada de arquitectura, accesibilidad y reglas de agentes; `npm.cmd run verify`; `git diff --check`. |
| Observaciones | Se actualizaron codigo fuente y documentacion Markdown, sin desplegar, regenerar el DOCX ni escribir datos en QA. La matriz visual manual permanece como requisito antes de promover el corte. |

### CHG-150

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-28 |
| Cambio | Separacion funcional de areas y puestos de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/data/mockDb.js`, `frontend/data/resources.js`, `frontend/i18n/translations.js`, `frontend/index.html`, `contracts/api/production-service.openapi.yaml`, `docs/arquitectura/apis_mvp.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `modulos/01_produccion.md`, `tools/validators/validate-labor-catalog.js`, `tools/validators/validate-all.js`, `package.json`, `TRAZABILIDAD.md` |
| Secciones | Produccion, areas, puestos, recursos, permisos, OpenAPI |
| Descripcion | Se sustituyo el formulario combinado por un catalogo independiente de areas y otro formulario para puestos. Los puestos seleccionan por `areaId` una area previamente creada; areas y puestos pueden editarse por separado y el renombrado conserva la relacion. Se definieron permisos independientes de lectura, creacion y edicion para ambos recursos. |
| Motivo | Evitar que errores tipograficos en un campo de texto creen areas implicitas y permitir delegar la administracion de areas y recursos laborales mediante roles distintos. |
| Impacto | El flujo local rechaza puestos con areas inexistentes, evita duplicados de area y puesto, migra registros demo anteriores hacia IDs estables y prepara el contrato de production-service para persistencia multitenant posterior. |
| Validacion | `npm.cmd run validate:labor-catalog`, paridad i18n ES/EN, validacion OpenAPI, sintaxis JavaScript y `npm.cmd run verify`. |
| Observaciones | No se implemento aun persistencia backend de areas/puestos, no hubo migraciones, seeds, despliegues ni escrituras en QA. Los endpoints documentados son el contrato objetivo del siguiente corte backend. |

### CHG-151

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-28 |
| Cambio | Restauracion del riel vertical y limites de cambios compartidos |
| Autor | Codex |
| Archivos | `frontend/styles.css`, `frontend/index.html`, `tools/validators/validate-responsive-ui.js`, `docs/arquitectura/estandar_responsive_transversal.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `AGENTS.md`, `AGENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Guias de flujo, responsive, limites de alcance, agentes |
| Descripcion | Se elimino la regla transversal que convertia toda guia abierta en una barra horizontal cuando el panel alcanzaba 1180 px. Se restauro el patron compartido de riel vertical izquierdo con estado comprimido y se formalizo que las excepciones deben usar clases especificas de pantalla. |
| Motivo | La correccion responsive originada en Inventario altero componentes de Areas y puestos y otros submodulos que no formaban parte del problema original. |
| Impacto | Los flujos descriptivos recuperan su distribucion estandar y futuras correcciones locales quedan impedidas de modificar globalmente el formato compartido sin delimitacion explicita. |
| Validacion | `npm.cmd run validate:responsive`, sintaxis, trazabilidad, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Cambio exclusivo de frontend, validadores y documentacion. No hubo despliegues, migraciones, seeds ni escrituras en QA. |

### CHG-152

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Inventario cero, recursos reales de receta y modulo RH |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260730_0009_inventory_recipe_flag.py`, `backend/services/inventory-service`, `contracts/api/inventory-service.openapi.yaml`, `frontend`, `modulos`, `docs/contexto`, `docs/qa` |
| Secciones | Inventario, Articulos, Recetas, Recursos Humanos |
| Descripcion | Inventario incluye articulos sin movimientos con saldo cero; Articulos incorpora Usar en receta; Recetas consume candidatos reales de Almacenes; Areas y puestos se mueve a RH con costo por hora y bandera productiva. |
| Motivo | El alta de articulos no era visible sin movimientos y Produccion seguia usando recursos fijos del frontend. |
| Impacto | Integracion local coherente entre inventario, receta y mano de obra sin escribir en QA. |
| Validacion | Migracion local aislada `0009`, pruebas inventory-service, validadores, consulta directa de balances y `npm.cmd run verify`. |
| Observaciones | No hubo despliegue, seed ni migracion sobre QA. RH conserva persistencia local y permisos transitorios `production.labor_*`. |

### CHG-153

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Desacoplamiento integral del modulo Recursos Humanos |
| Autor | Codex |
| Archivos | `backend/services/hr-service`, `backend/alembic/versions/20260730_0010_hr_service_initial.py`, `contracts/api/hr-service.openapi.yaml`, `frontend/api/hr.js`, `frontend/microfrontends/recursos-humanos`, `frontend/app.js`, `frontend/backoffice/app.js`, `AGENTES.md`, `modulos`, `docs`, `tools/validators` |
| Secciones | Entitlement SaaS, permisos, areas, puestos, idempotencia, auditoria, aislamiento tenant, agentes |
| Descripcion | RH se convirtio en modulo y servicio propietarios: se registro el entitlement `hr`, se agregaron permisos `hr.area.*` y `hr.position.*`, API y esquema propios, validacion de sesion/tenant/modulo/permiso, FK compuesta, idempotencia, auditoria y consumo de puestos elegibles desde Produccion. |
| Motivo | Permitir activar o suspender RH y delegar sus funciones sin depender de Produccion ni de controles exclusivamente visuales. |
| Impacto | Produccion deja de ser dueno del catalogo laboral; Administracion puede contratar el modulo por tenant y asignar permisos independientes; agentes transversales y especialistas cuentan con ownership y controles documentados. |
| Validacion | Pruebas unitarias de `hr-service`, validadores de arquitectura/agentes/OpenAPI, migracion local aislada y suite `npm.cmd run verify`. |
| Observaciones | Trabajo local. No se desplego ni se ejecuto migracion, seed, activacion o escritura sobre QA. |

### CHG-154

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Grupo de permisos de Recursos Humanos en Administracion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `backend/services/admin-service/tests/test_permission_seeds.py`, `tools/validators/validate-labor-catalog.js`, `modulos/10_recursos_humanos.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion, Permisos, Roles, Recursos Humanos |
| Descripcion | El catalogo de permisos muestra RH como Recursos Humanos y el selector de permisos de roles agrupa sus seis acciones por separado. Una prueba extrae los contratos completos y evita reintroducir permisos `production.labor_*`. |
| Motivo | Hacer visible y asignable el nuevo modulo con la misma estructura administrativa del resto de ERClave. |
| Impacto | Los administradores pueden identificar y asignar permisos de areas y puestos sin confundirlos con Produccion; activar el entitlement sigue sin conceder permisos implicitamente. |
| Validacion | Prueba de seeds OpenAPI, validador de catalogos laborales, sintaxis frontend y `npm.cmd run verify`. |
| Observaciones | Cambio local; QA no recibio seeds, migraciones, activaciones ni escrituras. |

### CHG-155

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Reconciliacion de permisos laborales heredados |
| Autor | Codex |
| Archivos | `backend/scripts/seed_admin_mvp.py`, `backend/services/admin-service/tests/test_permission_seeds.py`, `tools/validators/validate-labor-catalog.js`, `tools/validators/validate-db-guardrails.js`, `modulos/10_recursos_humanos.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion, permisos, seeds, Recursos Humanos |
| Descripcion | El seed idempotente desactiva nueve permisos laborales heredados de Produccion y mantiene como vigentes exclusivamente los seis permisos `hr.area.*` y `hr.position.*`. La prueba ahora bloquea cualquier prefijo `production.labor`, incluido el formato con punto observado en QA. |
| Motivo | Los seeds anteriores solo hacian upsert y dejaban activos permisos retirados del OpenAPI, provocando que Administracion siguiera mostrandolos bajo Produccion. |
| Impacto | Los permisos antiguos dejan de aparecer y de ser efectivos sin borrar sus registros o relaciones historicas; RH conserva ownership independiente. |
| Validacion | Seed aplicado dos veces en PostgreSQL local, consulta de estados, pruebas de contratos, guardrails de DB y `npm.cmd run verify`. |
| Observaciones | La reconciliacion se aplico solo a local. Ejecutarla en QA requiere autorizacion explicita. |

### CHG-156

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Sincronizacion autorizada del catalogo de permisos RH en QA |
| Autor | Codex, con autorizacion explicita del usuario |
| Archivos | PostgreSQL QA `admin.permissions`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion, permisos, Recursos Humanos, QA |
| Descripcion | Se ejecuto el seed idempotente contra `erclave_qa`: se activaron seis permisos `hr.area.*` y `hr.position.*`, y se inactivaron `production.labor.create/read/update`. |
| Motivo | El catalogo de QA conservaba permisos laborales heredados bajo Produccion y no mostraba el grupo Recursos Humanos. |
| Impacto | `GET /v1/permissions` devuelve 98 permisos activos, incluye seis bajo `module_code=hr` y no expone ningun prefijo `production.labor`. Las relaciones historicas se conservaron inactivas. |
| Validacion | Preflight de identidad `erclave_qa`, postcondiciones SQL y lectura final de la Admin API local conectada a QA. |
| Observaciones | No se ejecutaron migraciones, despliegues, datos dummy, cambios de entitlement ni escrituras en catalogos funcionales de RH. |

### CHG-157

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-30 |
| Cambio | Editor seguro e intuitivo de permisos por rol, sin plantillas |
| Autor | Codex con revision transversal de arquitectura, seguridad y frontend |
| Archivos | `frontend/app.js`, `frontend/api/admin.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `backend/services/admin-service/app/*`, `backend/services/admin-service/tests/*`, `backend/alembic/versions/20260730_0011_admin_permission_editor.py`, `backend/scripts/seed_admin_mvp.py`, `contracts/api/admin-service.openapi.yaml`, documentacion y validadores |
| Secciones | Administracion, roles, permisos, seguridad, multitenant, frontend, PostgreSQL |
| Descripcion | Se reemplazo la asignacion tortuosa por un editor con nombres funcionales ES/EN, busqueda, filtros, grupos, acciones masivas solo sobre resultados visibles, borrador, diff y guardado unico. El backend separa `admin.role.permissions.manage`, filtra permisos asignables por tenant y entitlement, aplica diffs, revision optimista e idempotencia persistente. |
| Motivo | Hacer entendible y agil la personalizacion de roles sin perder granularidad ni abrir escalaciones hacia permisos internos o modulos no contratados. |
| Impacto | Los roles siguen siendo completamente personalizables. Las asignaciones heredadas no visibles se preservan, los scopes no se sobrescriben y los conflictos concurrentes requieren recarga antes de reintentar. |
| Validacion | `npm.cmd run verify`: 116 pruebas backend y todos los validadores aprobados; ademas, prueba PostgreSQL de integracion real, migracion/seed en `erclave_local`, smoke test del repositorio, OpenAPI offline y `git diff --check`. |
| Observaciones | No se implementaron plantillas ni presets. No hubo despliegue, migracion, seed ni escritura en QA. |

### CHG-158

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-31 |
| Cambio | Apertura explicita del visor de permisos cuando QA aun no tiene el permiso de gestion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `TRAZABILIDAD.md` |
| Secciones | Administracion, roles, permisos, UX, seguridad |
| Descripcion | El boton ya no aparenta estar operativo mientras permanece deshabilitado. Con `admin.role.read` abre el detalle como `Ver permisos`; si falta `admin.role.permissions.manage`, presenta un aviso visible de solo lectura y bloquea checkboxes, acciones masivas y guardado. |
| Motivo | La API QA actual conserva 98 permisos y aun no incluye el permiso nuevo, por lo que el boton anterior no ejecutaba eventos y no explicaba la causa. |
| Impacto | El usuario puede inspeccionar las asignaciones sin obtener capacidad de escritura por fallback. La edicion se habilitara automaticamente cuando backend, migracion y seed compatibles sean promovidos con autorizacion. |
| Validacion | `npm.cmd run verify`: 116 pruebas backend, i18n, sintaxis, responsive, editor de permisos, contratos y guardrails aprobados; `git diff --check` sin errores. |
| Observaciones | No hubo migracion, seed, despliegue ni escritura en QA. |

### CHG-159

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-31 |
| Cambio | Correccion del render del visor de permisos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `tools/validators/validate-permission-editor.js`, `TRAZABILIDAD.md` |
| Secciones | Administracion, roles, permisos, frontend |
| Descripcion | Se incorporo la utilidad compartida `escapeHtml` usada por el editor y formularios de RH. Su ausencia provocaba `ReferenceError` al abrir Ver permisos y detenía el render. |
| Motivo | El validador anterior comprobaba la presencia del flujo del editor, pero no que todas sus utilidades de render estuvieran definidas. |
| Impacto | Ver permisos abre correctamente; los textos dinamicos siguen escapados para evitar inyeccion de HTML. |
| Validacion | Validador del editor, sintaxis JavaScript y `npm.cmd run verify`: 116 pruebas backend y todos los guardrails aprobados. |
| Observaciones | El 404 de `favicon.ico` observado en consola es independiente y no afecta la aplicacion. No se toco QA. |

### CHG-160

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-31 |
| Cambio | Promocion autorizada de migraciones y editor de permisos a PostgreSQL QA |
| Autor | Codex, con autorizacion explicita del usuario |
| Archivos | PostgreSQL QA `erclave_qa`, `backend/alembic/versions/20260726_0007_inventory_mvp.py` a `20260730_0011_admin_permission_editor.py`, `backend/scripts/seed_admin_mvp.py`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `docs/qa/guia_pruebas_qa_mvp.md`, `TRAZABILIDAD.md` |
| Secciones | QA, PostgreSQL, Administracion, permisos, Almacenes, Recursos Humanos |
| Descripcion | Se genero y verifico un respaldo completo, se promovio Alembic desde `20260721_0006` hasta `20260730_0011`, y se ejecuto dos veces el seed administrativo para comprobar idempotencia. La Admin API local fue reiniciada contra QA con el codigo compatible. |
| Motivo | Habilitar el editor real de permisos y alinear el esquema QA con los contratos ya validados localmente. |
| Impacto | QA expone 99 permisos activos y el owner de ERClave Demo QA conserva el piso administrativo con `admin.role.permissions.manage`. Se crearon los esquemas de Inventory y RH sin cargar registros funcionales o dummy. |
| Validacion | Respaldo custom verificado con `pg_restore --list`; revision Alembic `20260730_0011`; tenant y modulo admin activos; un grant de gestion para el owner objetivo; cero owners del sistema sin piso, cero codigos activos duplicados, cero registros en almacenes, articulos, movimientos, areas y puestos; health/OpenAPI 200, llamada sin token 401; `npm.cmd run verify` con 116 pruebas aprobadas y todos los validadores. |
| Observaciones | Respaldo recuperable en `C:\tmp\erclave_qa_pre_permission_20260731_093634.dump`. No se desplego frontend ni servicio alguno, no se activaron entitlements adicionales y no se ejecutaron seeds demo o cargas de volumen. |

### CHG-161

| Campo | Contenido |
|---|---|
| Fecha | 2026-07-31 |
| Cambio | Cierre persistente de sesion y preparacion de publicacion |
| Autor | Codex |
| Archivos | `.gitignore`, `tools/session-context.js`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Operacion local, memoria persistente, repositorio |
| Descripcion | El comando `session:context` verifica la Admin API en el puerto real `8000` y el repositorio ignora temporales `.$*.drawio.dtmp` para que un reinicio no confunda archivos de recuperacion del editor con cambios funcionales. |
| Motivo | Dejar una lectura fiel y limpia del entorno al reiniciar la computadora o iniciar una nueva sesion de Codex. |
| Impacto | La siguiente sesion recupera rama, migracion, trazabilidad, decisiones, pendientes y servicios locales sin reportar falsamente apagada la Admin API ni proponer temporales de Draw.io para commit. |
| Validacion | `npm.cmd run session:context`, `git check-ignore`, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | No modifica datos, migraciones, seeds, despliegues ni configuracion de QA. |

### CHG-162

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Formaliza fronteras de ambientes |
| Autor | Codex, con decisiones aprobadas por el usuario propietario |
| Archivos | `AGENTS.md`, `AGENTES.md`, `.agents/skills/erclave-environment-boundaries/`, `.agents/skills/erclave-feature/SKILL.md`, `.agents/skills/erclave-db-migration/SKILL.md`, `docs/arquitectura/fronteras_ambientes_local_qa_produccion.md`, `docs/arquitectura/qa_prod.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `tools/validators/validate-environment-boundaries.js`, `tools/validators/validate-all.js`, `tools/validators/validate-codex-tooling.js`, `package.json`, `TRAZABILIDAD.md` |
| Secciones | Local, QA, Produccion, Firebase Emulator, release, agentes, skills y validadores |
| Descripcion | Se establecio Local aislado con Firebase Emulator y recursos locales, se separo la variante local conectada a QA bajo autorizacion explicita y se definieron gates de promocion, RPO 15 minutos, RTO 2 horas, aprobacion directa del usuario y alcance del primer release: Administracion, Backoffice, Produccion, Almacenes/Inventario, RH y Ventas. |
| Motivo | Evitar que procesos ejecutados en localhost consuman silenciosamente recursos QA y convertir las fronteras de ambientes en instrucciones reutilizables y validables. |
| Impacto | Las tareas de arranque, pruebas, migraciones, seeds y despliegues deben ejecutar preflight de ambiente. Firebase Emulator queda aprobado como objetivo local, pero su arranque canonico aun debe implementarse y validarse antes de declararlo operativo. |
| Validacion | `quick_validate.py` para la skill, `validate-environment-boundaries.js`, `validate-codex-tooling.js`, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | No se conecto ni escribio en QA, no se crearon recursos productivos y no hubo migraciones, seeds, cargas de datos ni despliegues. |

### CHG-163

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Actualiza agentes al estado operativo vigente |
| Autor | Codex |
| Archivos | `AGENTES.md`, `modulos/README.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `tools/validators/validate-agents.js`, `TRAZABILIDAD.md` |
| Secciones | Agentes transversales, agentes modulares, Local, QA, primer release y validadores |
| Descripcion | Se agrego una matriz obligatoria que separa capacidades desplegadas en QA, implementadas solo en Local, prototipos y objetivos futuros. Se corrigieron referencias obsoletas a API futura de Produccion, UI pendiente de Administracion, endpoints pendientes de Inventario y pendientes de agentes ya automatizados. |
| Motivo | Evitar que un agente confunda codigo, contrato, migracion o schema con una capacidad desplegada y asegurar que cada recomendacion nombre ambiente y evidencia. |
| Impacto | Todos los agentes consultan el mismo estado operativo antes de aprobar cambios; `validate-agents.js` bloquea la perdida de esa matriz y la reaparicion de frases obsoletas. |
| Validacion | `validate-agents.js`, `validate-environment-boundaries.js`, `validate-active-module-localization.js`, `validate-architecture.js`, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | No hubo conexiones o escrituras en QA, migraciones, seeds, cargas, despliegues ni infraestructura productiva. |

### CHG-164

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Habilita el stack local canonico y aislado con Firebase Emulator |
| Autor | Codex |
| Archivos | `firebase.json`, `frontend/api/config.js`, `frontend/auth.js`, `frontend/env.js`, `frontend/backoffice/env.js`, `frontend/backoffice/README.md`, `backend/services/admin-service/app/auth.py`, `backend/scripts/start_local.ps1`, `backend/scripts/seed_local_demo.py`, `backend/scripts/seed_admin_qa_demo.py`, `backend/services/admin-service/tests/test_local_demo_seed.py`, `backend/README.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `tools/validators/validate-environment-boundaries.js`, `TRAZABILIDAD.md` |
| Secciones | Arranque local, autenticacion, datos demo, Administracion, Produccion, Inventario, RH y frontend |
| Descripcion | Se agrego un arranque unico que valida las fronteras, prepara exclusivamente `erclave_local`, inicia Firebase Auth Emulator bajo el proyecto sintetico `demo-erclave`, crea el usuario local y levanta frontend y APIs en loopback. El seed local activa `admin`, `production`, `inventory`, `hr`, `sales` e `integrations`. El frontend ignora modos de autenticacion persistidos y rechaza URLs remotas cuando se ejecuta en localhost. |
| Motivo | Permitir revisar y continuar el flujo funcional completo sin consumir autenticacion, APIs, base de datos ni infraestructura de QA. |
| Impacto | El entorno local queda reproducible mediante `backend/scripts/start_local.ps1`, con autenticacion Firebase emulada y datos locales independientes. |
| Validacion | Pruebas focalizadas de seeds, validadores de fronteras, sintaxis JavaScript y PowerShell, smoke autenticado de sesion, productos, recetas, almacenes, balances, areas y puestos, mas `npm.cmd run verify`. |
| Observaciones | Solo se escribio el seed en PostgreSQL local `127.0.0.1:5434/erclave_local`. El JDK portatil reside en `C:\\tmp`; no hubo solicitudes, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-165

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Corrige persistencia de movimientos y refresco de inventario |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `tools/validators/validate-inventory-movement-flow.js`, `tools/validators/validate-all.js`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Almacenes, Movimientos, Inventario calculado, Kardex, Recetas y validacion automatica |
| Descripcion | El guardado de un movimiento en modo API ahora ejecuta `createInventoryMovement` antes del fallback maqueta, invalida los estados de Movimientos e Inventario y recarga la lista desde PostgreSQL. Se retiro de `saveRecipeForm` el comando de inventario que estaba desplazado y se agrego una validacion estructural para impedir su reaparicion. |
| Motivo | Movimientos mostraba registros guardados solo en `localStorage`, mientras Inventario consultaba balances reales sin esas entradas y por ello mostraba saldo cero. |
| Impacto | Nuevas entradas, salidas, ajustes y transferencias en modo API comparten una sola fuente de verdad con balances y Kardex. Los dos registros mock anteriores no se migran: deben repetirse localmente para conservar un comando auditable con sus datos originales. |
| Validacion | Revision de agentes funcional, tecnico y arquitectonico; inspeccion read-only de PostgreSQL local; `validate-inventory-movement-flow.js`, `validate-all.js`, sintaxis JavaScript, paridad i18n y `npm.cmd run verify`. |
| Observaciones | No hubo migraciones ni cambios de esquema. No se conecto, escribio, cargo, migro ni desplego en QA o Produccion. |

### CHG-166

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Implementa persistencia integral del ciclo de Produccion en Local |
| Autor | Codex, con revision arquitectonica transversal |
| Archivos | `backend/alembic/versions/20260804_0012_production_cycle.py`, `backend/services/production-service/app/`, `backend/services/production-service/tests/test_production_api.py`, `backend/services/production-service/README.md`, `contracts/api/production-service.openapi.yaml`, `frontend/api/production.js`, `frontend/app.js`, `tools/validators/validate-production-cycle.js`, `tools/validators/validate-all.js`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Productos/Servicios, Recetas, Maquinaria, validacion de recursos y costos, Ordenes, etapas, OpenAPI y frontend |
| Descripcion | Productos/Servicios y Maquinaria persisten por API; Recetas separan version vigente de borrador; las Ordenes exigen receta aprobada vigente, revalidan recursos, guardan snapshots y ejecutan maquinas de estado backend para orden y etapas con permisos, auditoria e idempotencia. |
| Motivo | Sustituir persistencia maqueta y evitar que el frontend sea fuente de verdad del ciclo productivo. |
| Impacto | El ciclo funcional se recarga desde PostgreSQL Local. La disponibilidad es una observacion conservada en la orden y no reserva ni consume Inventario; ese contrato queda como trabajo posterior. |
| Validacion | Alembic Local `upgrade`, `downgrade` y `upgrade`; 25 pruebas focalizadas de Production; smoke autenticado con Firebase Emulator del ciclo producto-maquina-receta-validacion-orden-etapa-cierre; `npm.cmd run verify` con 126 pruebas aprobadas y 1 omitida. |
| Observaciones | La migracion y los datos sinteticos se aplicaron solo a `127.0.0.1:5434/erclave_local`. No hubo conexiones, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-167

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Normaliza snapshots de receta al recargar ordenes de Produccion |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/utils/production.js`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `TRAZABILIDAD.md` |
| Secciones | Produccion, ordenes, recetas, notificaciones y cache frontend |
| Descripcion | La lectura de ordenes transforma el snapshot OpenAPI de receta a la estructura de calculo del frontend antes de generar costos, faltantes y notificaciones. El calculador tambien tolera recursos ausentes durante estados parciales de carga y se actualizo la version del modulo principal para invalidar cache. |
| Motivo | Una orden persistida entregaba un objeto de receta con `versions`, mientras `calculateRecipe` esperaba `resources` en la raiz y fallaba al ejecutar `.map()`. |
| Impacto | Produccion vuelve a renderizar productos, recetas, ordenes y notificaciones sin perder el snapshot historico de cada orden. |
| Validacion | Validador estructural actualizado, sintaxis JavaScript y `npm.cmd run verify` con 126 pruebas aprobadas y 1 omitida. |
| Observaciones | Correccion exclusiva de codigo Local; no hubo conexiones, escrituras, migraciones ni despliegues en QA o Produccion. El `403` de lectura administrativa de entitlements es independiente y no causa el fallo de Produccion. |

### CHG-168

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-04 |
| Cambio | Corrige autorizacion y rotulado de entitlements en Administracion Local |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/api.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `docs/arquitectura/apis_mvp.md`, `frontend/app.js`, `frontend/index.html`, `TRAZABILIDAD.md` |
| Secciones | Administracion, entitlements, autorizacion, OpenAPI y fronteras visuales de ambiente |
| Descripcion | La consulta de modulos del tenant exige `admin.tenant.read`, disponible para el owner y acotado por el tenant de la ruta. Modificar entitlements conserva `admin.entitlement.manage`. La interfaz identifica endpoints loopback como `API Local` y mantiene `API QA` solo para URLs remotas. |
| Motivo | El GET de entitlements exigia un permiso interno no asignable a roles humanos y devolvia 403 al owner autenticado en Firebase Emulator; ademas la etiqueta fija mostraba QA aunque la URL efectiva era local. |
| Impacto | El panel de Administracion carga modulos y limites en Local sin relajar permisos de escritura ni ocultar el ambiente efectivo. |
| Validacion | 53 pruebas focalizadas de Admin; smoke autenticado contra Firebase Emulator y Admin API Local con HTTP 200; OpenAPI, sintaxis, cache frontend y `npm.cmd run verify`. |
| Observaciones | Se reinicio unicamente Admin API Local. No hubo conexiones, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-169

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Retira la evaluacion interna de policy del dashboard de Administracion |
| Autor | Codex |
| Archivos | `frontend/api/admin.js`, `frontend/index.html`, `tools/validators/validate-permission-editor.js`, `TRAZABILIDAD.md` |
| Secciones | Administracion, session context, autorizacion frontend y cache |
| Descripcion | El dashboard obtiene la indicacion visual de lectura desde los permisos efectivos devueltos por `session/context` y deja de invocar `POST /v1/policy/evaluate`. El endpoint interno conserva intacta su autorizacion `internal.policy.evaluate`. |
| Motivo | La interfaz de un usuario tenant llamaba un contrato interno y recibia correctamente 403, lo que convertia una comprobacion visual redundante en error de carga de todo el panel. |
| Impacto | Administracion carga exclusivamente con contratos autorizados para el owner, sin duplicar la decision backend ni conceder permisos internos a usuarios humanos. |
| Validacion | Validador del editor actualizado, smoke autenticado de todos los GET del dashboard contra Firebase Emulator y APIs Local, sintaxis y `npm.cmd run verify`. |
| Observaciones | Cambio exclusivo de frontend Local; no se modifico la autorizacion del evaluador interno y no hubo conexiones, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-170

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Corrige el guardado API de areas de Recursos Humanos |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/index.html`, `tools/validators/validate-labor-catalog.js`, `TRAZABILIDAD.md` |
| Secciones | Recursos Humanos, areas, frontera frontend/API y cache |
| Descripcion | Se retiro del formulario de areas un bloque desplazado de Productos/Servicios que intentaba usar `item` antes de inicializarlo. El flujo ahora valida, construye el area y llama exclusivamente a `createHrArea` o `updateHrArea` antes del fallback mock. |
| Motivo | Al guardar un area en modo API, JavaScript lanzaba `Cannot access 'item' before initialization` y nunca enviaba el comando a `hr-service`. |
| Impacto | Altas y ediciones de areas pueden persistir en PostgreSQL Local mediante HR API y recargar su catalogo. |
| Validacion | Guardrail que impide APIs de Productos dentro del flujo de areas y exige inicializacion previa; pruebas focalizadas de HR, sintaxis, cache frontend y `npm.cmd run verify`. |
| Observaciones | No se registro automaticamente el area capturada por el usuario para evitar duplicar su comando al reintentar. No hubo conexiones, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-171

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Conecta Recetas exclusivamente con catalogos reales de Inventory y RH |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260805_0013_recipe_hr_areas.py`, `backend/services/production-service/app/schemas.py`, `backend/services/production-service/app/repositories.py`, `backend/services/production-service/tests/test_production_api.py`, `backend/services/production-service/README.md`, `contracts/api/production-service.openapi.yaml`, `frontend/app.js`, `frontend/utils/production.js`, `frontend/i18n/translations.js`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Recetas, Inventory, Recursos Humanos, etapas y fronteras de datos |
| Descripcion | En modo API el selector de recursos usa solo articulos activos con `use_in_recipe=true` y puestos RH activos con `intervenes_in_production=true`; excluye maquinaria y seeds. Las etapas se eligen entre areas RH activas y guardan `labor_area_ref_id` externo mas `labor_area_name` snapshot. Recursos historicos fuera del catalogo se omiten al editar una nueva version, sin alterar versiones aprobadas existentes. |
| Motivo | El formulario seguia precargando IDs mock y permitia etapas genericas por texto aunque Inventory y HR ya exponian APIs reales. |
| Impacto | Las nuevas versiones de receta quedan explicables y vinculadas a maestros existentes, sin FKs ni escrituras cruzadas. Actualmente Local devuelve cero materiales elegibles, dos puestos productivos y dos areas activas; los articulos deben marcarse para uso en receta antes de aparecer. |
| Validacion | Migracion Local `upgrade`, `downgrade` y `upgrade` hasta `20260805_0013`; 25 pruebas focalizadas de Production; smoke autenticado read-only de Inventory, HR y Production; validadores de OpenAPI, i18n, fronteras y ciclo productivo; `npm.cmd run verify`. |
| Observaciones | Se migro y reinicio exclusivamente Production API Local. No se crearon recetas ni catalogos durante el smoke. No hubo conexiones, escrituras, migraciones, seeds ni despliegues en QA o Produccion. |

### CHG-172

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Filtra y mejora el selector de areas productivas en Recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `docs/contexto/DECISIONES.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion, Recetas, Recursos Humanos, responsive y accesibilidad |
| Descripcion | Las areas seleccionables se derivan exclusivamente de puestos activos con `intervenes_in_production=true`. El fieldset anterior se reemplazo por tarjetas compactas con codigo, check visual, foco de teclado, estado seleccionado y una columna en contenedores estrechos. |
| Motivo | Un area activa de Ventas aparecia como etapa aunque ninguno de sus puestos interviniera en Produccion; los checkboxes heredaban estilos globales y se renderizaban desalineados. |
| Impacto | Recetas muestra solo areas realmente productivas y ofrece una seleccion legible, accesible y responsive sin cambiar el catalogo maestro de RH. |
| Validacion | Smoke autenticado read-only: dos puestos productivos, una area seleccionable y una area activa excluida; i18n, sintaxis, guardrail de ciclo productivo, cache frontend, responsive y `npm.cmd run verify`. |
| Observaciones | No hubo escrituras de datos, migraciones nuevas, seeds, conexiones o despliegues en QA o Produccion. |

### CHG-173

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Hace obligatorio reportar las APIs afectadas por cada cambio |
| Autor | Codex |
| Archivos | `AGENTS.md`, `AGENTES.md`, `.agents/skills/erclave-feature/SKILL.md`, `tools/traceability-draft.js`, `tools/validators/validate-codex-tooling.js`, `TRAZABILIDAD.md` |
| Secciones | Agentes, skills, trazabilidad, entrega y validadores |
| Descripcion | Cada cambio debe cerrar con un inventario que separe contratos API modificados, endpoints consumidos sin cambio y APIs no tocadas. El reporte incluye metodo, ruta, servicio, permiso y cambio de request/response cuando aplique; el borrador de trazabilidad incorpora el mismo campo. |
| Motivo | Evitar que el impacto contractual quede implicito o se omita durante la entrega y revision del usuario. |
| Impacto | Los agentes tecnicos y transversales, la skill de funcionalidades y el flujo de trazabilidad comparten una obligacion verificable y persistente. |
| APIs afectadas | Ninguna. Este cambio solo modifica instrucciones, automatizacion documental y validadores locales. |
| Validacion | `quick_validate.py` para `$erclave-feature`, `validate-codex-tooling.js`, borrador de trazabilidad y `npm.cmd run verify`. |
| Observaciones | No hubo cambios funcionales, conexiones, escrituras de datos, migraciones, seeds ni despliegues en Local, QA o Produccion. |

### CHG-174

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Separa materiales, mano de obra y maquinaria en recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/utils/production.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `modulos/01_produccion.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas / Recursos por unidad |
| Descripcion | El formulario de receta presenta tres bloques independientes para materiales, mano de obra y maquinaria. Materiales conserva la unidad base de Almacenes; mano de obra usa horas-persona y maquinaria horas-maquina. La UI convierte los tiempos a minutos al construir el payload para mantener compatibilidad con validacion, disponibilidad y costo existentes. |
| Motivo | Evitar mezclar recursos con semanticas distintas y hacer explicita la magnitud que el usuario debe capturar. |
| Impacto | Mejora el editor responsive ES/EN sin modificar persistencia ni contratos. Solo ofrece materiales elegibles, puestos productivos activos y maquinaria activa; recetas y ordenes existentes conservan sus cantidades internas en minutos. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/inventory/items?use_in_recipe=true&status=active` (`inventory-service`, `inventory.item.read`), `GET /v1/inventory/balances?limit=200` (`inventory-service`, `inventory.balance.read`), `GET /v1/hr/areas` (`hr-service`, `hr.area.read`), `GET /v1/hr/positions?production_only=true` (`hr-service`, `hr.position.read`) y `GET /v1/production/machines` (`production-service`, `production.machine.read`); request y response permanecen sin cambios. **APIs no tocadas:** Admin, Ventas y todos los comandos de escritura de Produccion, Inventory y HR. |
| Validacion | Sintaxis JavaScript, `validate-production-cycle.js`, `npm.cmd run validate:responsive` y `npm.cmd run verify`. |
| Observaciones | Cambio `local-write` de codigo y documentacion. No hubo migraciones, seeds, escrituras de datos, conexiones QA/Produccion ni despliegues. |

### CHG-175

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Vincula maquinaria con areas activas de RH |
| Autor | Codex |
| Archivos | `frontend/api/hr.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `modulos/01_produccion.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Maquinaria y Recursos Humanos / Areas y puestos |
| Descripcion | El formulario de Maquinaria reemplaza el texto libre de area por un selector alimentado con areas activas de RH. Si no existen opciones, bloquea el guardado, explica la dependencia y permite navegar al catalogo propietario para registrar el area primero. |
| Motivo | Evitar nombres inventados, duplicados o divergentes y mantener a RH como unica fuente de verdad de las areas organizacionales. |
| Impacto | Produccion consume el catalogo RH sin escribirlo. El payload de Maquinaria conserva `area_name` como snapshot compatible; una maquina ligada a un area inactiva debe reasignarse a un area activa al editarla. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/hr/areas` (`hr-service`, `hr.area.read`, request/response sin cambios); `POST /v1/production/machines` (`production-service`, `production.machine.create`) y `PATCH /v1/production/machines/{machine_id}` (`production-service`, `production.machine.update`) conservan su contrato y reciben `area_name` desde la seleccion RH. **APIs no tocadas:** Admin, Inventory, Ventas, contratos OpenAPI y comandos de escritura de RH. |
| Validacion | Sintaxis JavaScript, guardrail que rechaza area libre, paridad i18n, responsive y `npm.cmd run verify`. |
| Observaciones | Operacion `local-write` de codigo y documentacion. No hubo migraciones, seeds, escrituras de datos, conexiones QA/Produccion ni despliegues. |

### CHG-176

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Oculta IDs tecnicos en el buscador de productos de Recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `modulos/01_produccion.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas / Buscador de producto o servicio y selector compartido de Ventas |
| Descripcion | El valor seleccionado se presenta como `Nombre - codigo de producto`; los resultados muestran codigo, tipo y unidad. El ID `prs_*` permanece solo en atributos e inputs internos para resolver la relacion. |
| Motivo | Priorizar informacion reconocible para el usuario y evitar exponer identificadores de infraestructura en la interfaz operativa. |
| Impacto | Cambio exclusivamente visual y de busqueda: ahora tambien se busca por SKU. No cambia la identidad interna ni los payloads de Recetas o Ventas. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/production/product-services?limit=200` (`production-service`, `production.product_service.read`); request y response permanecen sin cambios. **APIs no tocadas:** Admin, Inventory, HR, Ventas backend y todos los comandos de escritura. |
| Validacion | Sintaxis JavaScript, guardrail que impide mostrar IDs internos en el resultado de Recetas y `npm.cmd run verify`. |
| Observaciones | Cambio `local-write` de codigo y documentacion. No hubo migraciones, seeds, escrituras de datos, conexiones QA/Produccion ni despliegues. |

### CHG-177

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Permite precision por minutos en tiempos de receta |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/styles.css`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `modulos/01_produccion.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas / Mano de obra y Maquinaria |
| Descripcion | Los inputs de horas-persona y horas-maquina dejan de exigir incrementos de `0.25` horas y aceptan cualquier decimal. La UI muestra la equivalencia `0.5 h = 30 min`; al guardar conserva la conversion decimal por 60 al contrato interno en minutos. |
| Motivo | Permitir tiempos operativos con precision menor a 15 minutos sin que la validacion nativa del navegador rechace valores intermedios. |
| Impacto | Cambio de captura y ayuda visual ES/EN. No modifica cantidades persistidas, calculo de costos ni compatibilidad de recetas existentes. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `POST /v1/production/recipes`, `PATCH /v1/production/recipe-versions/{version_id}` y `POST /v1/production/recipes/{recipe_id}/versions` (`production-service`; permisos `production.recipe.create` o `production.recipe.update` segun operación); request/response permanecen sin cambios y las cantidades temporales siguen enviandose en minutos. **APIs no tocadas:** Admin, Inventory, HR, Ventas y demas contratos de Produccion. |
| Validacion | Sintaxis JavaScript, paridad i18n, guardrail de precision temporal, responsive y `npm.cmd run verify`. |
| Observaciones | Cambio `local-write` de codigo y documentacion. No hubo migraciones, seeds, escrituras de datos, conexiones QA/Produccion ni despliegues. |

### CHG-178

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-05 |
| Cambio | Oculta IDs tecnicos en la visualizacion de Recetas |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/index.html`, `tools/validators/validate-production-cycle.js`, `modulos/01_produccion.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas guardadas, validacion, ordenes, mensajes y documento imprimible |
| Descripcion | La UI reemplaza títulos `rec_*` por `Nombre del producto - codigo`, acompañados de versión donde corresponde. Los IDs permanecen en `value`, `data-recipe-id`, snapshots y payloads internos. |
| Motivo | Evitar que identificadores técnicos dominen la experiencia operativa o confundan al usuario final. |
| Impacto | Cambio exclusivamente de presentación en listas, selectores, confirmaciones, notificaciones y orden imprimible. No modifica identidad, relaciones ni persistencia. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/production/recipes?limit=200` y `GET /v1/production/product-services?limit=200` (`production-service`; permisos `production.recipe.read` y `production.product_service.read`); request/response permanecen sin cambios. **APIs no tocadas:** Admin, Inventory, HR, Ventas y comandos de escritura de Produccion. |
| Validacion | Sintaxis JavaScript, paridad i18n, guardrail que impide IDs visibles en títulos de receta y `npm.cmd run verify`. |
| Observaciones | Cambio `local-write` de codigo y documentacion. No hubo migraciones, seeds, escrituras de datos, conexiones QA/Produccion ni despliegues. |

### CHG-179

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-06 |
| Cambio | Prepara el candidato e inventaria QA en modo lectura |
| Autor | Codex |
| Archivos | `docs/operaciones/preparacion_release_qa_20260806.md`, `TRAZABILIDAD.md` |
| Secciones | Release / QA / Fronteras de ambientes |
| Descripcion | Registra la validacion integral local, la cadena de migraciones, los servicios y revisiones desplegados, Hosting, Cloud SQL, backups y bloqueos previos a una liberacion controlada. |
| Motivo | Producir evidencia reproducible antes de solicitar autorizaciones independientes para migrar, desplegar servicios o publicar el frontend. |
| Impacto | Documental y operativo. Confirma que Inventory y RH aun no estan desplegados en QA y detecta configuracion local en el endpoint de version de Produccion. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consultados sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin y Produccion. **APIs no tocadas:** endpoints funcionales de Admin, Produccion, Inventory, HR y Ventas. |
| Validacion | `npm.cmd run session:context`, `git diff --check`, `npm.cmd run verify`, inventario GCP/Firebase sanitizado y healthchecks publicos no destructivos. |
| Observaciones | Operacion `local-write` para documentacion y `read-only` sobre QA. No hubo migraciones, seeds, cargas, despliegues, cambios de trafico, IAM, secretos ni datos. |

### CHG-180

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-07 |
| Cambio | Prepara pipeline seguro, identidades y servicios del candidato QA |
| Autor | Codex |
| Archivos | `.github/workflows/qa-candidate.yml`, `.github/workflows/qa-release.yml`, `.github/workflows/pages.yml`, `backend/Dockerfile`, `backend/.dockerignore`, `backend/shared/erclave_common/config.py`, `backend/shared/erclave_common/health.py`, mains y pruebas de servicios, `backend/scripts/smoke_qa.ps1`, `tools/build-qa-frontend.js`, `tools/validators/validate-qa-release-pipeline.js`, `firebase.qa.json`, `infra/qa/*`, documentacion y `package.json` |
| Secciones | Plataforma / QA / CI-CD / Inventory / RH / Administracion / Produccion |
| Descripcion | Agrega construccion inmutable por SHA y digest, promocion manual con aprobaciones separadas, revisiones sin trafico, smoke, frontend sanitizado, Firebase Hosting gobernado y plan de identidades dedicadas con Workload Identity Federation. El backend rechaza configuracion local en QA/Produccion y readiness usa la base efectiva de cada servicio. |
| Motivo | Cerrar los bloqueos de preparacion antes de solicitar autorizaciones para crear infraestructura, migrar o desplegar QA, evitando autodeploy, credenciales persistentes y configuracion localhost. |
| Impacto | El repositorio queda preparado para construir Admin, Produccion, Inventory y RH y promoverlos de forma controlada. No crea recursos cloud ni cambia el estado operativo de QA. GitHub Pages pasa de automatico a manual. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints tecnicos con contrato sin cambio:** `GET /health`, `GET /ready`, `GET /version`; readiness ahora evalua la URL efectiva de Inventory/RH y QA/Prod valida su configuracion al arranque. **APIs no tocadas:** endpoints funcionales de Admin, Produccion, Inventory, HR y Ventas. |
| Validacion | YAML parseable, pruebas de configuracion/CORS, build frontend QA sanitizado, validador de pipeline, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Operacion `local-write`. No hubo migraciones, seeds, escrituras de datos, creacion IAM, publicacion de imagenes, despliegues, cambios de trafico ni modificaciones en QA/Produccion. Docker no esta instalado en el host local; el build real de imagenes queda como gate de `qa-candidate.yml`. |

### CHG-181

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-08 |
| Cambio | Aprovisiona controles previos al candidato QA |
| Autor | Codex |
| Archivos | Estado externo de GCP/GitHub, `infra/qa/README.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / IAM / CI-CD / Cloud SQL |
| Descripcion | Crea Artifact Registry `erclave-qa`, seis cuentas dedicadas, WIF OIDC restringido al repositorio, bindings de minimo privilegio, cinco GitHub Environments con aprobador y variables QA. Crea un backup manual de Cloud SQL, exige cifrado y habilita PITR con siete dias de logs. |
| Motivo | Completar exclusivamente los pasos 1, 2 y 3 previos al despliegue QA autorizado por el propietario. |
| Impacto | El control plane de QA queda listo para construir el candidato y gobernar sus aprobaciones. No se publicaron imagenes, no se desplegaron Inventory/RH, no se modificaron revisiones ni trafico y no se publico Hosting. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** APIs administrativas de Google Cloud y GitHub para IAM, WIF, Artifact Registry, Environments, variables, backups y configuracion de Cloud SQL. **APIs no tocadas:** endpoints funcionales y tecnicos de Admin, Produccion, Inventory, HR y Ventas. |
| Validacion | WIF `ACTIVE` y limitado a `ChemaPsan/eslaclave-erclave`; seis cuentas presentes; Artifact Registry creado; cinco environments con `ChemaPsan`; 21 variables QA presentes; backup `1786227437185` exitoso; Cloud SQL `RUNNABLE`, `ENCRYPTED_ONLY`, PITR activo y siete dias de logs. |
| Observaciones | Operacion `qa-write` de infraestructura y configuracion. No hubo migraciones, seeds, cargas de datos, consultas SQL, builds, publicacion de imagenes, despliegues de servicios, cambios de trafico ni despliegue de frontend. |

### CHG-182

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-11 |
| Cambio | Elimina persistencia mock y entitlements sin backend del candidato QA |
| Autor | Codex |
| Archivos | `frontend/api/config.js`, `frontend/data/mockDb.js`, `.dockerignore`, `backend/Dockerfile`, `backend/scripts/configure_qa_tenant.py`, seeds y pruebas Admin, workflows QA, validador de pipeline, documentacion operativa y contexto |
| Secciones | Plataforma / QA / Frontend / Administracion / Produccion / Inventory / RH / CI-CD |
| Descripcion | Fuera de localhost, el frontend ignora overrides de modo, URLs, tenant y actor; en modo API conserva la proyeccion temporal solo en memoria y la reconstruye desde servicios reales. El pipeline empaca contratos y scripts estructurales, exige confirmacion adicional y reconcilia permisos y entitlements para habilitar exclusivamente Admin, Produccion, Inventory y RH, desactivando modulos sin microservicio real. |
| Motivo | Garantizar que la interfaz liberada a QA no muestre ni persista datos operativos de `localStorage` como si provinieran de Cloud SQL y que ningun entitlement exponga una funcionalidad mock. |
| Impacto | El candidato queda preparado para desplegar cuatro servicios reales y migrar/configurar QA de forma gobernada. Las preferencias visuales pueden seguir en `localStorage`, pero catalogos y transacciones del modo API no. La configuracion estructural no carga almacenes, articulos, movimientos, areas, puestos, recetas ni ordenes. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** endpoints vigentes de Admin, Produccion, Inventory y HR usados por el frontend en modo API; permisos y request/response permanecen sin cambios. **APIs no tocadas:** Ventas y modulos sin backend. |
| Validacion | `npm.cmd run validate:qa-release`, YAML parseable, build frontend QA sanitizado, pruebas dirigidas `11 passed`, `git diff --check` y `npm.cmd run verify` con `135 passed, 1 skipped`. |
| Observaciones | Operacion `local-write` y consultas `read-only` de inventario Cloud Run/Cloud SQL QA. No hubo migraciones, seeds, cargas de datos, builds Docker, publicacion de imagenes, despliegues, cambios de trafico, entitlements ni Hosting. |

### CHG-183

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Hace idempotente el bootstrap de servicios nuevos en QA |
| Autor | Codex |
| Archivos | `.github/workflows/qa-release.yml`, `tools/validators/validate-qa-release-pipeline.js`, `infra/qa/README.md`, `docs/arquitectura/qa_prod.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Cloud Run / CI-CD / Inventory / RH |
| Descripcion | El despliegue candidato detecta si cada servicio Cloud Run existe. Conserva `--no-traffic` para Admin, Produccion y cualquier servicio previamente creado; durante el bootstrap omite ese argumento porque Cloud Run exige trafico en la primera revision. Todos quedan etiquetados `candidate` y deben superar el smoke antes del siguiente gate. |
| Motivo | El primer intento CHG-182 desplego Admin con cero trafico, pero se detuvo al crear Inventory porque Cloud Run rechaza `--no-traffic` para servicios inexistentes. |
| Impacto | El retry puede completar Inventory y RH sin reconstruir imagenes ni alterar los digests aprobados. La excepcion de trafico se limita a servicios nuevos; `qa-traffic` y `qa-frontend` conservan aprobaciones independientes. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin, Produccion, Inventory y RH durante smoke; request/response y permisos permanecen sin cambios. **APIs no tocadas:** endpoints funcionales de todos los servicios. |
| Validacion | Validador QA ampliado para exigir deteccion de servicio, `--no-traffic` en revisiones existentes y excepcion bootstrap; YAML parseable, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Operacion inicial `local-write`. El intento previo fue `qa-write`: migro Cloud SQL a `head`, reconcilio permisos/entitlements y creo `admin-service-qa-00014-weg` con tag `candidate` y cero trafico; Inventory/RH no se crearon, Produccion no cambio y no hubo Hosting. |

### CHG-184

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Fija la fuente exacta del smoke en el job de servicios QA |
| Autor | Codex |
| Archivos | `.github/workflows/qa-release.yml`, `tools/validators/validate-qa-release-pipeline.js`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / CI-CD |
| Descripcion | `deploy_candidate` obtiene el repositorio en `inputs.release_sha` antes de ejecutar `backend/scripts/smoke_qa.ps1`. El validador delimita ese job y exige checkout, referencia inmutable y script de smoke dentro de la misma unidad de ejecucion. |
| Motivo | Los jobs de GitHub Actions no comparten filesystem; el checkout de `preflight` no deja disponible el script para `deploy_candidate`. |
| Impacto | El relanzamiento puede ejecutar los cuatro smokes con el script perteneciente al mismo commit cuyas imagenes por digest se promueven, sin reconstruir artefactos. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin, Produccion, Inventory y RH. **APIs no tocadas:** endpoints funcionales de todos los servicios. |
| Validacion | Validador QA dirigido, YAML parseable, `git diff --check` y `npm.cmd run verify` con `135 passed, 1 skipped`. |
| Observaciones | Operacion `local-write`. No hubo migraciones, seeds, cargas de datos, despliegues, cambios de trafico ni Hosting durante este ajuste. |

### CHG-185

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Corrige la resolucion de URLs candidatas en el smoke QA |
| Autor | Codex |
| Archivos | `backend/scripts/smoke_qa.ps1`, `tools/validators/validate-qa-release-pipeline.js`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Cloud Run / CI-CD |
| Descripcion | El smoke obtiene la descripcion JSON de cada servicio, valida la salida de `gcloud` y selecciona en PowerShell la entrada de trafico cuyo tag coincide con `candidate`, en lugar de depender de una proyeccion `value()` que devolvia vacio. |
| Motivo | El release corregido desplego las cuatro revisiones, pero el smoke no encontro la URL de Admin aunque Cloud Run si la exponia dentro de `status.traffic`. |
| Impacto | Los checks de health, readiness, version y URL publica pueden ejecutarse contra la revision etiquetada exacta. El gate sigue bloqueando `qa-traffic` si cualquier servicio incumple. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin, Produccion, Inventory y RH. **APIs no tocadas:** endpoints funcionales de todos los servicios. |
| Validacion | Resolucion de tags protegida por el validador QA, sintaxis PowerShell, smoke `read-only` de los cuatro candidatos con health/readiness/Cloud SQL/SHA aprobados, YAML parseable, `git diff --check` y `npm.cmd run verify` con `135 passed, 1 skipped`. |
| Observaciones | Operacion `local-write` y consultas `read-only` de Cloud Run. El intento previo fue `qa-write`: creo candidatos Admin/Produccion con cero trafico y realizo el bootstrap Inventory/RH con trafico inicial obligatorio; no hubo promocion `qa-traffic` ni Hosting. |

### CHG-186

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Separa el SHA del workflow del SHA del artefacto candidato |
| Autor | Codex |
| Archivos | `.github/workflows/qa-release.yml`, `tools/validators/validate-qa-release-pipeline.js`, `infra/qa/README.md`, `docs/arquitectura/qa_prod.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / CI-CD |
| Descripcion | `deploy_candidate` obtiene el smoke desde `github.sha`, que identifica inmutablemente la revision del workflow despachado. Los contenedores, la version esperada y el manifest siguen ligados a `inputs.release_sha` y a sus digests aprobados. |
| Motivo | Usar `inputs.release_sha` para el checkout tambien fijaba una version anterior de la automatizacion y evitaba que una correccion del smoke validara el mismo candidato ya construido. |
| Impacto | Las correcciones al pipeline pueden revalidar artefactos inmutables sin reconstruirlos ni alterar su identidad. El smoke continua exigiendo que `/version` coincida con el SHA candidato. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de Admin, Produccion, Inventory y RH. **APIs no tocadas:** endpoints funcionales de todos los servicios. |
| Validacion | Guardrail del job actualizado a `github.sha`, YAML parseable, smoke `read-only` de los cuatro candidatos, `git diff --check` y `npm.cmd run verify` con `135 passed, 1 skipped`. |
| Observaciones | Operacion `local-write`. No hubo migraciones, seeds, cargas de datos, despliegues, cambios de trafico ni Hosting durante este ajuste. |

### CHG-187

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Hace atomico el preflight de promocion de trafico QA |
| Autor | Codex |
| Archivos | `backend/scripts/promote_qa_traffic.ps1`, `.github/workflows/qa-release.yml`, `tools/validators/validate-qa-release-pipeline.js`, `infra/qa/README.md`, `docs/arquitectura/qa_prod.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Cloud Run / CI-CD |
| Descripcion | El job `qa-traffic` obtiene su script desde `github.sha`, describe los cuatro servicios en JSON, exige exactamente un tag `candidate` por servicio y completa la lista antes de modificar routing. Luego mueve cada servicio y verifica 100% en la revision certificada. |
| Motivo | La proyeccion `gcloud value(status.traffic[?tag=candidate].revisionName)` devolvia vacio y abortaba antes del primer cambio aunque los tags existian. |
| Impacto | Una resolucion incompleta ya no puede iniciar una promocion parcial. Los cambios de routing siguen bajo aprobacion `qa-traffic`; `qa-frontend` permanece independiente. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** APIs administrativas de Cloud Run para describir servicios y actualizar trafico. **APIs no tocadas:** endpoints tecnicos y funcionales de Admin, Produccion, Inventory y RH. |
| Validacion | Sintaxis PowerShell, guardrail de preflight/promocion/verificacion, YAML parseable, estado QA previo sin cambios parciales, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Operacion inicial `local-write` y consultas `read-only` de Cloud Run. El intento anterior de `qa-traffic` fallo antes de cambiar servicios; las cuatro revisiones estables conservaron 100% y `qa-frontend` fue omitido. |

### CHG-188

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Promueve y verifica el trafico backend CHG-182 en QA |
| Autor | Codex |
| Archivos | Estado externo de GitHub Actions y Cloud Run, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Cloud Run / Admin / Produccion / Inventory / RH |
| Descripcion | La ejecucion `31647661435` revalido los digests CHG-182, repitio Alembic/configuracion estructural de forma idempotente, desplego candidatos a cero trafico, aprobo los cuatro smoke tests y promovio las revisiones certificadas al 100%. |
| Motivo | Completar la autorizacion `qa-traffic` despues de corregir la resolucion del tag `candidate` y proteger el preflight de los cuatro servicios. |
| Impacto | QA sirve Admin `00017-dih`, Inventory `00003-zus`, RH `00003-gor` y Produccion `00008-vuv`, todos con version `4e9c6881dab61239f1abd5fff688019fdd697977`. Inventory/RH usan Cloud SQL real y no contienen carga funcional o dummy. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de los cuatro servicios; APIs administrativas de Cloud Run para routing. **APIs no tocadas:** contratos funcionales de Admin, Produccion, Inventory y RH. |
| Validacion | Jobs `preflight`, `migrate`, `deploy_candidate` y `promote_traffic` exitosos; comprobacion independiente de 100% por revision, ambiente `qa`, readiness, Cloud SQL configurado y SHA candidato en las cuatro URLs estables. |
| Observaciones | Operacion `qa-write` limitada a migracion/configuracion idempotente, revisiones Cloud Run y routing. Tenant estructural `ten_739ee59d765d5e14818674800d`. No hubo datos funcionales, fixtures, seeds demo, Produccion real ni Firebase Hosting; `qa-frontend` permanece pendiente. Rollback: Admin `00013-xmz`, Inventory `00001-jum`, RH `00001-vin` y Produccion `00005-bmp`. |

### CHG-189

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Habilita el despliegue gobernado de Firebase Hosting QA |
| Autor | Codex |
| Archivos | `infra/qa/identity-plan.json`, `infra/qa/README.md`, `tools/validators/validate-qa-release-pipeline.js`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md`; IAM del proyecto QA `erclave` |
| Secciones | Plataforma / QA / Firebase Hosting / IAM / CI-CD |
| Descripcion | Agrega `roles/firebasehosting.admin` a la identidad federada `erclave-github-deployer-qa` y hace que el validador rechace un plan de identidad que omita el permiso requerido por `qa-frontend`. |
| Motivo | El artefacto frontend CHG-182 se construyo y conservo, pero Firebase CLI fallo antes de publicar porque la identidad no podia resolver el proyecto ni administrar Hosting. |
| Impacto | El pipeline puede consultar el proyecto Firebase `erclave` y publicar Hosting solamente despues de la aprobacion protegida `qa-frontend`; no se amplian permisos sobre base de datos, tenants, servicios backend ni Produccion. |
| APIs afectadas | **Contratos modificados:** Ninguno. **APIs administrativas consumidas sin cambio:** Firebase Management y Firebase Hosting mediante Firebase CLI. **APIs no tocadas:** contratos funcionales de Admin, Produccion, Inventory y RH. |
| Validacion | Politica IAM leida con la cuenta propietaria y roles `roles/firebasehosting.admin` y `roles/run.admin` confirmados para la identidad; validador QA y `git diff --check` aprobados. |
| Observaciones | Operacion `qa-write` limitada a un binding IAM del proyecto `erclave`. No hubo migraciones, seeds, cargas de datos, trafico Cloud Run, cambios de tenant ni publicacion de Hosting. Rollback: retirar `roles/firebasehosting.admin` de la identidad desplegadora. |

### CHG-190

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Publica y verifica el frontend CHG-182 en Firebase Hosting QA |
| Autor | Codex |
| Archivos | Estado externo del run `31647661435`, Firebase Hosting `erclave`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Firebase Hosting / Admin / Produccion / Inventory / RH |
| Descripcion | Reintenta solamente el job fallido `qa-frontend`, reconstruye de forma determinista y conserva el artefacto del `release_sha` aprobado, autentica por WIF y publica el directorio sanitizado en `https://erclave.web.app`. |
| Motivo | Completar la promocion QA del candidato CHG-182 despues de corregir el permiso minimo de Firebase Hosting en CHG-189. |
| Impacto | El frontend QA consume las APIs reales de Admin, Produccion, Inventory y RH respaldadas por Cloud SQL QA; no contiene referencias a Local, Emulator ni al tenant sintetico. Ventas e Integraciones continúan fuera del conjunto de servicios reales activos. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /health`, `GET /ready` y `GET /version` de los cuatro servicios; Firebase Hosting para publicacion. **APIs no tocadas:** contratos funcionales de Admin, Produccion, Inventory y RH. |
| Validacion | Job `frontend` exitoso; dominio QA HTTP 200; recursos publicados sin `localhost`, `127.0.0.1`, `firebase-emulator` ni `demo-erclave`; cuatro URLs Cloud Run QA presentes; health, readiness y SHA `4e9c6881dab61239f1abd5fff688019fdd697977` confirmados en los cuatro servicios. |
| Observaciones | Operacion `qa-write` limitada a Firebase Hosting. No hubo migraciones, seeds, cargas de datos, cambios de tenant, revisiones o trafico Cloud Run ni recursos de Produccion. Rollback: restaurar el release anterior de Firebase Hosting. La validacion funcional autenticada permanece como siguiente gate. |

### CHG-191

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Prepara la allowlist gobernada del Backoffice QA |
| Autor | Codex |
| Archivos | `.github/workflows/qa-release.yml`, `.github/workflows/qa-admin-backoffice-config.yml`, `backend/scripts/configure_qa_backoffice.ps1`, `tools/validators/validate-qa-release-pipeline.js`, `infra/qa/README.md`, `docs/contexto/ESTADO_ACTUAL.md`, `docs/contexto/PENDIENTES.md`, `TRAZABILIDAD.md` |
| Secciones | Plataforma / QA / Admin / Backoffice / Autorizacion / CI-CD |
| Descripcion | Hace obligatoria la variable `QA_BACKOFFICE_ADMIN_EMAILS` en releases futuros y agrega un workflow manual que reutiliza la imagen Admin certificada, crea una revision sin trafico bajo `qa-services` y la promueve bajo `qa-traffic` solo despues de validar allowlist, imagen, version y ausencia de drift. |
| Motivo | La revision Admin activa no tenia `ERCLAVE_BACKOFFICE_ADMIN_EMAILS`; el seed concedia rol owner dentro del tenant demo, pero la allowlist interna vacia producia 403 en las rutas del Backoffice. |
| Impacto | Se conserva la separacion entre administracion interna SaaS y roles de clientes. La correccion no convierte owners de tenant en administradores globales ni requiere migraciones, seeds o reconstruccion de imagenes. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/backoffice/tenants`, `GET /health`, `GET /ready`, `GET /version`; APIs administrativas de Cloud Run. **APIs no tocadas:** contratos de tenant, permisos, Produccion, Inventory y RH. |
| Validacion | Diagnostico read-only de revision/env y logs 403; parser PowerShell, guardrails de workflow/configuracion, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Implementacion `local-write`; la variable externa, revision Cloud Run y trafico QA no se modificaron. Rollback previsto: restaurar 100% a `rollback_revision` registrado antes de promover. |

### CHG-192

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-12 |
| Cambio | Optimiza agentes y corrige paridad segura Local-QA |
| Autor | Codex |
| Archivos | `AGENTS.md`, `AGENTES.md`, `.agents/skills/`, `.github/workflows/validate.yml`, `backend/shared/erclave_common/config.py`, `backend/services/admin-service/tests/test_config.py`, `backend/services/admin-service/tests/test_admin_api.py`, `backend/scripts/seed_admin_qa_demo.py`, `frontend/api/config.js`, `frontend/api/admin.js`, `frontend/app.js`, `frontend/data/modules.js`, `tools/verify.js`, `tools/validators/`, `tools/traceability-draft.js`, `docs/`, `modulos/README.md`, `README.md`, `package.json`, `TRAZABILIDAD.md` |
| Secciones | Agentes / Skills / Local / QA / Seguridad / Backoffice / Frontend / Validadores / Operacion |
| Agentes consultados | Arquitecto SaaS; Arquitecto de datos; Custodio DB; Arquitecto API; Ingeniero de Seguridad/IAM/supply chain; QA/Release; Administracion; tecnicos de Produccion, Inventory y RH. Se realizaron auditorias independientes de agentes/skills, pipeline y paridad. |
| Descripcion | Crea `$erclave-qa-release` y el flujo canonico Local→QA, actualiza agentes y skills, elimina snapshots operativos duplicados, protege CI ante cambios de workflows QA y agrega `validate-local-qa-parity`. Corrige que Settings cargara un `.env` hibrido, bloquea URLs/bases/Firebase QA en Local, impide que `verify` herede una base remota y conserva en memoria el tenant seleccionado desde membresias en QA sin fallback demo. Retira correos Backoffice hardcodeados del seed y KPIs/reservas simuladas de superficies API. |
| Motivo | La memoria transversal estaba desactualizada tras CHG-182/191 y los validadores aprobaban contradicciones. Dos huecos P0 permitian un Local marcado como tal consumir QA y hacian que usuarios QA de tenants nuevos enviaran el tenant demo al solicitar `session/context`. |
| Impacto | El siguiente candidato alineara Local aislado y QA real sin sacrificar gates. No modifica contratos HTTP ni datos existentes. Un administrador Backoffice ya no se agrega implicitamente como owner en futuras ejecuciones del seed; membresias historicas no se eliminan. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** `GET /v1/session/tenants`, `GET /v1/session/context`, `GET /health`, `GET /ready`, `GET /version`; APIs administrativas de GitHub Actions, Cloud Run y Firebase Hosting documentadas. **APIs no tocadas:** requests/responses funcionales de Admin, Produccion, Inventory y RH. |
| Validacion | Auditorias independientes y forward-test de la nueva skill; pruebas nuevas de Settings Local; evaluacion dinamica de tenant QA; validadores de CI/seed/skills/paridad; `git diff --check`; `npm.cmd run verify`; smoke publico read-only de cuatro servicios y frontend QA vigente. |
| Observaciones | Cambios de repositorio `local-write`; no se desplego este candidato ni hubo nuevas migraciones, seeds, datos, IAM, revisiones, trafico o frontend QA. Deuda prioritaria: promocion multi-servicio compensatoria, frontend build-once, provenance fuerte, gates DB condicionales y smoke autenticado/post-Hosting. |

### CHG-193

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-17 |
| Cambio | Expedientes RH y responsables de Produccion |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260817_0014_hr_workers.py`, `backend/services/hr-service/`, `backend/services/production-service/`, `backend/shared/erclave_common/config.py`, `backend/scripts/start_local.ps1`, `backend/services/admin-service/app/seeds/permissions.py`, `contracts/api/`, `frontend/`, `.github/workflows/qa-release.yml`, `docs/`, `modulos/10_recursos_humanos.md`, `TRAZABILIDAD.md` |
| Secciones | RH / Trabajadores / Produccion / Ordenes / Responsables / Permisos / Datos / Local / QA |
| Agentes consultados | Negocio y tecnico de RH; negocio y tecnico de Produccion; Arquitectura SaaS/API/datos; Custodio DB; Seguridad; Diseno/i18n; QA/Release. |
| Descripcion | Agrega expedientes de trabajadores con un puesto vigente, identidad CURP/RFC/NSS, datos complementarios opcionales, aislamiento e idempotencia. Sustituye responsables libres de ordenes por IDs de trabajadores elegibles validados por HR y snapshots historicos. |
| Motivo | Impedir nombres arbitrarios y conectar la responsabilidad operativa con personas reales dadas de alta en RH. |
| Impacto | Cambio contractual incompatible para crear ordenes: `responsible_name` se sustituye por `responsible_worker_id` y cada etapa exige trabajador. Ordenes historicas conservan snapshots y referencias nulas compatibles. Datos personales se minimizan en listados visuales. |
| APIs afectadas | **Contratos modificados:** HR `GET/POST /v1/hr/workers` (`hr.worker.read/create`), `PATCH /v1/hr/workers/{id}` (`hr.worker.update`), `GET /v1/hr/workers/production-eligible` (`production.order.create`); Production `POST /v1/production/orders` (`production.order.create`) cambia request a IDs de trabajador y response agrega referencias externas. **Endpoints consumidos sin cambio:** `GET /v1/session/context`. **APIs no tocadas:** Inventory, Admin funcional, recetas, maquinaria y transiciones de orden/etapa. |
| Validacion | Validadores de sintaxis, i18n y OpenAPI; `36 passed`; migracion Local `20260805_0013 -> 20260817_0014`; smoke autenticado de permisos, alta de expediente y proyeccion elegible; `npm.cmd run verify`. |
| Observaciones | Solo `local-write`. Se aplicaron migracion y seeds idempotentes exclusivamente en `127.0.0.1:5434/erclave_local` y se creo un expediente sintetico `EMP-LOCAL-001`. No hubo QA/Produccion, despliegue ni escritura externa. |

### CHG-194

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-17 |
| Cambio | Catalogo transversal de unidades de medida |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260817_0015_units_of_measure.py`, `backend/services/admin-service/`, `backend/services/production-service/`, `backend/services/inventory-service/`, `contracts/api/admin-service.openapi.yaml`, `frontend/`, `docs/catalogos_base.md`, `modulos/01_produccion.md`, `modulos/08_administracion_configuracion.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion / Catalogos / Produccion / Inventarios / Ventas / Datos / Local |
| Agentes consultados | Administracion y Configuracion; tecnicos de Produccion e Inventarios; Arquitectura SaaS/API/datos; Custodio DB; Seguridad; Diseno/i18n; QA/Release. |
| Descripcion | Implementa un catalogo tenant-safe con 50 unidades predeterminadas basadas en UN/CEFACT Rec. 20, soporte ES/EN, unidades personalizadas, edicion, activacion/inactivacion y provision automatica. Configuracion base conserva solo la tarjeta-resumen y abre una vista dedicada para administrar sus registros. Sustituye capturas libres visibles por selectores y valida codigos activos en Produccion e Inventarios. |
| Motivo | Evitar variantes libres como pieza, pz o pza y establecer codigos estables para operacion, integraciones y reportes. |
| Impacto | Los campos existentes conservan su estructura string pero ahora almacenan codigos normalizados. La migracion transforma valores historicos comunes; movimientos de inventario deben coincidir con la unidad base del articulo hasta implementar conversiones. |
| APIs afectadas | **Contratos nuevos:** Admin `GET/POST /v1/catalogs/units-of-measure`, `GET /v1/catalogs/units-of-measure/{code}` y `PATCH /v1/catalogs/units-of-measure/{id}`. **Consumidores modificados:** altas/ediciones de productos, recetas, recursos, articulos y movimientos en Produccion e Inventory. **APIs no tocadas:** RH, Billing y transiciones documentales. |
| Validacion | Compilacion Python, sintaxis frontend, OpenAPI, pruebas unitarias/integracion, migracion y smoke Local, `npm.cmd run verify`. |
| Observaciones | Solo `local-write`; no se desplego ni escribio en QA/Produccion. Los defaults se crean para tenants existentes y futuros. Rollback: downgrade Alembic `20260817_0015 -> 20260817_0014`; los valores normalizados no regresan a sus alias libres. |

### CHG-195

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Saneamiento integral previo a Ventas |
| Autor | Codex |
| Archivos | `AGENTS.md`, `AGENTES.md`, `backend/pyproject.toml`, `backend/alembic/versions/20260817_0015_units_of_measure.py`, `backend/services/admin-service/`, `backend/services/production-service/app/api.py`, `backend/services/inventory-service/app/authorization.py`, `contracts/api/`, `contracts/microfrontend.md`, `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/microfrontends/`, `tools/validators/`, `docs/`, `modulos/08_administracion_configuracion.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion / Catalogos / Contratos / Microfrontends / i18n / Arquitectura / Agentes / Local |
| Agentes consultados | Negocio y tecnico de Administracion; tecnicos de Produccion, Inventory y RH; Arquitectura SaaS/API/datos; Custodio DB; Seguridad; Diseno/i18n; QA/Release. |
| Descripcion | Cierra la auditoria previa a Ventas: vuelve parseables y verificables los OpenAPI, documenta rutas reales y marca operaciones futuras como `planned`; normaliza manifiestos y permisos; completa ES/EN; elimina caracteres danados; actualiza estado, pendientes, decisiones, agentes y diagramas. Endurece Unidades de medida con idempotencia, correlacion, auditoria y migracion autosuficiente. |
| Motivo | El repositorio permitia YAML invalido, drift entre contrato y runtime, permisos de manifiesto obsoletos, textos nuevos sin i18n, diagramas de julio y comandos de catalogo sin garantias backend suficientes. |
| Impacto | No crea schema nuevo ni cambia los codigos UOM persistidos. La consulta por codigo se mueve a una ruta no ambigua; Produccion e Inventory actualizan su consumidor interno. Ventas queda explicitamente `planned` y no se presenta como servicio real antes de su corte vertical. |
| APIs afectadas | **Contratos modificados:** Admin `GET /v1/session/tenants` (`internal.session.tenant.read`), `GET /v1/backoffice/tenants` (`internal.backoffice.tenant.read`), `PATCH /v1/backoffice/tenants/{tenant_id}/status` (`internal.backoffice.tenant.manage`), `DELETE /v1/backoffice/tenants/{tenant_id}` (`internal.backoffice.tenant.delete`) se documentan sin cambiar runtime; `POST /v1/catalogs/units-of-measure` (`admin.unit.create`) y `PATCH /v1/catalogs/units-of-measure/{unit_id}` (`admin.unit.update`) formalizan correlacion/idempotencia y auditoria sin cambiar response; `GET /v1/catalogs/units-of-measure/by-code/{code}` (`admin.unit.read`) sustituye la ruta ambigua anterior. Production/Inventory solo actualizan ese endpoint Admin consumido. Operaciones contractuales aun no implementadas en Admin, Production e Inventory y los servicios Sales/Billing/Provisioning/Integration se marcan `planned`. **APIs no tocadas:** payloads operativos de HR, Production e Inventory. |
| Validacion | Integracion PostgreSQL real de replay/conflicto/auditoria con rollback (`2 passed`); `npm.cmd run verify` (`151 passed, 2 skipped`); OpenAPI YAML + paridad FastAPI; i18n/sintaxis/arquitectura; reinicio canonico y smoke autenticado Local de frontend, cuatro APIs, readiness, sesion y catalogo de 50 unidades. |
| Observaciones | Alcance `local-write` sobre el tenant autorizado `ten_739ee59d765d5e14818674800d`. El arranque reejecuto el seed local idempotente; las pruebas de integracion hicieron rollback. No hubo escrituras, migraciones, seeds ni despliegues en QA/Produccion. Rollback de codigo: revertir CHG-195; no se requiere downgrade porque no agrega revision y 0015 conserva el mismo schema/datos. |

### CHG-196

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Gobierno de modulos por tenant desde Backoffice |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260818_0016_tenant_module_preference.py`, `backend/services/admin-service/app/`, `backend/services/admin-service/tests/`, `contracts/api/admin-service.openapi.yaml`, `frontend/api/admin.js`, `frontend/api/backoffice.js`, `frontend/app.js`, `frontend/backoffice/`, `frontend/i18n/translations.js`, `AGENTES.md`, `docs/arquitectura/`, `docs/contexto/`, `modulos/08_administracion_configuracion.md`, `TRAZABILIDAD.md` |
| Secciones | Backoffice / Tenants / Entitlements / Autorizacion / Datos / Frontend / Local |
| Agentes consultados | Negocio y tecnico de Administracion; Arquitectura SaaS; Arquitectura de datos y persistencia; Custodio DB; Arquitectura API; Seguridad; Diseno/i18n; QA/Release. |
| Descripcion | Separa el entitlement contractual gobernado por Backoffice (`status`) de la preferencia operativa del administrador del tenant (`tenant_enabled`). Backoffice ahora lista el catalogo versionado, edita datos basicos del tenant y habilita, suspende o retira modulos implementados; `admin` es obligatorio y los modulos planeados permanecen bloqueados. El tenant solo enciende o apaga modulos concedidos. `session/context`, policy, permisos y navegacion usan `effective_active = status active AND tenant_enabled`. |
| Motivo | El unico `status` anterior permitia que un administrador del cliente modificara la misma decision comercial que Backoffice, sin distinguir contrato de preferencia local. |
| Impacto | La revision 0016 agrega `admin.tenant_modules.tenant_enabled` con backfill compatible `true` e indice efectivo. Retirar un entitlement no borra permisos ni datos. Al conceder un modulo, el owner recibe permisos tenant asignables; la autorizacion desaparece mientras cualquiera de los dos estados este apagado. El request tenant del PUT de entitlement cambia de `status/limits/source` a `enabled`; el response agrega `source`, `tenant_enabled` y `effective_active`. |
| APIs afectadas | **Contratos nuevos/modificados:** Admin `GET /v1/backoffice/modules` (`internal.backoffice.tenant.read`); `PATCH /v1/backoffice/tenants/{tenant_id}` (`internal.backoffice.tenant.manage`); `PUT /v1/backoffice/tenants/{tenant_id}/entitlements/{module_code}` (`internal.backoffice.entitlement.manage`); `PUT /v1/tenants/{tenant_id}/entitlements/{module_code}` (`admin.entitlement.manage`) ahora solo acepta `{enabled}`; `GET /v1/backoffice/tenants` y `GET /v1/tenants/{tenant_id}/entitlements` amplian response con el estado contractual y efectivo. **Endpoints consumidos sin cambio:** `GET /v1/session/context`, cuya forma externa conserva `active_modules` pero cambia el calculo efectivo. **APIs no tocadas:** HR, Production, Inventory, Sales, Billing, Provisioning e Integration. |
| Validacion | Compilacion Python; sintaxis JS; OpenAPI YAML y paridad FastAPI; `66 passed` de Admin API; `4 passed` de seeds; ciclo Alembic Local upgrade/downgrade/upgrade `0015 <-> 0016`; integracion PostgreSQL real con aislamiento, replay, conflicto, policy y auditoria (`3 passed`, rollback); smoke autenticado Local de catalogo (8 modulos: 4 implementados/4 planeados) y tenant permitido; `npm.cmd run verify` (`157 passed, 3 skipped`). |
| Observaciones | Alcance exclusivo `local-write`: PostgreSQL `127.0.0.1:5434/erclave_local`, Firebase Emulator `127.0.0.1:9099` y tenant permitido `ten_739ee59d765d5e14818674800d`. No hubo escrituras, migraciones, seeds ni despliegues en QA/Produccion. Rollback: downgrade Alembic `20260818_0016 -> 20260817_0015`; todos los registros previos recuperan el comportamiento compatible `tenant_enabled=true`. |

### CHG-197

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Recursos autoritativos, reservas, capacidad y costo real |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260818_0017_authoritative_resources.py`, `backend/services/production-service/`, `backend/services/inventory-service/`, `backend/services/hr-service/`, `backend/shared/erclave_common/config.py`, `.github/workflows/qa-release.yml`, `contracts/api/`, `frontend/`, `tools/validators/`, `AGENTES.md`, `docs/`, `modulos/`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Inventarios / RH / Recursos / Reservas / Capacidad / Valuacion / Concurrencia / Integridad / Frontend / Documentacion |
| Agentes consultados | Negocio y tecnico de Produccion, Almacenes e Inventarios y RH; Sinergia modular; Arquitectura SaaS; Arquitectura de datos y persistencia; Custodio DB; Arquitectura API; Seguridad; Diseno/i18n; QA/Release. La revision complementaria posterior de Administracion y Costos se registra, sin atribuirla retroactivamente al corte original, en CHG-198. Las skills `$erclave-feature`, `$erclave-db-migration` y `$erclave-environment-boundaries` indicadas por el repositorio no estaban disponibles en la sesion; se siguieron directamente sus guardrails documentados, sin QA ni despliegue. |
| Descripcion | Elimina `observed_resources` y vuelve autoritativas las consultas de materiales/valuacion en Inventory, capacidad laboral basada en trabajadores activos en RH y maquinaria/capacidad comprometida en Production. Liberar una orden crea reservas por almacen y compromisos por fecha; cancelar libera y cerrar consume movimientos inmutables, exige cantidades reales temporales y calcula el costo real. Revalida referencias/unidades al editar y aprobar recetas, bloquea unidades maestras con historia y agrega controles concurrentes e idempotentes. Limpia datos mock especificos de industria y bloquea Ventas planeado como modulo funcional. |
| Motivo | Cerrar los huecos donde el navegador podia declarar disponibilidad/costo, dos ordenes podian sobreasignar stock o capacidad, el costo real podia copiar el planeado y referencias/unidades podian quedar huerfanas o mutar sin proteccion. |
| Impacto | Cambio incompatible en validacion/alta de orden: ya no se acepta `observed_resources`; el request agrega `planned_for`. Las ordenes exponen recursos planeados/reales y referencias de reserva. Inventory incorpora reservas, disponible neto, costo promedio e importe; RH expone capacidad productiva; Maquinaria exige area HR estable. La revision 0017 agrega tablas/indices/restricciones sin FK entre dominios propietarios. QA conserva el corte anterior hasta una promocion gobernada. |
| APIs afectadas | **HR:** nuevo `GET /v1/hr/production-capacity` (`production.order.validate` o `production.order.create`), request por fecha/puestos y response con capacidad, costo por hora/minuto y trabajadores activos. **Inventory:** nuevos `POST /v1/inventory/availability-checks` (`production.order.validate` o `production.order.create`), `POST /v1/inventory/reservation-requests` (`production.order.create`), `POST /v1/inventory/reservations/{id}/release` y `/consume` (`production.order.status.update`); requests identifican fuente/orden, articulo, unidad, cantidad y almacenes, y responses exponen asignaciones, estados, costo snapshot y movimiento de consumo. `GET /v1/inventory/balances` (`inventory.balance.read`) agrega reservado, disponible, costo promedio e importe; alta/edicion/lectura de articulos (`inventory.item.create/update/read`) agrega `default_unit_cost`. **Production:** `POST /v1/production/resource-validations` (`production.order.validate`) elimina `observed_resources`, recibe `planned_for` y responde observaciones autoritativas; `POST /v1/production/orders` (`production.order.create`) usa responsables por ID, fecha planeada y devuelve snapshots/recursos/reservas; `PATCH /v1/production/orders/{id}/status` (`production.order.status.update`) ya no acepta costo real y orquesta liberacion/consumo; nuevo `PATCH /v1/production/orders/{id}/resources/{resource_id}` (`production.order.update`) registra cantidades reales; recetas/aprobacion (`production.recipe.create/update/approve`) exigen referencias autoritativas y maquinaria (`production.machine.create/update`) exige `area_ref_id`. **Consumidos sin cambio estructural:** Admin UOM y `session/context`, HR trabajadores elegibles/areas e Inventory articulos. **No tocadas:** APIs funcionales de Ventas, Compras, Costos, Contabilidad, Billing, Provisioning e Integraciones. |
| Validacion | Compilacion Python; sintaxis JS; YAML y paridad OpenAPI/FastAPI; pruebas unitarias de Production, Inventory y RH; validadores de arquitectura, datos, ambientes, agentes, i18n y trazabilidad; `npm.cmd run verify` (`161 passed, 3 skipped`); upgrade Alembic Local `20260818_0016 -> 20260818_0017` y confirmacion de `head`. |
| Observaciones | Alcance exclusivo `local-write`. La revision 0017 se aplico solo a `127.0.0.1:5434/erclave_local`; no se cargo ni modifico dato funcional. No hubo QA/Produccion, despliegues ni escrituras externas. Pendientes deliberados: producto terminado/merma, lotes/series y calendarios/turnos/ausencias/mantenimiento multi-dia. |

### CHG-198

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Sincronizacion documental posterior al corte autoritativo |
| Autor | Codex |
| Archivos | `AGENTES.md`, `TRAZABILIDAD.md`, `modulos/README.md`, `modulos/01_produccion.md`, `modulos/02_almacenes_inventarios.md`, `modulos/10_recursos_humanos.md`, `docs/arquitectura/ownership_datos_mvp.md`, `docs/arquitectura/modelo_datos_mvp.md`, `docs/arquitectura/diagramas/`, `docs/contexto/ESTADO_ACTUAL.md`, `tools/validators/validate-agents.js` |
| Secciones | Agentes / Produccion / Inventarios / RH / Costos / Administracion / Ownership / Datos / Diagramas / Estado por ambiente / Validadores |
| Agentes consultados | Revision complementaria de negocio y tecnica de Produccion, Almacenes e Inventarios, RH, Costos y Administracion; Sinergia modular; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n; QA/Release. |
| Descripcion | Elimina contradicciones que aun presentaban reservas, consumo, valuacion, capacidad y backend de Produccion como futuros; separa con precision el corte implementado en Local del desplegado en QA; corrige la cabeza Alembic de diagramas; mantiene Ventas como `planned/mock`; actualiza ownership y el caracter vivo del modelo de datos. Amplia el detalle contractual historico de CHG-197 y agrega guardrails semanticos contra regresiones documentales. |
| Motivo | Los validadores estructurales aprobaban aunque fichas de modulos, diagramas y ownership conservaran frases del corte anterior, lo que podia inducir a agentes y usuarios a decisiones incorrectas. |
| Impacto | Solo documentacion y validadores. No cambia runtime, contratos OpenAPI, persistencia, datos, permisos, frontend ni estado de ambientes. La historia QA se conserva; las capacidades 0017 siguen siendo exclusivas de Local. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** Ninguno. **APIs no tocadas:** todas las APIs de Admin, Production, Inventory, HR, Sales, Billing, Provisioning e Integration. |
| Validacion | `npm.cmd run validate:agents`, validacion de trazabilidad, busqueda semantica de frases obsoletas, enlaces Markdown locales y `npm.cmd run verify`. |
| Observaciones | Revision de solo documentacion y validadores en el workspace Local. No hubo migraciones, seeds, datos funcionales, QA, Produccion, despliegues ni escrituras externas. |

### CHG-199

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Gobierno y validacion automatica de documentacion viva |
| Autor | Codex |
| Archivos | `docs/arquitectura/gobierno_documentacion_viva.md`, `tools/validators/validate-documentation-freshness.js`, `tools/validators/validate-all.js`, `tools/validators/validate-session-context.js`, `package.json`, `AGENTS.md`, `AGENTES.md`, `docs/contexto/INICIO_SESION.md`, `docs/contexto/DECISIONES.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Gobierno documental / Agentes / Estado / Migraciones / Modulos / Enlaces / Automatizacion / Trazabilidad |
| Agentes consultados | Todos los agentes quedan sujetos a la matriz de documentacion viva. Para este corte aplicaron Arquitectura SaaS, Arquitectura de datos, Custodio DB, Arquitectura API, Seguridad, QA/Release, Sinergia modular y responsables tecnicos de todos los modulos como custodios de sus fuentes; no cambio una regla funcional de negocio. |
| Descripcion | Define fuentes vivas, evidencia historica y objetivos futuros; asigna fuente de verdad y responsabilidad por agente; establece una matriz obligatoria por tipo de cambio. Agrega `npm.cmd run validate:documentation` al `verify` para derivar y comparar cabezas Alembic Local/QA, ultimo CHG, campos de trazabilidad, indice de modulos, enlaces Markdown y presencia del gobierno en instrucciones de agentes y sesion. |
| Motivo | Evitar que codigo, contratos, migraciones, diagramas, fichas, agentes y memoria operativa vuelvan a divergir aunque los validadores funcionales permanezcan verdes. |
| Impacto | Solo proceso, documentacion y validadores. Todo cambio futuro debe actualizar las fuentes afectadas en el mismo corte o fallara la validacion objetiva correspondiente. No cambia runtime, UI, contratos OpenAPI, datos, permisos ni ambientes. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Endpoints consumidos sin cambio:** Ninguno. **APIs no tocadas:** todas las APIs de Admin, Production, Inventory, HR, Sales, Billing, Provisioning e Integration. |
| Validacion | `npm.cmd run validate:documentation`, `npm.cmd run validate:session-context`, `npm.cmd run validate:agents`, `npm.cmd run validate:traceability`, enlaces Markdown locales, `git diff --check` y `npm.cmd run verify`. |
| Observaciones | Alcance exclusivo del workspace Local. No hubo migraciones, seeds, datos funcionales, QA, Produccion, despliegues ni escrituras externas. La automatizacion complementa, pero no sustituye, la revision semantica de negocio y tecnica. |

### CHG-200

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Primer corte real de Ventas: Clientes y Cotizaciones |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260818_0018_sales_customers_quotes.py`, `backend/services/sales-service/`, `backend/services/hr-service/`, `backend/services/production-service/`, `backend/services/admin-service/`, `backend/shared/erclave_common/`, `contracts/api/`, `frontend/`, `tools/validators/`, `AGENTES.md`, `docs/`, `modulos/`, `TRAZABILIDAD.md` |
| Secciones | Ventas / Clientes / Contactos / Cotizaciones / Referencias autoritativas / Calculo / Estados / Permisos / Frontend / Agentes / Documentacion / Pruebas |
| Agentes consultados | Especialista comercial y Especialista tecnico de ventas; RH por responsables y minimizacion de datos; Produccion por productos/servicios y costo estandar; Administracion por unidades; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n; QA/Release y Sinergia modular. Las skills de repositorio no estaban disponibles en esta sesion; se aplicaron directamente sus guardrails documentados y no se toco QA/Produccion. |
| Descripcion | Materializa `sales-service` y el schema `sales` para Clientes/Cotizaciones. Clientes exige responsable RH activo y contacto principal; el perfil fiscal permanece opcional pero completo al iniciarse. Cotizaciones exige cliente activo, productos/servicios activos y unidad base activa, calcula subtotal/descuento/total/costo snapshot/margen estimado en backend y controla transiciones. La UI consume API y deja pedidos/entregas como planeados sin escritura mock. |
| Motivo | Sustituir la maqueta comercial por un corte vertical verificable, evitando responsables, clientes, productos, unidades, totales o estados declarados libremente por el navegador. |
| Impacto | Sales cambia de `planned` a implementado solo para Clientes/Cotizaciones en Local. La revision 0018 crea tablas tenant-safe, indices, checks, idempotencia y auditoria sin FK cruzadas. RH agrega una proyeccion minima de trabajadores elegibles; Production y Admin permiten validacion de lectura con permisos Sales. Pedidos, reservas, entregas, devoluciones y facturacion siguen fuera de alcance. QA permanece inactivo y en `20260805_0013`. |
| APIs afectadas | **Sales nuevas:** `GET /v1/sales/reference-data`, CRUD acotado de `/customers` y `/quotes`, mas `/quotes/{id}/submit`, `/approve`, `/expire`, `/cancel`. **HR:** `GET /v1/hr/workers/sales-eligible` con proyeccion sin expediente sensible. **Production consumida:** lectura de `/v1/production/product-services` acepta permisos de cotizacion. **Admin consumida:** unidades activas aceptan permisos de cotizacion. **No implementadas:** pedido, fulfillment, entrega, devolucion, reserva comercial y facturacion. |
| Validacion | `validate:sales-cycle`, paridad OpenAPI/FastAPI, sintaxis JS/Python, pruebas Sales, suite backend completa, validadores de agentes/documentacion/trazabilidad y `npm.cmd run verify` (`166 passed, 4 skipped`). Integracion PostgreSQL real `1 passed` con tenant efimero y limpieza; smoke Firebase Local confirmo Sales activo, health, 3 monedas, 6 condiciones, clientes y autoridades RH/Produccion/Admin. |
| Observaciones | Alcance `local-write`. La revision 0018 se aplico exclusivamente a `127.0.0.1:5434/erclave_local`; el seed Local sincronizo catalogo, permisos y entitlement demo, y `sales-service` quedo escuchando en `127.0.0.1:8008`. La prueba de persistencia elimino sus datos efimeros. No se desplego, migro, activo ni escribio QA/Produccion. |

### CHG-201

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Auditoria y cierre de sinergia modular de Ventas |
| Autor | Codex |
| Archivos | `backend/scripts/start_local.ps1`, `backend/services/admin-service/`, `backend/services/sales-service/`, `contracts/api/admin-service.openapi.yaml`, `contracts/api/sales-service.openapi.yaml`, `frontend/api/sales.js`, `frontend/app.js`, `frontend/backoffice/app.js`, `frontend/i18n/translations.js`, `tools/validators/validate-sales-cycle.js`, `tools/validators/validate-agents.js`, `AGENTES.md`, `docs/contexto/`, `frontend/backoffice/README.md`, `modulos/04_ventas_clientes.md`, `modulos/08_administracion_configuracion.md`, `TRAZABILIDAD.md` |
| Secciones | Ventas / Administracion / Backoffice / Onboarding / Entitlements / Dependencias / Permisos / Lectura parcial / Idempotencia / Pruebas / Documentacion |
| Agentes consultados | Especialista comercial y tecnico de Ventas; negocio y tecnico de Administracion; Sinergia modular; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n y QA/Release. Se revisaron sus reglas versionadas en `AGENTES.md`; no se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Audita el primer corte de Ventas y corrige sus fronteras. El catalogo declara `sales -> hr, production`; Backoffice y Administracion impiden activar Ventas sin autoridades efectivas o apagar una dependencia en uso, con validacion bajo bloqueo de todas las filas modulares del tenant. Onboarding agrega dependencias seleccionadas y asigna permisos al owner despues de crear los entitlements. La UI carga documentos por permisos de lectura y catalogos de mutacion por separado, oculta acciones no autorizadas, agrega expiracion y conserva lectura ante fallas parciales. Backend amplia busqueda de clientes, valida promesa de entrega e implementa claim idempotente concurrente con `ON CONFLICT`. El arranque Local amplia la espera del emulador de 15 a 30 segundos para evitar falsos fallos en equipos donde Auth tarda mas en escuchar. |
| Motivo | La auditoria encontro que un tenant podia quedar con Ventas efectivo pero RH/Produccion apagados, el onboarding podia crear modulos antes de que el owner recibiera sus permisos, y un usuario lector perdia toda la pantalla por llamadas a catalogos de captura no autorizadas. Tambien faltaban expiracion en UI, busqueda por contacto y proteccion del primer claim idempotente concurrente. |
| Impacto | No agrega migracion ni cambia datos existentes. Fortalece los dos niveles de habilitacion y evita estados operativos rotos. Los lectores conservan visibilidad sin adquirir permisos de mutacion; las escrituras siguen revalidando autoridades. El tenant Local existente ya cumple las dependencias. Pedidos, entregas, reservas comerciales y facturacion permanecen planeados. |
| APIs afectadas | **Admin modificado:** `GET /v1/backoffice/modules` agrega `dependencies`; onboarding y ambos `PUT` de entitlement pueden responder `409 module_dependencies_required` o `module_dependency_in_use`. **Sales modificado:** `GET /v1/sales/reference-data` admite cualquiera de los permisos comerciales de lectura/edicion declarados; formas de response sin cambio. **Endpoints consumidos sin cambio:** lecturas reducidas de RH, Production y Admin UOM. **APIs no tocadas:** Inventory, Billing, Provisioning e Integration. |
| Validacion | Pruebas unitarias Sales `8 passed` y Admin API `69 passed`; `npm.cmd run verify` aprobo todos los validadores, OpenAPI, sintaxis, compilacion y `172 passed, 6 skipped`; integraciones PostgreSQL reales Sales `2 passed` y Admin `4 passed`, con concurrencia, aislamiento, dependencias, onboarding y limpieza/rollback. Reinicio canonico Local con cinco APIs saludables; smoke Firebase comprobo `dependencies=hr,production`, bloqueo `409` en ambos niveles, denegacion API `403` al apagar cada nivel y restauracion final efectiva de Sales/RH/Production. |
| Observaciones | Alcance exclusivo `local-write` sobre codigo y PostgreSQL `erclave_local`. Las pruebas efimeras limpiaron o revirtieron sus datos; el smoke conservo la auditoria/idempotencia Local de los apagados/restauraciones solicitados y dejo el estado funcional original restaurado. No se agrego revision Alembic. No hubo migracion, seed, despliegue ni escritura en QA/Produccion. Rollback de codigo: revertir CHG-201; la cabeza Local permanece `20260818_0018`. |

### CHG-202

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Segundo corte de Ventas y plantilla documental tenant-safe |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260818_0019_sales_orders_deliveries_catalogs.py`, `backend/services/admin-service/`, `backend/services/sales-service/`, `backend/services/inventory-service/`, `backend/services/production-service/`, `contracts/api/`, `frontend/`, `AGENTES.md`, `docs/`, `modulos/`, `TRAZABILIDAD.md` |
| Secciones | Ventas / Pedidos / Surtido / Reservas / Solicitudes de Produccion / Entregas / Costo real / Catalogos comerciales / Plantillas PDF / Permisos / UI / Pruebas / Documentacion |
| Agentes consultados | Reglas versionadas del especialista comercial y tecnico de Ventas; negocio/tecnico de Administracion, Produccion e Inventarios; Sinergia modular; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n y QA/Release. Las skills `$erclave-feature`, `$erclave-db-migration` y `$erclave-environment-boundaries` referidas por el repositorio no estaban disponibles; se aplicaron directamente sus guardrails documentados. |
| Descripcion | Convierte una cotizacion aprobada una sola vez en Pedido; configura cada partida como servicio, reserva de existencia o solicitud idempotente a Produccion; registra Entregas parciales/totales, consume parcialmente reservas y calcula costo/margen real. Admin incorpora catalogos tenant-safe de monedas/condiciones de pago y `document.template`; cotizaciones y ordenes de Produccion aplican el logo/colores al imprimir. La UI de Pedidos/Entregas deja el panel planeado y consume API real. |
| Motivo | Cerrar el siguiente tramo comercial sin aceptar maestros libres, sin confundir solicitudes de Produccion con ordenes liberadas y sin duplicar identidad visual en cada generador PDF. |
| Impacto | Revision 0019 Local crea catalogos comerciales, pedidos, partidas, referencias de reserva, entregas y solicitudes Production. Inventory acepta origen Sales y consumo parcial; Production valida y conserva solicitudes sin escritura cruzada. Los estados operativos siguen protegidos y no se convierten en catalogos editables. Logo data URL es solucion Local; object storage queda como gate previo a QA. |
| APIs afectadas | **Admin:** CRUD acotado `/v1/catalogs/commercial/{currencies|payment_terms}` y `GET/PUT /v1/document-template`. **Sales:** `GET/POST /orders`, `GET /orders/{id}`, `/fulfillment`, `/cancel`; `GET/POST /deliveries`, `GET /deliveries/{id}`, `/confirm`, `/cancel`. **Inventory:** reserva/liberacion/consumo aceptan permisos Sales y consumo opcional parcial. **Production:** `GET/POST /v1/production/order-requests`. **No tocadas:** Billing, Provisioning e Integration. |
| Validacion | `npm.cmd run verify` aprobo validadores, compilacion y `173 passed, 6 skipped`; integracion PostgreSQL Sales aprobo `11 passed` con pedido/entrega parcial/costo real; migracion Local `0018 -> 0019`; smoke Firebase autenticado confirmo frontend y cinco APIs en `200`, tres monedas, seis condiciones de pago, plantilla, Pedidos, Entregas y solicitudes Production. |
| Observaciones | Alcance exclusivo `local-write` sobre `127.0.0.1:5434/erclave_local`. APIs locales fueron reiniciadas y permanecen escuchando en 8000/8002/8004/8006/8008. No hubo despliegue, migracion, seed ni escritura en QA/Produccion. |

### CHG-203

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Auditoria integral del segundo corte de Ventas |
| Autor | Codex |
| Archivos | `docs/auditorias/ventas_segundo_corte_2026-08-18.md`, `AGENTES.md`, `modulos/04_ventas_clientes.md`, `modulos/README.md`, `backend/services/sales-service/README.md`, `docs/contexto/ESTADO_ACTUAL.md`, `DECISIONES.md`, `PENDIENTES.md`, `contracts/api/admin-service.openapi.yaml`, `tools/validators/validate-sales-cycle.js`, `TRAZABILIDAD.md` |
| Secciones | Veredicto / Bloqueadores QA / UI de Entregas / Orquestacion y concurrencia / Integridad producto-articulo / XSS / Costos / Resiliencia / Validaciones / Agentes / Pendientes |
| Agentes consultados | Especialista comercial y tecnico de Ventas; negocio/tecnico de Inventory, Production y Administracion; Sinergia modular; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n; QA/Release y gobierno de documentacion viva. |
| Descripcion | Se audito codigo, migraciones, contratos, permisos, frontend, pruebas, catalogos y plantilla documental del corte 0018/0019. Se confirmo el happy path backend, pero se corrigio la documentacion que lo presentaba como flujo integral cerrado y se registraron bloqueadores verificables antes de QA. |
| Motivo | Evitar que rutas existentes y pruebas felices oculten huecos de operacion real, seguridad o consistencia entre Sales, Inventory y Production. |
| Impacto | No cambia runtime ni base. La memoria vigente ahora distingue backend disponible de UI incompleta y prioriza: alta de Entregas, sanitizacion, saga/locks/reconciliacion, mapeo producto-articulo, costo por fuente, resiliencia y pruebas negativas/concurrentes. Los agentes incorporan esos guardrails. |
| APIs afectadas | Sin cambio de rutas ni payloads. Se alineo solamente metadata `x-permissions` del OpenAPI Admin con permisos alternativos ya aceptados por runtime para catalogos comerciales. |
| Validacion | Antes y despues de documentar, `npm.cmd run verify` aprobo `173 passed, 6 skipped`; Sales con PostgreSQL Local aprobo `11 passed`; sintaxis JS, `git diff --check` y paridad OpenAPI aprobaron. Prueba dirigida confirmo que nombre comercial/contacto/telefono aceptan espacios y que RFC con `Ñ` se rechaza, sustentando el hallazgo de validacion. |
| Observaciones | Auditoria y documentacion exclusivamente Local; sin migraciones, seeds, datos funcionales, despliegues ni escrituras en QA/Produccion. El detalle autoritativo del hallazgo esta en `docs/auditorias/ventas_segundo_corte_2026-08-18.md`. |

### CHG-204

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-18 |
| Cambio | Correccion integral del plan de auditoria CHG-203 |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260818_0020_sales_chg203_hardening.py`, `backend/services/sales-service/`, `backend/services/production-service/`, `backend/services/inventory-service/`, `contracts/api/`, `frontend/api/sales.js`, `frontend/app.js`, `tools/run_pytest.py`, `tools/validators/`, `AGENTES.md`, `docs/`, `modulos/`, `TRAZABILIDAD.md` |
| Secciones | Ventas / Entregas / Orquestacion durable / Concurrencia / Mapeo producto-articulo / Costos / Sanitizacion / Resiliencia / Contratos / Pruebas / Agentes / Documentacion |
| Agentes consultados | Reglas versionadas del especialista comercial y tecnico de Ventas; negocio/tecnico de Inventory, Production y Administracion; Sinergia modular; Arquitectura SaaS, datos y API; Custodio DB; Seguridad; Diseno/i18n, QA/Release y gobierno de documentacion viva. No se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Aplica el plan CHG-203. Production exige para cada producto un articulo activo de Inventory con la misma unidad y conserva el mapeo autoritativo. Sales revalida esa identidad, guarda snapshots y reclama durablemente surtido, cancelacion y confirmacion antes de efectos externos; claves derivadas estables permiten reanudar estados `needs_reconciliation`. Las Entregas bloquean Pedido/partidas y descuentan borradores concurrentes. El costo real queda trazado a `inventory_consumption` o `service_capture`; Production queda pendiente hasta reportar `production_report`. La UI habilita alta de Entregas, oculta campos ignorados, conserva lecturas parciales ante fallas de referencias y escapa contenido comercial. |
| Motivo | Cerrar los bloqueadores funcionales, de seguridad e integridad encontrados por CHG-203 sin promover un happy path incompleto como listo para QA. |
| Impacto | Revision Local `20260818_0020`; cambia schema Production/Sales, contratos, API, UI, pruebas y fuentes vivas. Corrige la evidencia RFC de CHG-203: el patron UTF-8 aceptaba `Ñ`; el fallo observado provenia del transporte de consola. Campos obligatorios con espacios si fueron corregidos y cubiertos. Paginacion, PDF de Pedido/Entrega, object storage, devoluciones/facturacion y callback Production permanecen explicitamente fuera del corte. |
| APIs afectadas | **Production:** ProductService agrega `inventory_item_id` y valida su autoridad; lecturas admiten permisos Sales necesarios. **Inventory:** lectura puntual de articulo admite validacion Production/Sales. **Sales:** mismos endpoints; respuestas de Pedido/Entrega agregan estados de orquestacion, snapshots de articulo y procedencia de costo; crear Entrega admite costo real de servicio. **No tocadas:** Billing, Provisioning e Integration. |
| Validacion | `npm.cmd run verify` aprobo validadores, compilacion y `177 passed, 8 skipped`. Unitarias Sales `12 passed`; Production `29 passed`; integracion PostgreSQL Sales `4 passed` con sobrecompromiso, claim exclusivo, replay terminado y carrera cancelacion-confirmacion; sintaxis JS, contratos OpenAPI y documentacion viva aprobados. |
| Observaciones | Alcance exclusivo `local-write`. Alembic `20260818_0020` fue aplicado solo a `127.0.0.1:5434/erclave_local`. No hubo despliegue, migracion, seed ni escritura en QA/Produccion. Reanudar el mismo payload conserva la clave durable original; la operacion visible puede quedar `needs_reconciliation` para recuperacion, nunca degradar a mock. |

### CHG-205

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Endurecimiento funcional y de seguridad de identidad PDF |
| Autor | Codex |
| Archivos | `backend/services/admin-service/app/schemas.py`, `backend/services/admin-service/tests/test_admin_api.py`, `contracts/api/admin-service.openapi.yaml`, `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `tools/validators/validate-production-cycle.js`, `tools/validators/validate-sales-cycle.js`, `docs/arquitectura/plantillas_documentales.md`, `docs/contexto/`, `modulos/08_administracion_configuracion.md`, `TRAZABILIDAD.md` |
| Secciones | Administracion / Identidad PDF / Ventas / Produccion / Seguridad / Archivos / Permisos / i18n / Responsive / Pruebas / Documentacion |
| Agentes consultados | Negocio y tecnico de Administracion; negocio/tecnico de Ventas y Produccion; Arquitectura SaaS, datos y API; Custodio DB; Seguridad transversal; Diseno/i18n; Responsive; QA/Release y gobierno de documentacion viva. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Completa el flujo Local de `document.template`: permite reemplazar y quitar logo, valida MIME/tamano en UI y Base64/firma/tamano decodificado en backend, corrige el checkbox, mueve todos los textos a ES/EN y oculta controles mutables sin permiso. Cotizaciones y Ordenes de Produccion reintentan cargar el registro API si falta en cache y muestran un error visible si no existe. La salida de Produccion escapa datos operativos interpolados en `innerHTML`. |
| Motivo | La revision funcional encontro deformacion visual, fallos silenciosos ante cache incompleta, ausencia de retiro de logo, textos no gobernados por i18n, validacion superficial del data URL y campos de Produccion sin escape consistente. |
| Impacto | Sin migracion ni cambio de modelo persistente. Endurece el payload vigente y la experiencia de Administracion; conserva la cache de presentacion respaldada por API. Pedido/Entrega y object storage siguen pendientes y fuera del corte. |
| APIs afectadas | **Contrato modificado:** Admin `PUT /v1/document-template`, permiso `admin.setting.update`; mismo request/response, pero `logo_data_url` documenta maximo, formatos, firma valida y `null` para eliminar. **Endpoints consumidos sin cambio:** Admin `GET /v1/document-template`, permisos alternativos de lectura vigentes; lecturas de Cotizaciones Sales y Ordenes Production ya cargadas por sus workspaces. **APIs no tocadas:** Inventory, HR, Billing, Provisioning e Integration. |
| Validacion | Pruebas focalizadas Admin, validadores i18n/responsive/sintaxis/OpenAPI y guardrails documentales/funcionales; `npm.cmd run verify` aprobo validadores, compilacion y 181 pruebas con 8 omitidas. |
| Observaciones | Alcance exclusivo de codigo `local-write`. No hubo migracion, seed, carga, despliegue ni escritura en QA/Produccion. Rollback: revertir CHG-205; `document.template` conserva compatibilidad de lectura y estructura. |

### CHG-206

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Vinculacion guiada de producto terminado |
| Autor | Codex |
| Archivos | `backend/services/production-service/`, `backend/services/sales-service/app/authorities.py`, `contracts/api/production-service.openapi.yaml`, `frontend/api/production.js`, `frontend/app.js`, `frontend/i18n/translations.js`, `modulos/`, `TRAZABILIDAD.md` |
| Agentes consultados | Especialistas de Almacenes, Produccion y Ventas. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se tocaron ambientes externos. |
| Descripcion | Agrega selector opcional de producto de Produccion al alta de un terminado, crea el articulo en Inventory y conserva en Produccion el vinculo 1:1 por IDs. Permite nombres comercial y logistico distintos, filtra candidatos sin mapa y valida tipo, estado y unidad. |
| Impacto | Sin migracion. Mantiene ownership por servicio y agrega recuperacion explicita ante alta parcial. Ventas endurece la validacion del articulo terminado al surtir. |
| APIs afectadas | **Production:** `GET /v1/production/product-services` agrega `inventory_mapping`; nuevo `PUT /v1/production/product-services/{id}/finished-good-link`. **Inventory:** consume sin cambio `POST /v1/inventory/items` y `GET /v1/inventory/items/{id}`. **Sales:** mismos endpoints; validacion de surtido mas estricta. |
| Validacion | Pruebas unitarias focalizadas Production/Sales, contrato OpenAPI, frontend y `npm.cmd run verify`. |
| Observaciones | Alcance exclusivo `local-write`; sin seed, migracion, despliegue ni escritura en QA/Produccion. |

### CHG-207

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Custodio y skill de manuales funcionales de solucion |
| Autor | Codex |
| Archivos | `AGENTES.md`, `.agents/skills/erclave-solution-manuals/`, `docs/manuales_solucion/`, `docs/contexto/ESTADO_ACTUAL.md`, `tools/validators/validate-agents.js`, `TRAZABILIDAD.md` |
| Agentes consultados | Gobierno de documentacion viva y especialistas modulares como fuentes obligatorias del nuevo custodio. Se uso `$skill-creator`; no se tocaron ambientes externos. |
| Descripcion | Crea un agente transversal y una skill para producir y mantener manuales de usuario por modulo, con fuente Markdown, salida DOCX, estructura funcional, registro de cobertura, consulta a agentes de negocio/tecnicos y control de alcance por ambiente. |
| Impacto | Documental y de tooling Local. No crea aun todos los manuales; establece el proceso reproducible para que crezcan con la solucion sin convertirse en bitacoras tecnicas. |
| APIs afectadas | Ninguna. |
| Validacion | Validacion estructural de skill, generacion y apertura de DOCX de prueba, validador de agentes y `npm.cmd run verify`. |
| Observaciones | Sin migracion, seed, despliegue ni escritura en QA/Produccion. Los DOCX distribuidos deben regenerarse desde sus fuentes Markdown. |

### CHG-208

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Fecha de Entrega y busqueda escalable de documentos comerciales |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/i18n/translations.js`, `frontend/index.html`, `tools/validators/validate-sales-cycle.js`, `modulos/04_ventas_clientes.md`, `docs/arquitectura/seleccion_escalable_documentos.md`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Agentes consultados | Negocio y tecnico de Ventas; criterios de UX/i18n, arquitectura API, QA y gobierno documental definidos en `AGENTES.md`. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se tocaron ambientes externos. |
| Descripcion | Corrige el campo fecha oculto por una condicion de modo mock. Sustituye selectores masivos de Cotizacion y Pedido por buscadores que filtran por folio, cliente, producto/servicio, importe o estado y limitan resultados a documentos elegibles. |
| Impacto | UI Local, textos ES/EN, guardrail automatizado y documentacion funcional. Sin cambio de datos, contrato ni permisos. |
| APIs afectadas | Ninguna modificada. Se consumen sin cambio `GET /v1/sales/quotes`, `GET /v1/sales/orders` y `POST /v1/sales/deliveries`. |
| Validacion | Sintaxis, i18n, validador de Ventas, documentacion viva y `npm.cmd run verify`. |
| Observaciones | Sin migracion, seed, despliegue ni escritura en QA/Produccion. Busqueda backend paginada queda pendiente para superar el limite preventivo actual de 200 documentos. |

### CHG-209

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Selectores escalables transversales |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `tools/validators/validate-scalable-selectors.js`, `tools/validators/validate-all.js`, `package.json`, `AGENTS.md`, `AGENTES.md`, `docs/arquitectura/seleccion_escalable_documentos.md`, `docs/contexto/ESTADO_ACTUAL.md`, `modulos/` y `TRAZABILIDAD.md` |
| Secciones | Administracion / Produccion / Almacenes / Ventas / Recursos Humanos / Accesibilidad / i18n / Escalabilidad / Documentacion |
| Agentes consultados | Reglas versionadas de especialistas modulares, UX/i18n, arquitectura API, QA y gobierno documental en `AGENTES.md`. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Incorpora un lookup reutilizable para referencias crecientes: búsqueda normalizada por texto, máximo de 20 resultados, selección por ID, validación de resultado real, teclado y sincronización ante cambios del catálogo. Lo aplica a roles, sucursales, entidades legales, artículos, almacenes, productos vinculables, recetas, recursos, áreas, puestos y responsables. Los buscadores documentales especializados de Ventas permanecen vigentes. |
| Motivo | Evitar listas inmanejables conforme crecen los registros y fijar una regla transversal sin convertir innecesariamente los catálogos cerrados en buscadores. |
| Impacto | UI y documentación Local. No modifica persistencia, permisos ni contratos. La consulta server-side paginada continúa siendo obligatoria antes de exceder los límites preventivos actuales. |
| APIs afectadas | Ninguna modificada. Los catálogos siguen consumiendo sus endpoints actuales de Admin, Production, Inventory, HR y Sales sin cambio contractual. |
| Validacion | `npm.cmd run validate:selectors`, sintaxis, i18n, responsive, documentación viva y `npm.cmd run verify`. |
| Observaciones | Sin migración, seed, despliegue ni escritura en QA/Producción. Rollback: revertir CHG-209; los `select` fuente conservan las opciones y valores originales. |

### CHG-210

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Portadas de reportes estándar por módulo |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `frontend/index.html`, `tools/validators/validate-module-report-hubs.js`, `tools/validators/validate-all.js`, `package.json`, `AGENTS.md`, `AGENTES.md`, `docs/arquitectura/reportes_estandar_por_modulo.md`, `docs/contexto/ESTADO_ACTUAL.md`, `modulos/README.md`, `modulos/07_reportes_inteligencia_operativa.md` y `TRAZABILIDAD.md` |
| Secciones | Portadas modulares / Reportes estándar / Producción / Almacenes / Recursos Humanos / Ventas / Administración / Módulos futuros / Reportes especializados / i18n / Responsive |
| Agentes consultados | Reglas versionadas de negocio y técnica de todos los módulos, arquitectura SaaS, UX/i18n, responsive, QA y gobierno documental en `AGENTES.md`. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Convierte la raíz de cada módulo en un centro de consulta de solo lectura con indicadores, catálogo de reportes, filtros sugeridos, fuentes del módulo y vista previa. Retira de esa portada altas, captura rápida y acciones operativas, incluida la acción global superior. Declara reportes propios para los cinco módulos activos y los cuatro módulos operativos planeados; conserva una configuración fallback para módulos futuros. Reportes permanece planeado para análisis especializados. |
| Motivo | Separar la consulta cotidiana de la operación, evitar acciones ambiguas en la primera pestaña y establecer desde ahora la frontera entre reportes propios del módulo y analítica transversal. |
| Impacto | UI, i18n, responsive, reglas de agentes y documentación Local. Las acciones existentes siguen en sus submódulos; no cambian permisos, datos ni contratos. |
| APIs afectadas | Ninguna modificada. Las vistas continúan leyendo los datos ya cargados desde Admin, Production, Inventory, HR y Sales mediante sus endpoints vigentes; no se agregan endpoints agregados ni exportaciones. |
| Validacion | `npm.cmd run validate:module-reports`, sintaxis, i18n, responsive, documentación viva y `npm.cmd run verify`. |
| Observaciones | Alcance exclusivo `local-write`; sin migración, seed, carga, despliegue ni escritura en QA/Producción. Filtros ejecutables, paginación/exportación y reportes especializados permanecen pendientes. Rollback: revertir CHG-210 para restaurar las portadas operativas anteriores. |

### CHG-211

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-20 |
| Cambio | Rollback de portada de Administración |
| Autor | Codex |
| Archivos | `frontend/app.js`, `frontend/index.html`, `tools/validators/validate-module-report-hubs.js`, `docs/arquitectura/reportes_estandar_por_modulo.md`, `docs/contexto/ESTADO_ACTUAL.md`, `modulos/README.md`, `modulos/08_administracion_configuracion.md`, `AGENTS.md`, `AGENTES.md` y `TRAZABILIDAD.md` |
| Secciones | Administración / Configuración / Portadas modulares / Reportes estándar / Gobierno documental |
| Agentes consultados | Reglas versionadas del especialista de negocio/técnico de Administración, arquitectura SaaS, UX, QA y gobierno documental en `AGENTES.md`. Se aplicaron `$erclave-feature` y `$erclave-environment-boundaries`; no se delegaron tareas ni se tocaron ambientes externos. |
| Descripcion | Revierte solamente la raíz de Administración para que vuelva a renderizar su centro de configuración con organización, usuarios, roles, permisos, módulos activos y catálogos base. Mantiene sin cambios las portadas de reportes estándar de los módulos operativos y documenta Administración como excepción deliberada. |
| Motivo | Administración es el lugar donde se configura y gobierna el sistema; convertir su portada en consulta impedía localizar y operar esas capacidades esenciales. |
| Impacto | UI y documentación Local de Administración. No altera los submódulos operativos, permisos, datos ni contratos. |
| APIs afectadas | Ninguna modificada. Administración vuelve a consumir sus endpoints vigentes de `admin-service` sin cambios de request/response ni permisos. |
| Validacion | `npm.cmd run validate:module-reports`, sintaxis, documentación viva y `npm.cmd run verify`. |
| Observaciones | Alcance exclusivo `local-write`; sin migración, seed, carga, despliegue ni escritura en QA/Producción. Rollback del rollback: restaurar la rama CHG-210 de Administración, aunque contradice la excepción funcional acordada. |

### CHG-212

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Codigos de negocio, fases ponderadas y costo unitario |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260821_0021_production_stage_weights.py`, `backend/alembic/versions/20260821_0022_admin_code_sequences.py`, Admin/Production/Inventory/Sales services y OpenAPI, `frontend/api/admin.js`, `frontend/app.js`, `frontend/styles.css`, `frontend/i18n/translations.js`, `AGENTES.md`, arquitectura, fichas `modulos/`, manuales de solucion y `TRAZABILIDAD.md` |
| Secciones | Administracion / Produccion / Almacenes / Recursos Humanos / Ventas / API / Datos / UI / Manuales funcionales |
| Agentes consultados | Especialistas de Produccion, Almacenes y Ventas revisaron ownership, contratos, fases, avance, costo y efectos comerciales. Se aplicaron `$erclave-feature`, `$erclave-environment-boundaries`, `$erclave-db-migration` y `$erclave-solution-manuals`, junto con reglas transversales de arquitectura, seguridad, UX, QA y documentacion de `AGENTES.md`. |
| Descripcion | Agrega el catalogo tenant-safe de folios administrados/manuales con reservas atomicas e idempotentes y defaults por modulo; sus consumidores UI asignan codigos a productos, recetas, ordenes, maquinaria, almacenes, articulos, areas, empleados y documentos de Ventas. Las recetas enumeran fases con pesos que suman 100%, las ordenes conservan snapshots de peso/area y exponen avance ponderado; Entregables por area muestra ese contexto. Corrige la deteccion frontend de version aprobada. Inventory expone costo por unidad base y conversion compatible de cantidad/costo. RH trata areas/puestos como generales y solo expone a Produccion la bandera productiva explicita, desmarcada por defecto. |
| Motivo | Dar identificadores de negocio gobernados, medir avance productivo de acuerdo con la aportacion real de cada area, calcular materiales desde una unidad economica clara y evitar que toda la estructura RH se interprete como productiva. |
| Impacto | Dos migraciones Local con backfill seguro: `0021` distribuye exactamente 100% entre etapas existentes y copia peso/area a etapas de orden; `0022` crea y provisiona secuencias por tenant. Cambian contratos y UI Local. Los documentos historicos conservan sus codigos y snapshots. QA/Produccion no fueron tocados. |
| APIs afectadas | Modificadas: Admin `GET /v1/catalogs/code-sequences` (`admin.setting.read`), `PATCH /v1/catalogs/code-sequences/{sequence_id}` (`admin.setting.update`) y `POST /v1/catalogs/code-sequences/{document_type}/next` (permiso de alta consumidor); Production requests/reads de recetas y ordenes, etapas y progreso en rutas existentes; Inventory `POST /v1/inventory/items/{id}/unit-conversion` (`inventory.item.read`) y lecturas de items con `default_unit_cost_per_base_unit`; Sales conserva sus rutas existentes y formaliza `BusinessDocumentCode`. Consumidas sin cambio: catalogo Admin de UOM y proyecciones HR/Inventory/Production. |
| Validacion | Pruebas dirigidas: Admin 76, Production 33, Inventory 13 y Sales 14 aprobadas; cinco DOCX validos; migraciones aplicadas de `20260818_0020` a `20260821_0022` en PostgreSQL Local; smoke autenticado con 14 secuencias y proyecciones reales de pesos, progreso y costo. `npm.cmd run verify`: todos los validadores, compilacion y `192 passed, 8 skipped`. |
| Observaciones | Rollback tecnico disponible en orden `0022 -> 0021 -> 0020`; eliminar `0021` pierde pesos/snapshots nuevos y solo debe hacerse bajo procedimiento de ambiente. Compras debe definir despues la actualizacion automatica de costo desde adquisiciones. Clientes API externos aun deben integrar la reserva central o usar el modo manual autorizado. |

### CHG-213

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Diagnostico operativo y errores accionables de Inventario, RH y Produccion |
| Autor | Codex |
| Archivos | Frontend e i18n; validadores de selectores, Produccion y RH; HR/Production services, pruebas y OpenAPI; manuales funcionales, contexto y `TRAZABILIDAD.md` |
| Secciones | Almacenes / Recursos Humanos / Recetas / Ordenes / Reservas y consumo / Seguridad de errores / Manuales funcionales |
| Agentes consultados | Especialistas de Almacenes, Produccion y revision transversal RH/API/UX/seguridad. Se aplicaron `$erclave-feature`, `$erclave-environment-boundaries` y `$erclave-solution-manuals`; alcance exclusivo Local. |
| Diagnostico | El selector de almacen filtraba por su propia etiqueta `Todos los almacenes`: bug UI. El empleado llevaba NSS de 9 digitos: error operativo, agravado por un 422 tecnico que podia reflejar datos personales. La receta usa articulos heredados con `LTS` y `MT`, codigos ausentes del catalogo UOM activo: error de datos maestros y hueco UX. La orden aprobada requiere capacidad del puesto `Fundidor A`, pero RH reporta cero trabajadores/minutos: bloqueo operativo correcto oculto por mensaje generico. |
| Descripcion | Al abrir un lookup se listan candidatos antes de escribir. RH responde errores estructurados sin valores personales y la UI declara 18/13/11 caracteres para CURP/RFC/NSS. Recetas marcan y bloquean materiales con unidad no activa sin eliminarlos silenciosamente de versiones existentes. Ordenes revalidan recursos antes de reservar un folio y muestran recurso, requerido, disponible y unidad. Los errores interpolados en formularios se escapan. El ciclo documenta y protege reserva al liberar, inicio sin salida, consumo/salida al completar y liberacion al cancelar. |
| Impacto | UI y contratos Local; sin migracion ni correccion automatica de maestros. Los articulos historicos con unidad invalida deben sustituirse o corregirse conforme a su historia. Una asignacion de responsable no sustituye la capacidad del puesto requerido por la receta. |
| APIs afectadas | **HR:** `POST /v1/hr/workers` (`hr.worker.create`) conserva request y normaliza respuestas 409/422 seguras. **Production:** `PATCH /v1/production/orders/{id}/status` (`production.order.status.update`) documenta y valida transiciones/reservas; request/response sin cambio estructural. **Consumidas sin cambio:** Inventory `GET /v1/inventory/warehouses`, `GET /v1/inventory/balances`, `GET /v1/inventory/items`; Admin UOM; Production `POST /v1/production/resource-validations` y `POST /v1/production/orders`; HR production-capacity. |
| Validacion | `npm.cmd run verify` aprobo todos los validadores, compilacion y `196 passed, 8 skipped`; Production dirigido aprobo 35 y RH 12. Los tres DOCX generados son contenedores validos. Tras reiniciar solo Production/RH Local, ambos `/health` y el frontend respondieron correctamente. |
| Observaciones | No se modificaron registros Local ni ambientes externos. `01_produccion.docx` estaba abierto y no pudo reemplazarse; se genero `01_produccion_CHG-213.docx`. Los Word de Almacenes y RH se regeneraron desde Markdown. |

### CHG-214

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Normalizacion auditada de alias heredados de unidad |
| Autor | Codex |
| Archivos | `backend/alembic/versions/20260821_0023_legacy_uom_aliases.py`, `frontend/app.js`, `frontend/i18n/translations.js`, contexto, arquitectura, ficha de Almacenes, manuales funcionales y `TRAZABILIDAD.md` |
| Secciones | Almacenes / Produccion / Ventas / Unidades de medida / Migraciones / Auditoria / UX / Manuales funcionales |
| Agentes consultados | Diagnosticos previos de especialistas de Almacenes y Produccion, mas reglas transversales de arquitectura, seguridad, datos, QA y gobierno documental. Se aplicaron `$erclave-feature`, `$erclave-environment-boundaries`, `$erclave-db-migration` y `$erclave-solution-manuals`; alcance exclusivo Local. |
| Diagnostico | `cera_01` se habia creado con el alias legado `LTS`, pero Administracion solo reconoce `LTR`. La pantalla proyectaba el equivalente `LTR`; al guardar, Inventory comparaba `LTR` contra el valor persistido `LTS` y activaba correctamente el bloqueo de cambio de unidad por historial. La migracion 0015 habia normalizado `L` y `M`, pero omitio los alias heredados `LTS` y `MT`. |
| Descripcion | La revision `20260821_0023` valida por tenant que existan activas las unidades destino y normaliza solo `LTS -> LTR` y `MT -> MTR` en columnas UOM de Inventory, Production y Sales. Registra antes/despues, tabla, columna y fila en `admin.audit_events`. La UI traduce el conflicto legitimo de unidad bloqueada y explica la accion segura. |
| Motivo | Permitir editar los demas datos de articulos historicos sin reinterpretar su inventario, conservando la proteccion contra cambios reales de unidad y eliminando una inconsistencia de codigos inequivocamente equivalentes. |
| Impacto | Se corrigieron seis filas del tenant demo Local: dos articulos, dos movimientos y dos recursos de receta. No cambiaron IDs, cantidades, costos, almacenes, estatus ni relaciones. `cera_01` quedo en `LTR`; el conjunto de columnas UOM ya no contiene `LTS/MT`. |
| APIs afectadas | Ninguna API ni contrato fue modificado. La UI sigue consumiendo `PATCH /v1/inventory/items/{item_id}` (`inventory.item.update`); solo mejora la presentacion del error `item_base_unit_locked_by_movements`. |
| Validacion | Migracion compilada y guardrails aprobados. Ciclo real Local `0022 -> 0023 -> 0022 -> 0023`: seis eventos al subir, restauracion exacta y retiro de auditoria al bajar, cero alias al finalizar. `npm.cmd run verify` aprobo todos los validadores, compilacion y `196 passed, 8 skipped`; los Word de Almacenes y Produccion abren correctamente. |
| Observaciones | Alcance `local-write` solo sobre `127.0.0.1:5434/erclave_local`. QA y Produccion permanecen en `20260805_0013`, sin conexiones, migraciones, seeds, despliegues ni escrituras. Rollback: `alembic downgrade 20260821_0022`; restaura solo filas auditadas cuyo valor actual aun coincide con el aplicado por 0023. |

### CHG-215

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Recetas rechazan maquinaria sin area RH con error accionable |
| Autor | Codex |
| Archivos | Production API, pruebas y OpenAPI; frontend e i18n; validador de Produccion; ficha modular, contexto, manual de Produccion y `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas / Maquinaria / Recursos Humanos / API / UX / Seguridad de errores / Manual funcional |
| Agentes consultados | Reglas versionadas de especialistas de Produccion y RH, arquitectura de APIs, seguridad, UX/i18n, QA y gobierno documental. Se aplico `$erclave-solution-manuals`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | El POST de receta si alcanzaba Production API. `h_002` estaba activa y mostraba el texto `Produccion Planta`, pero su `area_ref_id` era nulo; el area RH `P_PLANTA` existe activa. El repositorio rechazo correctamente `machine_resource_invalid`, pero el `ValueError` no estaba traducido y produjo `500` sin respuesta CORS util, por lo que el cliente lo presento como desconexion. |
| Descripcion | Crear, crear version o actualizar version traduce errores conocidos de normalizacion autoritativa a envelopes `422` seguros. La UI solo ofrece maquinas activas con `areaId`, muestra las maquinas pendientes y traduce `machine_resource_invalid`. Abrir la maquina puede proponer el area por su nombre visible, pero el operador debe confirmar y guardar el ID estable; no existe escritura automatica por texto. |
| Motivo | Separar un bloqueo operativo correcto de un bug de manejo de errores, evitar recetas con referencias incompletas y dar al usuario una ruta de correccion sin ocultar la causa ni relacionar maestros por similitud. |
| Impacto | Runtime y UI Local. No se modificaron maestros ni se creo la receta fallida. La maquina `h_002` permanece sin `area_ref_id` hasta que el operador la edite. No cambia schema ni revision Alembic. |
| APIs afectadas | `POST /v1/production/recipes` (`production.recipe.create`), `POST /v1/production/recipes/{id}/versions` y `PATCH /v1/production/recipe-versions/{version_id}` (`production.recipe.update`) documentan y devuelven `422` para recursos no elegibles; requests y respuestas exitosas no cambian. |
| Validacion | Production API dirigida: `36 passed`; validadores de ciclo, i18n y OpenAPI aprobados. `npm.cmd run verify` aprobo todos los validadores, compilacion y `197 passed, 8 skipped`; `01_produccion_CHG-215.docx` abre correctamente. |
| Observaciones | No se conecto, migro, desplego ni escribio QA/Produccion. Correccion operativa pendiente del usuario: editar `h_002`, seleccionar el area RH activa `P_PLANTA`, guardar la maquina y volver a crear la receta. |

### CHG-216

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Salidas de materiales al iniciar produccion |
| Autor | Codex |
| Archivos | Production API, repositorio, pruebas, OpenAPI y README; frontend e i18n; validador de ciclo; ownership/API, decisiones, contexto, fichas y manuales de Produccion/Almacenes; `TRAZABILIDAD.md` |
| Secciones | Produccion / Ordenes / Almacenes / Reservas / Kardex / Costeo / Estados / Idempotencia / UX / Manuales funcionales |
| Agentes consultados | Reglas versionadas de especialistas de Produccion e Inventarios y transversales de arquitectura, APIs, seguridad, datos, UX/i18n, QA y gobierno documental. Se aplicaron `$erclave-feature`, `$erclave-environment-boundaries` y `$erclave-solution-manuals`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | El flujo anterior reservaba por almacen al liberar y consumia al completar. Eso no satisfacia la regla solicitada de reconocer la salida fisica al comenzar la ejecucion. Ademas, iniciar una etapa podia cambiar la orden a `in_progress` dentro del repositorio sin pasar por el comando que coordina Inventory. |
| Descripcion | La primera transicion `released/waiting_resources -> in_progress` consume todas las reservas mediante Inventory con claves derivadas estables; cada reserva crea una salida `exit/out` en su propio almacen y devuelve cantidad/costo para el real de materiales. Reanudar desde pausa, volver desde validacion y completar no consumen otra vez. Cancelar antes del inicio libera; cancelar despues conserva las salidas. Una etapa solo inicia si la orden ya esta `in_progress`; la UI ejecuta primero la transicion controlada. |
| Motivo | Alinear Kardex, existencia fisica y costo real con el momento operativo en que los materiales salen del almacen, sin duplicar movimientos por reintentos, reanudaciones o cierre. |
| Impacto | Cambio de semantica solo en codigo Local, sin schema ni migracion. Las ordenes futuras registran salidas al primer inicio. Las salidas ya registradas son inmutables y una cancelacion posterior no las revierte automaticamente; una correccion fisica debe seguir el flujo autorizado de reversa/ajuste de Inventory. |
| APIs afectadas | **Contrato modificado:** Production `PATCH /v1/production/orders/{id}/status` (`production.order.status.update`) conserva request/response y cambia la semantica de `in_progress`, cancelacion y cierre; `PATCH /v1/production/order-stages/{stage_id}` (`production.order_stage.update`) conserva payload y exige que la orden ya este en produccion. **Consumido sin cambio:** Inventory `POST /v1/inventory/reservations/{id}/consume` y `/release` (`production.order.status.update`); Inventory sigue siendo propietario de reservas, almacenes, movimientos y valuacion. **APIs no tocadas:** contratos de Inventory y demas servicios. |
| Validacion | Production dirigida `38 passed`; Production + Inventory `61 passed`; `npm.cmd run verify` aprobo todos los validadores, compilacion y `199 passed, 8 skipped`. Los Word `01_produccion_CHG-216.docx` y `02_almacenes_inventarios.docx` abren correctamente. |
| Observaciones | No se mutaron ordenes, reservas ni movimientos Local existentes; no hubo conexion, migracion, seed, despliegue ni escritura en QA/Produccion. El consumo entre servicios es reintentable mediante una clave estable por orden/reserva; si una interrupcion ocurre entre Inventory y Production, se debe reintentar el mismo cambio de estatus para reconciliar. |

### CHG-217

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Validacion autoritativa de recursos en ordenes |
| Autor | Codex |
| Archivos | `frontend/app.js`, `tools/validators/validate-production-cycle.js`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Ordenes / Validacion de recursos / Inventario / RH / Maquinaria / UX |
| Agentes consultados | Reglas versionadas de Produccion, Inventarios y RH, mas arquitectura, seguridad, UX y QA. Se reviso el manual funcional vigente y no requirio cambio porque ya atribuye la decision al backend autoritativo. Alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | En modo API, `validateOrder` ejecutaba primero `getReleaseReview`, una calculadora de maqueta basada en recursos locales. Esa prevalidacion produjo cinco falsos faltantes y detuvo el flujo antes de llamar `POST /v1/production/resource-validations`. Los tres materiales reales tienen disponibilidad suficiente: Aroma 88.8/0.12 LTR, Cera 196.5/0.35 LTR y Mecha 74/0.1 MTR; tambien existe un trabajador Fogonero y la maquina H_002 activa. |
| Descripcion | La validacion local conserva campos obligatorios, responsables y fecha. En modo API omite faltantes de maqueta y consulta al backend autoritativo, que decide con existencias menos reservas, capacidad laboral y maquinaria. El modo mock conserva su calculadora local. El validador transversal impide reintroducir el bloqueo. |
| Motivo | Evitar que datos simulados contradigan Almacenes/RH reales y asegurar que el operador reciba cantidades requeridas/disponibles provenientes de los servicios propietarios. |
| Impacto | Correccion frontend Local sin cambios de schema, datos ni contrato. Tras actualizar la pagina, **Validar orden** alcanzara Production API y mostrara el resultado real. La fecha 25/05/2026 permanece permitida por la regla vigente, aunque la orden nacera vencida; no se invento una prohibicion de fechas pasadas. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Consumidas sin cambio:** Production `POST /v1/production/resource-validations` (`production.order.validate`) y `POST /v1/production/orders` (`production.order.create`); Production consulta Inventory availability y HR capacity internamente. **APIs no tocadas:** Inventory, HR, Admin, Sales y demas servicios. |
| Validacion | `npm.cmd run verify` aprobo todos los validadores, compilacion y `199 passed, 8 skipped`. Diagnostico Local realizado con consultas `SELECT` y logs; sin mutaciones. |
| Observaciones | No se crearon ordenes, reservas, movimientos ni folios durante el diagnostico. No hubo conexion, migracion, seed, despliegue ni escritura en QA/Produccion. |

### CHG-218

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Receta aprobada vigente en validacion de orden |
| Autor | Codex |
| Archivos | `frontend/app.js`, `tools/validators/validate-production-cycle.js`, `docs/contexto/ESTADO_ACTUAL.md`, `TRAZABILIDAD.md` |
| Secciones | Produccion / Recetas / Aprobacion / Ordenes / Snapshots / UX |
| Agentes consultados | Reglas versionadas de Produccion, arquitectura de datos/API, UX, seguridad y QA. Se reviso el manual funcional y continua correcto: la orden usa la version vigente aprobada y conserva snapshot al crearse. Alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | PostgreSQL confirma `rec-000004` activa, version 1 aprobada y `current_version_id=rcv_7ded645afcb24a5fa32c1c6b47`; la aprobacion se registro correctamente. La lista tambien la mostraba aprobada. El boton **Validar orden** usaba `order.recipeSnapshot`, un snapshot transitorio sin `currentVersionId`, y concluia falsamente que no existia una version vigente. |
| Descripcion | En modo API, la vista previa/validacion obtiene la receta maestra recargada mediante `mockDb.findRecipe(order.recipeId)` y usa su `currentVersionId/currentVersionData`. El modo mock conserva el snapshot. Los PDF y ordenes persistidas siguen resolviendo sus snapshots historicos; no se reemplaza historia por el maestro actual. Un guardrail impide reintroducir la lectura incorrecta. |
| Motivo | Distinguir el maestro vigente requerido para crear/validar una orden del snapshot historico que se conserva despues de crearla. |
| Impacto | Correccion frontend Local sin cambio de contrato, schema ni datos. La aprobacion existente no se repitio ni modifico. Tras recarga forzada, **Validar orden** debe alcanzar la validacion autoritativa de recursos con la version aprobada. |
| APIs afectadas | **Contratos modificados:** Ninguno. **Consumidas sin cambio:** Production `GET /v1/production/recipes` (`production.recipe.read`), `POST /v1/production/resource-validations` (`production.order.validate`) y `POST /v1/production/orders` (`production.order.create`). **APIs no tocadas:** Inventory, HR, Admin, Sales y demas servicios. |
| Validacion | `npm.cmd run verify` aprobo todos los validadores, compilacion y `199 passed, 8 skipped`. Diagnostico de persistencia realizado exclusivamente con `SELECT`; sin mutaciones. |
| Observaciones | No se aprobo nuevamente la receta ni se creo una orden durante el diagnostico. La fecha 25/05/2026 sigue siendo una fecha pasada permitida por la regla actual y generaria una orden vencida. No hubo conexion ni escritura en QA/Produccion. |

### CHG-219

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Cierre valido de reservas al iniciar produccion |
| Autor | Codex |
| Archivos | Inventory repository y prueba; guardrail de movimientos; contexto y `TRAZABILIDAD.md` |
| Secciones | Produccion / Ordenes / Almacenes / Reservas / Salidas / Kardex / Transacciones |
| Agentes consultados | Reglas versionadas de Produccion, Inventarios, arquitectura de datos/API, seguridad y QA. Alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | No fue un error operativo. Al pasar `OP-000003` de `waiting_resources` a `in_progress`, Inventory creo la salida dentro de la transaccion pero intento dejar la reserva con cantidad cero. El constraint `ck_inventory_reservation_quantity` exige cantidad positiva, produjo `500`, y PostgreSQL revirtio salida y estatus. La orden quedo en espera, sus tres reservas activas y no existen movimientos parciales. |
| Descripcion | El consumo total conserva la ultima cantidad positiva reservada como snapshot historico y cambia el estatus a `consumed`; el saldo operativo devuelto es cero. El consumo parcial actualiza la cantidad al saldo positivo y conserva `active`. El movimiento de salida, la auditoria y la idempotencia no cambian. |
| Motivo | Respetar la integridad de la tabla y conservar evidencia de la reserva sin representar una reserva activa de cantidad cero. |
| Impacto | Correccion tecnica Local sin migracion, cambio de contrato ni mutacion automatica de la orden fallida. El operador puede reintentar el cambio a **En produccion**; cada reserva generara una sola salida en su almacen. |
| APIs afectadas | **Contrato modificado:** Ninguno. **Implementacion corregida sin cambio de request/response:** Inventory `POST /v1/inventory/reservations/{id}/consume`, consumido por Production al ejecutar `PATCH /v1/production/orders/{id}/status`. |
| Validacion | Inventario + Produccion: `62 passed`; guardrails de movimientos y ciclo de Produccion aprobados. `npm.cmd run verify` aprobo todos los validadores, compilacion y `200 passed, 8 skipped`. Inventory Local reinicio en `127.0.0.1:8004` y respondio `health=ok`, ambiente `local`. |
| Observaciones | La comprobacion del intento fallido fue de solo lectura. No se cambiaron datos Local ni hubo conexion, migracion, seed, despliegue o escritura en QA/Produccion. |

### CHG-220

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Cierre guiado y precondiciones visibles de orden de produccion |
| Autor | Codex |
| Archivos | Production repository, prueba, OpenAPI y README; frontend e i18n; guardrail; ficha modular, contexto, manual funcional y `TRAZABILIDAD.md` |
| Secciones | Produccion / Ordenes / Etapas / Validacion / Consumos reales / Costo real / Estados / UX |
| Agentes consultados | Reglas versionadas de Produccion, Inventarios, RH, arquitectura de datos/API, seguridad, UX/i18n, QA y gobierno documental. Se aplico `$erclave-solution-manuals`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | No fue un error de Almacenes. `OP-000003` estaba persistida en `in_validation`, pero Fundicion (80%) y Produccion Planta (20%) permanecian `pending` con avance cero. El backend rechazo correctamente `completed` con `production_stages_incomplete`, pero el selector habia permitido entrar manualmente a validacion antes de cerrar fases y el cliente mostro el mensaje tecnico generico. Ademas, la captura de uso real solo era descubrible dentro de PDF/Imprimir. |
| Descripcion | Entrar a `in_validation` exige todas las fases `completed/skipped`; la ultima fase completada realiza el cambio automaticamente. El selector muestra solo transiciones validas y ofrece `Terminada` unicamente cuando las fases y usos reales estan completos. Las tarjetas explicitan que se pulsan para avanzar; el acceso se llama **Cierre/consumos** mientras falten cantidades reales. Los errores de fases, consumos e invalid transition se presentan de forma accionable en ES/EN. |
| Motivo | Evitar estados generales incoherentes, guiar el cierre en su orden real y conservar las validaciones autoritativas sin obligar al operador a interpretar codigos tecnicos. |
| Impacto | Cambio funcional/UX Local sin migracion ni mutacion automatica de la orden existente. `OP-000003` se recupera seleccionando **En produccion**, avanzando ambas tarjetas, guardando consumos reales y eligiendo **Terminada**. No se repiten salidas de materiales al volver desde validacion. |
| APIs afectadas | **Semantica endurecida sin cambiar payload/response:** Production `PATCH /v1/production/orders/{id}/status` (`production.order.status.update`): `in_validation` exige fases terminales; `completed` mantiene materiales consumidos, fases terminales y uso real. **Sin cambio:** etapas y recursos reales conservan sus endpoints actuales. |
| Validacion | Production dirigida: `39 passed`; guardrails de ciclo, i18n y OpenAPI aprobados. `npm.cmd run verify` aprobo todos los validadores, compilacion y `201 passed, 8 skipped`; el Word `01_produccion_CHG-220.docx` es un contenedor valido. Production Local reinicio en `127.0.0.1:8002` y respondio `health=ok`, ambiente `local`. |
| Observaciones | Diagnostico de PostgreSQL realizado exclusivamente con `SELECT`; no se modifico la orden. No hubo conexion, migracion, seed, despliegue ni escritura en QA/Produccion. |

### CHG-221

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Avance porcentual de fases sin minutos obligatorios |
| Autor | Codex |
| Archivos | Production schemas, repository, pruebas, OpenAPI y README; frontend e i18n; guardrail; ficha modular, contexto, manual funcional y `TRAZABILIDAD.md` |
| Secciones | Produccion / Ordenes / Etapas / Porcentaje / Validacion / Cierre / Eficiencia futura / UX |
| Agentes consultados | Reglas versionadas de Produccion, RH, Inventarios, arquitectura de datos/API, UX/i18n, seguridad, QA y gobierno documental. Se aplico `$erclave-solution-manuals`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | El prompt nativo exigia minutos exactos al terminar una fase y el cierre requeria uso real de mano de obra/maquinaria. El dato era prematuro: todavia no existe un modelo completo de turnos, pausas, incidencias y eficiencia que permita auditarlo con calidad. La necesidad vigente es medir avance ponderado por fase. |
| Descripcion | Cada tarjeta abre un formulario propio de porcentaje. El backend exige coherencia: 0%=pending, 1..99%=in_progress y 100%=completed/skipped. Permite actualizar varias veces una fase y pasar directamente de pendiente a 100%. Todas las fases deben estar terminales y al 100% para entrar a validacion/cerrar. Minutos y consumos temporales dejan de ser obligatorios y la vista PDF los identifica como medicion futura; el cierre conserva la salida/costo real de materiales. |
| Motivo | Capturar un dato que el operador conoce y puede sostener, sin simular precision temporal antes de definir la base de auditoria y eficiencia. |
| Impacto | Cambio funcional/UX Local sin migracion ni mutacion automatica. La orden `OP-000003` ya tiene ambas fases `completed` al 100% y queda lista para seleccionar **Terminada** despues de recargar; los minutos previamente capturados se conservan como dato historico opcional. |
| APIs afectadas | **Contrato modificado:** `PATCH /v1/production/order-stages/{stage_id}` (`production.order_stage.update`) requiere `progress_percent` 0..100 coherente con `status`; `actual_minutes` permanece opcional. **Semantica de cierre modificada sin payload nuevo:** `PATCH /v1/production/orders/{id}/status` ya no exige uso real de recursos temporales, pero conserva materiales consumidos y fases terminales al 100%. |
| Validacion | Production dirigida: `40 passed`; guardrails de ciclo, i18n y OpenAPI aprobados. `npm.cmd run verify` aprobo todos los validadores, compilacion y `202 passed, 8 skipped`; el Word `01_produccion_CHG-221.docx` es un contenedor valido. Production Local reinicio en `127.0.0.1:8002` y respondio `health=ok`, ambiente `local`. |
| Observaciones | La comprobacion de `OP-000003` se realizo con `SELECT`; no se modificaron sus datos. La medicion de tiempos, capacidad ejecutada y eficiencia queda explicitamente diferida, no eliminada del modelo futuro. No hubo conexion, migracion, seed, despliegue ni escritura en QA/Produccion. |

### CHG-222

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Recepcion validada de producto terminado desde Almacenes |
| Autor | Codex |
| Archivos | Inventory schemas, autoridad Production, repository, API, pruebas y OpenAPI; frontend Inventory/Production e i18n; arquitectura, contexto, manuales funcionales y `TRAZABILIDAD.md` |
| Secciones | Almacenes / Movimientos / Entradas de produccion / Produccion / Ordenes terminadas / Kardex / Costo / Recepciones parciales |
| Agentes consultados | Reglas versionadas de Produccion, Inventarios, arquitectura de datos/API, seguridad, UX/i18n, QA y gobierno documental. Se aplicaron `$erclave-feature`, `$erclave-environment-boundaries` y `$erclave-solution-manuals`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | El ciclo descontaba materiales al iniciar, pero una orden terminada no tenia un procedimiento de recepcion fisica de su producto. Registrar una entrada manual permitia elegir articulo, unidad, costo o cantidad sin verificar la orden y podia duplicar existencias. |
| Descripcion | **Almacenes > Movimientos** consulta ordenes terminadas y cantidades ya recibidas. El almacenista confirma almacen, cantidad, fecha y notas; Inventory deriva por ID el producto comercial y articulo terminado, valida estatus/tipo/unidad, permite parciales, bloquea excedentes con lock transaccional y crea una entrada trazable `production_order_receipt`. El costo unitario usa costo real disponible o costo planeado de la orden. |
| Motivo | Separar correctamente producir de recibir: Produccion declara el resultado terminado y Almacenes confirma el conteo fisico y conserva el Kardex autoritativo. |
| Impacto | Nueva capacidad funcional Local sin migracion ni recepcion automatica de ordenes existentes. Las ordenes terminadas vinculadas apareceran como pendientes; cada confirmacion actualiza saldo y deja de mostrarse cuando queda totalmente recibida. |
| APIs afectadas | **Nuevas:** Inventory `GET /v1/inventory/finished-goods-receipts` (`inventory.movement.read`) y `POST /v1/inventory/finished-goods-receipts` (`inventory.movement.create`, idempotente). **Consumidas sin cambio:** Production `GET /v1/production/orders/{id}` y `GET /v1/production/product-services/{id}` para validacion autoritativa. |
| Validacion | Inventory dirigida: `16 passed`; OpenAPI, i18n, sintaxis y guardrails aprobados. `npm.cmd run verify` aprobo validadores, compilacion y `204 passed, 8 skipped`; ambos Word CHG-222 son contenedores validos. Inventory Local reinicio en `127.0.0.1:8004` y respondio `health=ok`, ambiente `local`. |
| Observaciones | No se recibio ni modifico automaticamente ninguna orden. No hubo migracion, seed, despliegue ni escritura en QA/Produccion. El endpoint revalida tenant, orden terminada, vinculo, tipo, estatus, unidad y saldo pendiente; la UI nunca elige articulo/costo por texto. |

### CHG-223

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Reinicio individual de Inventory con configuracion Local completa |
| Autor | Codex |
| Archivos | `backend/scripts/start_inventory_local.ps1`, contexto y `TRAZABILIDAD.md` |
| Secciones | Operacion Local / Inventory / Configuracion / PostgreSQL / Firebase / Diagnostico |
| Agentes consultados | Reglas versionadas de limites de ambiente, Inventory, seguridad y operacion Local. Se aplico `$erclave-environment-boundaries`; alcance exclusivo Local y sin delegacion nueva. |
| Diagnostico | Inventory respondia `/health=200`, pero `GET /v1/inventory/warehouses` devolvia `500`. El reinicio manual habia creado Uvicorn sin las variables heredadas del arranque canonico; health no usa base, mientras la consulta carecia de URL efectiva. No fue un error operativo del usuario ni de los datos. |
| Descripcion | El script de arranque individual carga la URL local desde `backend/.env`, verifica estrictamente `127.0.0.1:5434/erclave_local` y transmite ambiente, Firebase Emulator y URLs loopback de Admin, Production, Inventory y frontend antes de iniciar el proceso. |
| Motivo | Hacer que un reinicio aislado reproduzca los limites esenciales del arranque completo y evitar falsos positivos de health con dependencias sin configurar. |
| Impacto | Correccion operativa Local sin cambio de API, schema ni datos. Inventory se reinicio mediante el script corregido. |
| APIs afectadas | **Contrato modificado:** Ninguno. **Validacion runtime:** `GET /health`, `GET /v1/inventory/warehouses` y `GET /v1/inventory/finished-goods-receipts`. |
| Validacion | Parser PowerShell aprobado; arranque gobernado reporto PostgreSQL `5434` e Inventory `8004`; GET autenticado de almacenes devolvio `200` y 3 registros. Suite completa aprobada despues del cambio. |
| Observaciones | No hubo migracion, seed, recepcion, modificacion de ordenes ni escritura en QA/Produccion. |

### CHG-224

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Preparacion gobernada del candidato QA de cinco servicios |
| Autor | Codex |
| Archivos | Workflows QA, scripts de smoke/trafico/seed, builder frontend, configuracion runtime, plan/README IAM, pruebas, expediente de release, contexto, pendientes y `TRAZABILIDAD.md` |
| Secciones | QA / Release / Admin / Produccion / Inventory / RH / Ventas / Migraciones / IAM / Rollback |
| Agentes consultados | Reglas versionadas de limites de ambiente, release QA, feature y manuales funcionales. Se aplicaron `$erclave-environment-boundaries`, `$erclave-qa-release`, `$erclave-feature` y `$erclave-solution-manuals`; alcance de escritura exclusivo al repositorio y sin delegacion nueva. |
| Diagnostico | El pipeline vigente construia y promovia cuatro servicios, dejaba Sales fuera del artefacto y del tenant QA, y no entregaba a Inventory la URL de Produccion requerida por CHG-222. Promover ese estado habria creado paridad incompleta y una recepcion de producto terminado no operativa en QA. |
| Descripcion | El candidato incorpora Sales como quinto servicio por digest, identidad dedicada, variables/runtime HTTPS, smoke, promocion atomica de trafico y frontend sanitizado. Inventory recibe la dependencia Production; el runtime valida todas las autoridades no locales. El expediente registra alcance, migraciones `0013 -> 0023`, gates, matriz minima, rollback y bloqueos. |
| Motivo | Preparar un release reproducible que represente el sistema Local real sin mezclar ambientes ni habilitar modulos carentes de servicio. |
| Impacto | Solo preparacion de codigo/documentacion. QA vigente no cambia. La promocion es NO-GO hasta publicar un SHA inmutable, aprovisionar `erclave-sales-qa`/variables y obtener las aprobaciones protegidas. |
| APIs afectadas | **Contratos funcionales modificados:** Ninguno por CHG-224. **Runtime preparado:** cinco servicios exponen `GET /health`, `GET /ready` y `GET /version`; el frontend QA consumira Admin, Production, Inventory, HR y Sales. |
| Validacion | Health/readiness/version publicos de las cuatro APIs QA vigentes respondieron correctamente con version `4e9c6881dab61239f1abd5fff688019fdd697977`. La cuenta `gcloud` activa carece de `run.services.list`, documentado como preflight pendiente del aprobador. Validacion completa de repositorio se ejecuta antes de cerrar el corte. |
| Observaciones | No se ejecuto workflow, migracion, seed, configuracion de tenant, Cloud Run, trafico ni Firebase Hosting. No se consultaron secretos ni se copiaron datos Local a QA. Los manuales CHG-222 siguen vigentes porque el cambio es de liberacion, no de uso funcional. |

### CHG-225

| Campo | Contenido |
|---|---|
| Fecha | 2026-08-21 |
| Cambio | Aprovisionamiento minimo de identidad y variables Sales QA |
| Autor | Codex |
| Archivos | Plan IAM y expediente QA consultados; contexto, pendientes y `TRAZABILIDAD.md` actualizados |
| Secciones | QA / IAM / GitHub Actions / Ventas / Supply chain / Release |
| Agentes consultados | Arquitecto senior de plataforma SaaS, Ingeniero senior de seguridad IAM/supply chain e Ingeniero senior de QA/validadores/release conforme a `AGENTES.md`. Se aplicaron `$erclave-environment-boundaries` y `$erclave-qa-release`. |
| Diagnostico | La cuenta activa `chemapadillasanchez@gmail.com` no tenia acceso al proyecto `erclave`; el preflight se detuvo antes de escribir. La cuenta QA `eslaclavecaf@gmail.com` ya estaba autenticada y si resolvio el proyecto `erclave` numero `370105017372`. La identidad Sales y las dos variables aun no existian. |
| Descripcion | Se creo `erclave-sales-qa@erclave.iam.gserviceaccount.com` sin llaves administradas por usuario. Se concedio `roles/cloudsql.client`, acceso `roles/secretmanager.secretAccessor` solo sobre `erclave-database-url-qa` y `roles/run.invoker` sobre `admin-service-qa`, `hr-service-qa`, `production-service-qa` e `inventory-service-qa`. Se crearon las variables no secretas `QA_SALES_RUNTIME_SERVICE_ACCOUNT` y `QA_SALES_API_URL` en `ChemaPsan/eslaclave-erclave`. |
| Motivo | Cerrar el prerrequisito minimo de identidad/configuracion para construir un candidato QA de cinco servicios sin llaves JSON, permisos de secreto a nivel proyecto ni despliegue prematuro. |
| Impacto | Escritura externa acotada de IAM/configuracion QA. No se creo `sales-service-qa`, no se construyo imagen, no se leyo el secreto, no se ejecuto migracion o configuracion de tenant, no se movio trafico ni se publico frontend. El siguiente gate es `qa-build`. |
| APIs afectadas | **Contratos funcionales modificados:** Ninguno. **APIs operativas usadas:** Google Cloud IAM/Secret Manager/Cloud Run IAM y GitHub Actions repository variables. No se invocaron APIs ERClave. |
| Validacion | Identidad activa y sin llaves de usuario; roles de proyecto/secreto verificados; los cuatro bindings `run.invoker` verificados; ambas variables releidas con sus valores esperados. `main` remoto verificado en `adb134f7ac8b33b4a842d07db10c9b5f88525f2f`; su CI previo finalizo correctamente. |
| Rollback | Eliminar las dos variables; retirar los cuatro bindings `run.invoker`, el binding del secreto y `roles/cloudsql.client`; finalmente eliminar la cuenta de servicio. No hay datos ni revision Cloud Run que revertir. |
| Observaciones | La URL Sales se derivo del nombre estable `sales-service-qa` y del sufijo QA comprobado en los cuatro servicios existentes: `https://sales-service-qa-kgnfw5neua-uc.a.run.app`. La configuracion activa de `gcloud` no se cambio; todos los comandos QA declararon cuenta y proyecto explicitamente. |

## Convencion para futuros cambios

Cuando hagamos una edicion nueva, se debe agregar una entrada adicional con el siguiente ID correlativo y dejar claro si el cambio fue funcional, documental, visual o tecnico.
