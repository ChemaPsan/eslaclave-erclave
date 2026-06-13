export const manifest = {
  id: "reportes",
  title: "Reportes",
  icon: "RP",
  version: "0.1.0",
  service: "reporting-service",
  permissions: ["reportes:read"],
  routes: ["/reportes", "/reportes/produccion", "/reportes/inventarios", "/reportes/finanzas", "/reportes/comercial"]
};
