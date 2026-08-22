// Datos demostrativos exclusivamente para el modo mock local. El modo API nunca los mezcla con datos reales.
export const resourceCatalog = [
  { id: "componente_a", name: "Componente A", unit: "PZA", available: 220, cost: 42, type: "Materia prima", source: "Almacenes" },
  { id: "componente_b", name: "Componente B", unit: "PZA", available: 120, cost: 18, type: "Materia prima", source: "Almacenes" },
  { id: "consumible_a", name: "Consumible operativo", unit: "KGM", available: 140, cost: 2.5, type: "Materia prima", source: "Almacenes" },
  { id: "empaque_estandar", name: "Empaque estandar", unit: "PZA", available: 80, cost: 1.2, type: "Materia prima", source: "Almacenes" }
];

export const defaultLaborRoles = [
  { id: "operador_preparacion", name: "Operador de preparacion", areaId: "area_preparacion", area: "Preparacion", position: "Operador", quantity: 2, minutesPerResource: 420, unit: "MIN", available: 840, cost: 1.9, type: "Mano de obra", source: "Areas y puestos", status: "Activo" },
  { id: "operador_proceso", name: "Operador de proceso", areaId: "area_proceso", area: "Proceso", position: "Operador de proceso", quantity: 4, minutesPerResource: 480, unit: "MIN", available: 1920, cost: 2.2, type: "Mano de obra", source: "Areas y puestos", status: "Activo" },
  { id: "inspector_calidad", name: "Inspector de calidad", areaId: "area_calidad", area: "Calidad", position: "Inspector", quantity: 1, minutesPerResource: 240, unit: "MIN", available: 240, cost: 3.4, type: "Mano de obra", source: "Areas y puestos", status: "Activo" }
];

export const defaultLaborAreas = [
  { id: "area_preparacion", code: "PREP", name: "Preparacion", description: "Preparacion de materiales y recursos.", status: "Activo" },
  { id: "area_proceso", code: "PROC", name: "Proceso", description: "Ejecucion de operaciones productivas.", status: "Activo" },
  { id: "area_calidad", code: "CAL", name: "Calidad", description: "Inspeccion y liberacion del resultado.", status: "Activo" }
];

export const defaultMachines = [
  { id: "equipo_proceso_a", name: "Equipo de proceso A", areaId: "area_proceso", area: "Proceso", machineType: "Equipo de proceso", unit: "MIN", available: 480, cost: 1.8, type: "Maquinaria", source: "Maquinaria", status: "Activo" },
  { id: "equipo_proceso_b", name: "Equipo de proceso B", areaId: "area_proceso", area: "Proceso", machineType: "Equipo de proceso", unit: "MIN", available: 360, cost: 2.1, type: "Maquinaria", source: "Maquinaria", status: "Activo" }
];

export const defaultProductsServices = [
  { id: "PROD-DEMO-01", name: "Producto demostrativo", kind: "Producto", unit: "PZA", category: "Manufactura", center: "Produccion / General", status: "Activo", sku: "PROD-DEMO-01", owner: "Operacion", standardCost: 0, targetPrice: 210, expectedMargin: 35, description: "Ejemplo generico disponible solo en modo mock.", createdAt: "2026-05-18" },
  { id: "SER-DEMO-01", name: "Servicio operativo", kind: "Servicio", unit: "E48", category: "Servicios operativos", center: "Produccion / General", status: "Activo", sku: "SER-DEMO-01", owner: "Operacion", standardCost: 0, targetPrice: 450, expectedMargin: 40, description: "Servicio generico con etapas, responsables y tiempos.", createdAt: "2026-05-18" }
];

export const defaultRecipes = [{
  id: "REC-DEMO-01", productServiceId: "PROD-DEMO-01", product: "Producto demostrativo", version: 1,
  quantityBase: 1, unit: "PZA", status: "Activa", approvalStatus: "Aprobada", approvedBy: "Direccion de operaciones",
  approvedAt: "2026-05-18", changeReason: "Receta generica exclusiva del modo mock.", center: "Produccion / General",
  resources: [
    { resourceId: "componente_a", quantity: 2 }, { resourceId: "componente_b", quantity: 1 },
    { resourceId: "equipo_proceso_a", quantity: 30 }, { resourceId: "operador_proceso", quantity: 45 }
  ],
  steps: ["Preparacion", "Proceso", "Validacion", "Entrega"], createdAt: "2026-05-18"
}];

export const defaultOrders = [{
  id: "OP-DEMO-01", recipeId: "REC-DEMO-01", recipeName: "Producto demostrativo", quantity: 10, unit: "PZA",
  status: "En produccion", priority: "Media", dueDate: "2026-05-25", center: "Produccion / General",
  responsible: "Responsable de demostracion", plannedCost: 1439.5, actualCost: null, releaseStatus: "Liberada",
  areas: [
    { area: "Preparacion", responsible: "Operador asignado", status: "Terminada", progress: 100, actualCostFactor: 1 },
    { area: "Proceso", responsible: "Operador asignado", status: "En proceso", progress: 55, actualCostFactor: 1 },
    { area: "Validacion", responsible: "Inspector asignado", status: "Pendiente", progress: 0, actualCostFactor: 1 },
    { area: "Entrega", responsible: "Responsable asignado", status: "Pendiente", progress: 0, actualCostFactor: 1 }
  ], createdAt: "2026-05-18"
}];
