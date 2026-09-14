/** Stable backend codes only. No backend message, identifiers or personal data are interpolated. */
const messages = {};
function define(codes, es, en, fields) {
  for (const code of codes.split(' ')) messages[code] = Object.freeze({ es, en, ...(fields ? { fields } : {}) });
}

// Capture and identity validation (schemas); ambiguous multi-field conflicts stay in the summary.
define('invalid_curp', 'La CURP debe tener 18 caracteres y un formato válido. Revisa el dato capturado.', 'CURP must contain 18 characters in a valid format. Check the entered value.', ['curp']);
define('invalid_rfc invalid_mexican_rfc', 'El RFC no tiene un formato válido. Revisa letras, fecha y homoclave.', 'The RFC format is invalid. Check its letters, date and final characters.');
define('invalid_nss', 'El NSS debe contener exactamente 11 dígitos.', 'The social security number must contain exactly 11 digits.', ['nss']);
define('invalid_nss_check_digit', 'El dígito verificador del NSS no coincide. Revisa el número completo.', 'The social security check digit does not match. Check the complete number.', ['nss']);
define('invalid_birth_date', 'La fecha de nacimiento debe ser anterior al ingreso y no estar en el futuro.', 'The birth date must precede the hire date and cannot be in the future.', ['birth_date', 'hire_date']);
define('hire_date_in_future', 'La fecha de ingreso no puede estar en el futuro.', 'The hire date cannot be in the future.', ['hire_date']);
define('invalid_email', 'El correo no tiene un formato válido. Revisa la dirección capturada.', 'The email format is invalid. Check the entered address.');
define('email_required', 'Captura el correo para continuar.', 'Enter an email address to continue.', ['email']);
define('invalid_tax_id', 'El identificador fiscal no tiene un formato válido. Revisa el dato fiscal del cliente.', 'The tax identifier format is invalid. Check the customer tax information.', ['tax_id']);
define('invalid_mexican_postal_code', 'El código postal de México debe tener cinco dígitos.', 'A Mexican postal code must contain five digits.');
define('required_text_blank', 'Un texto obligatorio está vacío o contiene solo espacios. Completa los campos requeridos.', 'A required text is empty or contains only spaces. Complete the required fields.');
define('reason_too_short cancellation_reason_required service_order_reason_required', 'Escribe un motivo de al menos 3 caracteres.', 'Enter a reason with at least 3 characters.', ['reason']);
define('invalid_customer_code invalid_delivery_code invalid_quote_code invalid_sales_order_code', 'La clave del documento no cumple el formato permitido. Revisa la clave capturada.', 'The document code does not match the allowed format. Check the entered code.', ['code']);
define('manual_business_code_required', 'Esta numeración es manual. Captura una clave para continuar.', 'This numbering sequence is manual. Enter a code to continue.', ['code']);
define('invalid_document_logo', 'El logotipo no es válido. Selecciona una imagen PNG, JPEG o WebP de hasta 1 MB.', 'The logo is invalid. Select a PNG, JPEG or WebP image up to 1 MB.', ['logo_data_url']);
define('empty_update', 'No hay cambios válidos para actualizar. Revisa los campos editables.', 'There are no valid changes to update. Check the editable fields.');
define('invalid_stock_limits maximum_stock_must_be_greater_than_or_equal_to_minimum_stock', 'La existencia máxima debe ser mayor o igual a la mínima.', 'Maximum stock must be greater than or equal to minimum stock.', ['minimum_stock', 'maximum_stock']);
define('future_time_entry_not_allowed', 'El fin del trabajo no puede estar en el futuro. Corrige la hora final.', 'The work end time cannot be in the future. Correct the end time.', ['ended_at']);
define('invalid_time_interval', 'El fin del trabajo debe ser posterior al inicio. Revisa ambas fechas y horas.', 'The work end time must be after its start. Check both dates and times.', ['started_at', 'ended_at']);
define('valid_until_in_past', 'La vigencia no puede terminar en una fecha pasada. Actualiza la fecha.', 'Validity cannot end on a past date. Update the date.', ['valid_until']);
define('promised_delivery_date_in_past', 'La fecha prometida de entrega no puede estar en el pasado.', 'The promised delivery date cannot be in the past.', ['promised_delivery_date']);
define('invalid_usage_date_range', 'El periodo de consulta no es válido. Revisa la fecha inicial y la final.', 'The query period is invalid. Check the start and end dates.');
define('planning_start_dates_must_match', 'Las fechas de inicio de la planificación deben coincidir. Revisa el inicio de la orden.', 'Planning start dates must match. Check the order start date.', ['planned_start_date', 'planned_for']);

