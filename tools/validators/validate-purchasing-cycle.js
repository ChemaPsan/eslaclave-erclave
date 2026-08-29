const { fail, ok, readText } = require("./shared");

const frontend = readText("frontend/app.js");
const manifest = readText("frontend/microfrontends/compras/manifest.js");
const errors = [];

for (const token of [
  "purchasingOrderSourceRequisitionId",
  "data-create-order-from-requisition",
  'activeSubmodule:"ordenes-de-compra"',
  "sourceRequisitionId",
  "data-receive-order",
  "purchasingReceiptSourceOrderId",
  'activeSubmodule:"recepciones"',
  "renderReceiptLines",
  'hasPermission("purchasing.order.create")',
  'hasPermission("purchasing.order.issue")',
  'hasPermission("purchasing.receipt.create")',
  "pendingRequisitions=api.requisitions.filter",
  "Todas las ordenes de compra",
  "data-open-pending-purchasing-requisitions",
  'if(id==="reabastecimiento")',
  "No lista ni crea ordenes de compra",
  "contentFirst=false",
  "getPurchasingFlowTitle",
  "getPurchasingFlowSteps",
  '"ordenes-de-compra":[["Origen"',
  'renderFlowGuide(getPurchasingFlowTitle(title),getPurchasingFlowSteps(id))',
  "openPurchasingCancellationModal",
  'id="purchasingCancellationForm"',
  'renderFormErrors([t("cancellationReasonRequired")])'
]) {
  if (!frontend.includes(token)) errors.push(`Purchasing UI continuity missing ${token}`);
}

const purchasingUi = frontend.slice(frontend.indexOf("function purchasingStatus"), frontend.indexOf("function inventoryQueryKey"));
if (/\bprompt\s*\(/.test(purchasingUi)) errors.push("Purchasing cancellations must use the ERClave modal instead of a native prompt.");
if (!purchasingUi.includes('openPurchasingCancellationModal("requisition"') || !purchasingUi.includes('openPurchasingCancellationModal("order"')) {
  errors.push("Requisition and purchase-order cancellation must both use the shared Purchasing modal.");
}

for (const permission of [
  "purchasing.requisition.submit",
  "purchasing.requisition.approve",
  "purchasing.order.create",
  "purchasing.order.issue",
  "purchasing.receipt.create",
  "purchasing.receipt.reconcile"
]) {
  if (!manifest.includes(permission)) errors.push(`Purchasing manifest missing ${permission}`);
}

if (errors.length) fail("purchasing cycle validation failed", errors);
else ok("Purchasing requisition-to-order-to-receipt continuity and permissions are wired.");
