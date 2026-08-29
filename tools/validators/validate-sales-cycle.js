const { fail, ok, readText } = require("./shared");

const checks = {
  "backend/alembic/versions/20260818_0018_sales_customers_quotes.py": ["sales.customers", "customer_contacts", "quote_lines", "idempotency_records", "audit_events"],
  "backend/alembic/versions/20260818_0019_sales_orders_deliveries_catalogs.py": ["admin.catalog_items", "sales.orders", "sales.order_lines", "sales.deliveries", "sales_order_requests", "schema=\"production\"", "document.template"],
  "backend/alembic/versions/20260818_0020_sales_chg203_hardening.py": ["inventory_item_ref_id", "for column in (\"fulfillment\", \"cancellation\")", "f\"{column}_state\"", "confirmation_state", "actual_cost_source", "needs_reconciliation"],
  "backend/services/sales-service/app/api.py": ["active_customer_required", "quote_unit_mismatch", "sales.quote.submit", "sales.quote.approve", "sales.order.fulfill", "sales.delivery.confirm", "product_inventory_mapping_mismatch", "mark_fulfillment_reconciliation"],
  "backend/services/sales-service/app/repositories.py": ["class SalesRepository", "prepare_order_fulfillment", "prepare_cancel_order", "prepare_delivery_confirmation", "delivery_quantity_exceeds_uncommitted", "service_actual_cost_required", "inventory_consumption", "on conflict(tenant_id,operation,idempotency_key) do nothing"],
  "backend/services/sales-service/tests/test_sales_repository_integration.py": ["ERCLAVE_TEST_DATABASE_URL", "service_actual_cost_required", "test_fulfillment_claim_is_exclusive", "test_cancel_and_delivery_confirmation_cannot_claim_same_order", "delivery_quantity_exceeds_uncommitted"],
  "backend/services/sales-service/app/authorities.py": ["/v1/hr/workers/sales-eligible", "/v1/production/product-services/", "/v1/catalogs/units-of-measure/by-code/", "/v1/inventory/reservations", "/v1/production/order-requests"],
  "frontend/api/sales.js": ["createSalesCustomer", "createSalesQuote", "submitSalesQuote", "approveSalesQuote", "createSalesOrder", "configureSalesOrderFulfillment", "createSalesDelivery", "confirmSalesDelivery"],
  "frontend/app.js": ["loadSalesApiData", "Promise.allSettled", "renderSalesReferenceWarnings", "register-sales-delivery", "committedByLine", "deliveryActualCost-", "escapeAttribute(record.id)", "inventoryItemId", "isSalesProductServiceEligible", "getDocumentBranding", "getSalesDocumentMatches", "orderLookupPlaceholder", "quoteLookupPlaceholder", "name=\"deliveryDate\""],
  "backend/services/admin-service/app/seeds/catalog.py": ["dependencies=(\"hr\", \"production\")"],
  "backend/services/admin-service/app/repositories.py": ["_validate_module_transition", "module_dependencies_required", "module_dependency_in_use", "insert into admin.role_permissions", "list_catalog_items", "upsert_setting"],
  "frontend/backoffice/app.js": ["dependencies: [\"hr\", \"production\"]", "selectedModuleCodes", "dependencyBlocked"],
  "contracts/api/sales-service.openapi.yaml": ["version: 0.5.0", "/v1/sales/customers", "/v1/sales/quotes", "/v1/sales/orders", "/v1/sales/deliveries", "confirmation_state", "actual_cost_source"],
  "contracts/api/admin-service.openapi.yaml": ["/v1/catalogs/commercial/{catalog_code}", "/v1/document-template"],
  "contracts/api/production-service.openapi.yaml": ["/v1/production/order-requests", "x-implementation-status: implemented"],
  "modulos/04_ventas_clientes.md": ["### Pedidos, surtido y entregas", "## Resultado de auditoria CHG-203", "Devoluciones permanecen `planned`", "20260818_0020"],
  "docs/auditorias/ventas_segundo_corte_2026-08-18.md": ["## Cierre del plan CHG-203", "## Bloqueadores encontrados por CHG-203", "Orquestacion distribuida", "Producto de Ventas -> Articulo de Inventory", "Contenido comercial sin escape consistente"]
};
const errors=[];
for(const [path,fragments] of Object.entries(checks)){const source=readText(path);for(const fragment of fragments)if(!source.includes(fragment))errors.push(`${path} missing ${fragment}`);}
const frontend = readText("frontend/app.js");
const frontendStyles = readText("frontend/styles.css");
for(const token of ["async function openSalesQuotePrintModal", "documentRecordUnavailable", "remove-document-logo"]){if(!frontend.includes(token))errors.push(`Document template guardrail missing ${token}`);}
const productBuilder = frontend.slice(frontend.indexOf("function buildProductServiceFromForm"), frontend.indexOf("function validateProductService"));
if (!productBuilder.includes('inventoryItemId: String(data.get("inventoryItemId")')) errors.push("ProductService form does not persist the authoritative Inventory mapping.");
const laborAreaSaver = frontend.slice(frontend.indexOf("async function saveLaborAreaForm"), frontend.indexOf("function openLaborRoleModal"));
if (laborAreaSaver.includes("inventoryItemId")) errors.push("Labor Area payload must not absorb ProductService Inventory mapping fields.");
const salesUi = frontend.slice(frontend.indexOf("function renderSalesCustomersPanel"), frontend.indexOf("function getSalesFlowTitle"))
  + frontend.slice(frontend.indexOf("function openSalesCustomerModal"), frontend.indexOf("function openProductServiceModal"));