// Catalogs, duplicate identities and administrative configuration.
const missingEntities = [
  ['area_not_found','El área','The area'], ['position_not_found','El puesto','The position'],
  ['worker_not_found','El trabajador','The worker'], ['customer_not_found','El cliente','The customer'],
  ['supplier_not_found','El proveedor','The supplier'], ['item_not_found','El artículo','The item'],
  ['warehouse_not_found','El almacén','The warehouse'], ['machine_not_found','La máquina','The machine'],
  ['product_service_not_found','El producto o servicio','The product or service'], ['recipe_not_found','La receta','The recipe'],
  ['recipe_version_not_found','La versión de receta','The recipe version'], ['quote_not_found','La cotización','The quote'],
  ['sales_order_not_found','El pedido','The sales order'], ['delivery_not_found','La entrega','The delivery'],
  ['order_not_found','La orden de compra','The purchase order'], ['requisition_not_found','La requisición','The requisition'],
  ['receipt_not_found','La recepción','The receipt'], ['production_order_not_found','La orden de producción','The production order'],
  ['maintenance_order_not_found','La orden de mantenimiento','The maintenance order'],
  ['maintenance_material_request_not_found','La solicitud de refacciones','The spare-parts request'],
  ['service_order_not_found','La orden de servicio','The service order'], ['movement_not_found','El movimiento','The movement'],
  ['reservation_not_found','La reserva','The reservation'], ['transfer_not_found','La transferencia','The transfer'],
  ['role_not_found','El rol','The role'], ['user_not_found','El usuario','The user'],
  ['tenant_not_found','La empresa','The organization'], ['branch_not_found','La sucursal','The branch'],
  ['legal_entity_not_found','La razón social','The legal entity'], ['module_not_found','El módulo','The module'],
  ['unit_of_measure_not_found','La unidad de medida','The unit of measure'], ['code_sequence_not_found','La secuencia de numeración','The numbering sequence']
];
for (const [code, es, en] of missingEntities) define(code, `${es} ya no está disponible en esta empresa. Actualiza la lista y revisa la selección.`, `${en} is no longer available in this organization. Refresh the list and review the selection.`);
const conflicts = [
  ['area_conflict','del área','area'], ['position_conflict','del puesto','position'], ['machine_conflict','de la máquina','machine'],
  ['item_conflict','del artículo','item'], ['warehouse_conflict','del almacén','warehouse'], ['role_conflict','del rol','role'],
  ['recipe_conflict','de la receta','recipe'], ['product_service_conflict','del producto o servicio','product or service'],
  ['maintenance_order_conflict','de la orden de mantenimiento','maintenance order'], ['delivery_code_conflict','de la entrega','delivery'],
  ['order_code_conflict','de la orden de compra','purchase order'], ['requisition_code_conflict','de la requisición','requisition'],
  ['quote_code_conflict','de la cotización','quote'], ['production_order_code_already_exists','de la orden de producción','production order']
];
for (const [code, es, en] of conflicts) define(code, `Los datos ${es} entran en conflicto con un registro existente. Revisa la clave y los registros de la empresa.`, `The ${en} information conflicts with an existing record. Review the code and organization records.`);
define('sales_order_identity_conflict', 'La clave del pedido ya existe o la cotización ya se convirtió en pedido. Revisa los pedidos antes de volver a crear.', 'The sales order code already exists or the quote was already converted. Review sales orders before creating another.');
define('catalog_item_code_exists unit_code_exists', 'Esta clave ya existe en el catálogo. Revisa el registro existente o utiliza otra clave.', 'This code already exists in the catalog. Review the existing record or use another code.', ['code']);
define('catalog_item_not_found authoritative_reference_not_found', 'Una referencia seleccionada ya no existe o está inactiva. Actualiza el catálogo y revisa las selecciones.', 'A selected reference no longer exists or is inactive. Refresh the catalog and review the selections.');
define('catalog_not_found', 'El catálogo solicitado no está disponible. Regresa a los catálogos habilitados.', 'The requested catalog is unavailable. Return to the enabled catalogs.');
define('code_sequence_cannot_rewind', 'El siguiente número no puede ser menor al que ya tiene la secuencia. Revisa la numeración vigente.', 'The next number cannot be lower than the current sequence number. Check the current numbering.', ['next_number']);
define('permission_assignments_required', 'Completa la selección de permisos antes de guardar el rol.', 'Complete the permission selection before saving the role.');
define('permission_revision_required', 'Falta la revisión vigente del rol. Actualiza el editor de permisos y revisa tu selección.', 'The current role revision is missing. Refresh the permission editor and review your selection.');
define('role_permissions_not_updated setting_not_updated branch_not_created legal_entity_not_created', 'No se pudo confirmar el cambio administrativo. Actualiza la información y comprueba su estado antes de reintentar.', 'The administrative change could not be confirmed. Refresh the information and check its status before retrying.');
define('core_module_required admin_module_not_active', 'Administración debe permanecer habilitada para esta empresa. Revisa su configuración de módulos.', 'Administration must remain enabled for this organization. Review its module configuration.');
define('module_dependencies_required', 'Faltan módulos requeridos por la selección. Habilita también sus dependencias.', 'The selection requires additional modules. Enable its dependencies as well.');
define('duplicate_module', 'Un módulo está repetido en la configuración. Revisa la selección de módulos.', 'A module is repeated in the configuration. Review the module selection.');
define('tenant_not_active', 'La empresa no está activa. Solicita al administrador que revise su estado.', 'The organization is not active. Ask an administrator to review its status.');

