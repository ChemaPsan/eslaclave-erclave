const resourceCatalog = [
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

const defaultRecipes = [
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

const defaultOrders = [
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

const mockDb = {
  loadRecipes() {
    const raw = localStorage.getItem("erclave-recipes");
    return raw ? JSON.parse(raw) : defaultRecipes;
  },
  saveRecipes(recipes) {
    localStorage.setItem("erclave-recipes", JSON.stringify(recipes));
  },
  addRecipe(recipe) {
    const recipes = this.loadRecipes();
    recipes.unshift(recipe);
    this.saveRecipes(recipes);
    return recipes;
  },
  updateRecipe(recipe) {
    const recipes = this.loadRecipes().map((item) => (item.id === recipe.id ? recipe : item));
    this.saveRecipes(recipes);
    return recipes;
  },
  deleteRecipe(recipeId) {
    const recipes = this.loadRecipes().filter((item) => item.id !== recipeId);
    const nextRecipes = recipes.length ? recipes : defaultRecipes;
    this.saveRecipes(nextRecipes);
    return nextRecipes;
  },
  findRecipe(recipeId) {
    return this.loadRecipes().find((item) => item.id === recipeId);
  },
  loadOrders() {
    const raw = localStorage.getItem("erclave-orders");
    return raw ? JSON.parse(raw) : defaultOrders;
  },
  saveOrders(orders) {
    localStorage.setItem("erclave-orders", JSON.stringify(orders));
  },
  addOrder(order) {
    const orders = this.loadOrders();
    orders.unshift(order);
    this.saveOrders(orders);
    return orders;
  },
  updateOrder(order) {
    const orders = this.loadOrders().map((item) => (item.id === order.id ? order : item));
    this.saveOrders(orders);
    return orders;
  },
  findOrder(orderId) {
    return this.loadOrders().find((item) => item.id === orderId);
  }
};

function getResource(id) {
  return resourceCatalog.find((item) => item.id === id);
}

function calculateRecipe(recipe, batchQuantity = 100) {
  const rows = recipe.resources.map((item) => {
    const resource = getResource(item.resourceId);
    const required = Number(item.quantity) * batchQuantity;
    const available = resource?.available || 0;
    const cost = required * (resource?.cost || 0);
    return {
      name: resource?.name || item.resourceId,
      unit: resource?.unit || "",
      type: resource?.type || "",
      source: resource?.source || "",
      required,
      available,
      cost,
      ok: available >= required
    };
  });

  return {
    rows,
    totalCost: rows.reduce((sum, row) => sum + row.cost, 0),
    missing: rows.filter((row) => !row.ok)
  };
}

function getProductionModuleData() {
  const recipes = mockDb.loadRecipes();
  const orders = mockDb.loadOrders();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe");
  const activeRecipe = recipes.find((recipe) => recipe.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const validation = calculateRecipe(activeRecipe, validationQuantity);

  return {
    records: [
      ...orders.slice(0, 2).map((order) => [
        order.id,
        `${order.recipeName} · ${order.quantity} ${order.unit}`,
        order.status
      ]),
      ...recipes.slice(0, 3).map((recipe) => [
        recipe.id,
        `${recipe.product} · version ${recipe.version}`,
        recipe.status
      ]),
      [
        "VAL-REC",
        validation.missing.length
          ? `${activeRecipe.product} · ${validation.missing.length} recursos faltantes`
          : `${activeRecipe.product} · recursos suficientes`,
        validation.missing.length ? "Faltante" : "Validada"
      ]
    ],
    rows: [
      ...orders.slice(0, 4).map((order) => {
        const recipe = recipes.find((item) => item.id === order.recipeId) || activeRecipe;
        const calc = calculateRecipe(recipe, order.quantity);
        return [
          order.id,
          `${order.recipeName} · ${order.quantity} ${order.unit}`,
          order.status,
          calc.missing.length ? `${calc.missing.length} faltantes` : "Sin riesgo"
        ];
      })
    ],
    validation
  };
}

const modules = [
  {
    id: "produccion",
    icon: "PR",
    count: 18,
    title: "Produccion",
    titleEn: "Production",
    eyebrow: "Modulo operativo",
    summary: "Recetas, ordenes, recursos, etapas y validacion automatica contra almacenes.",
    primary: "Generar orden",
    status: "18 ordenes activas",
    kpis: [
      ["Ordenes activas", "18", "positive"],
      ["Faltantes", "3", "warning"],
      ["Merma real", "2.8%", "warning"]
    ],
    submodules: [
      ["Productos y servicios", "Catalogo base para fabricar o ejecutar servicios repetibles."],
      ["Recetas", "Versiones, recursos, etapas, tiempos, merma y rendimiento."],
      ["Ordenes", "Programacion, estados, responsables, prioridad y cantidades."],
      ["Entregables por area", "Corte, ensamble, calidad, empaque y responsables."],
      ["Validacion de recursos", "Disponibilidad, reservas, faltantes y compras sugeridas."]
    ],
    workflow: [
      "Seleccionar receta activa",
      "Calcular recursos por cantidad",
      "Validar inventario y herramientas",
      "Reservar insumos",
      "Ejecutar etapas",
      "Cerrar produccion y generar producto terminado"
    ],
    table: {
      columns: ["Orden", "Producto", "Estado", "Riesgo"],
      rows: []
    },
    validations: [
      ["Almacenes", "Consulta existencias, reservas y faltantes antes de programar."],
      ["Compras", "Recibe requisiciones automaticas si no hay insumos."],
      ["Costos", "Calcula costo estimado y real por orden."],
      ["Contabilidad", "Prepara mapeos para consumo, merma y producto terminado."]
    ],
    form: [
      ["Producto", "Playera basica morada"],
      ["Cantidad", "100 piezas"],
      ["Almacen origen", "Materia prima · Planta 1"],
      ["Centro de costos", "Produccion / Costura"]
    ],
    records: []
  },
  {
    id: "almacenes",
    icon: "AL",
    count: 7,
    title: "Almacenes",
    titleEn: "Warehouses",
    eyebrow: "Inventario vivo",
    summary: "Existencias, reservas, movimientos, kardex, ubicaciones y merma.",
    primary: "Reservar inventario",
    status: "7 articulos criticos",
    kpis: [
      ["Disponible", "$428k", "positive"],
      ["Reservado", "$96k", "warning"],
      ["Mermas mes", "2.1%", "danger"]
    ],
    submodules: [
      ["Almacenes", "Materia prima, herramientas, producto en proceso y terminado."],
      ["Ubicaciones", "Pasillos, racks, zonas y ubicaciones por centro de negocio."],
      ["Movimientos", "Entradas, salidas, transferencias, ajustes y devoluciones."],
      ["Reservas", "Apartado para ordenes de produccion o pedidos de venta."],
      ["Kardex", "Historial completo por articulo, lote, serie o ubicacion."]
    ],
    workflow: [
      "Recibir o registrar movimiento",
      "Validar documento origen",
      "Actualizar existencia",
      "Actualizar reserva o disponibilidad",
      "Actualizar kardex",
      "Notificar costos, ventas o produccion"
    ],
    table: {
      columns: ["Articulo", "Disponible", "Reservado", "Estado"],
      rows: [
        ["Tela algodon", "220 m", "200 m", "Suficiente"],
        ["Hilo morado", "12 cr", "18 cr", "Faltante"],
        ["Playera basica", "86 pz", "40 pz", "Disponible"]
      ]
    },
    validations: [
      ["Produccion", "Responde disponibilidad por receta y genera reservas."],
      ["Ventas", "Reserva producto terminado y registra entregas."],
      ["Compras", "Recibe materiales y actualiza costos de adquisicion."],
      ["Contabilidad", "Genera documentos origen por ajustes, merma y entradas."]
    ],
    form: [
      ["Tipo movimiento", "Reserva por produccion"],
      ["Articulo", "Hilo morado"],
      ["Cantidad", "18 carretes"],
      ["Origen", "Almacen MP / Planta 1"]
    ],
    records: [
      ["MAT-004", "Tela algodon · 220 m disponibles", "Disponible"],
      ["HER-011", "Tijeras industriales · 3 asignables", "Asignable"],
      ["PT-118", "Playera basica · 40 pz reservadas", "Reservado"]
    ]
  },
  {
    id: "compras",
    icon: "CO",
    count: 5,
    title: "Compras",
    titleEn: "Purchasing",
    eyebrow: "Abastecimiento",
    summary: "Requisiciones, ordenes de compra, recepciones y reabastecimiento.",
    primary: "Nueva requisicion",
    status: "5 compras pendientes",
    kpis: [
      ["Requisiciones", "9", "warning"],
      ["Recepciones", "14", "positive"],
      ["Ahorro precio", "6.4%", "positive"]
    ],
    submodules: [
      ["Proveedores", "Datos fiscales, condiciones, tiempos y productos relacionados."],
      ["Requisiciones", "Solicitudes desde faltantes, usuarios o ordenes de produccion."],
      ["Ordenes de compra", "Autorizacion, envio, estado y seguimiento."],
      ["Recepciones", "Parciales, totales y validacion contra pedido."],
      ["Reabastecimiento", "Minimos, puntos de reorden y compras sugeridas."]
    ],
    workflow: [
      "Recibir necesidad o faltante",
      "Crear requisicion",
      "Autorizar por monto o centro",
      "Emitir orden de compra",
      "Registrar recepcion",
      "Enviar a inventario, gasto y contabilidad"
    ],
    table: {
      columns: ["Documento", "Proveedor", "Estado", "Relacion"],
      rows: [
        ["REQ-087", "Textiles Norte", "Solicitada", "OP-1042"],
        ["OC-051", "Hilos MX", "Enviada", "Faltante"],
        ["REC-044", "Avios Centro", "Parcial", "Almacen MP"]
      ]
    },
    validations: [
      ["Almacenes", "Recepcion incrementa existencias y kardex."],
      ["Gastos", "Factura recibida crea cuenta por pagar."],
      ["Costos", "Actualiza costo de adquisicion y fletes."],
      ["Contabilidad", "Mapea inventario, proveedor, impuestos y pagos."]
    ],
    form: [
      ["Necesidad", "Hilo morado faltante"],
      ["Proveedor sugerido", "Hilos MX"],
      ["Fecha requerida", "24 mayo"],
      ["Centro de costos", "Produccion / Costura"]
    ],
    records: [
      ["REQ-087", "Hilo morado · OP-1042", "Solicitada"],
      ["OC-051", "Tela algodon · Proveedor Norte", "Enviada"],
      ["REC-044", "Recepcion parcial · 80%", "Parcial"]
    ]
  },
  {
    id: "ventas",
    icon: "VE",
    count: 12,
    title: "Ventas",
    titleEn: "Sales",
    eyebrow: "Demanda conectada",
    summary: "Clientes, cotizaciones, pedidos, reservas, entregas y margen.",
    primary: "Crear cotizacion",
    status: "12 pedidos abiertos",
    kpis: [
      ["Pedidos", "12", "positive"],
      ["Margen", "32.4%", "positive"],
      ["Entregas riesgo", "2", "warning"]
    ],
    submodules: [
      ["Clientes", "Datos comerciales, contactos, direcciones y condiciones."],
      ["Cotizaciones", "Precios, descuentos, vigencia y margen estimado."],
      ["Pedidos", "Aprobacion, reserva, produccion o surtido."],
      ["Entregas", "Parciales, totales, evidencia y devoluciones."],
      ["Margen", "Costo estimado, costo real y rentabilidad por cliente."]
    ],
    workflow: [
      "Crear cotizacion",
      "Aprobar pedido",
      "Validar inventario disponible",
      "Reservar o solicitar produccion",
      "Entregar parcial o total",
      "Calcular margen y asiento"
    ],
    table: {
      columns: ["Pedido", "Cliente", "Estado", "Margen"],
      rows: [
        ["PED-220", "Uniformes Delta", "En preparacion", "34%"],
        ["COT-144", "Servicios Vega", "Cotizado", "38%"],
        ["PED-228", "Textil Bravo", "Produccion", "29%"]
      ]
    },
    validations: [
      ["Almacenes", "Reserva producto terminado y descuenta en entrega."],
      ["Produccion", "Genera orden si no hay stock suficiente."],
      ["Costos", "Calcula margen estimado y real."],
      ["Contabilidad", "Mapea ingresos, cuentas por cobrar, impuestos y costo de venta."]
    ],
    form: [
      ["Cliente", "Uniformes Delta"],
      ["Producto", "Playera basica morada"],
      ["Cantidad", "140 piezas"],
      ["Fecha prometida", "Viernes 25"]
    ],
    records: [
      ["PED-220", "Uniformes Delta · entrega viernes", "En preparacion"],
      ["COT-144", "Servicio de ensamble · margen 38%", "Cotizado"],
      ["DEV-009", "Devolucion parcial · revision", "Calidad"]
    ]
  },
  {
    id: "gastos",
    icon: "GA",
    count: 9,
    title: "Gastos",
    titleEn: "Expenses",
    eyebrow: "Documentos y pagos",
    summary: "XML, PDF, proveedores, cuentas por pagar, anexos y asignaciones.",
    primary: "Cargar XML",
    status: "9 documentos por validar",
    kpis: [
      ["Por pagar", "$82k", "warning"],
      ["Sin asignar", "4", "danger"],
      ["Pagados", "21", "positive"]
    ],
    submodules: [
      ["Carga documental", "XML, PDF, comprobantes y anexos operativos."],
      ["Clasificacion", "Tipo de gasto, proveedor, impuestos y moneda."],
      ["Asignacion", "Centro de costos, orden, producto, servicio o proyecto."],
      ["Cuentas por pagar", "Vencimientos, pagos parciales y estado."],
      ["Pagos", "Comprobantes, trazabilidad y asiento contable."]
    ],
    workflow: [
      "Cargar XML/PDF",
      "Extraer datos fiscales",
      "Clasificar gasto",
      "Asignar centro o documento origen",
      "Generar cuenta por pagar",
      "Enviar a costos y contabilidad"
    ],
    table: {
      columns: ["Gasto", "Proveedor", "Estado", "Destino"],
      rows: [
        ["XML-330", "CFE", "Pendiente pago", "Produccion general"],
        ["GTO-212", "Mecatronica SA", "Asignado", "Maquina recta"],
        ["PAG-081", "Textiles Norte", "Pagado", "OC-051"]
      ]
    },
    validations: [
      ["Compras", "Compara factura contra orden y recepcion."],
      ["Costos", "Envio de gastos directos, indirectos y prorrateos."],
      ["Contabilidad", "Anexo XML/PDF, cuenta por pagar y asiento."],
      ["Reportes", "Gastos por proveedor, centro y periodo."]
    ],
    form: [
      ["Documento", "XML + PDF"],
      ["Proveedor", "Mecatronica SA"],
      ["Concepto", "Mantenimiento maquina"],
      ["Asignacion", "Centro mantenimiento"]
    ],
    records: [
      ["XML-330", "Energia planta · mayo", "Pendiente pago"],
      ["GTO-212", "Mantenimiento maquina recta", "Asignado"],
      ["PAG-081", "Pago proveedor · transferencia", "Registrado"]
    ]
  },
  {
    id: "costos",
    icon: "CS",
    count: 6,
    title: "Costos",
    titleEn: "Costs",
    eyebrow: "Rentabilidad",
    summary: "Costo estimado, real, variaciones, centros de costos y costo de venta.",
    primary: "Ver variacion",
    status: "6 variaciones relevantes",
    kpis: [
      ["Costo real", "$18.9k", "warning"],
      ["Variacion", "+4.2%", "warning"],
      ["Rentabilidad", "31%", "positive"]
    ],
    submodules: [
      ["Centros de costos", "Areas, centros de negocio, maquinas y responsables."],
      ["Costo estimado", "Desde receta, insumos, mano de obra y maquinaria."],
      ["Costo real", "Desde consumos, gastos, compras, tiempos y merma."],
      ["Variaciones", "Diferencias entre planeado, real y estandar."],
      ["Rentabilidad", "Margen por producto, servicio, cliente y periodo."]
    ],
    workflow: [
      "Tomar costo estimado de receta",
      "Recibir consumos reales",
      "Sumar gastos asignados",
      "Comparar variaciones",
      "Calcular costo de venta",
      "Publicar a reportes y contabilidad"
    ],
    table: {
      columns: ["Objeto", "Estimado", "Real", "Variacion"],
      rows: [
        ["OP-1042", "$18,420", "$19,194", "+4.2%"],
        ["CC-CORTE", "$8,100", "$7,980", "-1.5%"],
        ["MER-020", "$620", "$870", "+40%"]
      ]
    },
    validations: [
      ["Produccion", "Costo por orden, merma y horas."],
      ["Almacenes", "Valuacion de insumos y producto terminado."],
      ["Ventas", "Costo de venta y margen."],
      ["Contabilidad", "Variaciones, costo de venta y producto en proceso."]
    ],
    form: [
      ["Centro", "Costura"],
      ["Orden", "OP-1042"],
      ["Costo base", "Receta v3"],
      ["Metodo", "Promedio + real"]
    ],
    records: [
      ["OP-1042", "Costo estimado $18,420", "Vs real +4.2%"],
      ["CC-CORTE", "Centro de costo corte", "Dentro rango"],
      ["MER-020", "Merma tela · 2.8%", "Advertencia"]
    ]
  },
  {
    id: "contabilidad",
    icon: "CT",
    count: 11,
    title: "Contabilidad",
    titleEn: "Accounting",
    eyebrow: "Asientos y anexos",
    summary: "Cuentas, periodos, polizas, mapeos contables y documentos origen.",
    primary: "Validar asiento",
    status: "11 pendientes contables",
    kpis: [
      ["Asientos", "54", "positive"],
      ["Sin mapeo", "11", "danger"],
      ["Periodo", "Mayo", "positive"]
    ],
    submodules: [
      ["Catalogo de cuentas", "Cuentas, niveles, naturaleza y movimiento."],
      ["Periodos", "Apertura, revision, cierre y reapertura autorizada."],
      ["Asientos", "Cargos, abonos, polizas, estados y reversos."],
      ["Mapeos", "Reglas por modulo, operacion, producto, gasto o impuesto."],
      ["Anexos", "XML, PDF, pagos, ordenes, entregas y documentos origen."]
    ],
    workflow: [
      "Recibir documento origen",
      "Evaluar regla de mapeo",
      "Generar asiento balanceado",
      "Adjuntar anexos",
      "Validar o dejar pendiente",
      "Contabilizar en periodo"
    ],
    table: {
      columns: ["Asiento", "Origen", "Estado", "Periodo"],
      rows: [
        ["ASI-510", "Venta PED-220", "Generado", "Mayo"],
        ["MAP-018", "Merma ALM-338", "Sin mapeo", "Mayo"],
        ["POL-090", "Gasto XML-330", "Contabilizado", "Mayo"]
      ]
    },
    validations: [
      ["Ventas", "Ingresos, clientes, impuestos y costo de venta."],
      ["Gastos", "Cuentas por pagar, pagos y anexos."],
      ["Almacenes", "Inventario, ajustes, merma y transferencias."],
      ["Costos", "Variaciones, producto en proceso y rentabilidad."]
    ],
    form: [
      ["Periodo", "Mayo 2026"],
      ["Documento origen", "PED-220"],
      ["Regla", "Venta producto nacional"],
      ["Estado", "Pendiente validar"]
    ],
    records: [
      ["ASI-510", "Venta PED-220 · ingreso", "Generado"],
      ["MAP-018", "Merma sin cuenta contable", "Pendiente"],
      ["POL-090", "Gasto energia · XML anexo", "Contabilizado"]
    ]
  },
  {
    id: "reportes",
    icon: "RP",
    count: 14,
    title: "Reportes",
    titleEn: "Reports",
    eyebrow: "Inteligencia operativa",
    summary: "Indicadores por modulo, periodo, centro, producto, cliente y proveedor.",
    primary: "Ver tablero",
    status: "14 reportes listos",
    kpis: [
      ["Dashboards", "8", "positive"],
      ["Exportaciones", "36", "positive"],
      ["Alertas", "5", "warning"]
    ],
    submodules: [
      ["Produccion", "Ordenes, avance, cumplimiento, carga y merma."],
      ["Inventarios", "Disponibles, reservas, kardex, rotacion y criticos."],
      ["Finanzas", "Gastos, costos, asientos, cuentas y rentabilidad."],
      ["Comercial", "Ventas, pedidos, clientes, margen y demanda."],
      ["Constructor", "Filtros, columnas, agrupaciones y exportaciones."]
    ],
    workflow: [
      "Elegir indicador",
      "Aplicar filtros por dimension",
      "Cruzar datos de modulos",
      "Guardar vista por rol",
      "Exportar o compartir",
      "Dar seguimiento a alertas"
    ],
    table: {
      columns: ["Reporte", "Dimension", "Estado", "Uso"],
      rows: [
        ["RPT-01", "Produccion por area", "Actualizado", "Diario"],
        ["RPT-08", "Margen por cliente", "Listo", "Semanal"],
        ["RPT-12", "Asientos por periodo", "Finanzas", "Mensual"]
      ]
    },
    validations: [
      ["Administracion", "Respeta rol, alcance y centro de negocio."],
      ["Contabilidad", "Periodos, cuentas y asientos."],
      ["Costos", "Rentabilidad y variaciones."],
      ["Todos", "Usa dimensiones comunes y documentos origen."]
    ],
    form: [
      ["Vista", "Margen por cliente"],
      ["Periodo", "Mayo 2026"],
      ["Centro", "Planta 1"],
      ["Exportacion", "Excel / PDF"]
    ],
    records: [
      ["RPT-01", "Produccion pendiente por area", "Actualizado"],
      ["RPT-08", "Margen por cliente", "Listo"],
      ["RPT-12", "Asientos por periodo", "Finanzas"]
    ]
  }
];

const flow = [
  ["1", "Pedido aprobado", "Ventas reserva inventario o solicita produccion."],
  ["2", "Orden programada", "Produccion valida receta contra almacenes."],
  ["3", "Faltante detectado", "Compras recibe requisicion automatica."],
  ["4", "Insumos consumidos", "Almacen descuenta y Costos calcula real."],
  ["5", "Asiento generado", "Contabilidad recibe documento origen y anexo."]
];

const translations = {
  es: {
    tenant: "Cliente piloto",
    title: "Centro operativo",
    search: "Buscar orden, producto, cliente",
    newOrder: "Nueva orden",
    metricProduction: "Produccion activa",
    metricInventory: "Inventario critico",
    metricMargin: "Margen estimado",
    metricAccounting: "Pendiente contable",
    synergy: "Sinergia",
    flowTitle: "Flujo vivo",
    recipe: "Receta",
    createPurchase: "Generar requisicion"
  },
  en: {
    tenant: "Pilot customer",
    title: "Operations center",
    search: "Search order, product, customer",
    newOrder: "New order",
    metricProduction: "Active production",
    metricInventory: "Critical inventory",
    metricMargin: "Estimated margin",
    metricAccounting: "Accounting pending",
    synergy: "Synergy",
    flowTitle: "Live flow",
    recipe: "Recipe",
    createPurchase: "Create requisition"
  }
};

const state = {
  active: modules[0].id,
  theme: localStorage.getItem("erclave-theme") || "light",
  lang: localStorage.getItem("erclave-lang") || "es"
};

const shell = document.querySelector(".app-shell");
const moduleNav = document.getElementById("moduleNav");
const modulePanel = document.getElementById("modulePanel");
const flowList = document.getElementById("flowList");
const themeToggle = document.getElementById("themeToggle");
const langToggle = document.getElementById("langToggle");
const topbarPrimary = document.querySelector(".topbar .primary-action");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalContent = document.getElementById("modalContent");
const toast = document.getElementById("toast");

function renderNav() {
  moduleNav.innerHTML = modules
    .map((module) => {
      const label = state.lang === "en" ? module.titleEn : module.title;
      return `
        <button class="nav-button ${module.id === state.active ? "active" : ""}" type="button" data-module="${module.id}" title="${label}">
          <span class="nav-icon">${module.icon}</span>
          <span>${label}</span>
          <small class="nav-count">${module.count}</small>
        </button>
      `;
    })
    .join("");

  moduleNav.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.active = button.dataset.module;
      render();
    });
  });
}