for (const forbidden of ['data-delivery-id="${delivery.id}"', 'data-record-id="${record.id}"']) {
  if (salesUi.includes(forbidden)) errors.push(`Sales UI contains an unescaped mutable attribute: ${forbidden}`);
}
if (frontend.includes("function renderSalesPlannedPanel")) errors.push("Sales UI must not retain obsolete planned copy for implemented Orders and Deliveries.");
if (frontend.includes('["Pedidos","Planeado","warning"]') || frontend.includes('["Orders","Planned","warning"]')) errors.push("Sales root must count implemented Orders instead of labeling them planned.");
for (const token of ["isSalesMarginSubmodule", "renderSalesMarginPanel", 'hasPermission("sales.order.read")', "actualCostSource", 'activeSubmodule: button.dataset.salesMarginTarget', "const isReadOnlySalesMargin", 'module.id === "ventas" && submodule?.id === "margen"']) {
  if (!frontend.includes(token)) errors.push(`Read-only Sales margin projection missing ${token}`);
}
if (!frontendStyles.includes(".topbar-actions .primary-action[hidden]")) errors.push("Hidden topbar actions need an explicit CSS guard so read-only Sales Margin cannot expose generic creation.");
const marginPanel = frontend.slice(frontend.indexOf("function renderSalesMarginPanel"), frontend.indexOf("function findSalesQuoteByCode"));
for (const forbidden of ["mockDb.addModuleRecord", "saveGenericRecordForm", 'data-action="module-primary"']) {
  if (marginPanel.includes(forbidden)) errors.push(`Sales Margin must remain read-only and cannot contain ${forbidden}.`);
}
const salesModuleDoc = readText("modulos/04_ventas_clientes.md");
if (!/\| QA \|[^\n]*sales-service[^\n]*20260821_0023/i.test(salesModuleDoc)) errors.push("Sales module environment table must reflect the deployed QA service and revision 20260821_0023.");
const salesManifest = readText("frontend/microfrontends/ventas/manifest.js");
if (!salesManifest.includes('"/ventas/margen"')) errors.push("Sales manifest must expose the implemented read-only Margin route.");
if(errors.length)fail("sales cycle validation failed",errors);else ok("Sales baseline and CHG-203 correction guardrails are documented and wired.");