// Warehouse and commercial item references.
define('unit_of_measure_invalid', 'La unidad de medida no está disponible para esta operación. Selecciona una unidad vigente del catálogo.', 'The unit of measure is unavailable for this operation. Select a current catalog unit.');
define('suggested_warehouse_invalid', 'El almacén sugerido no es válido. Selecciona un almacén activo de esta empresa.', 'The suggested warehouse is invalid. Select an active warehouse in this organization.', ['suggested_warehouse_id']);
define('inventory_item_invalid inactive_inventory_item', 'El artículo no está disponible para esta operación. Revisa que exista y esté activo en Almacenes.', 'The item is unavailable for this operation. Check that it exists and is active in Warehouse.');
define('inactive_purchase_warehouse', 'El almacén de recepción no está activo. Selecciona un almacén activo.', 'The receiving warehouse is inactive. Select an active warehouse.');
define('inventory_item_required', 'Selecciona el artículo de inventario para la partida.', 'Select the inventory item for the line.');
define('inventory_warehouse_required', 'Selecciona un almacén para cada partida inventariable que recibes.', 'Select a warehouse for every inventory line being received.');
define('insufficient_available_stock_for_reversal', 'No hay existencia disponible suficiente para revertir el movimiento. Revisa existencias y reservas en Almacenes.', 'There is insufficient available stock to reverse the movement. Review stock and reservations in Warehouse.');
define('finished_good_mapping_required product_inventory_mapping_required product_inventory_item_required', 'Falta vincular el producto con su artículo de inventario. Completa el vínculo en la ficha del producto.', 'The product needs a linked inventory item. Complete the link in the product record.');
define('finished_good_product_required', 'Selecciona un producto para crear su artículo de producto terminado.', 'Select a product to create its finished-goods inventory item.');
define('finished_goods_receipt_quantity_exceeded', 'La cantidad supera el saldo disponible para recibir de la orden de producción. Revisa las recepciones anteriores.', 'The quantity exceeds the production order balance available for receipt. Review previous receipts.', ['quantity']);
define('finished_goods_receipt_reference_invalid finished_goods_receipt_reference_not_found production_reference_not_found', 'La referencia de producción no está disponible para recibir. Actualiza las órdenes y revisa la selección.', 'The production reference is unavailable for receipt. Refresh the orders and review the selection.');
define('finished_goods_receipt_unit_mismatch product_inventory_unit_mismatch', 'La unidad del producto y la de su artículo de inventario no coinciden. Revisa ambas fichas antes de continuar.', 'The product unit does not match its inventory item unit. Review both records before continuing.');
define('product_inventory_mapping_invalid product_inventory_mapping_mismatch', 'El vínculo entre producto y artículo de inventario no es válido para esta operación. Revisa la ficha del producto.', 'The product-to-inventory-item link is invalid for this operation. Review the product record.');
define('product_inventory_item_already_linked product_inventory_item_already_mapped', 'El artículo de inventario ya tiene un vínculo con otro producto. Revisa el vínculo existente.', 'The inventory item is already linked to another product. Review the existing link.', ['inventory_item_id']);
define('product_not_linkable', 'Este producto no admite el vínculo solicitado. Revisa su tipo y vínculo actual.', 'This product does not allow the requested link. Review its type and current link.');
define('product_base_unit_locked_by_recipe', 'La unidad base está utilizada por una receta y no puede cambiarse directamente. Revisa las recetas vinculadas.', 'The base unit is used by a recipe and cannot be changed directly. Review the linked recipes.', ['base_unit']);
define('reservation_quantity_exceeded', 'La cantidad supera el saldo de la reserva. Actualiza la reserva antes de continuar.', 'The quantity exceeds the reservation balance. Refresh the reservation before continuing.');
define('reservation_not_active', 'La reserva ya no está activa. Actualiza la información y revisa su estado.', 'The reservation is no longer active. Refresh the information and check its status.');
define('reservation_reference_invalid reservation_source_conflict', 'La reserva no coincide con las referencias de esta operación. Revisa el documento origen y sus reservas.', 'The reservation does not match this operation’s references. Review the source document and its reservations.');
define('reservation_unit_mismatch', 'La unidad no coincide con la reserva. Revisa la unidad de la partida reservada.', 'The unit does not match the reservation. Check the reserved line unit.');
define('reserved_stock_missing', 'No se encontró la existencia reservada necesaria. Revisa las reservas y la conciliación en Almacenes.', 'The required reserved stock was not found. Review reservations and reconciliation in Warehouse.');
define('duplicate_availability_item', 'La consulta contiene un artículo repetido. Revisa los artículos seleccionados.', 'The query contains a repeated item. Review the selected items.');

