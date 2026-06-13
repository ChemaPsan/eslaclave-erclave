export const manifest = {
  id: "ventas",
  title: "Ventas",
  icon: "VE",
  version: "0.1.0",
  service: "sales-service",
  permissions: ["ventas:read"],
  routes: ["/ventas", "/ventas/clientes", "/ventas/cotizaciones", "/ventas/pedidos", "/ventas/entregas"]
};
