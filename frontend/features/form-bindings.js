/** Explicit request-to-control bindings. Indices describe submitted payloads, never DOM guesses. */
export const FORM_BINDING_COVERAGE = Object.freeze([
  'standardReportForm', 'admin-invite-user', 'admin-create-role', 'admin-update-corporate',
  'admin-create-legal-entity', 'admin-create-branch', 'admin-code-sequence', 'admin-create-unit',
  'admin-create-commercial-item', 'admin-document-template', 'maintenanceTimeModalForm',
  'maintenanceActionForm', 'maintenanceOrderForm', 'maintenanceMaterialForm', 'maintenanceTimeForm',
  'purchasingCancellationForm', 'purchasingSupplierForm', 'purchasingRequisitionForm',
  'purchasingOrderForm', 'purchasingReceiptForm', 'serviceOrderPlanForm', 'serviceOrderTimeForm',
  'serviceOrderCostForm', 'serviceOrderEvidenceForm', 'serviceTransitionForm',
  'warehouseProductionIssueForm', 'warehousePartsIssueForm', 'genericRecordForm', 'warehouseForm',
  'inventoryItemForm', 'movementForm', 'salesCustomerForm', 'salesQuoteForm', 'finishedGoodsReceiptForm',
  'salesOrderForm', 'salesOrderEditForm', 'salesDeliveryForm', 'productServiceForm', 'laborAreaForm',
  'salesOrderFulfillmentForm', 'adminUnitForm', 'laborRoleForm', 'workerForm', 'machineForm',
  'productionServiceEvidenceForm', 'recipeForm', 'orderForm', 'order-stage-progress', 'auth-email', 'operational-handoff-dialog',
  'login', 'tenant-onboarding', 'tenant-search', 'usage-search', 'tenant-editor'
]);

const ALIASES = {
  productionServiceEvidenceForm: { description: 'startDescription', files: 'startFiles' },
  movementForm: { movement_type: 'movementType', inventory_item_id: 'itemId', warehouse_id: 'warehouseId', destination_warehouse_id: 'destinationWarehouseId', 'source.id': 'sourceDocument', occurred_at: 'movementDate' },
  warehouseForm: { business_center: 'businessCenter', inventory_policy: 'policy' },
  inventoryItemForm: { base_unit: 'unit', suggested_warehouse_id: 'defaultWarehouseId', minimum_stock: 'minStock', maximum_stock: 'maxStock', default_unit_cost: 'defaultUnitCost', use_in_recipe: 'useInRecipe', inventory_policy: 'policy' },
  salesCustomerForm: { commercial_name: 'commercialName', customer_type: 'customerType', responsible_worker_id: 'responsibleWorkerId', 'primary_contact.name': 'contactName', 'primary_contact.email': 'contactEmail', 'primary_contact.phone': 'contactPhone', payment_terms: 'paymentTerms', credit_limit: 'creditLimit', legal_name: 'billingLegalName', tax_id: 'taxId', tax_regime: 'taxRegime', cfdi_use: 'cfdiUse', billing_email: 'billingEmail', billing_phone: 'billingPhone', 'billing_address.street': 'billingStreet', 'billing_address.exterior_number': 'billingExterior', 'billing_address.interior_number': 'billingInterior', 'billing_address.neighborhood': 'billingNeighborhood', 'billing_address.city': 'billingCity', 'billing_address.state': 'billingState', 'billing_address.postal_code': 'billingZipCode', 'billing_address.country': 'billingCountry', notes: 'commercialNotes' },
  salesQuoteForm: { customer_id: 'customerId', payment_terms: 'paymentTerms', valid_until: 'validUntil', promised_delivery_date: 'deliveryPromise' },
  salesOrderForm: { quote_id: 'quoteId', promised_delivery_date: 'deliveryPromise' },
  salesOrderEditForm: { promised_delivery_date: 'deliveryPromise' },
  salesDeliveryForm: { order_id: 'orderId', scheduled_date: 'deliveryDate', recipient_name: 'recipient', evidence_reference: 'deliveryReference' },
  salesOrderFulfillmentForm: { reason: 'cancelReason' },
  finishedGoodsReceiptForm: { production_order_id: 'productionOrderId', warehouse_id: 'warehouseId', received_at: 'receivedAt' },
  productServiceForm: { code: 'sku', type: 'kind', base_unit: 'unit', target_price: 'targetPrice', responsible_area: 'owner', cost_center: 'center', expected_margin: 'expectedMargin', inventory_item_id: 'inventoryItemId' },
  laborRoleForm: { labor_area_id: 'areaId', recipe_name: 'name', resource_quantity: 'quantity', minutes_per_resource: 'minutesPerResource', hourly_cost: 'hourlyCost', intervenes_in_production: 'intervenesInProduction', intervenes_in_maintenance: 'intervenesInMaintenance' },
  machineForm: { machine_type: 'machineType', area_ref_id: 'area', area_name: 'area', available_minutes_per_day: 'available', cost_per_minute: 'cost' },
  recipeForm: { base_quantity: 'quantityBase', base_unit: 'unit', suggested_duration_days: 'suggestedDurationDays', change_reason: 'changeReason', product_service_id: 'productServiceId' },
  orderForm: { recipe_version_id: 'recipeId', planned_start_date: 'plannedStartDate', planned_start_at: 'plannedStartDate', planned_duration_days: 'plannedDurationDays', required_at: 'dueDate', responsible_worker_id: 'responsibleWorkerId' },
  'order-stage-progress': { progress_percent: 'progressPercent' },
  maintenanceTimeModalForm: { started_at: 'time_started_at', ended_at: 'time_ended_at', notes: 'time_notes' },
  'admin-invite-user': { 'role_ids.0': 'role_id' },
  'admin-document-template': { logo_data_url: 'logo' }
};