// Purchasing and Sales documents; array errors retain the server's precise line path when supplied.
define('active_customer_required', 'El cliente debe estar activo para continuar. Revisa su ficha o selecciona otro cliente.', 'The customer must be active to continue. Review the record or select another customer.', ['customer_id']);
define('active_supplier_required', 'El proveedor debe estar activo para continuar. Revisa su ficha o selecciona otro proveedor.', 'The supplier must be active to continue. Review the record or select another supplier.', ['supplier_id']);
define('approved_quote_required', 'Selecciona una cotización aprobada para crear el pedido.', 'Select an approved quote to create the sales order.', ['quote_id']);
define('approved_requisition_required', 'Selecciona una requisición aprobada para crear la orden de compra.', 'Select an approved requisition to create the purchase order.', ['requisition_id']);
define('purchase_origin_required', 'Falta el origen de la compra. Revisa la requisición o la justificación de compra directa.', 'The purchase origin is missing. Review the requisition or direct-purchase reason.');
define('purchase_line_description_required', 'Completa la descripción de cada partida de compra.', 'Complete the description of every purchase line.');
define('purchase_unit_required', 'Selecciona una unidad para cada partida de compra.', 'Select a unit for every purchase line.');
define('purchase_unit_mismatch quote_unit_mismatch', 'La unidad de una partida no coincide con la de su artículo o producto. Revisa las unidades de las partidas.', 'A line unit does not match its item or product unit. Review the line units.');
define('unit_price_required', 'Captura el precio unitario de cada partida antes de continuar.', 'Enter the unit price for every line before continuing.');
define('supplier_fiscal_profile_required', 'Completa los datos fiscales del proveedor antes de continuar con la compra.', 'Complete the supplier tax information before continuing with the purchase.');
define('duplicate_requisition_item duplicate_material_item', 'Hay un artículo repetido. Conserva una sola partida por artículo y ajusta su cantidad.', 'An item is repeated. Keep one line per item and adjust its quantity.');
define('duplicate_quote_product', 'Hay un producto o servicio repetido. Conserva una sola partida y ajusta su cantidad.', 'A product or service is repeated. Keep a single line and adjust its quantity.');
define('duplicate_delivery_line duplicate_receipt_line duplicate_order_fulfillment_line', 'Una partida del documento está repetida. Revisa las partidas antes de continuar.', 'A document line is repeated. Review the lines before continuing.');
define('delivery_quantity_exceeds_remaining delivery_quantity_exceeds_uncommitted delivery_exceeds_reserved_quantity', 'Una cantidad de entrega supera su saldo disponible o reservado. Actualiza el pedido y revisa las cantidades de sus partidas.', 'A delivery quantity exceeds its available or reserved balance. Refresh the order and review its line quantities.');
define('order_line_not_found sales_order_line_not_found', 'Una partida ya no está disponible en el documento. Actualiza el documento origen y revisa sus partidas.', 'A line is no longer available in the document. Refresh the source document and review its lines.');
define('order_not_editable quote_not_editable', 'El documento ya no está en un estado editable. Actualiza la lista y revisa su estado actual.', 'The document is no longer editable in its current state. Refresh the list and review its current status.');
define('order_origin_locked', 'El origen de la orden de compra no puede cambiarse. Conserva la requisición original.', 'The purchase order origin cannot be changed. Keep the original requisition.', ['requisition_id']);
define('order_requisition_lines_mismatch', 'Las partidas de compra no coinciden con la requisición. Actualiza la requisición y revisa las partidas de la orden.', 'The purchase lines do not match the requisition. Refresh the requisition and review the order lines.');
define('purchase_receipt_payload_invalid purchase_receipt_reference_invalid', 'La recepción no coincide con su documento de compra. Actualiza la recepción y revisa sus partidas antes de confirmar.', 'The receipt does not match its purchasing document. Refresh the receipt and review its lines before confirming.');
define('product_service_inactive', 'Un producto o servicio de la operación está inactivo. Revisa las fichas de las partidas.', 'A product or service in this operation is inactive. Review the line item records.');
define('sales_order_line_already_configured', 'La partida ya tiene configurado su surtido. Revisa la configuración existente.', 'The line already has a fulfillment configuration. Review the existing configuration.');
define('sales_order_line_already_delivered', 'La partida ya tiene entregas registradas. Revisa su historial antes de cambiar el surtido.', 'The line already has recorded deliveries. Review its history before changing fulfillment.');
define('stock_allocations_required', 'Completa el artículo y almacén de las partidas que se surtirán de existencia.', 'Complete the item and warehouse for lines fulfilled from stock.');
define('stock_allocation_quantity_mismatch', 'La cantidad asignada no coincide con la cantidad por surtir. Revisa la asignación de la partida.', 'The allocated quantity does not match the quantity to fulfill. Review the line allocation.');
define('allocations_only_for_stock', 'Solo las partidas surtidas de existencia admiten asignación de inventario. Revisa el modo de surtido.', 'Only lines fulfilled from stock accept inventory allocations. Review the fulfillment mode.');
define('single_inventory_item_required', 'La partida debe utilizar un solo artículo de inventario. Revisa su asignación.', 'The line must use a single inventory item. Review its allocation.');
define('product_fulfillment_required', 'Completa el modo de surtido del producto antes de continuar.', 'Complete the product fulfillment mode before continuing.');
define('stock_cost_is_authoritative', 'El costo de existencia lo determina Almacenes. Revisa el artículo y la reserva; no captures un costo manual para esa partida.', 'Warehouse determines stock cost. Review the item and reservation; do not enter a manual cost for that line.');
define('service_order_code_unavailable', 'No se pudo obtener la clave de la orden de servicio. Revisa la numeración y el estado del pedido antes de reintentar.', 'The service order code could not be obtained. Review numbering and the sales order status before retrying.');

