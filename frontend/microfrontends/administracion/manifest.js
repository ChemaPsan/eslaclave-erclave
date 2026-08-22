export const manifest = {
  id: "administracion",
  title: "Administracion",
  icon: "AD",
  version: "0.1.0",
  service: "admin-service",
  implementationStatus: "implemented",
  permissions: ["admin.tenant.read"],
  routes: ["/administracion", "/administracion/usuarios", "/administracion/roles", "/administracion/configuracion"]
};
