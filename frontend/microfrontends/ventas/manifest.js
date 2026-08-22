export const manifest = {
  id: "ventas",
  title: "Ventas",
  icon: "VE",
  version: "0.4.0",
  service: "sales-service",
  implementationStatus: "implemented",
  permissions: ["sales.customer.read", "sales.quote.read", "sales.order.read", "sales.delivery.read"],
  routes: ["/ventas", "/ventas/clientes", "/ventas/cotizaciones", "/ventas/pedidos", "/ventas/entregas"],
  plannedRoutes: ["/ventas/devoluciones"]
};
