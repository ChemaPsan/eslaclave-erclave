# Auditoria del segundo corte de Ventas

Fecha: 2026-08-18.

Ambiente auditado: Local aislado. QA y Produccion no fueron modificados.

## Veredicto

La auditoria CHG-203 detecto bloqueadores reales y su plan de correccion fue aplicado en Local por CHG-204, revision `20260818_0020`. El segundo corte ya cuenta con alta operable de Entregas, integridad producto-articulo, sanitizacion comercial, reservas de cantidad concurrentes, estados durables de orquestacion y costo real con fuente explicita. No se promovio a QA: object storage para logos, pruebas del candidato inmutable y los gates normales de release siguen siendo requisitos de ambiente.

## Evidencia aprobada

- `npm.cmd run verify`: validadores, compilacion y `173 passed, 6 skipped`.
- Pruebas Sales con PostgreSQL Local: `11 passed`.
- OpenAPI parseable y rutas `implemented` presentes en FastAPI.
- Tenant, permisos, maquinas de estado, calculos decimales, snapshots, catalogos comerciales y plantilla documental existen.
- El happy path de servicio convierte cotizacion aprobada, crea pedido, confirma entrega parcial y calcula costo snapshot.

Esta evidencia corresponde al momento de la auditoria. CHG-204 agrego pruebas negativas y concurrentes; su evidencia vigente se registra en `TRAZABILIDAD.md`.

## Cierre del plan CHG-203

- La UI expone alta de Entregas solo con `sales.delivery.create`, calcula saldo no entregado ni comprometido y captura costo unitario real para servicios.
- `production.product_services.inventory_item_ref_id` define el mapeo autoritativo uno a uno para productos. Production valida que el articulo exista, este activo y use la misma unidad; Sales revalida el mismo ID antes de reservar y conserva ID, codigo y nombre snapshot.
- Surtido, cancelacion y confirmacion reclaman primero estado durable bajo bloqueo. Las suboperaciones externas usan claves estables; una interrupcion queda en `needs_reconciliation` y el mismo payload reanuda sin crear una reserva, solicitud o consumo distinto.
- Crear Entregas bloquea Pedido y partidas y descuenta otros borradores, evitando comprometer dos veces el mismo saldo. Cancelacion y confirmacion no pueden reclamar simultaneamente el mismo Pedido.
- `stock` toma costo del consumo confirmado por Inventory; `service` exige captura operativa y usa `service_capture`; Production no se presenta como costo real mientras no reporte `production_report`.
- Clientes, Cotizaciones, Pedidos, Entregas y referencias cargan con `Promise.allSettled`: la falla de una autoridad conserva los documentos ya disponibles y bloquea solo la captura dependiente.
- Se escaparon textos y atributos comerciales en tarjetas, lookups, modales y Cotizacion imprimible. Los campos obligatorios rechazan espacios. La prueba original de RFC con `Ñ` estaba contaminada por la codificacion de la consola: el patron UTF-8 ya aceptaba `Ñ` y ahora existe una regresion automatica que lo demuestra.
- Permanecen fuera de este cierre la paginacion comercial mayor a 200, PDF de Pedido/Entrega, object storage del logo, devoluciones/facturacion y el callback de Production; son siguiente corte o gates de promocion, no fallbacks mock.

## Bloqueadores encontrados por CHG-203

Los apartados siguientes conservan la fotografia original para trazabilidad. Su resolucion funcional esta resumida arriba; no deben interpretarse como estado vigente.

### 1. Entregas no tiene alta operable desde la UI

`sales-service` implementa `POST /v1/sales/deliveries`, pero el panel visible mantiene deshabilitada la accion principal y `openGenericRecordModal` responde con un aviso de solo lectura. No existe actualmente un elemento renderizado con `data-action="register-sales-delivery"`; por ello un usuario no puede completar desde la interfaz el flujo que si existe por API.

Criterio de cierre: crear una entrega parcial o total desde un Pedido elegible, recargarla desde API, confirmarla/cancelarla segun permisos y mostrar sus cantidades/costos sin usar mock.

### 2. Orquestacion distribuida no protege todos los reintentos y carreras

