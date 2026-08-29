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
  "contentFirst=false"
]) {
  if (!frontend.includes(token)) errors.push(`Purchasing UI continuity missing ${token}`);
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