// Production and Maintenance resources and workflow prerequisites.
define('active_product_service_required active_product_and_matching_unit_required', 'Selecciona un producto o servicio activo y revisa que la unidad coincida con su ficha.', 'Select an active product or service and check that the unit matches its record.');
define('approved_recipe_required production_request_requires_approved_recipe', 'La operación requiere una versión de receta aprobada. Revisa la receta antes de continuar.', 'This operation requires an approved recipe version. Review the recipe before continuing.', ['recipe_version_id']);
define('recipe_unit_must_match_product_base_unit', 'La unidad base de la receta debe coincidir con la del producto o servicio.', 'The recipe base unit must match the product or service base unit.', ['base_unit']);
define('recipe_version_incomplete', 'La versión de receta está incompleta. Revisa sus recursos y fases antes de enviarla o aprobarla.', 'The recipe version is incomplete. Review its resources and stages before submitting or approving it.');
define('recipe_version_not_editable', 'Esta versión de receta ya no admite edición. Revisa su estado y utiliza una nueva versión cuando corresponda.', 'This recipe version can no longer be edited. Review its status and use a new version when appropriate.');
define('duplicate_recipe_resource', 'Un recurso está repetido en la receta. Conserva una sola entrada y ajusta su cantidad.', 'A resource is repeated in the recipe. Keep one entry and adjust its quantity.');
define('duplicate_recipe_stage_area', 'Un área está repetida en las fases de la receta. Revisa las áreas seleccionadas.', 'An area is repeated in the recipe stages. Review the selected areas.');
define('active_recipe_stage_phase_numbers_must_be_contiguous', 'El orden de las fases debe ser consecutivo y sin saltos. Revisa las fases activas.', 'Stage order must be consecutive without gaps. Review the active stages.');
define('active_recipe_stage_weight_must_total_100', 'Los porcentajes de las fases activas deben sumar 100%. Revisa los porcentajes de cada fase.', 'Active stage percentages must total 100%. Review each stage percentage.');
define('all_active_stages_require_one_assignment duplicate_stage_assignment', 'Cada fase activa necesita exactamente un responsable. Revisa las asignaciones de las fases.', 'Each active stage needs exactly one assignee. Review the stage assignments.');
define('responsible_worker_not_eligible', 'La persona responsable no es elegible para producción. Selecciona una persona activa habilitada para intervenir en producción.', 'The responsible worker is not eligible for production. Select an active worker enabled for production.', ['responsible_worker_id']);
define('stage_worker_not_eligible', 'Un responsable de fase no es elegible para producción. Revisa las asignaciones de las fases.', 'A stage assignee is not eligible for production. Review the stage assignments.');
define('labor_position_invalid', 'El puesto seleccionado no está disponible. Selecciona un puesto activo de esta empresa.', 'The selected position is unavailable. Select an active position in this organization.', ['labor_position_id']);
define('labor_area_invalid area_reference_required', 'El área seleccionada no es válida o no está activa. Revisa el catálogo de áreas en Recursos Humanos.', 'The selected area is invalid or inactive. Review the area catalog in Human Resources.');
define('inventory_resource_invalid', 'Un material de la receta no es válido para producción. Revisa su ficha y disponibilidad en Almacenes.', 'A recipe material is invalid for production. Review its record and availability in Warehouse.');
define('labor_resource_invalid', 'Un recurso de mano de obra no es elegible. Revisa el puesto y su participación en producción.', 'A labor resource is not eligible. Review the position and its production participation.');
define('machine_resource_invalid', 'Una máquina de la receta no es elegible. Revisa su estado y área en el catálogo de máquinas.', 'A recipe machine is not eligible. Review its status and area in the machine catalog.');
define('resource_reference_required resource_type_not_authoritative', 'Un recurso no tiene una referencia válida a su catálogo. Selecciona el recurso desde el catálogo correspondiente.', 'A resource has no valid catalog reference. Select it from the appropriate catalog.');
define('timed_resource_unit_must_be_minute', 'Los recursos de tiempo deben utilizar minutos. Revisa las unidades de mano de obra y maquinaria.', 'Time resources must use minutes. Review labor and machine units.');
define('material_actual_is_inventory_owned', 'El consumo real de materiales se registra desde Almacenes. Revisa los movimientos asociados a la orden.', 'Actual material consumption is recorded in Warehouse. Review the movements linked to the order.');
define('pending_stage_requires_zero_progress', 'Una fase pendiente debe tener avance de 0%. Revisa el avance y el estado.', 'A pending stage must have 0% progress. Review progress and status.', ['progress_percent']);
define('in_progress_stage_requires_partial_progress', 'Una fase en proceso debe tener avance mayor que 0% y menor que 100%.', 'An in-progress stage must have progress greater than 0% and less than 100%.', ['progress_percent']);
define('production_order_not_completed', 'La orden de producción aún no está terminada. Revisa su estado antes de realizar esta operación.', 'The production order is not completed yet. Review its status before this operation.');
define('production_order_resource_not_found production_order_stage_not_found', 'El recurso o fase ya no está disponible en esta orden. Actualiza la orden y revisa su detalle.', 'The resource or stage is no longer available in this order. Refresh the order and review its details.');
define('production_request_source_conflict', 'La solicitud de producción entra en conflicto con su documento origen. Revisa si ya existe una orden asociada.', 'The production request conflicts with its source document. Check whether a linked order already exists.');
define('production_machine_required', 'Selecciona la máquina de producción que requiere mantenimiento.', 'Select the production machine that requires maintenance.', ['production_machine_id']);
define('production_machine_not_allowed', 'El tipo de objetivo seleccionado no admite una máquina de producción. Revisa el objetivo y la máquina.', 'The selected target type does not allow a production machine. Review the target and machine.');
define('production_machine_not_in_order maintenance_machine_not_in_order', 'La máquina no pertenece a la orden de producción seleccionada. Revisa ambas selecciones.', 'The machine does not belong to the selected production order. Review both selections.');
define('production_source_references_required', 'Completa la orden de producción y la máquina que originan el mantenimiento.', 'Complete the production order and machine that originated maintenance.');
define('manual_source_reference_not_allowed', 'Un mantenimiento de origen manual no debe incluir una referencia de producción. Revisa el origen seleccionado.', 'Manual maintenance must not include a production reference. Review the selected origin.');
define('production_order_not_maintenance_eligible', 'La orden de producción no admite esta intervención en su estado actual. Revisa su estado antes de continuar.', 'The production order does not allow this intervention in its current state. Review its status before continuing.');
define('machine_held_by_other_maintenance_order', 'La máquina ya está retenida por otra orden de mantenimiento. Revisa la intervención existente.', 'The machine is already held by another maintenance order. Review the existing intervention.');
define('maintenance_order_does_not_hold_machine', 'Esta orden de mantenimiento no tiene retenida la máquina. Revisa el vínculo y el estado de las órdenes.', 'This maintenance order does not hold the machine. Review the link and order statuses.');
define('assigned_worker_required', 'Asigna un técnico a la orden antes de registrar el trabajo.', 'Assign a technician to the order before recording work.');
define('spare_parts_warehouse_required', 'Selecciona un almacén de refacciones activo para esta solicitud.', 'Select an active spare-parts warehouse for this request.', ['warehouse_id']);
define('maintenance_material_invalid', 'Una refacción no es válida para esta solicitud. Revisa el artículo, su unidad y estado.', 'A spare part is invalid for this request. Review the item, its unit and status.');
define('maintenance_time_status_invalid', 'La orden no permite registrar tiempo en su estado actual. Revisa su estado antes de continuar.', 'The order does not allow time entries in its current state. Review its status before continuing.');
define('maintenance_reconciliation_incomplete', 'La conciliación de mantenimiento sigue pendiente. Revisa el estado de materiales y máquina antes de reintentar.', 'Maintenance reconciliation is still pending. Review material and machine status before retrying.');

