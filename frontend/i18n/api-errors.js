import { FORM_BUSINESS_ERRORS } from "./form-business-errors.js";
const TRANSITION_GUIDANCE = {
  "production_order": {
    "in_progress": {
      "es": "Para iniciar o reanudar, la orden debe estar Liberada, En espera de recursos o Pausada. Producción debe revisar la orden; Almacén debe confirmar antes la salida de materiales en Movimientos.",
      "en": "To start or resume, the order must be Released, Waiting for resources, or Paused. Production must review the order; Warehouse must first confirm material issue in Movements."
    },
    "in_validation": {
      "es": "Solo una orden en producción puede pasar a validación. Producción debe completar todas sus fases al 100% y después enviarla a validación desde Órdenes.",
      "en": "Only an in-progress order can move to validation. Production must complete every phase at 100%, then send it to validation from Orders."
    },
    "completed": {
      "es": "Primero envía la orden a Validación. Producción debe completar sus fases y verificar sus materiales; después puede seleccionar Terminar en Órdenes.",
      "en": "First send the order to Validation. Production must complete its phases and verify its materials, then select Complete in Orders."
    },
    "paused": {
      "es": "Solo se puede pausar una orden que esté en producción. Revisa su estatus confirmado en Producción → Órdenes.",
      "en": "Only an in-progress order can be paused. Check its confirmed status in Production → Orders."
    },
    "released": {
      "es": "Una orden nueva se libera validando receta, responsables y recursos desde Crear orden. Las órdenes terminadas o canceladas conservan su historial; crea una orden nueva para otro trabajo.",
      "en": "A new order is released by validating its recipe, owners, and resources in Create order. Completed or cancelled orders retain their history; create a new order for additional work."
    },
    "waiting_resources": {
      "es": "Solo una orden liberada puede ponerse en espera de recursos. Revisa su estatus en Producción → Órdenes; si ya trabaja, utiliza Pausar.",
      "en": "Only a released order can wait for resources. Check its status in Production → Orders; if it is running, use Pause."
    },
    "cancelled": {
      "es": "La cancelación se solicita desde Producción → Órdenes mientras la orden está liberada, esperando recursos, en producción o pausada. Una orden terminada conserva su historial; sus sobrantes se tramitan como devolución.",
      "en": "Cancellation is requested in Production → Orders while the order is released, waiting for resources, in progress, or paused. A completed order retains its history; unused materials require a return."
    }
  },
  "requisition": {
    "submitted": {
      "es": "Solo se envía una requisición en Borrador. El solicitante debe completar sus partidas en Compras → Requisiciones y seleccionar Enviar.",
      "en": "Only a Draft requisition can be submitted. The requester must complete its lines in Purchasing → Requisitions and select Submit."
    },
    "approved": {
      "es": "Primero el solicitante debe Enviar la requisición. Después una persona con permiso de aprobación podrá autorizarla en Compras → Requisiciones.",
      "en": "The requester must Submit the requisition first. A person with approval permission can then authorize it in Purchasing → Requisitions."
    },
    "rejected": {
      "es": "Solo se rechaza una requisición Enviada, indicando el motivo. Revisa la solicitud en Compras → Requisiciones antes de continuar.",
      "en": "Only a Submitted requisition can be rejected, with a reason. Review it in Purchasing → Requisitions before continuing."
    }
  },
  "recipe": {
    "submit": {
      "es": "Solo una versión en Borrador se envía a revisión. Completa sus recursos y fases en Producción → Recetas y selecciona Enviar a revisión.",
      "en": "Only a Draft version can be submitted for review. Complete its resources and phases in Production → Recipes, then select Submit for review."
    },
    "approve": {
      "es": "Primero envía la versión de receta a Revisión. Después una persona con permiso de aprobación podrá autorizarla en Producción → Recetas.",
      "en": "First submit the recipe version for Review. A person with approval permission can then authorize it in Production → Recipes."
    }
  },
  "maintenance": {
    "request": {
      "es": "Primero crea la orden en Borrador y revisa el equipo. Después selecciona Solicitar en Mantenimiento → Órdenes para registrar el paro cuando corresponda.",
      "en": "First create the Draft order and check the equipment. Then select Request in Maintenance → Orders to record downtime when applicable."
    },
    "assign": {
      "es": "La orden debe estar solicitada antes de asignar un técnico. Revisa la solicitud y selecciona un trabajador habilitado en Mantenimiento → Órdenes.",
      "en": "The order must be requested before assigning a technician. Review the request and select an eligible worker in Maintenance → Orders."
    },
    "start": {
      "es": "Primero asigna un técnico habilitado a la orden solicitada. Después podrá iniciarse o retomarse desde Mantenimiento → Órdenes.",
      "en": "First assign an eligible technician to the requested order. It can then be started or resumed in Maintenance → Orders."
    },
    "resolve": {
      "es": "El técnico debe iniciar el mantenimiento y registrar trabajo, verificación y tiempo. Almacén debe confirmar las refacciones solicitadas; después puede seleccionar Resolver.",
      "en": "The technician must start maintenance and record work, verification, and time. Warehouse must confirm requested spare parts; then Resolve can be selected."
    },
    "close": {
      "es": "Primero el técnico debe Resolver la orden con su evidencia y refacciones conciliadas. Después puede cerrarse en Mantenimiento → Órdenes.",
      "en": "The technician must first Resolve the order with evidence and reconciled spare parts. It can then be closed in Maintenance → Orders."
    },
    "reopen": {
      "es": "Solo una orden Resuelta puede reabrirse. Revisa su estatus en Mantenimiento → Órdenes; una orden Cerrada conserva su historial.",
      "en": "Only a Resolved order can be reopened. Review its status in Maintenance → Orders; a Closed order retains its history."
    },
    "cancel": {
      "es": "Revisa el estatus confirmado de la orden en Mantenimiento → Órdenes. Las refacciones pendientes deben cancelarse; las entregadas se tramitan como devolución física.",
      "en": "Check the confirmed order status in Maintenance → Orders. Pending spare parts must be cancelled; issued parts require a physical return."
    },
    "resume": {
      "es": "Solo se reanuda una orden En espera de refacciones. Confirma con Almacén la entrega pendiente y selecciona Reanudar en Mantenimiento → Órdenes.",
      "en": "Only an order Waiting for parts can be resumed. Confirm the pending issue with Warehouse and select Resume in Maintenance → Orders."
    },
    "wait_for_parts": {
      "es": "Primero inicia la orden de mantenimiento asignada. Mientras esté En ejecución podrás ponerla En espera de refacciones y solicitar las piezas.",
      "en": "First start the assigned maintenance order. While In progress, it can be placed Waiting for parts and the parts requested."
    }
  },
  "sales_service": {
    "start": {
      "es": "Primero Planea la orden y Asigna un responsable activo. Después selecciona Iniciar en Ventas → Órdenes de servicio.",
      "en": "First Plan the order and Assign an active owner. Then select Start in Sales → Service orders."
    },
    "resume": {
      "es": "Solo se reanuda una orden En espera. Revisa el responsable y su estatus en Ventas → Órdenes de servicio y selecciona Reanudar.",
      "en": "Only an On hold order can be resumed. Check its owner and status in Sales → Service orders, then select Resume."
    },
    "wait": {
      "es": "Solo una orden En ejecución puede ponerse En espera. Revisa su estatus y registra el motivo en Ventas → Órdenes de servicio.",
      "en": "Only an In progress order can be placed On hold. Check its status and record the reason in Sales → Service orders."
    },
    "submit_acceptance": {
      "es": "Primero inicia la ejecución del servicio y registra evidencia y tiempo o costos. Después selecciona Enviar a aceptación en la orden de servicio.",
      "en": "First start the service and record evidence and time or costs. Then select Submit for acceptance on the service order."
    },
    "accept": {
      "es": "Primero envía el servicio a Aceptación con evidencia y tiempo o costos registrados. Después la persona autorizada podrá Aceptar la orden.",
      "en": "First submit the service for Acceptance with evidence and time or costs recorded. The authorized person can then Accept the order."
    }
  }
};
const ERROR_MESSAGES = Object.freeze({
  ...FORM_BUSINESS_ERRORS,
  material_return_not_cancellable: {"es": "La devolución ya fue recibida físicamente y no puede cancelarse. Almacén debe finalizar su conciliación en Movimientos si sigue pendiente.", "en": "The return has already been physically received and cannot be cancelled. Warehouse must finish reconciliation in Movements if it is still pending."},
  material_return_not_receivable: {"es": "La solicitud de devolución está cancelada. Revisa el sobrante real y solicita una nueva devolución desde la orden si todavía corresponde.", "en": "The return request is cancelled. Review the actual unused materials and request a new return from the order if still needed."},
  material_return_not_found: {"es": "Esta devolución ya no está disponible en la empresa activa. Actualiza las devoluciones pendientes en Almacenes → Movimientos.", "en": "This return is unavailable in the active company. Refresh pending returns in Inventory → Movements."},
  material_return_dependency_unavailable: {"es": "No fue posible confirmar el paso con la orden de origen. Almacén debe actualizar Devoluciones en Movimientos y reintentar la conciliación; el sistema conserva cualquier entrada ya registrada.", "en": "The originating order could not confirm this step. Warehouse must refresh Returns in Movements and retry reconciliation; any recorded entry is preserved."},
  order_line_not_ready_for_delivery: {"es": "No se puede entregar esta partida: falta surtido confirmado. Ventas debe revisar el pedido y sus reservas en Pedidos. Las solicitudes pendientes de Producción aún no pueden pasar a entrega.", "en": "This line cannot be delivered: confirmed fulfillment is missing. Sales must review the order and its reservations in Orders. Pending Production requests cannot proceed to delivery yet."},
  material_return_terminal_order_required: {"es": "No se solicitó la devolución: primero termina o cancela la orden de producción, o resuelve/cancela el mantenimiento. Después solicita devolver el sobrante desde la orden; Almacén confirmará su entrada en Movimientos.", "en": "The return was not requested: first complete or cancel production, or resolve/cancel maintenance. Then request return of unused materials from the order; Warehouse confirms their entry in Movements."},
  material_return_quantity_exceeded: {"es": "La cantidad excede lo entregado que todavía puede devolverse. Revisa las devoluciones ya recibidas y las solicitudes pendientes en Movimientos antes de registrar otra.", "en": "The quantity exceeds issued materials still available for return. Review received returns and pending requests in Movements before recording another."},
  material_return_source_invalid: {"es": "No se identificó una salida de materiales de esta orden. Revisa la entrega confirmada por Almacén antes de solicitar la devolución.", "en": "An issued material movement for this order could not be identified. Review the Warehouse-confirmed issue before requesting a return."},
  material_return_receipt_required: {"es": "La devolución todavía no tiene una recepción física confirmada. Almacén debe recibirla desde Almacenes → Movimientos → Devoluciones de materiales por recibir.", "en": "The return has no confirmed physical receipt yet. Warehouse must receive it in Inventory → Movements → Material returns awaiting receipt."},
  production_creation_recovery_pending: {"es": "La orden no pudo crearse y quedaron reservas por recuperar. En Producción → Órdenes, usa Recuperar reservas en la sección de creaciones pendientes. Cuando termine, vuelve a crear la orden.", "en": "The order could not be created and reservations still need recovery. In Production → Orders, use Recover reservations in the pending creations section. Once complete, create the order again."},
  production_creation_attempt_failed: {"es": "Este intento de creación ya falló. Recupera sus reservas pendientes en Producción → Órdenes y abre nuevamente Crear orden para iniciar otro intento.", "en": "This creation attempt has already failed. Recover its pending reservations in Production → Orders, then reopen Create order to start a new attempt."},
  production_creation_recovery_not_allowed: {"es": "Solo quien intentó crear la orden puede recuperar sus reservas fallidas. Pide a esa persona usar Recuperar reservas en Producción → Órdenes. No se cancelan órdenes existentes.", "en": "Only the person who attempted to create the order can recover its failed reservations. Ask that person to use Recover reservations in Production → Orders. Existing orders are not cancelled."},
  production_creation_materials_already_issued: {"es": "Las reservas ya registran una salida física y no se pueden liberar automáticamente. Almacén debe revisar los movimientos vinculados antes de continuar con la recuperación.", "en": "The reservations already have a physical issue and cannot be released automatically. Warehouse must review the linked movements before continuing recovery."},

  sales_responsible_invalid: {"es": "No se continuó la operación: el responsable ya no está activo o su puesto no está habilitado. RH debe revisar el expediente en Recursos humanos → Trabajadores; después vuelve a Ventas e intenta nuevamente.", "en": "The operation did not continue: the owner is no longer active or their position is not enabled. HR must review the record in Human resources → Workers; then return to Sales and try again."},
  transfer_return_already_requested: {"es": "La devolución del saldo ya fue solicitada. Espera la recepción física y pide al almacén de origen confirmarla desde Transferencias en tránsito.", "en": "Return of the remainder was already requested. Wait for physical receipt and ask the origin warehouse to confirm it in Transfers in transit."},
  transfer_return_request_required: {"es": "Antes de recibir una devolución, el almacén destino debe solicitar el retorno del saldo en Transferencias en tránsito. Después el origen podrá confirmar lo recibido.", "en": "Before receiving a return, the destination must request return of the remainder in Transfers in transit. The origin can then confirm receipt."},
  transfer_return_in_progress: {"es": "No se recibió en destino: ya se solicitó devolver el saldo al origen. El almacén de origen debe confirmar la devolución cuando reciba los bienes.", "en": "Destination receipt was not recorded: return of the remainder was already requested. The origin warehouse must confirm the return when the goods arrive."},
  transfer_already_completed: {"es": "La transferencia ya no tiene saldo en tránsito. Actualiza Movimientos para consultar las recepciones o devoluciones confirmadas.", "en": "The transfer has no remaining quantity in transit. Refresh Movements to review confirmed receipts or returns."},
  transfer_receipt_quantity_exceeded: {"es": "No se registró la recepción: indica una cantidad mayor a cero que no exceda el saldo en tránsito. Actualiza la transferencia para consultar el saldo y registra solo lo que llegó.", "en": "The receipt was not recorded: enter a positive quantity no greater than the quantity still in transit. Refresh the transfer to check the balance and record only what arrived."},
  transfer_receiving_warehouse_required: {"es": "No se registró la recepción: debe confirmarse en el almacén indicado como destino. Para una devolución, debe confirmar el almacén de origen. Actualiza la transferencia y revisa ambos almacenes.", "en": "The receipt was not recorded: it must be confirmed at the designated destination. For a return, the origin warehouse must confirm. Refresh the transfer and check both warehouses."},
  transfer_requires_receipt_or_return: {"es": "No se revirtió la transferencia: los bienes salieron del origen. Continúa en Almacenes → Movimientos → Transferencias en tránsito; el destino confirma la recepción o solicita devolver el saldo, y el origen confirma la devolución al recibirla.", "en": "The transfer was not reversed: the goods left the origin. Continue in Inventory → Movements → Transfers in transit; the destination confirms receipt or requests return of the remainder, and the origin confirms the return when received."},
  movement_already_reversed: {"es": "El movimiento ya fue revertido. Actualiza Movimientos para consultar la corrección registrada; no necesitas repetirla.", "en": "The movement was already reversed. Refresh Movements to view the recorded correction; you do not need to repeat it."},
  reversal_cannot_be_reversed: {"es": "Esta corrección ya compensa otro movimiento y no puede volver a revertirse. Revisa el movimiento original y registra una corrección nueva con Almacén si corresponde.", "en": "This correction already compensates another movement and cannot be reversed again. Review the original movement and record a new correction with Warehouse if appropriate."},
  linked_movement_requires_return: {"es": "No se revirtió el movimiento porque está vinculado a una orden. Para sobrantes de Producción o Mantenimiento, solicita la devolución desde Órdenes y pide a Almacén recibirla en Movimientos. Para compras o ventas, solicita revisión del documento: la devolución comercial aún no está disponible.", "en": "The movement was not reversed because it is linked to an order. For unused Production or Maintenance materials, request a return from Orders and ask Warehouse to receive it in Movements. For purchases or sales, request a document review: commercial returns are not yet available."},
  sales_warehouse_dispatch_required: {"es": "La entrega sigue pendiente de salida. Almacén debe ir a Almacenes → Movimientos → Salidas de pedidos de venta y confirmar la entrega física de los productos. Después Ventas mostrará el pedido actualizado.", "en": "The delivery is awaiting dispatch. Warehouse must go to Inventory → Movements → Sales order dispatches and confirm the physical product handoff. Sales will then show the updated order."},
  purchased_service_requester_required: {"es": "No se aceptó el servicio: debe confirmarlo quien creó la requisición. Si fue una compra directa, lo confirma quien creó la orden de compra. Esa persona encontrará la tarea en Compras → Requisiciones u Órdenes de compra.", "en": "The service was not accepted: the requisition creator must confirm it. For a direct purchase, the purchase order creator confirms it. That person will find the task in Purchasing → Requisitions or Purchase orders."},
  purchase_warehouse_receipt_required: {"es": "La recepción sigue pendiente. Almacén debe ir a Almacenes → Movimientos → Recepciones de compras pendientes y confirmar los bienes recibidos. Compras prepara la solicitud; los servicios los acepta el solicitante en Compras.", "en": "The receipt is still pending. Warehouse must go to Inventory → Movements → Pending purchase receipts and confirm the goods received. Purchasing prepares the request; services are accepted by their requester in Purchasing."},
  production_execution_worker_not_eligible: {"es": "No se inició ni reanudó la orden: el responsable o un encargado de fase ya no está habilitado para producción. RH debe revisar que el trabajador y su puesto estén activos y sean elegibles en Recursos humanos → Trabajadores; después vuelve a intentar.", "en": "The order was not started or resumed: the owner or a phase assignee is no longer eligible for production. HR must check the worker and position are active and eligible in Human resources → Workers, then try again."},
  production_machine_unavailable: {"es": "No se inició ni reanudó la orden: una máquina asignada está inactiva. Producción debe revisar su disponibilidad en Maquinaria antes de volver a intentar.", "en": "The order was not started or resumed: an assigned machine is inactive. Production must review its availability in Machinery before trying again."},
  machine_maintenance_release_required: {"es": "No se cambió la máquina: tiene un mantenimiento abierto. Mantenimiento debe resolver o cancelar esa orden para liberarla. Después podrás cambiar su estatus desde Producción → Maquinaria.", "en": "The machine was not changed: it has an open maintenance order. Maintenance must resolve or cancel that order to release it. You can then change its status in Production → Machinery."},
  production_machine_maintenance_required: {"es": "No se inició ni reanudó la orden: una máquina sigue bloqueada por Mantenimiento. Pide a Mantenimiento resolver la orden y liberar la máquina; después vuelve a Producción → Órdenes para iniciar o reanudar.", "en": "The order was not started or resumed: a machine is still blocked by Maintenance. Ask Maintenance to resolve its order and release the machine, then return to Production → Orders to start or resume."},
  network_unavailable: {
    es: "No pudimos comunicarnos con {service}. Comprueba que el servicio esté disponible y vuelve a intentar.",
    en: "We could not reach {service}. Check that the service is available and try again."
  },
  request_timeout: {
    es: "La operación tardó demasiado y no pudimos confirmar el resultado. Recarga la información antes de volver a intentar.",
    en: "The operation took too long and we could not confirm the result. Reload the information before trying again."
  },
  rate_limit_exceeded: {
    es: "Se alcanzó el límite temporal de solicitudes. Espera unos minutos antes de volver a intentar.",
    en: "The temporary request limit was reached. Wait a few minutes before trying again."
  },
  auth_required: {
    es: "Tu sesión ya no está disponible. Inicia sesión nuevamente antes de continuar.",
    en: "Your session is no longer available. Sign in again before continuing."
  },
  firebase_auth_required: {
    es: "Inicia sesión con una cuenta autorizada antes de continuar.",
    en: "Sign in with an authorized account before continuing."
  },
  invalid_token: {
    es: "Tu sesión dejó de ser válida. Inicia sesión nuevamente.",
    en: "Your session is no longer valid. Sign in again."
  },
  tenant_required: {
    es: "No se pudo identificar la empresa activa. Recarga la sesión y selecciona una sucursal antes de continuar.",
    en: "The active organization could not be identified. Reload the session and select a branch before continuing."
  },
  tenant_access_denied: {
    es: "Tu usuario no tiene acceso a la empresa seleccionada. Cambia de empresa o solicita acceso al administrador.",
    en: "Your user does not have access to the selected organization. Switch organizations or ask an administrator for access."
  },
  permission_denied: {
    es: "No tienes permiso para realizar esta acción. Solicita al administrador el permiso correspondiente.",
    en: "You do not have permission to perform this action. Ask an administrator for the required permission."
  },
  authorization_denied: {
    es: "No fue posible confirmar tu autorización. Recarga la sesión; si continúa, solicita acceso al administrador.",
    en: "Your authorization could not be confirmed. Reload the session; if it continues, ask an administrator for access."
  },
  module_not_enabled: {
    es: "Este módulo no está activo para la empresa. Actívalo en Administración o solicita ayuda al administrador.",
    en: "This module is not active for the organization. Enable it in Administration or ask an administrator for help."
  },
  module_not_contracted: {
    es: "Este módulo no está habilitado en el plan de la empresa. Solicita su habilitación en Backoffice.",
    en: "This module is not enabled in the organization's plan. Request enablement in Backoffice."
  },
  module_not_implemented: {
    es: "Esta función todavía no está disponible. No se realizó ningún cambio.",
    en: "This feature is not available yet. No changes were made."
  },
  idempotency_key_reused: {
    es: "La operación ya se utilizó con información diferente. Recarga los datos e inicia la acción nuevamente.",
    en: "This operation was already used with different information. Reload the data and start the action again."
  },
  idempotency_request_in_progress: {
    es: "La misma operación sigue en proceso. Espera y recarga antes de volver a intentar.",
    en: "The same operation is still in progress. Wait and reload before trying again."
  },
  command_in_progress: {
    es: "La operación todavía está en proceso. Recarga el registro para confirmar su resultado antes de repetirla.",
    en: "The operation is still in progress. Reload the record to confirm its result before repeating it."
  },
  invalid_order_transition: {
    es: "No se cambió el estatus: la orden no admite esa transición desde su estado actual. Recarga y completa primero los requisitos pendientes.",
    en: "Status was not changed: the order does not allow that transition from its current state. Reload and complete the pending requirements first."
  },
  invalid_status_transition: {
    es: "No se cambió el estatus porque el registro no admite esa transición desde su estado actual. Recarga la información y revisa el flujo.",
    en: "Status was not changed because the record does not allow that transition from its current state. Reload the information and review the workflow."
  },
  invalid_stage_transition: {
    es: "No se cambió la fase porque su estado actual no permite esa transición. Revisa el avance y el estado de la orden.",
    en: "The phase was not changed because its current state does not allow that transition. Review its progress and the order status."
  },
  invalid_quote_transition: {
    es: "No se cambió la cotización: su estado o vigencia no permiten esa transición. Recarga y revisa la vigencia antes de continuar.",
    en: "The quote was not changed: its status or validity does not allow that transition. Reload and review its validity before continuing."
  },
  invalid_requisition_transition: {
    es: "No se cambió la requisición porque su estado actual no permite esa transición. Recarga y revisa el flujo de aprobación.",
    en: "The requisition was not changed because its current status does not allow that transition. Reload and review the approval workflow."
  },
  invalid_maintenance_transition: {
    es: "No se cambió la orden de mantenimiento porque su estado actual no permite esa acción. Recarga y completa los requisitos pendientes.",
    en: "The maintenance order was not changed because its current status does not allow that action. Reload and complete the pending requirements."
  },
  material_reservation_required: {
    es: "No se puede iniciar la orden: faltan reservas vigentes de materia prima. Revisa disponibilidad y vuelve a liberar la orden.",
    en: "The order cannot start: active raw-material reservations are missing. Review availability and release the order again."
  },
  production_material_issue_pending: {"es": "No se canceló la orden: Almacén tiene una entrega de materiales sin terminar de confirmar. Debe continuar la misma solicitud en Almacenes → Movimientos → Solicitudes de materiales para producción. Después podrás cancelar y tramitar la devolución de lo entregado.", "en": "The order was not cancelled: Warehouse has a material issue whose confirmation is incomplete. Continue the same request in Inventory → Movements → Production material requests. You can then cancel and request return of issued materials."},
  material_consumption_required: {"es": "No se cambió el estatus de la orden: falta la salida completa de sus materiales. Pide a Almacén ir a Almacenes → Movimientos → Solicitudes de materiales para producción y seleccionar Autorizar y entregar. Después vuelve a Producción → Órdenes e intenta el cambio.", "en": "The order status was not changed: its materials have not all been issued. Ask Warehouse to go to Inventory → Movements → Production material requests and select Authorize and issue. Then return to Production → Orders and retry the status change."},
  production_stages_incomplete: {"es": "No se avanzó la orden a validación o terminación: hay fases pendientes. Producción debe registrar 100% de avance y terminar u omitir cada fase en la orden. Después podrá validar y terminar la orden.", "en": "The order was not moved to validation or completion: phases are pending. Production must record 100% progress and complete or skip each phase on the order. It can then validate and complete the order."},
  resources_unavailable: {
    es: "La disponibilidad cambió y la orden ya no puede liberarse con estos recursos. Valida nuevamente materiales, personal y maquinaria.",
    en: "Availability changed and the order can no longer be released with these resources. Validate materials, workers, and machinery again."
  },
  required_date_precedes_planned_end: {
    es: "La fecha requerida queda antes del fin calculado. Amplía la fecha requerida o ajusta la duración y los recursos.",
    en: "The required date is before the calculated completion date. Extend the required date or adjust duration and resources."
  },
  production_order_must_be_in_progress: {"es": "No se inició ni terminó la fase: primero debe estar trabajando la orden. Pide a Almacén confirmar sus materiales en Movimientos; después inicia o reanuda la orden en Producción → Órdenes y vuelve a la fase.", "en": "The phase was not started or completed: its order must be running first. Ask Warehouse to confirm its materials in Movements, then start or resume the order in Production → Orders and return to the phase."},
  terminal_stage_requires_full_progress: {
    es: "Una fase terminada debe conservar 100% de avance. Corrige el porcentaje o selecciona otro estado.",
    en: "A completed phase must remain at 100% progress. Correct the percentage or select another status."
  },
  terminal_order_resource_locked: {
    es: "Los recursos de una orden terminada o cancelada ya no pueden modificarse.",
    en: "Resources on a completed or cancelled order can no longer be changed."
  },
  sales_order_not_fulfillable: {
    es: "El pedido no admite configurar surtido en su estado actual. Recarga y revisa si ya fue surtido, cancelado o entregado.",
    en: "Fulfillment cannot be configured for the order in its current state. Reload and check whether it was already fulfilled, cancelled, or delivered."
  },
  sales_order_not_cancellable: {
    es: "No puedes cancelar un pedido con entregas parciales o completas. Revisa sus Entregas antes de continuar.",
    en: "You cannot cancel an order with partial or complete deliveries. Review its Deliveries before continuing."
  },
  sales_order_not_deliverable: {
    es: "El pedido aún no está listo para entrega. Completa o corrige su configuración de surtido.",
    en: "The order is not ready for delivery yet. Complete or correct its fulfillment configuration."
  },
  sales_order_fulfillment_in_progress: {
    es: "La configuración de surtido sigue en proceso. Recarga el pedido antes de repetir la acción.",
    en: "Fulfillment configuration is still in progress. Reload the order before repeating the action."
  },
  sales_order_cancellation_in_progress: {
    es: "La cancelación del pedido sigue en proceso. Recarga el pedido antes de repetirla.",
    en: "Order cancellation is still in progress. Reload the order before repeating it."
  },
  delivery_confirmation_in_progress: {
    es: "La confirmación de la entrega sigue en proceso. Recarga la entrega antes de repetir la acción.",
    en: "Delivery confirmation is still in progress. Reload the delivery before repeating the action."
  },
  delivery_not_confirmable: {
    es: "Solo una entrega en borrador puede confirmarse. Recarga y revisa su estatus actual.",
    en: "Only a draft delivery can be confirmed. Reload and review its current status."
  },
  delivery_not_cancellable: {
    es: "Solo una entrega en borrador puede cancelarse. Recarga y revisa su estatus actual.",
    en: "Only a draft delivery can be cancelled. Reload and review its current status."
  },
  requisition_not_cancellable: {
    es: "La requisición ya fue convertida, rechazada o cancelada y no admite cancelación. Recarga y revisa su estatus.",
    en: "The requisition was already converted, rejected, or cancelled and cannot be cancelled. Reload and review its status."
  },
  requisition_not_editable: {
    es: "Solo una requisición en borrador puede editarse. Recarga y revisa su estatus actual.",
    en: "Only a draft requisition can be edited. Reload and review its current status."
  },
  order_not_issuable: {
    es: "Solo una orden de compra en borrador puede emitirse. Recarga y revisa su estatus actual.",
    en: "Only a draft purchase order can be issued. Reload and review its current status."
  },
  order_not_cancellable: {
    es: "La orden de compra ya no admite cancelación. Revisa si tiene recepciones o conciliaciones pendientes.",
    en: "The purchase order can no longer be cancelled. Check for receipts or pending reconciliation."
  },
  order_not_receivable: {
    es: "La orden de compra no está emitida o ya fue recibida/cancelada. Recarga antes de registrar la recepción.",
    en: "The purchase order is not issued or was already received/cancelled. Reload before recording the receipt."
  },
  receipt_reconciliation_pending: {
    es: "La recepción todavía requiere conciliación. Ve a Recepciones y resuelve las partidas pendientes antes de continuar.",
    en: "The receipt still requires reconciliation. Go to Receipts and resolve pending lines before continuing."
  },
  receipt_not_reconcilable: {
    es: "La recepción no tiene partidas pendientes que puedan conciliarse. Recarga para consultar su estado actual.",
    en: "The receipt has no pending lines that can be reconciled. Reload to review its current status."
  },
  over_receipt: {
    es: "La cantidad recibida excede el saldo pendiente de la orden. Corrige la cantidad de la partida.",
    en: "The received quantity exceeds the remaining order balance. Correct the line quantity."
  },
  maintenance_resolution_evidence_required: {"es": "No se resolvió el mantenimiento: faltan los datos del trabajo. El técnico debe completar Diagnóstico, Trabajo realizado y Verificación en la orden de Mantenimiento y volver a seleccionar Resolver.", "en": "Maintenance was not resolved: work details are missing. The technician must complete Diagnosis, Work performed, and Verification on the Maintenance order, then select Resolve again."},
  maintenance_time_required: {"es": "No se resolvió el mantenimiento: falta registrar tiempo trabajado. El técnico asignado debe agregar al menos una entrada de tiempo en la orden de Mantenimiento y después volver a seleccionar Resolver.", "en": "Maintenance was not resolved: worked time is missing. The assigned technician must add at least one time entry to the Maintenance order, then select Resolve again."},
  maintenance_materials_not_reconciled: {"es": "No se resolvió el mantenimiento: hay refacciones sin entrega confirmada. Almacén debe atender la solicitud en Almacenes → Movimientos → Solicitudes de refacciones. Si ya no se necesitan, cancela la solicitud pendiente en Mantenimiento; después vuelve a resolver la orden.", "en": "Maintenance was not resolved: some spare parts have no confirmed issue. Warehouse must process the request in Inventory → Movements → Spare-parts requests. If they are no longer needed, cancel the pending request in Maintenance, then resolve the order again."},
  maintenance_integration_pending: {
    es: "Hay una operación externa pendiente. Concíliala antes de cambiar el estatus de mantenimiento.",
    en: "An external operation is pending. Reconcile it before changing the maintenance status."
  },
  maintenance_time_worker_not_assigned: {
    es: "Solo el técnico asignado puede registrar tiempo. Asigna al técnico correcto antes de continuar.",
    en: "Only the assigned technician can log time. Assign the correct technician before continuing."
  },
  maintenance_time_overlap: {
    es: "El técnico ya tiene tiempo registrado en ese intervalo. Corrige las horas para evitar traslapes.",
    en: "The technician already has time recorded in that interval. Correct the times to avoid overlap."
  },
  maintenance_worker_not_eligible: {
    es: "El trabajador seleccionado ya no es elegible para mantenimiento. Selecciona un técnico activo y vuelve a intentar.",
    en: "The selected worker is no longer eligible for maintenance. Select an active technician and try again."
  },
  maintenance_order_not_editable: {
    es: "La orden de mantenimiento ya no puede editarse en su estado actual. Recarga y revisa el flujo disponible.",
    en: "The maintenance order can no longer be edited in its current state. Reload and review the available workflow."
  },
  maintenance_material_status_invalid: {
    es: "No se pueden solicitar refacciones en el estado actual de la orden. Revisa primero su asignación e inicio.",
    en: "Spare parts cannot be requested in the order's current state. Review its assignment and start first."
  },
  material_request_not_cancellable: {
    es: "La solicitud de refacciones ya no admite cancelación. Recarga y revisa su estado.",
    en: "The spare-parts request can no longer be cancelled. Reload and review its status."
  },
  material_request_not_reconcilable: {
    es: "La solicitud de refacciones no tiene una operación pendiente que pueda conciliarse.",
    en: "The spare-parts request has no pending operation that can be reconciled."
  },
  insufficient_stock: {
    es: "No hay existencia suficiente para completar la operación. Revisa el saldo disponible o reduce la cantidad.",
    en: "There is not enough stock to complete the operation. Review available stock or reduce the quantity."
  },
  insufficient_available_stock: {
    es: "La existencia disponible no alcanza porque parte del inventario está reservada. Revisa reservas o reduce la cantidad.",
    en: "Available stock is insufficient because part of the inventory is reserved. Review reservations or reduce the quantity."
  },
  item_base_unit_locked_by_movements: {
    es: "La unidad base no puede cambiar porque el artículo ya tiene movimientos o reservas. Crea un artículo sustituto si necesitas otra unidad.",
    en: "The base unit cannot be changed because the item already has movements or reservations. Create a replacement item if another unit is required."
  },
  unit_conversion_unsupported: {
    es: "Las unidades no son compatibles o no tienen una conversión estándar segura. Usa la unidad base del artículo.",
    en: "The units are not compatible or do not have a safe standard conversion. Use the item's base unit."
  },
  worker_identity_conflict: {
    es: "Ya existe un trabajador con el mismo número de empleado, CURP, RFC o NSS. Revisa el expediente existente.",
    en: "A worker already exists with the same employee number, CURP, RFC, or NSS. Review the existing worker file."
  },
  customer_identity_conflict: {
    es: "Ya existe un cliente con el mismo código o identidad fiscal. Revisa el catálogo antes de crear otro.",
    en: "A customer already exists with the same code or tax identity. Review the catalog before creating another one."
  },
  supplier_identity_conflict: {
    es: "Ya existe un proveedor con el mismo código o RFC. Revisa el catálogo antes de crear otro.",
    en: "A supplier already exists with the same code or tax ID. Review the catalog before creating another one."
  },
  incomplete_supplier_fiscal_profile: {
    es: "Completa razón social, RFC, régimen fiscal, correo de facturación y código postal fiscal.",
    en: "Complete legal name, tax ID, tax regime, billing email, and fiscal postal code."
  },
  incomplete_billing_profile: {
    es: "El perfil fiscal está incompleto. Completa juntos los datos de facturación requeridos.",
    en: "The billing profile is incomplete. Complete the required billing fields together."
  },
  material_request_not_issuable: {
    es: "La solicitud no está lista para entregar. Actualiza la lista y verifica que Mantenimiento haya completado la reserva.",
    en: "The request is not ready for delivery. Refresh the list and check that Maintenance has completed the reservation."
  },
  purchase_unit_not_found: {
    es: "No se cambió el documento: la unidad no está activa en Administración. Revisa el catálogo de unidades y vuelve a intentar.",
    en: "The document was not changed because the unit is not active in Administration. Review the unit catalog and try again."
  },
  purchasing_inventory_required: {
    es: "La partida inventariable no se guardó: activa Almacenes e Inventarios o cambia la partida a Servicio.",
    en: "The inventory line was not saved. Enable Inventory or change the line to Service."
  },
  service_inventory_item_forbidden: {
    es: "El servicio no se guardó porque no debe vincularse con un artículo de Inventario. Limpia el vínculo y vuelve a intentar.",
    en: "The service was not saved because it cannot be linked to an Inventory item. Clear the link and try again."
  },
  service_warehouse_not_allowed: {
    es: "No se registró la recepción: una partida de servicio no debe indicar almacén. Limpia el almacén y vuelve a intentar.",
    en: "The receipt was not recorded because a service line cannot specify a warehouse. Clear the warehouse and try again."
  },
  service_line_requires_service_order: { es: "No se cambió la entrega: los servicios se cumplen desde su Orden de servicio.", en: "The delivery was not changed. Services are fulfilled through their Service order." },
  service_order_not_plannable: { es: "La orden ya no admite planeación desde su estado actual. Recárgala y revisa su avance.", en: "The service order can no longer be planned from its current status. Reload it and review its progress." },
  service_order_not_assignable: { es: "La orden debe estar planeada antes de asignar un responsable.", en: "The service order must be planned before assigning an owner." },
  service_order_entries_not_allowed: { es: "No se registró la entrada: la orden debe estar en ejecución, espera o pendiente de aceptación.", en: "The entry was not recorded. The order must be in progress, on hold, or pending acceptance." },
  service_order_transition_invalid: { es: "No se cambió el estado: completa primero el paso anterior y recarga la orden.", en: "The status was not changed. Complete the previous step and reload the service order." },
  service_order_action_invalid: { es: "La acción solicitada no pertenece al flujo de Ordenes de servicio. Recarga y usa una acción disponible.", en: "The requested action is not part of the Service order flow. Reload and use an available action." },
  service_order_not_acceptable: { es: "El servicio todavía no está pendiente de aceptación. Completa la ejecución y envíalo primero.", en: "The service is not pending acceptance yet. Complete execution and submit it first." },
  service_order_assign_worker_required: { es: "Selecciona un trabajador activo y elegible para asignar la orden.", en: "Select an active eligible worker to assign the service order." },
  service_order_evidence_required: { es: "No se envió a aceptación: registra al menos una evidencia del servicio.", en: "The service was not submitted for acceptance. Record at least one service evidence item." },
  service_order_cost_required: { es: "No se envió a aceptación: registra tiempo trabajado o un costo trazable.", en: "The service was not submitted for acceptance. Record worked time or a traceable cost." },
  service_order_plan_dates_invalid: { es: "La fecha final debe ser igual o posterior a la fecha inicial.", en: "The end date must be on or after the start date." },
  report_date_range_invalid: { es: "La fecha final debe ser igual o posterior a la fecha inicial.", en: "The end date must be on or after the start date." },
  report_filter_invalid: { es: "Uno de los filtros del reporte no es válido. Revisa los filtros e intenta nuevamente.", en: "One of the report filters is invalid. Review the filters and try again." },
  report_not_found: { es: "El reporte solicitado no está disponible en este módulo.", en: "The requested report is not available in this module." },
  report_row_limit_exceeded: { es: "El reporte supera 50,000 filas. Reduce el periodo o agrega filtros para descargarlo.", en: "The report exceeds 50,000 rows. Shorten the date range or add filters before downloading it." },
  movement_unit_must_match_item_base_unit: {
    es: "La unidad debe coincidir con la unidad base del artículo. Selecciona su unidad base.",
    en: "The unit must match the item's base unit. Select its base unit."
  },
  movement_reference_inactive: {
    es: "El artículo o el almacén está inactivo. Selecciona registros activos; si necesitas habilitarlos, solicita apoyo al responsable del catálogo.",
    en: "The item or warehouse is inactive. Select active records; ask the catalog manager if they need to be enabled."
  },
  movement_reference_invalid: {
    es: "No se encontró el artículo o el almacén seleccionado. Actualiza los catálogos y selecciona ambos nuevamente.",
    en: "The selected item or warehouse was not found. Refresh the catalogs and select both again."
  },
  validation_failed: {
    es: "No se pudo validar la solicitud. Revisa los requisitos indicados; si no hay un campo que corregir, contacta a soporte.",
    en: "The request could not be validated. Review the indicated requirements; if no field can be corrected, contact support."
  },
  service_unavailable: {
    es: "El servicio no está disponible temporalmente. No pudimos confirmar el resultado; recarga antes de volver a intentar.",
    en: "The service is temporarily unavailable. We could not confirm the result; reload before trying again."
  }
});

