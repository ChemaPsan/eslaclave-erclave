export const manifest = {
  id: "produccion",
  title: "Produccion",
  icon: "PR",
  version: "0.2.0",
  service: "production-service",
  implementationStatus: "implemented",
  permissions: [
    "production.product_service.read", "production.product_service.create", "production.product_service.update", "production.product_service.status.update",
    "production.recipe.read", "production.recipe.create", "production.recipe.update", "production.recipe.submit", "production.recipe.approve", "production.recipe.obsolete",
    "production.machine.read", "production.machine.create", "production.machine.update",
    "production.order.read", "production.order.update", "production.order.validate", "production.order.release", "production.order.wait_resources", "production.order.start", "production.order.pause", "production.order.resume", "production.order.send_to_validation", "production.order.complete", "production.order.cancel",
    "production.order_stage.reset", "production.order_stage.update", "production.order_stage.complete", "production.order_stage.block", "production.order_stage.skip"
  ],
  routes: ["/produccion", "/produccion/productos-servicios", "/produccion/recetas", "/produccion/ordenes"]
};