// Dependencies and authorization: do not claim that a multi-step mutation was rolled back.
define('actor_required actor_mismatch idempotency_actor_mismatch session_context_not_found', 'No se pudo validar la sesión para esta operación. Revisa la empresa activa y vuelve a iniciar sesión.', 'The session could not be validated for this operation. Check the active organization and sign in again.');
define('backoffice_admin_required', 'Esta operación requiere acceso de administración interna. Solicita la revisión de tus permisos.', 'This operation requires internal administration access. Ask for your permissions to be reviewed.');
define('authority_validation_denied hr_worker_validation_denied maintenance_authorization_denied purchasing_authorization_denied sales_authorization_denied production_reference_denied unit_catalog_validation_denied', 'No se autorizó validar una referencia necesaria para esta operación. Solicita al administrador que revise los permisos y módulos habilitados.', 'Validation of a required reference was not authorized. Ask an administrator to review permissions and enabled modules.');
define('authority_unavailable authorization_service_unavailable hr_service_unavailable unit_catalog_unavailable resource_authority_unavailable production_service_unavailable maintenance_dependency_unavailable purchasing_dependency_unavailable inventory_response_incomplete', 'No se pudo consultar un servicio necesario. Conserva la captura y revisa el estado de la operación antes de reintentar.', 'A required service could not be queried. Keep the entered information and check the operation status before retrying.');
define('purchasing_dependency_rejected', 'Un servicio relacionado rechazó la operación de compra. Revisa el documento y las referencias antes de reintentar.', 'A related service rejected the purchasing operation. Review the document and references before retrying.');
define('firebase_admin_missing firebase_emulator_forbidden', 'La autenticación no está configurada correctamente para este ambiente. Solicita al administrador que revise la configuración.', 'Authentication is not configured correctly for this environment. Ask an administrator to review the configuration.');
define('firebase_identity_permission_denied', 'El servicio de identidad no autorizó la operación. Solicita al administrador que revise la configuración de acceso.', 'The identity service did not authorize the operation. Ask an administrator to review access configuration.');
define('firebase_identity_unavailable firebase_invitation_unavailable firebase_invitation_failed', 'No se pudo confirmar la operación de identidad o invitación. Revisa si el usuario ya aparece registrado antes de reintentar.', 'The identity or invitation operation could not be confirmed. Check whether the user is already registered before retrying.');
define('idempotency_key_required', 'Falta la referencia de control de la operación. Conserva tu captura y vuelve a abrir el formulario si el problema continúa.', 'The operation control reference is missing. Keep your entered information and reopen the form if the problem persists.');
define('invalid_cursor', 'La página de resultados ya no es válida. Regresa a la primera página y actualiza la consulta.', 'The results page is no longer valid. Return to the first page and refresh the query.');

