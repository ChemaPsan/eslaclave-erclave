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
    "sales.service_order.read", "sales.service_order.plan", "sales.service_order.assign", "sales.service_order.start", "sales.service_order.wait", "sales.service_order.resume",
    "sales.service_order.time.create", "sales.service_order.cost.create", "sales.service_order.evidence.create", "sales.service_order.submit_acceptance", "sales.service_order.accept", "sales.service_order.cancel",
    "sales.delivery.read", "sales.delivery.create", "sales.delivery.confirm", "sales.delivery.cancel"
  ],
  routes: ["/ventas", "/ventas/clientes", "/ventas/cotizaciones", "/ventas/pedidos", "/ventas/ordenes-de-servicio", "/ventas/entregas", "/ventas/margen"],
  plannedRoutes: ["/ventas/devoluciones"]
};
