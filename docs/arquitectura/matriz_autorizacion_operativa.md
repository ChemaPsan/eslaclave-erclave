# Matriz de autorizacion operativa

Ultima revision: 2026-08-24. Estado: implementado solo en Local.

## Regla transversal

Cada aprobacion, aceptacion o transicion con significado de negocio se autoriza mediante un permiso puntual asignable a roles del tenant. La interfaz solo presenta la accion autorizada, pero el backend vuelve a resolver el permiso exacto a partir de la transicion solicitada. Tener otro permiso del mismo flujo no autoriza la accion. La membresia del usuario hereda los permisos de sus roles mediante `admin-service /v1/session/context`.

No se codifican nombres de puestos como politica IAM. Un tenant puede asignar, por ejemplo, `production.order.complete` al rol Gerente de Produccion e `inventory.finished_goods_receipt.receive` al rol Almacenista sin cambiar los servicios.

## Produccion

| Accion | Permiso |
|---|---|
| Validar, reservar y liberar una orden nueva | `production.order.release` |
| Declarar espera de recursos | `production.order.wait_resources` |
| Iniciar por primera vez | `production.order.start` |
| Pausar / reanudar | `production.order.pause` / `production.order.resume` |
| Enviar a validacion / finalizar | `production.order.send_to_validation` / `production.order.complete` |
| Cancelar | `production.order.cancel` |
| Reiniciar, actualizar, terminar, bloquear u omitir una etapa | `production.order_stage.reset`, `.update`, `.complete`, `.block`, `.skip` |

En el dominio vigente no existe borrador de orden: `POST /v1/production/orders` valida recursos, reserva materiales y nace `released`; por eso exige liberar y no el permiso historico generico de crear. Separar captura de borrador y liberacion queda fuera de este corte.

## Mantenimiento

El comando de transiciones exige el permiso correspondiente a `request`, `assign`, `start`, `wait_for_parts`, `resume`, `resolve`, `close`, `reopen` o `cancel` bajo `maintenance.order.*`. Conciliar conserva `maintenance.order.reconcile`. Solicitar refacciones, cancelarlas, conciliarlas y capturar tiempo mantienen permisos independientes.

## Almacenes

Consultar recepciones de producto terminado exige `inventory.finished_goods_receipt.read`; confirmar la recepcion fisica exige `inventory.finished_goods_receipt.receive`. Este ultimo no se obtiene por `inventory.movement.create`. Produccion publica `/v1/production/finished-goods-candidates[/{id}]`: solo folio, producto vinculado, cantidad, unidad, estado terminado y costo unitario requerido para valuacion. Receta, recursos, responsables y costos totales permanecen protegidos por los permisos de Produccion.

## Flujos ya granulares auditados

Compras ya separa enviar, aprobar, rechazar y cancelar requisiciones; emitir/cancelar ordenes; recibir y conciliar. Ventas ya separa emitir, aprobar, vencer y cancelar cotizaciones; surtir/cancelar pedidos; confirmar/cancelar entregas. Recetas ya separa enviar, aprobar y volver obsoleta una version. Esos contratos no requirieron cambio.

## Administracion

Los permisos se derivan de OpenAPI, se sincronizan con el catalogo Admin y son asignables desde **Administracion > Roles > Permisos** cuando el modulo correspondiente esta activo. Los permisos genericos retirados dejan de producir autorizacion; no se convierten automaticamente en todos los permisos nuevos para evitar escalar privilegios silenciosamente.
