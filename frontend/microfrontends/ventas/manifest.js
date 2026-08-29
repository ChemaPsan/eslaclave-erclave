export const manifest = {
  id: "ventas",
  title: "Ventas",
  icon: "VE",
  version: "0.5.0",
  service: "sales-service",
  implementationStatus: "implemented",
  permissions: [
    "sales.customer.read", "sales.customer.create", "sales.customer.update",
    "sales.quote.read", "sales.quote.create", "sales.quote.update", "sales.quote.submit", "sales.quote.approve", "sales.quote.expire", "sales.quote.cancel",
    "sales.order.read", "sales.order.create", "sales.order.fulfill", "sales.order.cancel",
    "sales.delivery.read", "sales.delivery.create", "sales.delivery.confirm", "sales.delivery.cancel"
  ],
  routes: ["/ventas", "/ventas/clientes", "/ventas/cotizaciones", "/ventas/pedidos", "/ventas/entregas", "/ventas/margen"],
  plannedRoutes: ["/ventas/devoluciones"]
};
