export const manifest = {
  id: "recursos-humanos",
  title: "Recursos Humanos",
  icon: "RH",
  version: "0.2.0",
  service: "hr-service",
  implementationStatus: "implemented",
  permissions: [
    "hr.area.read", "hr.area.create", "hr.area.update",
    "hr.position.read", "hr.position.create", "hr.position.update",
    "hr.worker.read", "hr.worker.create", "hr.worker.update"
  ],
  routes: ["/recursos-humanos", "/recursos-humanos/areas-puestos", "/recursos-humanos/trabajadores"]
};
