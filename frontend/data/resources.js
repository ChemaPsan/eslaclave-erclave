export const resourceCatalog = [
  { id: "tela_algodon", name: "Tela algodon", unit: "m", available: 220, cost: 42, type: "Materia prima", source: "Almacenes" },
  { id: "hilo_morado", name: "Hilo morado", unit: "cr", available: 12, cost: 85, type: "Materia prima", source: "Almacenes" },
  { id: "etiqueta", name: "Etiqueta", unit: "pz", available: 140, cost: 2.5, type: "Materia prima", source: "Almacenes" },
  { id: "empaque_bolsa", name: "Bolsa empaque", unit: "pz", available: 80, cost: 1.2, type: "Materia prima", source: "Almacenes" },
  { id: "tijeras", name: "Tijeras industriales", unit: "pz", available: 3, cost: 0, type: "Herramienta", source: "Almacenes" },
  { id: "molde_playera", name: "Molde playera", unit: "pz", available: 2, cost: 0, type: "Herramienta", source: "Almacenes" }
];

export const defaultLaborRoles = [
  { id: "operador_corte", name: "Operador de corte", area: "Corte", position: "Operador", quantity: 2, minutesPerResource: 420, unit: "min", available: 840, cost: 1.9, type: "Mano de obra", source: "Areas y puestos", status: "Activo" },
  { id: "costurero", name: "Costurero", area: "Costura", position: "Costurero", quantity: 20, minutesPerResource: 480, unit: "min", available: 9600, cost: 2.2, type: "Mano de obra", source: "Areas y puestos", status: "Activo" },
  { id: "supervisor", name: "Supervisor", area: "Calidad", position: "Supervisor", quantity: 1, minutesPerResource: 240, unit: "min", available: 240, cost: 3.4, type: "Mano de obra", source: "Areas y puestos", status: "Activo" }
];

export const defaultMachines = [
  { id: "maquina_recta", name: "Maquina recta", area: "Costura", machineType: "Costura", unit: "min", available: 480, cost: 1.8, type: "Maquinaria", source: "Maquinaria", status: "Activo" },
  { id: "maquina_overlock", name: "Maquina overlock", area: "Costura", machineType: "Costura", unit: "min", available: 360, cost: 2.1, type: "Maquinaria", source: "Maquinaria", status: "Activo" },
  { id: "cortadora_industrial", name: "Cortadora industrial", area: "Corte", machineType: "Corte", unit: "min", available: 300, cost: 2.6, type: "Maquinaria", source: "Maquinaria", status: "Activo" }
];

export const defaultProductsServices = [
  {
    id: "PROD-221",
    name: "Playera basica morada",
    kind: "Producto",
    unit: "pieza",
    category: "Confeccion",
    center: "Produccion / Costura",
    status: "Activo",
    sku: "PLY-MOR-001",
    owner: "Operacion",
    standardCost: 0,
    targetPrice: 210,
    expectedMargin: 35,
    description: "Producto fabricable para ordenes de produccion.",
    createdAt: "2026-05-18"
  },
  {
    id: "SER-014",
    name: "Servicio de ensamble",
    kind: "Servicio",
    unit: "servicio",
    category: "Servicios operativos",
    center: "Produccion / Ensamble",
    status: "Activo",
    sku: "SER-ENS-014",
    owner: "Operacion",
    standardCost: 0,
    targetPrice: 450,
    expectedMargin: 40,
    description: "Servicio repetible con etapas, responsables y tiempos.",
    createdAt: "2026-05-18"
  },
  {
    id: "SER-022",
    name: "Empaque especial",
    kind: "Servicio",
    unit: "servicio",
    category: "Empaque",
    center: "Produccion / Empaque",
    status: "Activo",
    sku: "SER-EMP-022",
    owner: "Operacion",
    standardCost: 0,
    targetPrice: 180,
    expectedMargin: 30,
    description: "Servicio operativo para empaques por pedido.",
    createdAt: "2026-05-18"
  }
];

export const defaultRecipes = [
  {
    id: "REC-221",
    productServiceId: "PROD-221",
    product: "Playera basica morada",
    version: 3,
    quantityBase: 1,
    unit: "pieza",
    status: "Activa",
    approvalStatus: "Aprobada",
    approvedBy: "Direccion de operaciones",
    approvedAt: "2026-05-18",
    changeReason: "Version vigente para produccion recurrente.",
    center: "Produccion / Costura",
    resources: [
      { resourceId: "tela_algodon", quantity: 2 },
      { resourceId: "hilo_morado", quantity: 0.18 },
      { resourceId: "etiqueta", quantity: 1 },
      { resourceId: "maquina_recta", quantity: 30 },
      { resourceId: "costurero", quantity: 45 }
    ],
    steps: ["Preparacion", "Ejecucion", "Validacion", "Entrega"],
    createdAt: "2026-05-18"
  }
];

export const defaultOrders = [
  {
    id: "OP-1042",
    recipeId: "REC-221",
    recipeName: "Playera basica morada",
    quantity: 100,
    unit: "pieza",
    status: "En produccion",
    priority: "Alta",
    dueDate: "2026-05-25",
    center: "Produccion / Costura",
    responsible: "Mariana Torres",
    plannedCost: 14395,
    actualCost: 15114.75,
    releaseStatus: "Liberada",
    areas: [
      { area: "Preparacion", responsible: "Luis Perez", status: "Terminada", progress: 100, actualCostFactor: 1.02 },
      { area: "Ejecucion", responsible: "Ana Ruiz", status: "En proceso", progress: 55, actualCostFactor: 1.08 },
      { area: "Validacion", responsible: "Sofia Mendez", status: "Pendiente", progress: 0, actualCostFactor: 1 },
      { area: "Entrega", responsible: "Carlos Diaz", status: "Pendiente", progress: 0, actualCostFactor: 1 }
    ],
    createdAt: "2026-05-18"
  }
];
