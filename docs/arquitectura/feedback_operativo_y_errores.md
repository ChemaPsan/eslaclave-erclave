# Feedback operativo y errores

## Objetivo

Toda respuesta visible debe explicar qué ocurrió, si hubo un cambio real y qué puede hacer la persona a continuación. El idioma de la interfaz gobierna el feedback; el texto diagnóstico de una API nunca es la fuente directa de copy.

## Contrato transversal

- El backend mantiene `error.code` como identificador estable, `message` como diagnóstico, `details` como contexto estructurado y `correlation_id` como referencia de soporte.
- El frontend resuelve `error.code` en un catálogo ES/EN. Si el código no tiene copy específico, usa una categoría localizada derivada de código y HTTP, nunca traduce ni muestra el mensaje técnico.
- Errores inesperados, de red o `5xx` muestran `correlation_id` cuando existe. URLs, trazas, correos internos, tokens y detalles de infraestructura no se presentan al usuario.
- `detail` de validación FastAPI se normaliza a la misma envoltura en el cliente. La lista técnica puede conservarse para diagnóstico, pero el usuario recibe una instrucción localizada.
- Un fallo de mutación no modifica visualmente el estado confirmado. Selectores y tarjetas se restauran o recargan desde la proyección autoritativa antes de permitir otro intento.

## Taxonomía visible

| Tipo | Presentación | Persistencia | Contenido mínimo |
|---|---|---|---|
| Validación de captura | Bloque dentro del formulario, `role=alert` y foco | Hasta corregir | Campo o requisito y forma de corregirlo |
| Bloqueo de negocio | Warning ámbar | 6 segundos o dentro del flujo | Qué no cambió, precondición pendiente y siguiente acción |
| Conciliación/degradación | Warning ámbar | Visible junto al registro | Qué sí ocurrió, qué quedó pendiente y cómo conciliar |
| Acceso | Error visible | 8 segundos o pantalla bloqueada | Acción denegada y a quién solicitar permiso |
| Técnico o resultado incierto | Error rojo | 8 segundos | No confirmar éxito, pedir recarga y mostrar referencia de soporte |
| Éxito | Confirmación verde | 3.2 segundos | Resultado confirmado, sin detalles técnicos |

Los toasts informativos usan `role=status`/`aria-live=polite`; los errores usan `role=alert`/`aria-live=assertive`. El color complementa el texto y no es el único indicador.

## Validación de formularios

Este contrato es obligatorio para capturas de todos los módulos implementados y futuros, incluidas partidas, asistentes, formularios inline y Backoffice. La guía de ejecución es `.agents/skills/erclave-form-feedback/SKILL.md`. Estas exigencias describen el criterio de aceptación; no constituyen evidencia de que un formulario haya sido probado o desplegado.

- Conservar la respuesta estructurada hasta el manejador del formulario. Resolver el mensaje por código estable, tipo de validación y metadatos permitidos; no derivar causas ni campos desde `error.message` o texto libre.
- Vincular rutas exactas del payload con controles mediante su nombre o un mapa explícito del formulario. Normalizar prefijos conocidos del transporte conservando nombres e índices: un error en `items[1].quantity` corresponde a la segunda partida. Campos anidados, aliases y lookups con ID oculto requieren resolver el control visible correcto; no elegir por coincidencia parcial o por la primera fila.
- Mostrar junto al control el requisito y su corrección en ES/EN. Usar indicador textual/visual, `aria-invalid` y `aria-describedby` preservando ayudas existentes. El resumen permite navegar a errores resolubles; el foco se dirige al primer control inválido visible y habilitado o, si no existe, al resumen accesible.
- Limpiar las marcas propias al corregir o reiniciar el formulario sin eliminar ayudas ajenas. Un nuevo rechazo no duplica mensajes ni referencias ARIA.
- Un error no asociado con certeza permanece en el resumen con una siguiente acción segura. Nunca afirmar que hay campos marcados si no los hay. Un fallo técnico, falta de permiso o conflicto no equivale a captura incorrecta; no atribuir culpa al usuario ni mostrar detalles internos.
- Conservar captura, selecciones y partidas al rechazar. No cerrar ni resetear el formulario, anunciar éxito o duplicar envíos en el camino de error. Restaurar el estado operativo confirmado cuando la interacción haya sido optimista.
- Respetar campos condicionales y `hidden` también en CSS computado. No enfocar ni exigir controles ocultos o deshabilitados; si el requisito se resuelve en otra pantalla, explicar la acción correspondiente.

## Evidencia de formularios

Cada cambio de formularios debe incluir pruebas negativas conductuales de sus recorridos afectados. Si cambia el mecanismo compartido, inventariar y comprobar los consumidores de Administración, Producción, Almacenes, Compras, Ventas, RH y Mantenimiento, más Backoffice y módulos futuros que lo consuman. La matriz registra formulario, escenario, idioma, entorno, tipo de respuesta (real o simulada), resultado y pendientes.

