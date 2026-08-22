export const manifest = {
  id: "produccion",
  title: "Produccion",
  icon: "PR",
  version: "0.1.0",
  service: "production-service",
  implementationStatus: "implemented",
  permissions: ["production.product_service.read", "production.recipe.read", "production.order.read", "production.machine.read"],
  routes: ["/produccion", "/produccion/productos-servicios", "/produccion/recetas", "/produccion/ordenes"]
};
