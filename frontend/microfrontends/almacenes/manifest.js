export const manifest = {
  id: "almacenes",
  title: "Almacenes",
  icon: "AL",
  version: "0.1.0",
  service: "inventory-service",
  permissions: ["almacenes:read"],
  routes: ["/almacenes", "/almacenes/movimientos", "/almacenes/reservas", "/almacenes/kardex"]
};
