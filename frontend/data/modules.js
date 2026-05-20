export const modules = [
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
      ["Productos y servicios", "Catalogo base para fabricar o ejecutar servicios repetibles.", "productos-servicios"],
      ["Recetas", "Versiones, recursos, etapas, tiempos, merma y rendimiento.", "recetas"],
      ["Ordenes", "Programacion, estados, responsables, prioridad y cantidades.", "ordenes"],
      ["Entregables por area", "Corte, ensamble, calidad, empaque y responsables.", "entregables"],
      ["Validacion de recursos", "Disponibilidad, reservas, faltantes y compras sugeridas.", "validacion-recursos"]
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

export const erpSubmoduleCatalog = {
  produccion: {
    "productos-servicios": {
      enName: "Products and services",
      enDetail: "Base catalog for manufacturing or running repeatable services.",
      focus: {
        es: ["SKU, unidad y tipo", "Receta vigente", "Rendimiento esperado", "Centro de costos"],
        en: ["SKU, unit, and type", "Current recipe", "Expected yield", "Cost center"]
      }
    },
    recetas: {
      enName: "Recipes",
      enDetail: "Versions, resources, stages, times, waste, and yield.",
      focus: {
        es: ["Version activa", "Recursos por unidad", "Etapas y tiempos", "Merma estimada"],
        en: ["Active version", "Resources per unit", "Stages and times", "Estimated waste"]
      }
    },
    ordenes: {
      enName: "Orders",
      enDetail: "Scheduling, statuses, owners, priority, and quantities.",
      focus: {
        es: ["Cantidad solicitada", "Fecha requerida", "Responsable", "Estado operativo"],
        en: ["Requested quantity", "Required date", "Owner", "Operational status"]
      }
    },
    entregables: {
      enName: "Area deliverables",
      enDetail: "Cutting, assembly, quality, packing, and owners.",
      focus: {
        es: ["Area asignada", "Responsable", "Criterios de salida", "Evidencia"],
        en: ["Assigned area", "Owner", "Exit criteria", "Evidence"]
      }
    },
    "validacion-recursos": {
      enName: "Resource validation",
      enDetail: "Availability, reservations, shortages, and suggested purchases.",
      focus: {
        es: ["Disponible vs requerido", "Reservas", "Faltantes", "Compra sugerida"],
        en: ["Available vs required", "Reservations", "Shortages", "Suggested purchase"]
      }
    }
  },
  almacenes: {
    almacenes: {
      enName: "Warehouses",
      enDetail: "Raw materials, tools, work in process, and finished goods.",
      focus: {
        es: ["Tipo de almacen", "Responsable", "Centro de negocio", "Politicas de inventario"],
        en: ["Warehouse type", "Owner", "Business center", "Inventory policies"]
      }
    },
    ubicaciones: {
      enName: "Locations",
      enDetail: "Aisles, racks, zones, and locations by business center.",
      focus: {
        es: ["Zona", "Rack o pasillo", "Capacidad", "Reglas de surtido"],
        en: ["Zone", "Rack or aisle", "Capacity", "Picking rules"]
      }
    },
    movimientos: {
      enName: "Movements",
      enDetail: "Receipts, issues, transfers, adjustments, and returns.",
      focus: {
        es: ["Entrada/salida", "Documento origen", "Lote o serie", "Costo de movimiento"],
        en: ["Receipt/issue", "Source document", "Lot or serial", "Movement cost"]
      }
    },
    reservas: {
      enName: "Reservations",
      enDetail: "Stock held for production orders or sales orders.",
      focus: {
        es: ["Documento relacionado", "Cantidad apartada", "Vencimiento", "Liberacion"],
        en: ["Linked document", "Reserved quantity", "Expiration", "Release"]
      }
    },
    kardex: {
      enName: "Kardex",
      enDetail: "Full history by item, lot, serial number, or location.",
      focus: {
        es: ["Existencia inicial", "Entradas", "Salidas", "Costo promedio"],
        en: ["Opening stock", "Receipts", "Issues", "Average cost"]
      }
    }
  },
  compras: {
    proveedores: {
      enName: "Suppliers",
      enDetail: "Tax data, terms, lead times, and linked products.",
      focus: {
        es: ["Datos fiscales", "Condiciones de pago", "Lead time", "Productos autorizados"],
        en: ["Tax data", "Payment terms", "Lead time", "Approved products"]
      }
    },
    requisiciones: {
      enName: "Requisitions",
      enDetail: "Requests from shortages, users, or production orders.",
      focus: {
        es: ["Necesidad", "Solicitante", "Autorizacion", "Centro de costos"],
        en: ["Need", "Requester", "Approval", "Cost center"]
      }
    },
    "ordenes-de-compra": {
      enName: "Purchase orders",
      enDetail: "Approval, sending, status, and follow-up.",
      focus: {
        es: ["Proveedor", "Monto", "Fecha promesa", "Estado de envio"],
        en: ["Supplier", "Amount", "Promise date", "Sending status"]
      }
    },
    recepciones: {
      enName: "Receipts",
      enDetail: "Partial and full receipts with purchase order validation.",
      focus: {
        es: ["Cantidad recibida", "Diferencias", "Lote", "Entrada a almacen"],
        en: ["Received quantity", "Differences", "Lot", "Warehouse receipt"]
      }
    },
    reabastecimiento: {
      enName: "Replenishment",
      enDetail: "Minimums, reorder points, and suggested purchases.",
      focus: {
        es: ["Minimos y maximos", "Punto de reorden", "Consumo promedio", "Compra sugerida"],
        en: ["Minimums and maximums", "Reorder point", "Average consumption", "Suggested purchase"]
      }
    }
  },
  ventas: {
    clientes: {
      enName: "Customers",
      enDetail: "Commercial data, contacts, addresses, and terms.",
      focus: {
        es: ["Datos comerciales", "Contactos", "Credito", "Condiciones"],
        en: ["Commercial data", "Contacts", "Credit", "Terms"]
      }
    },
    cotizaciones: {
      enName: "Quotes",
      enDetail: "Prices, discounts, validity, and estimated margin.",
      focus: {
        es: ["Lista de precios", "Descuentos", "Vigencia", "Margen objetivo"],
        en: ["Price list", "Discounts", "Validity", "Target margin"]
      }
    },
    pedidos: {
      enName: "Orders",
      enDetail: "Approval, reservation, production, or fulfillment.",
      focus: {
        es: ["Aprobacion", "Reserva", "Produccion ligada", "Promesa de entrega"],
        en: ["Approval", "Reservation", "Linked production", "Delivery promise"]
      }
    },
    entregas: {
      enName: "Deliveries",
      enDetail: "Partial and full deliveries, evidence, and returns.",
      focus: {
        es: ["Parcialidades", "Evidencia", "Devoluciones", "Estatus logistico"],
        en: ["Partials", "Evidence", "Returns", "Logistics status"]
      }
    },
    margen: {
      enName: "Margin",
      enDetail: "Estimated cost, actual cost, and profitability by customer.",
      focus: {
        es: ["Costo estimado", "Costo real", "Rentabilidad", "Variacion"],
        en: ["Estimated cost", "Actual cost", "Profitability", "Variance"]
      }
    }
  },
  gastos: {
    "carga-documental": {
      enName: "Document upload",
      enDetail: "XML, PDF, receipts, and operational attachments.",
      focus: {
        es: ["XML/PDF", "Validacion fiscal", "Proveedor", "Anexos"],
        en: ["XML/PDF", "Tax validation", "Supplier", "Attachments"]
      }
    },
    clasificacion: {
      enName: "Classification",
      enDetail: "Expense type, supplier, taxes, and currency.",
      focus: {
        es: ["Tipo de gasto", "Impuestos", "Moneda", "Cuenta sugerida"],
        en: ["Expense type", "Taxes", "Currency", "Suggested account"]
      }
    },
    asignacion: {
      enName: "Allocation",
      enDetail: "Cost center, order, product, service, or project.",
      focus: {
        es: ["Centro de costos", "Documento origen", "Prorrateo", "Responsable"],
        en: ["Cost center", "Source document", "Allocation", "Owner"]
      }
    },
    "cuentas-por-pagar": {
      enName: "Accounts payable",
      enDetail: "Due dates, partial payments, and status.",
      focus: {
        es: ["Vencimiento", "Saldo", "Parcialidades", "Autorizacion de pago"],
        en: ["Due date", "Balance", "Installments", "Payment approval"]
      }
    },
    pagos: {
      enName: "Payments",
      enDetail: "Receipts, traceability, and accounting entry.",
      focus: {
        es: ["Metodo de pago", "Comprobante", "Conciliacion", "Asiento"],
        en: ["Payment method", "Receipt", "Reconciliation", "Journal entry"]
      }
    }
  },
  costos: {
    "centros-de-costos": {
      enName: "Cost centers",
      enDetail: "Areas, business centers, machines, and owners.",
      focus: {
        es: ["Area", "Responsable", "Capacidad", "Metodo de acumulacion"],
        en: ["Area", "Owner", "Capacity", "Accumulation method"]
      }
    },
    "costo-estimado": {
      enName: "Estimated cost",
      enDetail: "From recipe, supplies, labor, and machinery.",
      focus: {
        es: ["Receta base", "Insumos", "Mano de obra", "Maquinaria"],
        en: ["Base recipe", "Supplies", "Labor", "Machinery"]
      }
    },
    "costo-real": {
      enName: "Actual cost",
      enDetail: "From consumption, expenses, purchases, times, and waste.",
      focus: {
        es: ["Consumos", "Compras", "Tiempos reales", "Merma"],
        en: ["Consumption", "Purchases", "Actual times", "Waste"]
      }
    },
    variaciones: {
      enName: "Variances",
      enDetail: "Differences between planned, actual, and standard cost.",
      focus: {
        es: ["Planeado vs real", "Causa", "Impacto", "Accion correctiva"],
        en: ["Planned vs actual", "Cause", "Impact", "Corrective action"]
      }
    },
    rentabilidad: {
      enName: "Profitability",
      enDetail: "Margin by product, service, customer, and period.",
      focus: {
        es: ["Producto", "Cliente", "Periodo", "Margen neto"],
        en: ["Product", "Customer", "Period", "Net margin"]
      }
    }
  },
  contabilidad: {
    "catalogo-de-cuentas": {
      enName: "Chart of accounts",
      enDetail: "Accounts, levels, nature, and movement.",
      focus: {
        es: ["Cuenta", "Naturaleza", "Nivel", "Modulo origen"],
        en: ["Account", "Nature", "Level", "Source module"]
      }
    },
    periodos: {
      enName: "Periods",
      enDetail: "Opening, review, close, and authorized reopening.",
      focus: {
        es: ["Apertura", "Cierre", "Bloqueos", "Reapertura autorizada"],
        en: ["Opening", "Close", "Locks", "Authorized reopening"]
      }
    },
    asientos: {
      enName: "Journal entries",
      enDetail: "Debits, credits, policies, statuses, and reversals.",
      focus: {
        es: ["Cargos", "Abonos", "Documento origen", "Balance"],
        en: ["Debits", "Credits", "Source document", "Balance"]
      }
    },
    mapeos: {
      enName: "Mappings",
      enDetail: "Rules by module, operation, product, expense, or tax.",
      focus: {
        es: ["Modulo", "Operacion", "Cuenta contable", "Condiciones"],
        en: ["Module", "Operation", "Ledger account", "Conditions"]
      }
    },
    anexos: {
      enName: "Attachments",
      enDetail: "XML, PDF, payments, orders, deliveries, and source documents.",
      focus: {
        es: ["Documento", "Tipo", "Relacion", "Auditoria"],
        en: ["Document", "Type", "Relation", "Audit"]
      }
    }
  },
  reportes: {
    produccion: {
      enName: "Production",
      enDetail: "Orders, progress, fulfillment, load, and waste.",
      focus: {
        es: ["Avance", "Carga por area", "Cumplimiento", "Merma"],
        en: ["Progress", "Load by area", "Fulfillment", "Waste"]
      }
    },
    inventarios: {
      enName: "Inventory",
      enDetail: "Available stock, reservations, Kardex, turnover, and critical items.",
      focus: {
        es: ["Disponibles", "Reservas", "Rotacion", "Criticos"],
        en: ["Available stock", "Reservations", "Turnover", "Critical items"]
      }
    },
    finanzas: {
      enName: "Finance",
      enDetail: "Expenses, costs, entries, accounts, and profitability.",
      focus: {
        es: ["Gastos", "Costos", "Asientos", "Rentabilidad"],
        en: ["Expenses", "Costs", "Entries", "Profitability"]
      }
    },
    comercial: {
      enName: "Commercial",
      enDetail: "Sales, orders, customers, margin, and demand.",
      focus: {
        es: ["Ventas", "Clientes", "Margen", "Demanda"],
        en: ["Sales", "Customers", "Margin", "Demand"]
      }
    },
    constructor: {
      enName: "Builder",
      enDetail: "Filters, columns, grouping, and exports.",
      focus: {
        es: ["Filtros", "Columnas", "Agrupaciones", "Exportacion"],
        en: ["Filters", "Columns", "Grouping", "Export"]
      }
    }
  }
};
