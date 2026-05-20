export const resourceCatalog = [
  { id: "tela_algodon", name: "Tela algodon", unit: "m", available: 220, cost: 42, type: "Materia prima", source: "Almacenes" },
  { id: "hilo_morado", name: "Hilo morado", unit: "cr", available: 12, cost: 85, type: "Materia prima", source: "Almacenes" },
  { id: "etiqueta", name: "Etiqueta", unit: "pz", available: 140, cost: 2.5, type: "Materia prima", source: "Almacenes" },
  { id: "empaque_bolsa", name: "Bolsa empaque", unit: "pz", available: 80, cost: 1.2, type: "Materia prima", source: "Almacenes" },
  { id: "tijeras", name: "Tijeras industriales", unit: "pz", available: 3, cost: 0, type: "Herramienta", source: "Almacenes" },
  { id: "molde_playera", name: "Molde playera", unit: "pz", available: 2, cost: 0, type: "Herramienta", source: "Almacenes" },
  { id: "maquina_recta", name: "Maquina recta", unit: "min", available: 480, cost: 1.8, type: "Maquinaria", source: "Almacenes" },
  { id: "maquina_overlock", name: "Maquina overlock", unit: "min", available: 360, cost: 2.1, type: "Maquinaria", source: "Almacenes" },
  { id: "operador_corte", name: "Operador de corte", unit: "min", available: 420, cost: 1.9, type: "Mano de obra", source: "Recursos Humanos" },
  { id: "costurero", name: "Costurero", unit: "min", available: 960, cost: 2.2, type: "Mano de obra", source: "Recursos Humanos" },
  { id: "supervisor", name: "Supervisor", unit: "min", available: 240, cost: 3.4, type: "Mano de obra", source: "Recursos Humanos" }
];

export const defaultRecipes = [
  {
    id: "REC-221",
    product: "Playera basica morada",
    version: 3,
    quantityBase: 1,
    unit: "pieza",
    status: "Activa",
    center: "Produccion / Costura",
    resources: [
      { resourceId: "tela_algodon", quantity: 2 },
      { resourceId: "hilo_morado", quantity: 0.18 },
      { resourceId: "etiqueta", quantity: 1 },
      { resourceId: "maquina_recta", quantity: 30 },
      { resourceId: "costurero", quantity: 45 }
    ],
    steps: ["Corte", "Costura", "Calidad", "Empaque"],
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
    areas: [
      { area: "Corte", responsible: "Luis Perez", status: "En proceso" },
      { area: "Costura", responsible: "Ana Ruiz", status: "Pendiente" },
      { area: "Calidad", responsible: "Sofia Mendez", status: "Pendiente" },
      { area: "Empaque", responsible: "Carlos Diaz", status: "Pendiente" }
    ],
    createdAt: "2026-05-18"
  }
];