function renderPanel() {
  const module = { ...(modules.find((item) => item.id === state.active) || modules[0]) };
  if (module.id === "produccion") {
    const production = getProductionModuleData();
    module.table = { ...module.table, rows: production.rows };
    module.records = production.records;
    module.kpis = [
      ["Ordenes activas", String(mockDb.loadOrders().filter((order) => order.status === "En produccion").length), "positive"],
      ["Faltantes", String(production.validation.missing.length), production.validation.missing.length ? "warning" : "positive"],
      [`Costo lote ${Number(localStorage.getItem("erclave-validation-qty") || 100)}`, formatCurrency(production.validation.totalCost), "positive"]
    ];
  }
  const label = state.lang === "en" ? module.titleEn : module.title;

  modulePanel.innerHTML = `
    <div class="panel-head">
      <div>
        <p class="eyebrow">${module.eyebrow}</p>
        <h2>${label}</h2>
      </div>
      <span class="chip active">${module.status}</span>
    </div>

    <div class="module-summary expanded">
      <div class="module-hero">
        <h1>${label}</h1>
        <p>${module.summary}</p>
        <button class="primary-action hero-action" type="button" data-action="${module.id === "produccion" ? "open-order" : "module-primary"}">
          <span>＋</span>
          <span>${module.primary}</span>
        </button>
      </div>

      <div class="module-kpis">
        ${module.kpis
          .map(
            ([name, value, tone]) => `
              <article class="mini-kpi ${tone}">
                <span>${name}</span>
                <strong>${value}</strong>
              </article>
            `
          )
          .join("")}
      </div>
    </div>

    <div class="module-section-grid">
      <section class="section-card wide">
        <div class="section-title">
          <span class="section-icon">▦</span>
          <strong>Submodulos</strong>
        </div>
        <div class="submodule-grid">
          ${module.submodules
            .map(
              ([name, detail]) => `
                <article class="submodule-card">
                  <strong>${name}</strong>
                  <p>${detail}</p>
                </article>
              `
            )
            .join("")}
        </div>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">↳</span>
          <strong>Flujo operativo</strong>
        </div>
        <ol class="workflow-list">
          ${module.workflow.map((step) => `<li>${step}</li>`).join("")}
        </ol>
      </section>

      <section class="section-card">
        <div class="section-title">
          <span class="section-icon">✓</span>
          <strong>Compatibilidad</strong>
        </div>
        <div class="compat-list">
          ${module.validations
            .map(
              ([name, detail]) => `
                <article>
                  <strong>${name}</strong>
                  <p>${detail}</p>
                </article>
              `
            )
            .join("")}
        </div>
      </section>
    </div>

    <div class="module-workbench">
      <section class="section-card table-card">
        <div class="section-title">
          <span class="section-icon">☷</span>
          <strong>Vista de trabajo</strong>
        </div>
        <div class="data-table" role="table">
          <div class="table-row table-head" role="row">
            ${module.table.columns.map((column) => `<span role="columnheader">${column}</span>`).join("")}
          </div>
          ${module.table.rows
            .map(
              (row) => `
                <div class="table-row" role="row">
                  ${row.map((cell) => `<span role="cell">${cell}</span>`).join("")}
                </div>
              `
            )
            .join("")}
        </div>
      </section>

      <section class="section-card form-preview">
        <div class="section-title">
          <span class="section-icon">✎</span>
          <strong>Captura rapida</strong>
        </div>
        ${module.form
          .map(
            ([labelText, value]) => `
              <label class="preview-field">
                <span>${labelText}</span>
                <input type="text" value="${value}" readonly />
              </label>
            `
          )
          .join("")}
        <button class="secondary-action full" type="button" data-action="${module.id === "produccion" ? "open-recipe" : "module-primary"}">${module.id === "produccion" ? "Nueva receta" : "Abrir formulario"}</button>
      </section>
    </div>

    ${module.id === "produccion" ? renderRecipeValidationCard() : ""}

    <div class="records module-records">
      ${module.records
        .map(
          ([code, desc, status]) => `
            <article class="record-row">
              <div class="record-main">
                <strong>${code}</strong>
                <span>${desc}</span>
              </div>
              <span class="chip">${status}</span>
            </article>
          `
        )
        .join("")}
    </div>
  `;

  modulePanel.querySelectorAll("[data-action='open-recipe']").forEach((button) => {
    button.addEventListener("click", openRecipeModal);
  });
  modulePanel.querySelectorAll("[data-action='open-order']").forEach((button) => {
    button.addEventListener("click", openOrderModal);
  });
  const validationQuantity = modulePanel.querySelector("#validationQuantity");
  if (validationQuantity) {
    validationQuantity.addEventListener("input", (event) => {
      localStorage.setItem("erclave-validation-qty", Math.max(1, Number(event.target.value || 1)));
      render();
    });
  }
  const selectedRecipe = modulePanel.querySelector("#selectedRecipe");
  if (selectedRecipe) {
    selectedRecipe.addEventListener("change", (event) => {
      localStorage.setItem("erclave-selected-recipe", event.target.value);
      render();
    });
  }
  modulePanel.querySelectorAll("[data-action='edit-recipe']").forEach((button) => {
    button.addEventListener("click", () => openRecipeModal(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='delete-recipe']").forEach((button) => {
    button.addEventListener("click", () => deleteRecipe(button.dataset.recipeId));
  });
  modulePanel.querySelectorAll("[data-action='print-order']").forEach((button) => {
    button.addEventListener("click", () => openOrderPrintModal(button.dataset.orderId));
  });
  modulePanel.querySelectorAll("[data-action='advance-order']").forEach((button) => {
    button.addEventListener("click", () => advanceOrderStatus(button.dataset.orderId));
  });
}

function renderRecipeValidationCard() {
  const recipes = mockDb.loadRecipes();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe");
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const validationQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);
  const validation = calculateRecipe(recipe, validationQuantity);

  return `
    <section class="section-card recipe-validator">
      <div class="section-title">
        <span class="section-icon">✓</span>
        <strong>Validacion de receta contra almacen</strong>
      </div>
      <div class="validator-head">
        <div>
          <span class="muted-label">Receta activa</span>
          <strong>${recipe.product}</strong>
        </div>
        <label class="quantity-control recipe-select-control">
          <span>Receta</span>
          <select id="selectedRecipe">
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${item.id} · ${item.product}
                  </option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="quantity-control">
          <span>Cantidad a producir</span>
          <input id="validationQuantity" type="number" min="1" value="${validationQuantity}" />
        </label>
        <span class="chip ${validation.missing.length ? "warning" : "active"}">
          ${validation.missing.length ? "Faltantes detectados" : "Lista para producir"}
        </span>
      </div>
      <p class="helper-copy">La validacion multiplica los recursos de la receta por la cantidad indicada. Materiales, herramientas y maquinaria vienen de Almacenes; mano de obra viene de Recursos Humanos.</p>
      <div class="inline-actions">
        <button class="primary-action" type="button" data-action="open-order">Generar orden de produccion</button>
        <button class="secondary-action" type="button" data-action="open-recipe">Nueva receta</button>
      </div>
      <div class="resource-check-grid">
        ${validation.rows
          .map(
            (row) => `
              <article class="resource-check ${row.ok ? "ok" : "risk"}">
                <div>
                  <strong>${row.name}</strong>
                  <span>${row.type} · ${row.source}</span>
                </div>
                <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
              </article>
            `
          )
          .join("")}
      </div>
    </section>
    ${renderOrderList(mockDb.loadOrders())}
    ${renderRecipeList(recipes)}
  `;
}

