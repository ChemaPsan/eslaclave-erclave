# Manual funcional de Produccion

- Audiencia: planeadores, supervisores y responsables de produccion
- Alcance por ambiente: Local y QA
- Ultima revision: 2026-08-25
- Capacidades cubiertas: productos/servicios, recetas, fases ponderadas, planeacion multi-dia, ordenes y entregables por area

## Proposito

Produccion define que se fabrica o ejecuta, que recursos consume y como se mide el avance de cada orden.

## Conceptos

- **Codigo de receta:** folio de negocio propio de la receta; no es el SKU ni el ID tecnico.
- **Version:** copia controlada de recursos y fases. Una orden conserva la version con la que fue liberada.
- **Fase:** etapa numerada asignada a un area productiva.
- **Peso de fase:** contribucion al avance total; las fases activas deben sumar 100%.
- **Codigo de orden:** folio visible de la orden de produccion.

## Acceso y prerequisitos

En Local, liberar, iniciar, pausar, reanudar, enviar a validacion, finalizar y cancelar requieren permisos independientes. Terminar una etapa exige `production.order_stage.complete`; capturar avance con `production.order_stage.update` no concede esa declaracion. La alta actual valida, reserva y nace liberada, por lo que requiere `production.order.release`.

Se requieren permisos `production.recipe.*`, `production.order.*` o `production.order_stage.update`, segun la tarea. La asignacion automatica de folio usa el permiso de alta; editar su configuracion pertenece a Administracion.

El producto debe estar activo. Una receta productiva requiere materiales elegibles de Almacenes con una unidad activa del catalogo de Administracion, puestos y areas productivas de RH y, cuando aplique, maquinaria existente que no este inactiva. Una maquina en mantenimiento puede formar parte de la receta, pero bloqueara la orden mientras no vuelva a estar activa. El area RH de la maquina es recomendable para asignacion y reportes, no un requisito para definir el proceso. Una orden requiere una version aprobada vigente.

## Crear una receta

1. Seleccione el producto o servicio.
2. Revise el codigo. En modo administrado se asigna al guardar; en modo manual capture uno unico.
3. Indique version, cantidad base, unidad y centro de costos.
4. Agregue materiales, mano de obra y maquinaria.
5. Seleccione las areas responsables; el sistema numera las fases.
6. Capture el peso de cada fase y confirme que la suma sea 100%.
7. Valide recursos, guarde y apruebe cuando corresponda.

Un articulo cuya unidad base no exista o este inactiva se muestra como no disponible y no puede agregarse. Corrija el articulo en Almacenes. Los alias heredados administrados `LTS -> LTR` y `MT -> MTR` se normalizan de forma auditada. Si se trata de cualquier otra unidad y ya existen movimientos o reservas, la historia permanece protegida: cree un articulo sustituto con la unidad activa y regularice existencias mediante el procedimiento autorizado.

## Generar y seguir una orden

Seleccione receta aprobada, cantidad, inicio planeado, dias productivos, fecha requerida, prioridad y responsables. La receta propone una duracion que puede ajustar en la orden. Antes de asignar el folio, el sistema valida materiales una sola vez y distribuye los minutos de capacidad laboral y maquinaria de lunes a viernes; muestra el horizonte, el minimo calculado y el desglose por fecha. Si falta un recurso, muestra su nombre, cantidad requerida, disponible y unidad. La fecha requerida no puede quedar antes del fin planeado. La orden copia recursos, costos, areas, numero y peso de cada fase; cambios posteriores en la receta no la alteran.

En el editor de Recetas, **Validar definicion** solo confirma que materiales, puestos y maquinas existan y sean elegibles, y proyecta cantidades y costo. No revisa inventario ni disponibilidad de horas. Es normal que una receta sea valida aunque una orden concreta no pueda liberarse por faltantes o mantenimiento; esa disponibilidad se comprueba al generar la orden usando sus dias planeados.

El avance es ponderado. Ejemplo: Fundicion pesa 70% y va al 50%; Empaque pesa 30% y va al 100%. El avance general es 65%, no 75%.

En **Entregables por area**, actualice la etapa de la orden. Se muestran folio, numero de fase, area, peso y avance general.

## Estados principales