const FIREBASE_MESSAGES = Object.freeze({
  "auth/invalid-credential": { es: "El correo o la contraseña no son correctos.", en: "The email or password is incorrect." },
  "auth/wrong-password": { es: "El correo o la contraseña no son correctos.", en: "The email or password is incorrect." },
  "auth/user-not-found": { es: "No encontramos una cuenta activa con ese correo.", en: "We could not find an active account with that email." },
  "auth/user-disabled": { es: "Esta cuenta está deshabilitada. Contacta al administrador.", en: "This account is disabled. Contact an administrator." },
  "auth/invalid-email": { es: "Captura un correo electrónico válido.", en: "Enter a valid email address." },
  "auth/too-many-requests": { es: "Hubo demasiados intentos. Espera unos minutos antes de volver a intentar.", en: "There were too many attempts. Wait a few minutes before trying again." },
  "auth/network-request-failed": { es: "No pudimos comunicarnos con el servicio de acceso. Revisa tu conexión e intenta nuevamente.", en: "We could not reach the sign-in service. Check your connection and try again." }
});

const GENERIC_MESSAGES = Object.freeze({
  es: {
    notFound: "El registro ya no está disponible. Recarga la información y selecciona un registro vigente.",
    state: "La operación no es válida en el estado actual. Recarga el registro y completa primero los requisitos pendientes.",
    conflict: "La información cambió o ya existe un registro equivalente. Recarga y revisa los datos antes de volver a intentar.",
    validation: "No se pudo completar la operación porque hay información inválida o incompleta. Revisa los datos y vuelve a intentar.",
    access: "No fue posible autorizar la operación. Recarga tu sesión o solicita acceso al administrador.",
    unavailable: "Una dependencia no está disponible. No pudimos confirmar el resultado; recarga antes de volver a intentar.",
    unexpected: "Ocurrió un error inesperado. Recarga la información y vuelve a intentar."
  },
  en: {
    notFound: "The record is no longer available. Reload the information and select a current record.",
    state: "The operation is not valid in the current state. Reload the record and complete the pending requirements first.",
    conflict: "The information changed or an equivalent record already exists. Reload and review the data before trying again.",
    validation: "The operation could not be completed because some information is invalid or incomplete. Review the data and try again.",
    access: "The operation could not be authorized. Reload your session or ask an administrator for access.",
    unavailable: "A dependency is unavailable. We could not confirm the result; reload before trying again.",
    unexpected: "An unexpected error occurred. Reload the information and try again."
  }
});

