export const manifest = {
  id: "almacenes",
  title: "Almacenes",
  icon: "AL",
  version: "0.2.0",
  service: "inventory-service",
  implementationStatus: "implemented",
  permissions: [
    "inventory.warehouse.read", "inventory.warehouse.create", "inventory.warehouse.update",
    "inventory.item.read", "inventory.item.create", "inventory.item.update",
    "inventory.balance.read",
    "inventory.movement.read", "inventory.movement.create", "inventory.movement.reverse",
    "inventory.kardex.read",
    "inventory.finished_goods_receipt.read", "inventory.finished_goods_receipt.receive"
  ],
  routes: ["/almacenes", "/almacenes/movimientos", "/almacenes/reservas", "/almacenes/kardex"]
};
