export const manifest = {
  id: "compras",
  title: "Compras",
  icon: "CO",
  version: "1.0.0",
  service: "purchasing-service",
  implementationStatus: "implemented",
  permissions: [
    "purchasing.supplier.read", "purchasing.supplier.create", "purchasing.supplier.update",
    "purchasing.requisition.read", "purchasing.requisition.create", "purchasing.requisition.update",
    "purchasing.requisition.submit", "purchasing.requisition.approve", "purchasing.requisition.reject", "purchasing.requisition.cancel",
    "purchasing.order.read", "purchasing.order.create", "purchasing.order.update", "purchasing.order.issue", "purchasing.order.cancel",
    "purchasing.receipt.read", "purchasing.receipt.create", "purchasing.receipt.reconcile"
  ],
  routes: ["/compras", "/compras/proveedores", "/compras/requisiciones", "/compras/ordenes-de-compra", "/compras/recepciones"],
  plannedRoutes: ["/compras/reabastecimiento"]
};
