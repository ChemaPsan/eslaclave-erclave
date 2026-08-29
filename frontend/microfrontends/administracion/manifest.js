export const manifest = {
  id: "administracion",
  title: "Administracion",
  icon: "AD",
  version: "0.2.0",
  service: "admin-service",
  implementationStatus: "implemented",
  permissions: [
    "admin.tenant.read",
    "admin.entitlement.manage",
    "admin.user.read", "admin.user.invite", "admin.user.update", "admin.user.disable", "admin.user.delete",
    "admin.role.read", "admin.role.create", "admin.role.update", "admin.role.permissions.manage",
    "admin.unit.read", "admin.unit.create", "admin.unit.update",
    "admin.catalog.read", "admin.catalog.create", "admin.catalog.update",
    "admin.setting.read", "admin.setting.update"
  ],
  routes: ["/administracion", "/administracion/usuarios", "/administracion/roles", "/administracion/configuracion"]
};
