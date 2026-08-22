export const manifest = {
  id: "recursos-humanos",
  title: "Recursos Humanos",
  icon: "RH",
  version: "0.1.0",
  service: "hr-service",
  implementationStatus: "implemented",
  permissions: ["hr.area.read", "hr.position.read", "hr.worker.read"],
  routes: ["/recursos-humanos", "/recursos-humanos/areas-puestos", "/recursos-humanos/trabajadores"]
};
