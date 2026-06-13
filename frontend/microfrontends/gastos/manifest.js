export const manifest = {
  id: "gastos",
  title: "Gastos",
  icon: "GA",
  version: "0.1.0",
  service: "expenses-service",
  permissions: ["gastos:read"],
  routes: ["/gastos", "/gastos/carga-documental", "/gastos/cuentas-por-pagar", "/gastos/pagos"]
};