function renderOrderList(orders) {
  return `
    <section class="section-card recipe-list-card">
      <div class="section-title">
        <span class="section-icon">▤</span>
        <strong>Ordenes de produccion</strong>
      </div>
      <div class="recipe-list">
        ${orders
          .map((order) => `
            <article class="recipe-list-row order-list-row">
              <div>
                <strong>${order.id} · ${order.recipeName}</strong>
                <span>${order.quantity} ${order.unit} · entrega ${order.dueDate || "sin fecha"} · responsable ${order.responsible}</span>
              </div>
              <span class="chip ${order.status === "Terminada" ? "active" : "warning"}">${order.status}</span>
              <div class="row-actions">
                <button class="secondary-action small-action" type="button" data-action="advance-order" data-order-id="${order.id}">Estatus</button>
                <button class="secondary-action small-action" type="button" data-action="print-order" data-order-id="${order.id}">PDF/Imprimir</button>
              </div>
            </article>
          `)
          .join("")}
      </div>
    </section>
  `;
}

function renderRecipeList(recipes) {
  return `
    <section class="section-card recipe-list-card">
      <div class="section-title">
        <span class="section-icon">☷</span>
        <strong>Recetas guardadas</strong>
      </div>
      <div class="recipe-list">
        ${recipes
          .map((recipe) => {
            const validation = calculateRecipe(recipe, Number(localStorage.getItem("erclave-validation-qty") || 100));
            return `
              <article class="recipe-list-row">
                <div>
                  <strong>${recipe.id} · ${recipe.product}</strong>
                  <span>v${recipe.version} · ${recipe.resources.length} recursos · ${recipe.steps.length} etapas · ${formatCurrency(validation.totalCost)}</span>
                </div>
                <span class="chip ${validation.missing.length ? "warning" : "active"}">
                  ${validation.missing.length ? `${validation.missing.length} faltantes` : "Validada"}
                </span>
                <div class="row-actions">
                  <button class="secondary-action small-action" type="button" data-action="edit-recipe" data-recipe-id="${recipe.id}">Editar</button>
                  <button class="secondary-action small-action danger-action" type="button" data-action="delete-recipe" data-recipe-id="${recipe.id}">Eliminar</button>
                </div>
              </article>
            `;
          })
          .join("")}
      </div>
    </section>
  `;
}

