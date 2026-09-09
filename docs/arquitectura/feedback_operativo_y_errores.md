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
