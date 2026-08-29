export const manifest = {
  id: "almacenes",
  title: "Almacenes",
  icon: "AL",
  version: "0.1.0",
  service: "inventory-service",
  implementationStatus: "implemented",
  permissions: ["inventory.warehouse.read", "inventory.item.read", "inventory.balance.read", "inventory.movement.read", "inventory.kardex.read", "inventory.finished_goods_receipt.read", "inventory.finished_goods_receipt.receive"],
  routes: ["/almacenes", "/almacenes/movimientos", "/almacenes/reservas", "/almacenes/kardex"]
};