function renderFlow() {
  flowList.innerHTML = flow
    .map(
      ([step, title, detail]) => `
        <article class="flow-item">
          <span class="flow-step">${step}</span>
          <div>
            <strong>${title}</strong>
            <p>${detail}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function formatCurrency(value) {
  return new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN",
    maximumFractionDigits: 0
  }).format(value);
}

function formatNumber(value) {
  return new Intl.NumberFormat("es-MX", {
    maximumFractionDigits: 2
  }).format(value);
}

function showToast(message) {
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(showToast.timeout);
  showToast.timeout = window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
}

function closeModal() {
  modalBackdrop.hidden = true;
  modalContent.innerHTML = "";
}

function openRecipeModal(recipeId = null) {
  const existingRecipe = recipeId ? mockDb.findRecipe(recipeId) : null;
  const isEditing = Boolean(existingRecipe);
  const recipeResources = existingRecipe?.resources?.length
    ? existingRecipe.resources
    : ["tela_algodon", "hilo_morado", "etiqueta", "maquina_recta", "costurero"].map((id) => ({
        resourceId: id,
        quantity: suggestedQuantity(id)
      }));

  modalContent.innerHTML = `
    <form class="recipe-form" id="recipeForm">
      <input type="hidden" name="recipeId" value="${existingRecipe?.id || ""}" />
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">${isEditing ? "Editar receta" : "Nueva receta"}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
        <label class="preview-field">
          <span>Producto o servicio</span>
          <input name="product" type="text" placeholder="Ej. Playera premium" value="${existingRecipe?.product || ""}" required />
        </label>
        <label class="preview-field">
          <span>Version</span>
          <input name="version" type="number" min="1" value="${existingRecipe?.version || 1}" required />
        </label>
        <label class="preview-field">
          <span>Cantidad base</span>
          <input name="quantityBase" type="number" min="1" value="${existingRecipe?.quantityBase || 1}" required />
        </label>
        <label class="preview-field">
          <span>Unidad</span>
          <input name="unit" type="text" value="${existingRecipe?.unit || "pieza"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Centro de costos</span>
          <input name="center" type="text" value="${existingRecipe?.center || "Produccion / Costura"}" required />
        </label>
        <label class="preview-field wide-field">
          <span>Cantidad para validar lote simulado</span>
          <input name="simulationQuantity" type="number" min="1" value="${localStorage.getItem("erclave-validation-qty") || 100}" required />
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">▦</span>
        <strong>Recursos por unidad</strong>
      </div>

      <p class="helper-copy">Solo puedes agregar recursos dados de alta previamente en Almacenes o Recursos Humanos. Este mock simula esos catalogos.</p>

      <div class="resource-picker">
        <select id="resourceSelect" aria-label="Seleccionar recurso">
          ${resourceCatalog
            .map(
              (resource) => `
                <option value="${resource.id}">
                  ${resource.name} · ${resource.type} · ${resource.source}
                </option>
              `
            )
            .join("")}
        </select>
        <button class="secondary-action" type="button" data-action="add-resource">Agregar recurso</button>
      </div>

      <div class="selected-resource-list" id="selectedResourceList">
        ${recipeResources
          .map((item) => renderSelectedResourceRow(item.resourceId, item.quantity))
          .join("")}
      </div>

      <label class="preview-field">
        <span>Etapas</span>
        <input name="steps" type="text" value="${existingRecipe?.steps?.join(", ") || "Corte, Costura, Calidad, Empaque"}" />
      </label>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="preview-recipe">Validar recursos</button>
        <button class="primary-action" type="submit">${isEditing ? "Actualizar receta" : "Guardar receta"}</button>
      </div>

      <div class="recipe-preview" id="recipePreview"></div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='add-resource']").addEventListener("click", addResourceRow);
  modalContent.querySelector("[data-action='preview-recipe']").addEventListener("click", previewRecipeForm);
  modalContent.querySelector("#recipeForm").addEventListener("submit", saveRecipeForm);
  bindResourceRowActions();
}