const SELECTORS = {
  movementForm: { inventory_item_id: '#movementItemSearch' },
  salesQuoteForm: { customer_id: '#quoteCustomerSearch' },
  salesDeliveryForm: { order_id: '[name="orderSearch"]' },
  recipeForm: { product_service_id: '#recipeProductSearch' }
};

function controls(scope) { return [...(scope?.querySelectorAll('input,select,textarea') || [])]; }
function named(scope, name) {
  const matches = controls(scope).filter(control => control.name === name);
  return matches.length === 1 ? matches[0] : null;
}
function leaves(value, prefix = '', result = new Set()) {
  if (value && typeof value === 'object') {
    for (const [key, child] of Object.entries(value)) leaves(child, prefix ? `${prefix}.${key}` : key, result);
  } else if (prefix) result.add(prefix);
  return result;
}

/** Return exact API paths without the FastAPI `body` prefix. Unsupported fields remain summary errors. */
export function captureFormBindings(form, request = {}) {
  const result = Object.create(null);
  if (!form?.querySelectorAll) return result;
  const key = form.id || form.dataset?.form || (form.classList?.contains('operational-handoff-dialog') ? 'operational-handoff-dialog' : '');
  if (!FORM_BINDING_COVERAGE.includes(key)) return result;
  let body;
  try { body = typeof request.body === 'string' ? JSON.parse(request.body) : request.body; } catch { return result; }
  if (!body || typeof body !== 'object') return result;
  const paths = leaves(body);
  const bind = (path, control) => { if (control) result[path] = control; };
  // Exact top-level names are safe only when unique. Repeated controls require explicit row bindings below.
  for (const path of paths) if (!path.includes('.')) bind(path, named(form, path));
  for (const [path, name] of Object.entries(ALIASES[key] || {})) bind(path, named(form, name));
  for (const [path, selector] of Object.entries(SELECTORS[key] || {})) bind(path, form.querySelector(selector));
  if (key === 'maintenanceActionForm' && /\/(?:times|time-entries)(?:\?|$)/.test(request.path || '')) {
    for (const name of ['started_at', 'ended_at', 'notes']) bind(name, named(form, `time_${name}`));
  }
  if (key === 'admin-update-corporate') {
    for (const name of Object.keys(body.value?.corporate || {})) bind(`value.corporate.${name}`, named(form, name));
  }
  const rows = selector => [...form.querySelectorAll(selector)];
  const rowFields = (row, prefix, fields) => {
    if (!row) return;
    for (const [field, name] of Object.entries(fields)) bind(`${prefix}.${field}`, named(row, name));
  };
  if (key === 'salesQuoteForm') {
    const quoteRows = rows('[data-quote-line]');
    (body.lines || []).forEach((line, i) => {
      rowFields(quoteRows[i], `lines.${i}`, { product_service_id: 'lineProductServiceId', quantity: 'lineQuantity', unit: 'lineUnit', unit_price: 'lineUnitPrice', discount_percentage: 'lineDiscount' });
      bind(`lines.${i}.product_service_id`, quoteRows[i]?.querySelector('.quote-product-search'));
    });
  }
  if (key === 'purchasingRequisitionForm' || key === 'maintenanceMaterialForm') {
    const lineRows = rows(key === 'purchasingRequisitionForm' ? '[data-requisition-line]' : '[data-maintenance-material-line]');
    (body.lines || []).forEach((line, i) => rowFields(lineRows[i], `lines.${i}`, Object.fromEntries(Object.keys(line).map(field => [field, field]))));
  }
  if (key === 'purchasingOrderForm') (body.lines || []).forEach((line, i) => bind(`lines.${i}.unit_price`, named(form, `unit_price_${i}`)));
  if (key === 'purchasingReceiptForm') {
    const receiptRows = rows('[data-receipt-line]');
    (body.lines || []).forEach((line, i) => {
      const matches = receiptRows.filter(row => row.dataset.lineId === line.order_line_id);
      if (matches.length === 1) rowFields(matches[0], `lines.${i}`, { quantity: 'quantity', warehouse_id: 'warehouse_id' });
    });
  }
  if (key === 'salesDeliveryForm') (body.lines || []).forEach((line, i) => bind(`lines.${i}.quantity`, named(form, `deliveryQuantity-${line.order_line_id}`)));
  if (key === 'salesOrderFulfillmentForm') (body.lines || []).forEach((line, i) => {
    bind(`lines.${i}.mode`, named(form, `mode-${line.order_line_id}`));
    if (line.allocations?.length === 1) {
      bind(`lines.${i}.allocations.0.inventory_item_id`, named(form, `item-${line.order_line_id}`));
      bind(`lines.${i}.allocations.0.warehouse_id`, named(form, `warehouse-${line.order_line_id}`));
    }
  });
  if (key === 'recipeForm') {
    const resourceRows = rows('[data-resource-row]');
    (body.resources || []).forEach((resource, i) => {
      const matches = resourceRows.filter(row => row.dataset.resourceRow === resource.resource_ref_id);
      if (matches.length === 1) bind(`resources.${i}.quantity`, named(matches[0], `resource_${resource.resource_ref_id}`));
    });
    const selected = controls(form).filter(control => control.name === 'stageAreaId' && control.checked);
    (body.stages || []).forEach((stage, i) => {
      const matches = selected.filter(control => control.value === stage.labor_area_ref_id);
      if (matches.length === 1) bind(`stages.${i}.weight_percent`, matches[0].closest('.recipe-area-option')?.querySelector('[data-stage-weight]'));
    });
  }
  if (key === 'orderForm') {
    const assignments = rows('.area-assignment-row');
    if (assignments.length === (body.stage_assignments || []).length) (body.stage_assignments || []).forEach((stage, i) => bind(`stage_assignments.${i}.responsible_worker_id`, assignments[i].querySelector('select')));
  }
  if (key === 'tenant-onboarding') {
    const owner = { email: 'owner_email', display_name: 'owner_name' };
    for (const [field, name] of Object.entries(owner)) bind(`owner.${field}`, named(form, name));
    const corporate = { commercial_name: 'commercial_name', legal_name: 'legal_name', tax_id: 'tax_id', phone: 'corporate_phone', contact_name: 'owner_name', contact_email: 'owner_email', contact_phone: 'owner_phone', contact_position: 'owner_position' };
    for (const [field, name] of Object.entries(corporate)) bind(`organization_profile.corporate.${field}`, named(form, name));
    const legal = { legal_name: 'legal_entity_name', tax_id: 'tax_id', fiscal_regime: 'fiscal_regime', cfdi_usage: 'cfdi_usage', fiscal_address: 'fiscal_address', contact_name: 'owner_name', contact_email: 'owner_email', contact_phone: 'owner_phone', contact_position: 'owner_position' };
    for (const [field, name] of Object.entries(legal)) bind(`organization_profile.legal_entities.0.${field}`, named(form, name));
    for (const field of ['name', 'code', 'address', 'phone']) bind(`organization_profile.branches.0.${field}`, named(form, `branch_${field}`));
    (body.modules || []).forEach((module, i) => bind(`modules.${i}.module_code`, named(form, `module_${module.module_code}`)));
  }
  // Declarative bindings are authoritative, including omitted fields reported as missing by the server.
  for (const control of controls(form)) {
    for (const path of String(control.dataset?.errorPath || '').split(/\s+/).filter(Boolean)) bind(path.replace(/^body\./, ''), control);
  }
  return result;
}