- Cancelar un Pedido libera reservas en Inventory antes de que Sales bloquee y valide la transicion. Un Pedido parcialmente entregado puede perder reservas externas aunque Sales rechace despues la cancelacion.
- Confirmar una Entrega consume Inventory antes de reclamar durablemente el comando en Sales. Tras una falla parcial, repetir con otra clave puede producir consumo adicional o dejar Sales e Inventory divergentes.
- Dos Entregas borrador pueden comprometer el mismo saldo porque crear el borrador no bloquea ni aparta cantidad pendiente; las confirmaciones tampoco serializan la partida del Pedido antes del efecto externo.
- Reconfigurar una partida nuevamente en modo `stock` crea reservas nuevas y elimina referencias locales anteriores sin liberar necesariamente las reservas externas previas.
- Una solicitud a Production creada antes de fallar la persistencia de Sales no tiene compensacion ni reconciliacion documentada.

Criterio de cierre: estado durable de orquestacion, locks por Pedido/partida, idempotencia ligada a actor/comando origen, compensaciones o reconciliacion verificable y pruebas de falla inyectada/concurrencia.

### 3. Falta identidad autoritativa Producto de Ventas -> Articulo de Inventory

La UI permite elegir cualquier articulo y almacen para una partida de producto. Inventory valida articulo, unidad y existencia, pero no existe una relacion autoritativa que demuestre que el articulo reservado corresponde al `product_service_id` vendido. Dos maestros con la misma unidad pueden cruzarse incorrectamente.

Criterio de cierre: definir ownership del mapeo estable, revalidarlo en backend al reservar y guardar ambos IDs/snapshots auditables.

### 4. Contenido comercial sin escape consistente

Tarjetas y vista imprimible de Cotizacion interpolan en `innerHTML` nombres, notas, unidades y otros valores provenientes de datos editables sin aplicar consistentemente `escapeHtml`/`escapeAttribute`. Esto permite HTML almacenado y potencial XSS en la interfaz o documento.

Criterio de cierre: escapar todo texto no confiable, limitar atributos a valores validados y agregar pruebas de payloads con HTML/script para tarjetas, modales y PDF.

## Hallazgos altos

### 5. “Costo real” no tiene el mismo significado en todos los modos

Inventory aporta costo de consumo para partidas `stock`. En servicios, `actual_cost` reutiliza `standard_unit_cost_snapshot`; no existe captura de esfuerzo real. Production aun no convierte su solicitud en partida entregable ni devuelve costo real. La interfaz y documentacion deben distinguir costo de consumo, costo estandar usado como proxy y costo pendiente.

### 6. Una falla de catalogos puede ocultar lecturas comerciales

La UI invoca Clientes, Cotizaciones, Pedidos, Entregas y `reference-data` en un mismo `Promise.all`. Como solicita referencias incluso para lectores, una falla de Admin puede llevar todo `salesApi` a error, contrario a la regla documentada de conservar las lecturas y bloquear solo la mutacion dependiente.

### 7. Validaciones de texto obligatorio y RFC incompletas

Las restricciones `min_length` se evalúan antes de algunos `strip()`: nombre comercial, nombre de contacto y telefono aceptaron solo espacios y terminaron como cadena vacia. La expresion de RFC contiene una codificacion incorrecta para `Ñ`; un RFC sintacticamente valido con esa letra fue rechazado.

## Hallazgos medios

- Formularios API de Pedido y Entrega muestran campos de estado, modo, responsable o proxima fecha que el payload ignora; generan expectativas falsas.
- Acciones de Pedido no reflejan completamente permisos: el alta/edicion puede mostrarse a lectores aunque backend rechace correctamente.
- La UI de surtido vuelve a incluir partidas ya configuradas o parcialmente entregadas y no conserva el modo seleccionado; dificulta configuracion incremental.
- El OpenAPI de Admin omitia varios permisos alternativos que el runtime acepta para leer catalogos comerciales.
- Faltan pruebas end-to-end de `stock`, permisos por cada comando, catalogos/plantilla, XSS, concurrencia de entregas y fallas entre servicios.
- Las listas Sales estan limitadas a 200 sin cursor; debe resolverse antes de volumen productivo.

## Plantilla documental

La configuracion tenant-safe valida colores y restringe el logo Local a PNG/JPEG/WebP data URL. Cotizaciones y Ordenes de Produccion la consumen. Pedidos, remisiones/Entregas y documentos futuros aun no tienen generador PDF; esto permanece contemplado, no implementado. Antes de QA el logo requiere object storage y una politica de snapshot documental.

## Orden recomendado de correccion

1. Sanitizacion/XSS y validaciones fundamentales.
2. Locks, orquestacion durable, reintentos y reconciliacion Sales-Inventory-Production.
3. Mapeo autoritativo producto-articulo.
4. Alta de Entregas y permisos/semantica real de formularios.
5. Semantica de costo real por modo y callback de Production.
6. Resiliencia de lecturas, pruebas negativas/concurrentes y paginacion.