function renderSelectedResourceRow(resourceId, quantity = 0) {
  const resource = getResource(resourceId);
  if (!resource) return "";
  return `
    <div class="selected-resource-row" data-resource-row="${resource.id}">
      <div>
        <strong>${resource.name}</strong>
        <span>${resource.type} · ${resource.source} · disponible ${formatNumber(resource.available)} ${resource.unit}</span>
      </div>
      <label>
        <span>Cantidad</span>
        <input name="resource_${resource.id}" type="number" min="0" step="0.01" value="${quantity}" />
      </label>
      <button class="icon-button remove-resource" type="button" data-action="remove-resource" aria-label="Quitar recurso">×</button>
    </div>
  `;
}

function addResourceRow() {
  const select = modalContent.querySelector("#resourceSelect");
  const list = modalContent.querySelector("#selectedResourceList");
  const resourceId = select.value;
  if (list.querySelector(`[data-resource-row="${resourceId}"]`)) {
    showToast("Ese recurso ya esta en la receta.");
    return;
  }
  list.insertAdjacentHTML("beforeend", renderSelectedResourceRow(resourceId, 1));
  bindResourceRowActions();
}

function bindResourceRowActions() {
  modalContent.querySelectorAll("[data-action='remove-resource']").forEach((button) => {
    button.onclick = () => {
      button.closest("[data-resource-row]").remove();
    };
  });
}

