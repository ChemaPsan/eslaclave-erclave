export const manifest = {
  id: "administracion",
  title: "Administracion",
  icon: "AD",
  version: "0.2.0",
  service: "admin-service",
  implementationStatus: "implemented",
  permissions: [
    "admin.society.read", "admin.society.create", "admin.society.update", "admin.society.status",
    "admin.division.read", "admin.division.create", "admin.division.update", "admin.division.status",
    "admin.fiscal_issuer.read", "admin.fiscal_issuer.create", "admin.fiscal_issuer.update", "admin.fiscal_issuer.status",
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