function language(value) {
  return value === "en" ? "en" : "es";
}

function interpolate(template, values = {}) {
  return Object.entries(values).reduce((result, [key, value]) => result.replaceAll(`{${key}}`, String(value ?? "")), template);
}

export function getApiErrorCode(error) {
  return String(error?.code || error?.payload?.error?.code || "").trim().toLowerCase();
}

export function getApiErrorCorrelationId(error) {
  return String(error?.correlationId || error?.payload?.error?.correlation_id || "").trim();
}

export function getApiErrorTone(error) {
  const status = Number(error?.status || 0);
  if (status === 409 || status === 422 || getApiErrorCode(error).includes("in_progress")) return "warning";
  return "danger";
}

function genericMessage(code, status, lang) {
  const copy = GENERIC_MESSAGES[lang];
  if (code.endsWith("_not_found") || status === 404) return copy.notFound;
  if (code.includes("transition") || /_not_(editable|cancellable|confirmable|issuable|receivable|fulfillable|deliverable|reconcilable)$/.test(code) || code.includes("terminal_")) return copy.state;
  if (code.includes("conflict") || code.includes("duplicate") || code.includes("already_") || code.endsWith("_exists") || status === 409) return copy.conflict;
  if (code.includes("permission") || code.includes("authorization") || status === 401 || status === 403) return copy.access;
  if (code.includes("unavailable") || code.includes("dependency") || status === 0 || status >= 500) return copy.unavailable;
  if (code.includes("invalid") || code.includes("required") || code.includes("mismatch") || code.includes("incomplete") || code.includes("exceeds") || code.includes("must_") || status === 400 || status === 422) return copy.validation;
  return copy.unexpected;
}