Cubrir validación local y de servidor, varios campos, rutas anidadas y partidas distintas de la primera, código de negocio conocido, ruta/código desconocido, permiso y red/5xx. Comprobar campo señalado, instrucciones, foco, asociaciones ARIA, conservación de valores, limpieza tras corregir, estado condicional y ausencia de éxito o doble envío. Verificar paridad ES/EN y visibilidad computada en navegador.

`npm run validate:error-feedback` y `npm run verify` son controles necesarios; un chequeo estático de cadenas o probar el helper aislado no demuestra que todos los formularios sean corregibles. Distinguir cobertura automatizada, integración con API y UAT. Registrar explícitamente recorridos no ejecutados; no declarar validación total con pendientes ni confundir evidencia Local con QA.

## Copy accionable

El patrón recomendado es: **resultado + causa operativa + siguiente paso**.

- Correcto: “No se cambió el estatus: la orden no admite esa transición desde su estado actual. Recarga y completa primero los requisitos pendientes.”
- Incorrecto: “Invalid order transition”, “Error”, “409” o el texto literal enviado por el servicio.

## Guardrail

`npm run validate:error-feedback` exige catálogo crítico ES/EN, normalización de red/FastAPI, correlación, severidades, accesibilidad, escape HTML y restauración de los controles de estatus más sensibles. Todo módulo nuevo debe integrarse al resolvedor compartido y agregar sus códigos de negocio relevantes.

## Alcance vigente

CHG-251 aplica este patrón en el cliente compartido, Backoffice, errores de carga y transiciones sensibles de Producción, Ventas, Compras y Mantenimiento. No modifica contratos HTTP. La estandarización backend de validaciones no canónicas, `500` inesperados y propagación de correlación entre servicios permanece pendiente.


## Flujo operativo Local CHG-265

CHG-265 añade guía por error.code y details.workflow/requested_status para transiciones: requisito faltante, responsable y pantalla. La respuesta conserva estado confirmado. Mensajes cubren salidas productivas y refacciones de CHG-263/264, recepción/aceptación/entrega, transferencias, devoluciones, máquinas, RH y recuperación. Conciliación pendiente distingue movimiento físico ya registrado del paso pendiente en el documento; reintentar no pide repetir entrega.

CHG-265 vigente en Local: Compras prepara recepciones pendientes; Almacén confirma bienes en Movimientos y el solicitante original acepta servicios comprados (comprador si la compra fue directa). Ventas prepara entregas y Almacén registra la salida. Las transferencias quedan en tránsito hasta recepción en destino, con recepción parcial y retorno confirmado en origen. Producción y Mantenimiento solicitan devolución de sobrantes de órdenes terminadas/canceladas; Almacén recibe y cada propietario registra su ajuste de costo. Se preserva la salida original. Inicio/reanudación revalida responsables RH y bloqueos de máquinas. Los errores ES/EN indican requisito, responsable y pantalla. Detalle contractual y evidencia: `docs/auditorias/flujos_almacen_mensajes_2026-09-08.md`.


## Recuperación de refacciones Local CHG-268

CHG-268 recupera reservas/cancelaciones de refacciones interrumpidas bajo locks por tenant/orden/solicitud y conserva claves Inventory. Corrige serialización Decimal; Mantenimiento ofrece reintento ES/EN con permiso propio, Almacén confirma la entrega por separado. MTO-000001 recuperada en Local: una reserva de 1 H87, existencia física 2, disponible 1, sin salida ni duplicados. Sin migraciones ni permisos nuevos. Detalle: `docs/auditorias/recuperacion_refacciones_2026-09-08.md`.


## Formularios Local CHG-272

El helper `frontend/features/form-feedback.js`, sus bindings y estilos compartidos resuelven errores de captura en los siete módulos implementados y Backoffice. Se conserva el objeto estructurado, la captura y el formulario propietario; se enlazan rutas explícitas a controles visibles y se evita marcar valores editados después de enviar. Las equivalencias literales de schemas legados se limitan a `VALIDATION_RULES`, verificadas contra el código; no se muestran diagnósticos libres.

Aplicar `.agents/skills/erclave-form-feedback/SKILL.md` y ejecutar `validate:form-feedback` y `test:form-feedback` además de los controles anteriores. El workflow prepara esta suite sin DB; no se ha ejecutado CI remoto en este corte. Inventario, pruebas, límites y APIs consumidas: `docs/auditorias/formularios_feedback_2026-09-13.md`. Solo Local: los manuales CHG-271 y QA no se actualizan por esta implementación.
