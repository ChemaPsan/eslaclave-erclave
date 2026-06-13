export const manifest = {
  id: "contabilidad",
  title: "Contabilidad",
  icon: "CT",
  version: "0.1.0",
  service: "accounting-service",
  permissions: ["contabilidad:read"],
  routes: ["/contabilidad", "/contabilidad/catalogo-de-cuentas", "/contabilidad/periodos", "/contabilidad/asientos", "/contabilidad/mapeos"]
};