export function getLocalizedErrorMessage(error, options = {}) {
  const lang = language(options.lang);
  const code = getApiErrorCode(error);
  const status = Number(error?.status || 0);
  const firebaseMessage = FIREBASE_MESSAGES[error?.code]?.[lang];
  const definition = Object.hasOwn(ERROR_MESSAGES, code) ? ERROR_MESSAGES[code] : null;
  const service = error?.details?.service || error?.payload?.error?.details?.service || options.service || (lang === "en" ? "the service" : "el servicio");
  let message = firebaseMessage || (definition ? interpolate(definition[lang], { service }) : "");
  const details=error?.details||error?.payload?.error?.details||{};
  const transition=["invalid_order_transition","invalid_status_transition","invalid_requisition_transition","invalid_maintenance_transition","service_order_transition_invalid"].includes(code);
  const guidance=transition?TRANSITION_GUIDANCE[details.workflow]?.[details.requested_status]?.[lang]:null;
  if(guidance)message=(lang==="en"?"The status was not changed. ":"No se cambió el estatus. ")+guidance;

  if (!message && error?.name !== "ErclaveApiError" && options.fallback) message = options.fallback;
  if (!message) message = genericMessage(code, status, lang);

  const correlationId = getApiErrorCorrelationId(error);
  const shouldShowReference = correlationId && (status === 0 || status >= 500 || !definition);
  if (shouldShowReference) {
    message += lang === "en" ? ` Support reference: ${correlationId}.` : ` Referencia para soporte: ${correlationId}.`;
  }
  return message;
}

export const API_ERROR_MESSAGES = ERROR_MESSAGES;
