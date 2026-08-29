const ERROR_MESSAGES = Object.freeze({
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
  material_consumption_required: {
    es: "No se puede continuar porque Almacenes no confirmó el consumo de todos los materiales reservados. Revisa los movimientos e intenta nuevamente.",
    en: "The operation cannot continue because Inventory did not confirm consumption of all reserved materials. Review the movements and try again."
  },
  production_stages_incomplete: {
    es: "No se puede terminar la orden: todas sus fases deben estar al 100%. Registra el avance pendiente y vuelve a intentar.",
    en: "The order cannot be completed: every phase must be at 100%. Record the pending progress and try again."
  },
  resources_unavailable: {
    es: "La disponibilidad cambió y la orden ya no puede liberarse con estos recursos. Valida nuevamente materiales, personal y maquinaria.",
    en: "Availability changed and the order can no longer be released with these resources. Validate materials, workers, and machinery again."
  },
  required_date_precedes_planned_end: {
    es: "La fecha requerida queda antes del fin calculado. Amplía la fecha requerida o ajusta la duración y los recursos.",
    en: "The required date is before the calculated completion date. Extend the required date or adjust duration and resources."
  },
  production_order_must_be_in_progress: {
    es: "No se puede actualizar la fase porque la orden todavía no está en producción. Inicia la orden y vuelve a intentar.",
    en: "The phase cannot be updated because the order is not in production yet. Start the order and try again."
  },
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
  maintenance_resolution_evidence_required: {
    es: "No se puede resolver la orden: completa Diagnóstico, Trabajo realizado y Verificación.",
    en: "The order cannot be resolved: complete Diagnosis, Work performed, and Verification."
  },
  maintenance_time_required: {
    es: "Registra al menos una entrada de tiempo antes de resolver la orden.",
    en: "Record at least one time entry before resolving the order."
  },
  maintenance_materials_not_reconciled: {
    es: "No se puede resolver la orden mientras existan solicitudes de refacciones sin emitir, cancelar o conciliar.",
    en: "The order cannot be resolved while spare-parts requests remain unissued, uncancelled, or unreconciled."
  },
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
  validation_failed: {
    es: "Hay información inválida o incompleta. Revisa los campos marcados y vuelve a intentar.",
    en: "Some information is invalid or incomplete. Review the marked fields and try again."
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
  const definition = ERROR_MESSAGES[code];
  const service = error?.details?.service || error?.payload?.error?.details?.service || options.service || (lang === "en" ? "the service" : "el servicio");
  let message = firebaseMessage || (definition ? interpolate(definition[lang], { service }) : "");

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