// Dynamic schema codes are expanded from the fixed SupplierUpdate field allowlist.
for (const [field, es, en] of [['commercial_name', 'nombre comercial', 'commercial name'], ['currency', 'moneda', 'currency'], ['payment_terms', 'condición de pago', 'payment terms'], ['lead_time_days', 'plazo de entrega', 'lead time'], ['status', 'estado', 'status']]) {
  define(`${field}_cannot_be_null`, `El campo ${es} no puede estar vacío. Completa un valor válido.`, `The ${en} field cannot be empty. Enter a valid value.`, [field]);
}

/** Exact known ValueError strings. Fields are relative to issue.loc for nested validators.
 * Empty fields preserve the supplied issue path or a general summary; never guess a row.
 * The single English literal is a pre-existing schema message, matched exactly (not displayed).
 */
const validationFields = {
  invalid_email: [], required_text_blank: [], invalid_customer_code: [], invalid_tax_id: [],
  incomplete_billing_profile: ['legal_name', 'tax_id', 'billing_email'], empty_update: [],
  invalid_quote_code: [], valid_until_in_past: [], promised_delivery_date_in_past: [],
  duplicate_quote_product: [], invalid_sales_order_code: [], stock_allocations_required: [],
  allocations_only_for_stock: [], duplicate_order_fulfillment_line: [], invalid_delivery_code: [],
  duplicate_delivery_line: [], service_order_plan_dates_invalid: ['scheduled_start_at', 'scheduled_end_at'], reason_too_short: [],
  purchase_line_description_required: [], purchase_unit_required: [], inventory_item_required: ['inventory_item_id'],
  service_inventory_item_forbidden: ['inventory_item_id'], invalid_mexican_rfc: [],
  supplier_fiscal_profile_required: ['tax_id'], invalid_mexican_postal_code: ['fiscal_postal_code'],
  duplicate_requisition_item: [], purchase_origin_required: ['requisition_id', 'direct_purchase_reason'], unit_price_required: [],
  product_inventory_item_required: ['inventory_item_id'], resource_reference_required: ['resource_ref_id'],
  duplicate_recipe_resource: [], duplicate_recipe_stage_area: [], active_recipe_stage_phase_numbers_must_be_contiguous: [],
  active_recipe_stage_weight_must_total_100: [], area_reference_required: ['area_ref_id'],
  planning_start_dates_must_match: ['planned_for', 'planned_start_date'], duplicate_stage_assignment: [],
  pending_stage_requires_zero_progress: ['progress_percent'], in_progress_stage_requires_partial_progress: ['progress_percent'],
  terminal_stage_requires_full_progress: ['progress_percent'],
  maximum_stock_must_be_greater_than_or_equal_to_minimum_stock: ['minimum_stock', 'maximum_stock'],
  'Transfer requires a different destination warehouse': ['destination_warehouse_id'], duplicate_availability_item: [],
  production_machine_required: ['production_machine_id'], production_machine_not_allowed: ['target_type', 'production_machine_id'],
  production_source_references_required: ['source_production_order_id', 'production_machine_id'],
  manual_source_reference_not_allowed: ['source_production_order_id'], assigned_worker_required: ['assigned_worker_id'],
  cancellation_reason_required: ['reason'], invalid_time_interval: ['started_at', 'ended_at'],
  future_time_entry_not_allowed: ['ended_at'], duplicate_material_item: [], invalid_curp: [], invalid_rfc: [],
  invalid_nss: [], invalid_nss_check_digit: [], hire_date_in_future: ['hire_date'],
  invalid_birth_date: ['birth_date', 'hire_date'], invalid_document_logo: []
};
for (const field of ['commercial_name', 'currency', 'payment_terms', 'lead_time_days', 'status']) validationFields[`${field}_cannot_be_null`] = [field];
// The schema emits this fixed-order subset. Enumerate the 31 exact literals instead of parsing arbitrary messages.
const fiscalFields = ['legal_name', 'tax_id', 'tax_regime', 'billing_email', 'fiscal_postal_code'];
for (let mask = 1; mask < 2 ** fiscalFields.length; mask += 1) {
  const fields = fiscalFields.filter((field, index) => mask & (1 << index));
  validationFields[`incomplete_supplier_fiscal_profile:${fields.join(',')}`] = fields;
}
define('transfer_destination_invalid', 'Selecciona un almacén destino diferente al almacén origen.', 'Select a destination warehouse different from the source warehouse.', ['destination_warehouse_id']);
export const VALIDATION_RULES = Object.freeze(Object.fromEntries(Object.entries(validationFields).map(([literal, fields]) => [literal, Object.freeze({ code: literal === 'Transfer requires a different destination warehouse' ? 'transfer_destination_invalid' : literal.startsWith('incomplete_supplier_fiscal_profile:') ? 'incomplete_supplier_fiscal_profile' : literal, fields: Object.freeze(fields) })])));