function suggestedQuantity(resourceId) {
  const defaults = {
    tela_algodon: 2,
    hilo_morado: 0.18,
    etiqueta: 1,
    tijeras: 0,
    maquina_recta: 30,
    costurero: 45
  };
  return defaults[resourceId] ?? 0;
}

function buildRecipeFromForm(form) {
  const data = new FormData(form);
  const recipeId = String(data.get("recipeId") || "").trim();
  const selectedRows = [...form.querySelectorAll("[data-resource-row]")];
  const resources = selectedRows
    .map((row) => {
      const resourceId = row.dataset.resourceRow;
      return {
        resourceId,
        quantity: Number(data.get(`resource_${resourceId}`) || 0)
      };
    })
    .filter((item) => item.quantity > 0);

  return {
    id: recipeId || `REC-${Date.now().toString().slice(-5)}`,
    product: String(data.get("product") || "").trim(),
    version: Number(data.get("version") || 1),
    quantityBase: Number(data.get("quantityBase") || 1),
    unit: String(data.get("unit") || "").trim(),
    status: recipeId ? (mockDb.findRecipe(recipeId)?.status || "Activa") : "Borrador",
    center: String(data.get("center") || "").trim(),
    resources,
    steps: String(data.get("steps") || "")
      .split(",")
      .map((step) => step.trim())
      .filter(Boolean),
    createdAt: recipeId ? (mockDb.findRecipe(recipeId)?.createdAt || new Date().toISOString().slice(0, 10)) : new Date().toISOString().slice(0, 10)
  };
}