| Estado | Significado |
|---|---|
| Liberada | Autorizada para iniciar. |
| En espera de recursos | Tiene un faltante o confirmacion pendiente. Puede iniciar solo si conserva las reservas materiales requeridas. |
| En produccion | Al entrar por primera vez, Almacenes consume las reservas y registra las salidas de materiales en sus almacenes de origen. |
| Pausada | Detenida temporalmente con causa. |
| En validacion | Las fases terminaron y el resultado se revisa. |
| Terminada | Cierre operativo; exige fases concluidas y consolida costos sin volver a registrar salidas. |
| Cancelada | No continuara. Antes de iniciar libera reservas; despues de iniciar conserva las salidas fisicas ya registradas. |

## Como terminar una orden

1. Mantenga la orden en **En produccion**.
2. Pulse la tarjeta de una fase y capture el porcentaje realmente completado.
3. Use de 1% a 99% mientras siga **En proceso**; capture 100% cuando la fase este **Terminada**.
4. Repita hasta que todas las fases tengan 100%. La orden pasa automaticamente a **En validacion**.
5. Seleccione **Terminada**. El cierre conserva el costo de materiales y no vuelve a descontarlos.

El selector solo muestra cambios validos para el estado actual. Si una orden heredada llego a **En validacion** con fases pendientes, vuelva a **En produccion** y lleve cada tarjeta a 100%; no registre otra salida manual en Almacenes.

Los minutos reales y la eficiencia de mano de obra/maquinaria no son obligatorios en este corte. Se incorporaran despues, cuando exista una base operativa suficiente para auditarlos sin inventar precision.

## Mensajes frecuentes

- **La validacion requiere una receta aprobada vigente:** recargue y confirme que la version aparezca Aprobada.
- **Los porcentajes deben sumar 100:** ajuste los pesos; ninguna fase activa puede valer cero.
- **Recurso no disponible:** revise existencia, trabajador productivo o capacidad de maquinaria.
- **Todas las fases deben tener 100%:** vuelva a **En produccion**, abra cada tarjeta y capture el porcentaje faltante.
- **Maquinaria sin area de RH vinculada:** abra **Produccion > Maquinaria**, edite el equipo, seleccione un area activa de Recursos Humanos y actualice. Despues vuelva a abrir la receta; el sistema no vincula por coincidencia de nombre.
- **Unidad de medida no activa:** el material usa un codigo que no pertenece al catalogo activo; corriga o sustituya el articulo de Almacenes.
- **Capacidad laboral insuficiente:** asigne trabajadores activos al puesto requerido por la receta. El responsable general o de fase no reemplaza una necesidad de mano de obra distinta.
- **Los dias productivos no alcanzan:** aumente el horizonte o libere capacidad ya comprometida. El calendario actual considera lunes a viernes; turnos, festivos, ausencias y mantenimiento configurable se incorporaran en una evolucion posterior.

## Integraciones y limitaciones

Almacenes es autoridad de existencias y costo; RH de areas, puestos y trabajadores; Administracion de unidades y folios. Produccion conserva snapshots y no escribe schemas ajenos.

La reserva y la salida son hechos distintos: liberar la orden aparta material y reduce la disponibilidad, pero no la existencia fisica. La primera entrada a **En produccion** confirma el inicio operativo: Produccion solicita consumir cada reserva y Almacenes crea una salida inmutable en el almacen que la otorgo. Si una orden pausada se reanuda o vuelve desde validacion, no se genera otra salida. El cierre tampoco vuelve a descontar; consolida materiales ya consumidos. Cancelar antes de iniciar libera lo apartado, mientras que cancelar despues conserva el Kardex real. No registre salidas manuales duplicadas.

Cuando la orden llega a **Terminada**, queda disponible en **Almacenes > Movimientos > Entradas de produccion terminada**. El almacenista valida la recepcion fisica total o parcial; Almacenes registra la entrada contra el articulo terminado vinculado. Su permiso solo obtiene una proyeccion de recepcion con folio, producto, cantidad, unidad y costo unitario: no expone receta, recursos, responsables ni costos totales de Produccion. Produccion no escribe existencias ni da por recibido automaticamente lo que aun no fue contado. La recepcion de merma permanece pendiente.

## Cobertura

Revisado con especialistas de Produccion, Almacenes y Ventas. Promocion a QA y pruebas de carga quedan pendientes del proceso gobernado.