define('service_evidence_start_required', 'Registra cómo se recibió el servicio antes de esperar recursos o iniciar. Abre la evidencia de inicio.', 'Record the service receipt before waiting for resources or starting. Open start evidence.');
define('service_evidence_finish_required', 'Registra el resultado del servicio en el formulario de avance antes de completar el 100%.', 'Record the service result in the progress form before completing 100%.');
define('service_evidence_service_only', 'La evidencia de servicio solo aplica a órdenes cuya receta proviene de un servicio.', 'Service evidence only applies to orders whose recipe comes from a service.');
define('service_evidence_already_recorded', 'Esta evidencia ya quedó registrada. Recarga la orden para consultar lo guardado; no se sobrescribió.', 'This evidence has already been recorded. Reload the order to review it; nothing was overwritten.');
define('service_evidence_order_locked', 'La orden está cerrada. No se puede agregar evidencia.', 'The order is closed. Evidence cannot be added.');
define('service_evidence_file_invalid', 'El archivo no es válido o su formato no está permitido. Usa una foto compatible, PDF, TXT, DOCX o XLSX.', 'The file is invalid or its format is not allowed. Use a supported photo, PDF, TXT, DOCX or XLSX.', ['files']);
define('service_evidence_file_too_large', 'Reduce la carga: máximo 3 archivos, fotos de hasta 5 MB y documentos de hasta 2 MB.', 'Reduce the upload: at most 3 files, photos up to 5 MB and documents up to 2 MB.', ['files']);
define('service_evidence_file_not_found', 'El adjunto no está disponible. Recarga la orden y consulta su evidencia escrita.', 'The attachment is unavailable. Reload the order and review its written evidence.');
define('service_evidence_expired', 'El adjunto cumplió su año de conservación. La evidencia escrita sigue disponible en la orden.', 'The attachment reached its one-year retention limit. Written evidence is still available on the order.');
define('service_evidence_storage_unavailable', 'No se pudo acceder al almacenamiento de evidencia. Conservamos tu captura; intenta de nuevo.', 'Evidence storage is unavailable. Your entries were kept; try again.');

export const FORM_BUSINESS_ERRORS = Object.freeze(messages);