function validateRecipe(recipe) {
  const errors = [];
  if (!recipe.product) errors.push("Captura el producto o servicio.");
  if (!recipe.unit) errors.push("Captura la unidad base.");
  if (!recipe.center) errors.push("Selecciona o captura centro de costos.");
  if (!recipe.resources.length) errors.push("Agrega al menos un recurso con cantidad mayor a cero.");
  if (!recipe.steps.length) errors.push("Captura al menos una etapa.");
  return errors;
}

function renderFormErrors(errors) {
  const box = modalContent.querySelector("#formErrors");
  if (!errors.length) {
    box.hidden = true;
    box.innerHTML = "";
    return;
  }
  box.hidden = false;
  box.innerHTML = errors.map((error) => `<p>${error}</p>`).join("");
}

function previewRecipeForm() {
  const form = modalContent.querySelector("#recipeForm");
  const recipe = buildRecipeFromForm(form);
  const simulationQuantity = Math.max(1, Number(new FormData(form).get("simulationQuantity") || 1));
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  localStorage.setItem("erclave-validation-qty", simulationQuantity);
  const validation = calculateRecipe(recipe, simulationQuantity);
  modalContent.querySelector("#recipePreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Lote simulado</span>
        <strong>${formatNumber(simulationQuantity)} ${recipe.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${validation.missing.length ? "warning" : "active"}">
        ${validation.missing.length ? `${validation.missing.length} faltantes` : "Recursos suficientes"}
      </span>
    </div>
    <div class="resource-check-grid compact">
      ${validation.rows
        .map(
          (row) => `
            <article class="resource-check ${row.ok ? "ok" : "risk"}">
              <div>
                <strong>${row.name}</strong>
                <span>${row.type}</span>
              </div>
              <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
            </article>
          `
        )
        .join("")}
    </div>
  `;
}

function saveRecipeForm(event) {
  event.preventDefault();
  const recipe = buildRecipeFromForm(event.currentTarget);
  const errors = validateRecipe(recipe);
  renderFormErrors(errors);
  if (errors.length) return;

  recipe.status = "Activa";
  const exists = Boolean(mockDb.findRecipe(recipe.id));
  if (exists) {
    mockDb.updateRecipe(recipe);
  } else {
    mockDb.addRecipe(recipe);
  }
  localStorage.setItem("erclave-selected-recipe", recipe.id);
  closeModal();
  state.active = "produccion";
  render();
  showToast(`Receta ${recipe.id} ${exists ? "actualizada" : "guardada"} y validada contra almacen.`);
}

function deleteRecipe(recipeId) {
  const recipe = mockDb.findRecipe(recipeId);
  if (!recipe) return;
  const confirmed = window.confirm(`Eliminar la receta ${recipe.id} · ${recipe.product}?`);
  if (!confirmed) return;
  const recipes = mockDb.deleteRecipe(recipeId);
  if (localStorage.getItem("erclave-selected-recipe") === recipeId) {
    localStorage.setItem("erclave-selected-recipe", recipes[0]?.id || defaultRecipes[0].id);
  }
  render();
  showToast(`Receta ${recipe.id} eliminada.`);
}

function openOrderModal() {
  const recipes = mockDb.loadRecipes();
  const selectedRecipeId = localStorage.getItem("erclave-selected-recipe") || recipes[0]?.id;
  const recipe = recipes.find((item) => item.id === selectedRecipeId) || recipes[0] || defaultRecipes[0];
  const defaultQuantity = Number(localStorage.getItem("erclave-validation-qty") || 100);

  modalContent.innerHTML = `
    <form class="recipe-form" id="orderForm">
      <div class="modal-head">
        <div>
          <p class="eyebrow">Produccion</p>
          <h2 id="modalTitle">Generar orden de produccion</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <div class="form-grid">
        <label class="preview-field wide-field">
          <span>Receta</span>
          <select name="recipeId" id="orderRecipeSelect" required>
            ${recipes
              .map(
                (item) => `
                  <option value="${item.id}" ${item.id === recipe.id ? "selected" : ""}>
                    ${item.id} · ${item.product} · v${item.version}
                  </option>
                `
              )
              .join("")}
          </select>
        </label>
        <label class="preview-field">
          <span>Cantidad de piezas/servicios</span>
          <input name="quantity" type="number" min="1" value="${defaultQuantity}" required />
        </label>
        <label class="preview-field">
          <span>Fecha requerida</span>
          <input name="dueDate" type="date" value="2026-05-25" required />
        </label>
        <label class="preview-field">
          <span>Prioridad</span>
          <select name="priority">
            <option>Alta</option>
            <option>Media</option>
            <option>Baja</option>
          </select>
        </label>
        <label class="preview-field">
          <span>Responsable general</span>
          <input name="responsible" type="text" value="Mariana Torres" required />
        </label>
      </div>

      <div class="section-title form-section-title">
        <span class="section-icon">↳</span>
        <strong>Responsables por area</strong>
      </div>
      <div class="area-assignment-list" id="areaAssignmentList">
        ${renderAreaAssignments(recipe)}
      </div>

      <div class="form-errors" id="formErrors" hidden></div>

      <div class="modal-actions">
        <button class="secondary-action" type="button" data-action="preview-order">Validar orden</button>
        <button class="primary-action" type="submit">Generar en produccion</button>
      </div>

      <div class="recipe-preview" id="orderPreview"></div>
    </form>
  `;

  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("#orderRecipeSelect").addEventListener("change", (event) => {
    const nextRecipe = mockDb.findRecipe(event.target.value) || defaultRecipes[0];
    modalContent.querySelector("#areaAssignmentList").innerHTML = renderAreaAssignments(nextRecipe);
  });
  modalContent.querySelector("[data-action='preview-order']").addEventListener("click", previewOrderForm);
  modalContent.querySelector("#orderForm").addEventListener("submit", saveOrderForm);
}

function renderAreaAssignments(recipe) {
  const defaults = ["Luis Perez", "Ana Ruiz", "Sofia Mendez", "Carlos Diaz", "Mariana Torres"];
  return (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step, index) => `
    <label class="selected-resource-row area-assignment-row" data-area="${step}">
      <div>
        <strong>${step}</strong>
        <span>Entregable operativo por area</span>
      </div>
      <input name="area_${slugify(step)}" type="text" value="${defaults[index] || "Responsable"}" required />
    </label>
  `).join("");
}

function slugify(value) {
  return value
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function buildOrderFromForm(form) {
  const data = new FormData(form);
  const recipe = mockDb.findRecipe(String(data.get("recipeId"))) || defaultRecipes[0];
  const quantity = Math.max(1, Number(data.get("quantity") || 1));
  const areas = (recipe.steps.length ? recipe.steps : ["Produccion"]).map((step) => ({
    area: step,
    responsible: String(data.get(`area_${slugify(step)}`) || "").trim(),
    status: "Pendiente"
  }));

  return {
    id: `OP-${Date.now().toString().slice(-5)}`,
    recipeId: recipe.id,
    recipeName: recipe.product,
    quantity,
    unit: recipe.unit,
    status: "En produccion",
    priority: String(data.get("priority") || "Media"),
    dueDate: String(data.get("dueDate") || ""),
    center: recipe.center,
    responsible: String(data.get("responsible") || "").trim(),
    areas,
    createdAt: new Date().toISOString().slice(0, 10)
  };
}

function validateOrder(order) {
  const errors = [];
  if (!order.recipeId) errors.push("Selecciona una receta.");
  if (!order.quantity) errors.push("Captura la cantidad.");
  if (!order.dueDate) errors.push("Captura fecha requerida.");
  if (!order.responsible) errors.push("Captura responsable general.");
  if (order.areas.some((area) => !area.responsible)) errors.push("Asigna responsable a cada area.");
  return errors;
}

function previewOrderForm() {
  const form = modalContent.querySelector("#orderForm");
  const order = buildOrderFromForm(form);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
  const validation = calculateRecipe(recipe, order.quantity);
  modalContent.querySelector("#orderPreview").innerHTML = `
    <div class="validator-head">
      <div>
        <span class="muted-label">Orden simulada</span>
        <strong>${order.quantity} ${order.unit} · ${formatCurrency(validation.totalCost)}</strong>
      </div>
      <span class="chip ${validation.missing.length ? "warning" : "active"}">
        ${validation.missing.length ? `${validation.missing.length} faltantes` : "Lista para produccion"}
      </span>
    </div>
    <div class="resource-check-grid compact">
      ${validation.rows
        .map((row) => `
          <article class="resource-check ${row.ok ? "ok" : "risk"}">
            <div>
              <strong>${row.name}</strong>
              <span>${row.type} · ${row.source}</span>
            </div>
            <p>${formatNumber(row.required)} / ${formatNumber(row.available)} ${row.unit}</p>
          </article>
        `)
        .join("")}
    </div>
  `;
}

function saveOrderForm(event) {
  event.preventDefault();
  const order = buildOrderFromForm(event.currentTarget);
  const errors = validateOrder(order);
  renderFormErrors(errors);
  if (errors.length) return;
  mockDb.addOrder(order);
  localStorage.setItem("erclave-selected-recipe", order.recipeId);
  localStorage.setItem("erclave-validation-qty", order.quantity);
  closeModal();
  render();
  showToast(`Orden ${order.id} generada en produccion.`);
  openOrderPrintModal(order.id);
}

function advanceOrderStatus(orderId) {
  const order = mockDb.findOrder(orderId);
  if (!order) return;
  const statuses = ["En produccion", "Pausada", "Terminada", "Cancelada"];
  const next = statuses[(statuses.indexOf(order.status) + 1) % statuses.length];
  mockDb.updateOrder({ ...order, status: next });
  render();
  showToast(`Orden ${order.id} ahora esta en ${next}.`);
}

function openOrderPrintModal(orderId) {
  const order = mockDb.findOrder(orderId);
  if (!order) return;
  const recipe = mockDb.findRecipe(order.recipeId) || defaultRecipes[0];
  const validation = calculateRecipe(recipe, order.quantity);
  modalContent.innerHTML = `
    <div class="recipe-form print-modal">
      <div class="modal-head no-print">
        <div>
          <p class="eyebrow">Orden de produccion</p>
          <h2>${order.id}</h2>
        </div>
        <button class="icon-button modal-close" type="button" aria-label="Cerrar">×</button>
      </div>

      <section class="print-area" id="printArea">
        <div class="print-header">
          <div>
            <strong>ERClave Produccion</strong>
            <span>Orden de produccion</span>
          </div>
          <h1>${order.id}</h1>
        </div>
        <div class="print-grid">
          <p><strong>Producto:</strong> ${order.recipeName}</p>
          <p><strong>Receta:</strong> ${recipe.id} · v${recipe.version}</p>
          <p><strong>Cantidad:</strong> ${order.quantity} ${order.unit}</p>
          <p><strong>Estado:</strong> ${order.status}</p>
          <p><strong>Prioridad:</strong> ${order.priority}</p>
          <p><strong>Fecha requerida:</strong> ${order.dueDate}</p>
          <p><strong>Responsable:</strong> ${order.responsible}</p>
          <p><strong>Centro:</strong> ${order.center}</p>
        </div>
        <h3>Responsables por area</h3>
        <table>
          <thead>
            <tr><th>Area</th><th>Responsable</th><th>Estado</th></tr>
          </thead>
          <tbody>
            ${order.areas.map((area) => `<tr><td>${area.area}</td><td>${area.responsible}</td><td>${area.status}</td></tr>`).join("")}
          </tbody>
        </table>
        <h3>Recursos calculados</h3>
        <table>
          <thead>
            <tr><th>Recurso</th><th>Tipo</th><th>Requerido</th><th>Disponible</th></tr>
          </thead>
          <tbody>
            ${validation.rows.map((row) => `<tr><td>${row.name}</td><td>${row.type}</td><td>${formatNumber(row.required)} ${row.unit}</td><td>${formatNumber(row.available)} ${row.unit}</td></tr>`).join("")}
          </tbody>
        </table>
        <p class="print-total"><strong>Costo estimado:</strong> ${formatCurrency(validation.totalCost)}</p>
      </section>

      <div class="modal-actions no-print">
        <button class="secondary-action" type="button" data-action="print-order-now">Imprimir / Guardar PDF</button>
        <button class="primary-action" type="button" data-action="close-print">Cerrar</button>
      </div>
    </div>
  `;
  modalBackdrop.hidden = false;
  modalContent.querySelector(".modal-close").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='close-print']").addEventListener("click", closeModal);
  modalContent.querySelector("[data-action='print-order-now']").addEventListener("click", () => {
    window.print();
  });
}

function applyI18n() {
  const dict = translations[state.lang];
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = dict[node.dataset.i18n] || node.textContent;
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.placeholder = dict[node.dataset.i18nPlaceholder] || node.placeholder;
  });
  langToggle.querySelector(".icon").textContent = state.lang.toUpperCase();
}

function render() {
  shell.dataset.theme = state.theme;
  document.body.dataset.theme = state.theme;
  renderNav();
  renderPanel();
  renderFlow();
  applyI18n();
}

themeToggle.addEventListener("click", () => {
  state.theme = state.theme === "light" ? "dark" : "light";
  localStorage.setItem("erclave-theme", state.theme);
  render();
});

langToggle.addEventListener("click", () => {
  state.lang = state.lang === "es" ? "en" : "es";
  localStorage.setItem("erclave-lang", state.lang);
  render();
});

modalBackdrop.addEventListener("click", (event) => {
  if (event.target === modalBackdrop) closeModal();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !modalBackdrop.hidden) closeModal();
});

topbarPrimary.addEventListener("click", () => {
  if (state.active === "produccion") {
    openOrderModal();
    return;
  }
  showToast("Este mock de captura inicia con recetas de Produccion.");
});

render();
