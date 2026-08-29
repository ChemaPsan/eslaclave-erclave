export const manifest = {
  id: "mantenimiento",
  title: "Mantenimiento",
  icon: "MT",
  version: "1.0.0",
  service: "maintenance-service",
  implementationStatus: "implemented",
  permissions: ["maintenance.order.read", "maintenance.order.create", "maintenance.order.update", "maintenance.order.request", "maintenance.order.assign", "maintenance.order.start", "maintenance.order.wait_for_parts", "maintenance.order.resume", "maintenance.order.resolve", "maintenance.order.close", "maintenance.order.reopen", "maintenance.order.cancel", "maintenance.order.reconcile", "maintenance.time.read", "maintenance.time.create", "maintenance.material_request.read", "maintenance.material_request.create", "maintenance.material_request.cancel", "maintenance.material_request.reconcile"],
  routes: [
    "/mantenimiento",
    "/mantenimiento/ordenes",
    "/mantenimiento/ordenes/:id",
    "/mantenimiento/refacciones"
  ]
};
