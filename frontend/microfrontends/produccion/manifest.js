export const manifest = {
  id: "produccion",
  title: "Produccion",
  icon: "PR",
  version: "0.1.0",
  service: "production-service",
  implementationStatus: "implemented",
  permissions: ["production.product_service.read", "production.recipe.read", "production.order.read", "production.order.release", "production.order.wait_resources", "production.order.start", "production.order.pause", "production.order.resume", "production.order.send_to_validation", "production.order.complete", "production.order.cancel", "production.order_stage.reset", "production.order_stage.update", "production.order_stage.complete", "production.order_stage.block", "production.order_stage.skip", "production.machine.read"],
  routes: ["/produccion", "/produccion/productos-servicios", "/produccion/recetas", "/produccion/ordenes"]
};
