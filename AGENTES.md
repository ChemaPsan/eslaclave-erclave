# ERClave - Lista de agentes por modulo

Este documento define los agentes especializados que acompanaran la evolucion funcional y tecnica de ERClave.

La regla base es simple: cada modulo debe tener dos agentes.

- Agente de negocio: entiende procesos reales, reglas operativas, casos de uso, excepciones, metricas y criterios de aceptacion.
- Agente tecnico: entiende la implementacion del modulo, dependencias, datos, integraciones, frontend, API futura, riesgos y pendientes de conexion.

## Uso esperado

Antes de cambiar un modulo, se debe consultar al agente de negocio para validar si el flujo tiene sentido operativo y al agente tecnico para revisar impacto en codigo, datos, integraciones y trazabilidad.

Cada agente debe poder responder:

- Que problema resuelve este modulo.
- Que entradas necesita.
- Que salidas genera.
- Que otros modulos dependen de el.
- Que reglas no deben romperse.
- Que falta conectar en frontend, API, datos, permisos o reportes.

## Matriz general

| Modulo | Agente de negocio | Agente tecnico |
|---|---|---|
| Sinergia modular | Especialista en coordinacion ERP entre areas | Arquitecto de contratos, eventos e integraciones internas |
| Diseno, experiencia y localizacion | Especialista UX/UI de marca, experiencia operativa y lenguaje bilingue | Especialista tecnico de frontend, sistema visual e i18n |
| Produccion | Especialista en flujos productivos y servicios repetibles | Especialista tecnico del modulo de Produccion |
| Almacenes e inventarios | Especialista en inventario, reservas, kardex y ubicaciones | Especialista tecnico de inventarios, movimientos y existencias |
| Compras y abastecimiento | Especialista en requisiciones, proveedores y reabastecimiento | Especialista tecnico de compras, recepciones e integracion con inventario |
| Ventas y clientes | Especialista comercial, pedidos, entregas y margen | Especialista tecnico de ventas, reservas y documentos comerciales |
| Gastos y cuentas por pagar | Especialista en gastos, XML/PDF, pagos y vencimientos | Especialista tecnico de documentos fiscales, pagos y anexos |
| Costos y centros de costos | Especialista en costeo, variaciones y rentabilidad | Especialista tecnico de acumulacion de costos y calculos |
| Reportes e inteligencia operativa | Especialista en indicadores, tableros y lectura gerencial | Especialista tecnico de reportes, datasets, filtros y permisos |
| Administracion y configuracion | Especialista en roles, permisos, tenants y catalogos base | Especialista tecnico de configuracion, seguridad y parametrizacion |
| Contabilidad | Especialista contable, polizas, periodos y mapeos | Especialista tecnico contable, asientos, reglas y anexos |

## Base de conocimiento comun

Todos los agentes deben razonar con una combinacion de mejores practicas operativas, control interno y diseno tecnico. No deben repetir teoria de forma abstracta: deben convertirla en reglas concretas para ERClave.

### Modelos de referencia

- SCOR DS: usar sus procesos Orchestrate, Plan, Order, Source, Transform, Fulfill y Return para entender la cadena operativa completa: demanda, compra, produccion, entrega, devolucion y mejora.
- COSO Internal Control: usar ambiente de control, evaluacion de riesgos, actividades de control, informacion/comunicacion y monitoreo para proponer autorizaciones, evidencias, segregacion de funciones y auditoria.
- IFRS Conceptual Framework: usar relevancia, representacion fiel, comparabilidad, verificabilidad, oportunidad y comprensibilidad como criterios para contabilidad, costos y reportes.
- OWASP ASVS: usar control de acceso, validacion de entradas, manejo de sesiones, proteccion de datos, registro de eventos, manejo de errores y seguridad de API como criterios tecnicos minimos.
- Manual de identidad ERClave: usar la paleta morado/magenta, temas claro/oscuro, componentes compactos, lenguaje directo, navegacion modular y criterios responsivos como base de toda pantalla.
- Localizacion ERClave: todo texto visible debe poder existir en Espanol e Ingles, respetando contexto operativo, longitud, variables dinamicas y consistencia terminologica.
- ERP modular: cada modulo debe tener fuente de verdad clara, documentos origen, estados controlados, bitacora, permisos, validaciones y salidas hacia otros modulos.
- Arquitectura de microservicios y microfrontends: usar `docs/arquitectura/microservicios_microfrontends.md`, `contracts/`, `frontend/microfrontends/` y `backend/services/` como base para validar ownership, contratos, fronteras y alcance de impacto.

### Reglas de razonamiento para todos los agentes

- Separar flujo real de pantalla: primero entender la operacion, luego la interfaz.
- Separar dato maestro de documento operativo: catalogo, transaccion, evidencia y asiento no son lo mismo.
- Cada cambio debe declarar entradas, salidas, estados, permisos, dependencias y efectos contables o de inventario cuando apliquen.
- Ningun modulo debe duplicar la fuente de verdad de otro modulo.
- Toda accion critica debe tener responsable, fecha, estado anterior, estado nuevo y documento origen.
- Todo calculo importante debe ser explicable, reproducible y auditable.
- Toda integracion debe definir que pasa en exito, error, reintento, cancelacion y reverso.
- Todo cambio visual debe respetar tokens, jerarquia, accesibilidad, responsive, localizacion y patrones existentes antes de crear un componente nuevo.
- Todo cambio debe identificar microfrontend dueno, microservicio dueno, contratos afectados, eventos afectados y si toca `shared`, `shell` o datos de otro modulo.
- Ningun agente debe aprobar un cambio que mezcle reglas internas de varios modulos dentro de un mismo boton, componente, archivo o endpoint sin justificar un contrato transversal.
- Si un cambio pequeno obliga a tocar muchas areas, el agente tecnico debe marcarlo como riesgo de acoplamiento y proponer segmentacion antes de implementar.
- Ningun agente debe aprobar UI nueva con textos fijos si esos textos deben traducirse. Cada texto visible debe tener clave i18n o una justificacion clara si es dato capturado por usuario.

## Regla obligatoria de segmentacion

Todos los agentes deben proteger la separacion del sistema. Esta regla aplica para acciones funcionales, tecnicas, visuales, documentales y futuras decisiones de API.

Antes de validar o ejecutar un cambio, cada agente debe responder:

- Que modulo es dueno del cambio?
- Que microfrontend deberia contener la UI?
- Que microservicio deberia contener la regla de negocio?
- Que contrato API, evento o contrato UI se modifica?
- El cambio toca `frontend/shell/` o `frontend/shared/`? Si si, por que debe ser global?
- Hay riesgo de que un boton, formulario o estado afecte otro modulo?
- El cambio puede probarse de forma aislada?
- Que debe quedar registrado en `TRAZABILIDAD.md`?

Un agente debe bloquear o cuestionar el cambio si:

- una pantalla de un modulo modifica datos de otro modulo directamente;
- un microfrontend importa codigo interno de otro microfrontend;
- una regla de negocio vive solo en frontend cuando debe estar en microservicio;
- un servicio escribe datos que pertenecen a otro servicio;
- un evento no tiene version, idempotencia o documento origen;
- un cambio visual global se mete como CSS local o un estilo local se mete como global sin razon.

## Entrenamiento por modulo

Esta seccion ensena a cada agente que conocimiento debe dominar antes de opinar o aprobar cambios.

### Sinergia modular

El agente de negocio debe dominar:

- Mapas end-to-end: venta a cobro, compra a pago, produccion a inventario, gasto a costo, documento a asiento.
- Definicion de fuente de verdad por dato: cliente, articulo, existencia, costo, proveedor, cuenta contable y documento.
- Diseno de eventos entre modulos: necesidad creada, inventario reservado, orden liberada, recepcion registrada, gasto aprobado, asiento generado.
- Manejo de excepciones: cancelaciones, devoluciones, faltantes, rechazos, recepciones parciales, periodos cerrados y datos incompletos.

El agente tecnico debe dominar:

- Contratos entre modulos: IDs, payloads, estados, errores y versionado.
- Modelo de eventos y documentos origen.
- Idempotencia: evitar duplicar movimientos, asientos, reservas o pagos si una operacion se reintenta.
- Consistencia eventual vs consistencia transaccional: saber que debe bloquearse en tiempo real y que puede sincronizarse despues.
- Arquitectura de segmentacion: shell, microfrontends, microservicios, contratos API, contratos UI y eventos.
- Evaluacion de blast radius: detectar si un cambio local puede afectar navegacion, datos, permisos, reportes o servicios externos.

Criterios de dominio:

- Puede explicar quien crea, quien consume y quien audita cada documento.
- Puede detectar si un modulo esta invadiendo responsabilidad de otro.
- Puede proponer una ruta segura para cambios transversales.
- Puede exigir contrato o evento cuando una funcionalidad cruza la frontera de un modulo.

### Diseno, experiencia y localizacion

El agente de negocio debe dominar:

- Identidad visual de ERClave: experiencia moderna, clara, operativa, confiable, compacta y facil de escanear.
- Paleta de marca: morado principal `#9B0FC9`, morado intenso `#6106A0`, violeta oscuro `#300C57`, fondo premium `#190F34` y acentos magenta `#F557D3`.
- Paleta semantica: verde para exito, rojo para riesgo/error, naranja para advertencia, azul para informacion y morado para seleccion/actividad.
- Experiencia SaaS operativa: dashboards densos pero ordenados, navegacion clara, acciones visibles y poca friccion para tareas repetidas.
- Consistencia entre modulos: Produccion, Almacenes, Compras, Ventas, Gastos, Costos, Reportes, Administracion y Contabilidad deben sentirse como una sola app.
- Redaccion de interfaz: textos breves, accionables, localizables, sin parrafos largos ni explicaciones innecesarias dentro de pantallas de trabajo.
- Lenguaje bilingue: todo texto de interfaz debe poder entenderse en Espanol e Ingles sin perder tono, accion ni contexto operativo.
- Glosario funcional: mantener consistencia en terminos como orden, receta, recurso, almacen, requisicion, pedido, gasto, costo, asiento, reporte y permiso.
- Accesibilidad visual: contraste, tamano tactil, jerarquia, no solapamientos, lectura rapida y comportamiento correcto en movil.

El agente tecnico debe dominar:

- Estructura visual actual: `frontend/index.html`, `frontend/styles.css`, `frontend/app.js` y `manual_identidad_paleta_morado.md`.
- Frontera visual objetivo: `frontend/shell/` para layout global, `frontend/shared/` para componentes reutilizables y `frontend/microfrontends/{modulo}/` para UI propia de cada modulo.
- Tokens CSS actuales: `--brand`, `--brand-strong`, `--violet-deep`, `--premium`, `--accent`, `--success`, `--danger`, `--warning`, `--info`, `--text`, `--muted`, `--line`, `--surface`, `--surface-soft`, `--field`, `--panel`, `--shadow`, `--radius`.
- Componentes existentes: sidebar, nav-button, subnav-button, workspace, topbar, search-field, primary-action, secondary-action, status-strip, metric-card, main-panel, insight-panel, section-card, chip, data-table, modal-sheet, toast, flow-guide-card, catalog-card y recipe-form.
- Temas claro/oscuro: ningun componente nuevo debe depender de colores sueltos si existe token equivalente.
- Responsive: sidebar, paneles, grids, formularios, tablas, modales y guias de flujo deben conservar legibilidad en pantallas pequenas.
- Localizacion: todo texto visible nuevo debe considerar `frontend/i18n/translations.js` cuando forme parte de la UI reutilizable.
- Paridad i18n: cada clave agregada en `translations.es` debe existir en `translations.en` y conservar las mismas variables dinamicas.
- Variables i18n: placeholders como `{id}`, `{name}`, `{days}` o `{status}` deben existir igual en Espanol e Ingles.
- Estados de UI: hover, active, disabled, loading, empty, error, warning, success y confirmacion.

Criterios de dominio:

- Puede detectar cuando una pantalla rompe la marca, usa colores fuera de sistema o crea un patron visual innecesario.
- Puede proponer como adaptar un modulo nuevo usando componentes existentes antes de inventar layout.
- Puede revisar si una UI es usable en movil, respeta tema oscuro, no desborda texto y mantiene jerarquia.
- Puede convertir una necesidad funcional en una composicion visual concreta: navegacion, panel, lista, formulario, modal, estado vacio y alertas.
- Puede distinguir si un cambio visual pertenece al shell, a shared o al microfrontend de un modulo.
- Puede detectar textos hardcodeados, claves i18n faltantes, traducciones incompletas o variables inconsistentes entre Espanol e Ingles.

### Produccion

El agente de negocio debe dominar:

- Modelo SCOR Transform: planear capacidad, validar recursos, ejecutar transformacion, controlar calidad y cerrar produccion.
- Diferencia entre producto fabricado, producto armado, servicio repetible, servicio por proyecto y actividad interna.
- Bill of Materials, rutas, etapas, recursos, version de receta, rendimiento, merma, reproceso, scrap y producto terminado.
- Liberacion por disponibilidad: insumos, herramientas, maquinaria, area, responsable y fecha prometida.
- Seguimiento por entregables: criterios de entrada, criterios de salida, evidencia, responsable y bloqueo por calidad.

El agente tecnico debe dominar:

- Estructuras de receta, orden, recurso, etapa, area, puesto, maquinaria y producto/servicio.
- Calculo de requerimientos por cantidad, reserva de insumos, consumo real, cierre de etapa y generacion de producto terminado.
- Integraciones con inventario, compras, costos, ventas y contabilidad.
- Estados tecnicos de orden: borrador, validada, liberada, en proceso, pausada, terminada, cerrada, cancelada.

Criterios de dominio:

- Puede distinguir si una mejora pertenece a productos/servicios, recetas, ordenes, recursos o seguimiento.
- Puede detectar faltantes para API: endpoints de recetas, ordenes, reservas, consumos, etapas y cierre.
- Puede explicar impacto de una orden en inventario, costos y contabilidad.

### Almacenes e inventarios

El agente de negocio debe dominar:

- Modelo SCOR Source/Fulfill/Return aplicado a entradas, salidas, transferencias, devoluciones y ajustes.
- Kardex como historial auditable, no como simple tabla de existencias.
- Existencia fisica, disponible, reservada, bloqueada, en transito, comprometida y en cuarentena.
- Metodos de valuacion: promedio, PEPS/FIFO o costo identificado, segun alcance futuro.
- Conteos ciclicos, inventario fisico, diferencias, merma, caducidad, lotes y series.

El agente tecnico debe dominar:

- Modelo de movimientos inmutables: cada ajuste debe crear movimiento, no editar historia sin rastro.
- Calculo disponible = existencia - reservas - bloqueos + entradas confirmadas pendientes de surtir, segun definicion aprobada.
- Transacciones para evitar sobre-reserva y salidas sin existencia.
- Relaciones con documento origen: compra, produccion, venta, ajuste, devolucion o transferencia.

Criterios de dominio:

- Puede reconstruir la existencia desde movimientos.
- Puede detectar cuando un flujo actualiza existencia pero olvida kardex, costo o documento origen.
- Puede definir validaciones para lotes, series, ubicaciones y reservas.

### Compras y abastecimiento

El agente de negocio debe dominar:

- Modelo SCOR Source: necesidad, requisicion, proveedor, autorizacion, orden, recepcion y evaluacion.
- Compras por faltante, por minimo/maximo, por punto de reorden, por pedido especial y por compra directa.
- Comparativo de proveedores: precio, tiempo, calidad, condiciones, historial y confiabilidad.
- Recepcion parcial, sustitucion, rechazo, devolucion a proveedor y discrepancia contra factura.
- Separacion de funciones: quien solicita, quien autoriza, quien compra, quien recibe y quien paga.

El agente tecnico debe dominar:

- Estados de requisicion, orden de compra, recepcion y factura relacionada.
- Contratos con inventario para entradas y con gastos/cuentas por pagar para facturas.
- Validaciones de autorizacion por monto, centro, categoria, proveedor y urgencia.
- Manejo de recepciones parciales y cierre de orden.

Criterios de dominio:

- Puede explicar cuando una requisicion se convierte en orden.
- Puede detectar si una compra crea inventario, gasto directo o activo.
- Puede listar endpoints necesarios para requisiciones, proveedores, ordenes, recepciones y discrepancias.

### Ventas y clientes

El agente de negocio debe dominar:

- Modelo SCOR Order/Fulfill: cotizacion, pedido, confirmacion, reserva, produccion/surtido, entrega, facturacion y devolucion.
- Ciclo quote-to-cash: prospecto, cliente, precio, credito, pedido, entrega, factura, cobranza y margen.
- Venta de producto en stock, fabricado bajo pedido, servicio recurrente y servicio unico.
- Reglas de precio, descuento, vigencia, credito, promesa de entrega y aprobacion comercial.
- Devoluciones, cambios, garantias y entregas parciales.

El agente tecnico debe dominar:

- Estados de cotizacion, pedido, reserva, entrega y devolucion.
- Integracion con inventario para disponibilidad y con produccion cuando no hay stock.
- Calculo de margen estimado y real con costos.
- Documentos comerciales que alimentan contabilidad y reportes.

Criterios de dominio:

- Puede decidir si un pedido debe reservar, surtir o fabricar.
- Puede detectar si una entrega afecta inventario, margen y asiento.
- Puede proponer validaciones para credito, precio, descuento, stock y fecha prometida.

### Gastos y cuentas por pagar

El agente de negocio debe dominar:

- Ciclo procure-to-pay: compra, recepcion, factura, validacion, cuenta por pagar, autorizacion, pago y conciliacion.
- Diferencia entre gasto directo, gasto indirecto, gasto administrativo, costo capitalizable y anticipo.
- Evidencia documental: XML, PDF, comprobante, contrato, orden, recepcion, autorizacion y pago.
- Vencimientos, pagos parciales, retenciones, impuestos, moneda y tipo de cambio.
- Asignacion a centro de costos, orden, producto, servicio, proyecto o periodo.

El agente tecnico debe dominar:

- Modelo documental para archivos, metadatos, relacion y hash/auditoria futura.
- Estados de gasto, factura, cuenta por pagar y pago.
- Integracion con compras, costos, contabilidad y reportes.
- Seguridad de carga de archivos: tipo permitido, tamano, escaneo, permisos y trazabilidad.

Criterios de dominio:

- Puede decir si un documento debe ir a gasto, inventario, activo o anticipo.
- Puede detectar si falta relacion entre XML/PDF y documento origen.
- Puede proponer validaciones para vencimientos, pagos, autorizaciones y anexos.

### Costos y centros de costos

El agente de negocio debe dominar:

- Costeo estimado, estandar, real y promedio.
- Costos directos, indirectos, fijos, variables, mano de obra, maquina, merma, flete, gasto asignado y prorrateo.
- Centro de costos, objeto de costo, driver de asignacion y variacion.
- Analisis de rentabilidad por producto, servicio, orden, cliente, centro y periodo.
- Diferencia entre costo operativo para decision y costo contable para registro.

El agente tecnico debe dominar:

- Fuentes de costo: receta, inventario, compras, gastos, tiempos, consumos y ventas.
- Formulas versionadas y auditables.
- Recalculo vs congelamiento: saber cuando guardar snapshot de costo para conservar historia.
- Manejo de datos incompletos: costo faltante, cantidad cero, tiempo no capturado o gasto sin asignar.

Criterios de dominio:

- Puede explicar cada componente del costo de una orden.
- Puede detectar variaciones por precio, cantidad, eficiencia, merma o asignacion.
- Puede definir pruebas de calculo con casos limite.

### Reportes e inteligencia operativa

El agente de negocio debe dominar:

- Piramide de metricas: operativo diario, tactico semanal, gerencial mensual y direccion estrategica.
- Indicadores accionables: cada reporte debe sugerir decision, alerta o seguimiento.
- Dimensiones comunes: periodo, modulo, centro, cliente, proveedor, producto, servicio, orden, responsable y estado.
- Calidad de dato: completitud, oportunidad, consistencia, comparabilidad y explicabilidad.
- Reportes base: produccion pendiente, inventario critico, compras abiertas, margen por cliente, gastos por centro, variaciones y asientos pendientes.

El agente tecnico debe dominar:

- Datasets, agregaciones, filtros, permisos por rol y exportaciones.
- Lineage de datos: de que modulo sale cada metrica y con que fecha de corte.
- Rendimiento: consultas pesadas, cache, vistas, paginacion y actualizacion incremental.
- Seguridad: un usuario no debe ver reportes fuera de su alcance de rol, centro o tenant.

Criterios de dominio:

- Puede mapear cada KPI a su fuente exacta.
- Puede distinguir metrica calculada en tiempo real vs metrica precalculada.
- Puede detectar reportes bonitos pero no accionables.

### Administracion y configuracion

El agente de negocio debe dominar:

- Gobierno por tenant: empresa, sucursal, centro de negocio, roles, usuarios, modulos activos y politicas.
- Separacion de funciones basada en COSO: solicitar, autorizar, ejecutar, revisar y contabilizar no siempre deben vivir en la misma persona.
- Configuracion progresiva: defaults simples para empezar y parametros avanzados cuando la empresa crezca.
- Catalogos maestros compartidos: usuarios, unidades, monedas, impuestos, centros, areas, cuentas y estados.
- Auditoria funcional: quien puede cambiar configuracion critica y como se aprueba.

El agente tecnico debe dominar:

- RBAC/ABAC: permisos por rol, modulo, accion, centro, tenant y condicion.
- Seguridad OWASP ASVS: control de acceso en backend, no solo ocultar botones en frontend.
- Configuracion versionada: cambios de permisos y parametros deben dejar bitacora.
- Bootstrap de tenant: datos minimos para que una empresa nueva pueda operar.

Criterios de dominio:

- Puede definir permisos CRUD y permisos de accion critica por modulo.
- Puede detectar riesgos de privilegios excesivos.
- Puede proponer defaults seguros sin bloquear la operacion inicial.

### Contabilidad

El agente de negocio debe dominar:

- Principios de registro: devengo, partida doble, periodo, materialidad, consistencia y evidencia.
- Elementos contables IFRS: activos, pasivos, patrimonio, ingresos y gastos.
- Mapeos por evento: venta, compra, gasto, pago, cobro, consumo, merma, produccion terminada, ajuste y devolucion.
- Periodos: apertura, bloqueo, cierre, reapertura autorizada y reverso.
- Anexos: cada asiento debe poder regresar a su documento origen.

El agente tecnico debe dominar:

- Generacion de asientos balanceados: cargos = abonos.
- Motor de reglas contables por modulo, operacion, impuesto, producto, proveedor, cliente o centro.
- Bloqueos por periodo cerrado y reversos en lugar de ediciones destructivas.
- Integridad de anexos: documentos, XML/PDF, pagos, ordenes, entregas y movimientos.

Criterios de dominio:

- Puede explicar que evento crea cada asiento.
- Puede detectar cuentas sin mapeo o documentos sin anexo.
- Puede proponer validaciones para balance, periodo, moneda, impuesto y reverso.

## Agentes transversales

### Sinergia modular

#### Agente de negocio: Coordinador ERP entre areas

Responsabilidad:

- Validar que los flujos entre modulos tengan sentido para una empresa real.
- Detectar duplicidad de responsabilidades entre modulos.
- Definir que modulo es fuente de verdad para cada dato.
- Revisar eventos entre produccion, inventario, compras, ventas, costos y contabilidad.

Preguntas que responde:

- Donde debe nacer una necesidad: ventas, produccion, compras o inventario?
- Que documento debe disparar el siguiente paso?
- Que pasa si un modulo esta incompleto o desactivado?
- Que reglas deben ser comunes para todos los modulos?

Dependencias principales:

- Todos los modulos operativos.
- Documentos origen.
- Estados compartidos.
- Reglas de autorizacion.

#### Agente tecnico: Arquitecto de contratos internos

Responsabilidad:

- Definir contratos de datos entre modulos.
- Revisar eventos, IDs, estados y documentos origen.
- Detectar impactos tecnicos antes de modificar un flujo compartido.
- Vigilar compatibilidad entre frontend mock, API futura y persistencia.

Preguntas que responde:

- Que modelo o estructura se rompe si cambia este campo?
- Que modulo consume este estado?
- Que endpoint o servicio futuro debe existir?
- Que validaciones deben estar en frontend y cuales en backend?

Entregables:

- Matriz de dependencias.
- Contratos de eventos.
- Reglas de compatibilidad.
- Lista de pendientes tecnicos cruzados.

### Diseno, experiencia y localizacion

#### Agente de negocio: Especialista UX/UI de marca, experiencia operativa y lenguaje bilingue

Responsabilidad:

- Cuidar que toda pantalla de ERClave se sienta como parte de la misma marca.
- Traducir necesidades operativas de cada modulo a experiencias claras, compactas y accionables.
- Revisar que la interfaz priorice lectura rapida, flujo de trabajo y acciones principales.
- Evitar pantallas decorativas, redundantes o demasiado explicativas para un SaaS operativo.
- Mantener consistencia visual entre modulos sin borrar la personalidad funcional de cada area.
- Cuidar que todo texto visible pueda vivir correctamente en Espanol e Ingles.
- Mantener tono claro, directo y operativo en ambos idiomas.
- Evitar traducciones literales que confundan el proceso de negocio.

Preguntas que responde:

- Esta pantalla ayuda a operar mas rapido o solo muestra informacion bonita?
- La jerarquia visual deja claro que mirar primero y que accion tomar?
- El flujo cabe bien en escritorio y movil?
- El texto es breve, claro y localizable?
- El modulo nuevo se siente parte de ERClave?
- El texto conserva el mismo significado operativo en Espanol e Ingles?
- La traduccion cabe en botones, chips, tabs, tablas, modales y tarjetas?

Dependencias principales:

- `manual_identidad_paleta_morado.md`: identidad, paleta, temas y lineamientos generales.
- `frontend/index.html`: estructura base de app, sidebar, workspace, topbar, paneles y modal.
- `frontend/styles.css`: tokens, componentes, responsive y temas.
- `frontend/app.js`: renderizado de modulos, submodulos, formularios, tablas, alertas y estados.
- `frontend/i18n/translations.js`: textos localizables.

Entregables:

- Recomendaciones UX por modulo.
- Checklist visual antes de cerrar cambios.
- Checklist de localizacion Espanol/Ingles.
- Glosario de terminos funcionales por modulo.
- Mapa de componentes reutilizables.
- Criterios para estados vacios, errores, alertas, modales y formularios.
- Observaciones de accesibilidad y responsive.

#### Agente tecnico: Especialista tecnico de frontend, sistema visual e i18n

Responsabilidad:

- Mantener el sistema visual implementado con tokens, clases y componentes reutilizables.
- Revisar que nuevos cambios no dupliquen estilos ni creen variantes innecesarias.
- Validar tema claro, tema oscuro, responsive, overflow, truncado y legibilidad.
- Detectar deuda tecnica visual en CSS, HTML generado y textos de UI.
- Alinear implementacion frontend con el manual de identidad.
- Validar que los textos de UI usen `frontend/i18n/translations.js` cuando correspondan.
- Mantener paridad de claves entre `es` y `en`.
- Revisar que variables dinamicas de traduccion coincidan entre idiomas.

Preguntas que responde:

- Que clase o patron existente deberia reutilizarse?
- Este nuevo componente necesita CSS propio o puede componerse con clases actuales?
- Hay colores hardcodeados que deberian ser tokens?
- El layout se rompe en movil, modal, tabla o cards?
- Faltan estados visuales para error, exito, alerta, vacio o deshabilitado?
- Hay textos hardcodeados dentro de componentes o renderizadores?
- La clave i18n existe en Espanol e Ingles?
- Las variables de la frase traducida coinciden en ambos idiomas?

Dependencias principales:

- Tokens CSS de `:root` y `[data-theme="dark"]`.
- Componentes existentes de navegacion, paneles, cards, chips, tablas, formularios, modal y toast.
- Renderizadores de `frontend/app.js`.
- Reglas de localizacion en `frontend/i18n/translations.js`.
- Manual de identidad visual.

Entregables:

- Auditoria de consistencia visual.
- Auditoria i18n de textos visibles.
- Lista de clases o tokens que deben reutilizarse.
- Lista de claves faltantes o variables inconsistentes.
- Pendientes de responsive y accesibilidad.
- Recomendaciones de refactor visual cuando haya duplicacion real.
- Validaciones visuales sugeridas antes de publicar.

### Administracion y configuracion

#### Agente de negocio: Administrador funcional del sistema

Responsabilidad:

- Definir roles, permisos, modulos activos, submodulos y configuracion por tenant.
- Validar que la configuracion sea entendible para empresas chicas y medianas.
- Asegurar que cada area vea solo lo que necesita operar.

Preguntas que responde:

- Que permisos necesita cada rol?
- Que parametros deben ser globales y cuales por modulo?
- Que catalogos base deben existir antes de operar?
- Como se configura una empresa nueva?

Dependencias principales:

- Roles y usuarios.
- Centros de negocio.
- Catalogos base.
- Modulos y submodulos activos.

#### Agente tecnico: Especialista tecnico de configuracion

Responsabilidad:

- Revisar modelo de permisos, tenants, configuraciones y banderas de modulo.
- Detectar impacto tecnico de activar, ocultar o restringir funciones.
- Definir dependencias de configuracion para frontend, API y datos.

Preguntas que responde:

- Que componentes dependen de permisos?
- Que configuracion debe cargarse al iniciar sesion?
- Que defaults necesita una empresa nueva?
- Que validaciones deben bloquear acciones no permitidas?

Entregables:

- Matriz de permisos.
- Configuracion inicial por tenant.
- Dependencias tecnicas de modulos activos.
- Checklist de seguridad funcional.

## Agentes por modulo operativo

### Produccion

#### Agente de negocio: Especialista en flujos productivos y servicios repetibles

Responsabilidad:

- Dominar flujos de produccion para empresas de servicios, comercializadoras con armado, talleres, fabricas y negocios con procesos repetibles.
- Definir productos, servicios, recetas, recursos, etapas, responsables, tiempos, mermas y criterios de cierre.
- Validar que las ordenes puedan ejecutarse con insumos, herramientas, maquinaria y mano de obra disponibles.

Preguntas que responde:

- Como se traduce una venta o necesidad interna en una orden de produccion?
- Que diferencia hay entre fabricar un producto y ejecutar un servicio?
- Que recursos deben validarse antes de liberar una orden?
- Que evidencia se necesita para cerrar una etapa o entregable?

Dependencias principales:

- Almacenes: existencias, reservas y consumos.
- Compras: requisiciones por faltantes.
- Costos: costo estimado, real, merma y variaciones.
- Contabilidad: consumo, producto en proceso, producto terminado y merma.
- Ventas: pedidos que requieren produccion.

#### Agente tecnico: Especialista tecnico del modulo de Produccion

Responsabilidad:

- Entender como Produccion esta representado en `frontend/app.js`, `frontend/data/modules.js`, `frontend/data/mockDb.js` y `frontend/utils/production.js`.
- Revisar dependencias con submodulos de productos/servicios, recetas, ordenes, recursos, areas, puestos y maquinaria.
- Detectar que falta conectar en API futura, persistencia, permisos, reportes e integraciones.

Preguntas que responde:

- Que funciones del frontend renderizan o modifican Produccion?
- Que datos mock deben convertirse en entidades reales?
- Que validaciones estan solo en UI y deben pasar al backend?
- Que se rompe si cambia receta, orden, recurso o estado?

Entregables:

- Mapa tecnico de funciones y datos.
- Lista de endpoints pendientes.
- Checklist de integracion con almacenes, compras, costos y contabilidad.
- Riesgos antes de actualizar el modulo.

### Almacenes e inventarios

#### Agente de negocio: Especialista en inventario vivo

Responsabilidad:

- Definir reglas para almacenes, ubicaciones, movimientos, reservas, kardex, ajustes, lotes, series y mermas.
- Validar que el inventario represente disponibilidad real y no solo existencia teorica.
- Cuidar que las reservas de produccion y ventas no compitan sin control.

Preguntas que responde:

- Cuando una existencia esta disponible, reservada, bloqueada o en transito?
- Que movimientos deben afectar kardex?
- Como se liberan reservas vencidas o canceladas?
- Que reglas aplican para merma, ajuste y devolucion?

Dependencias principales:

- Produccion: reservas, consumos y producto terminado.
- Ventas: reservas y entregas.
- Compras: recepciones y costos de adquisicion.
- Costos: valuacion.
- Contabilidad: inventario, ajustes y merma.

#### Agente tecnico: Especialista tecnico de inventarios

Responsabilidad:

- Revisar estructuras de existencias, movimientos, reservas y kardex.
- Validar que cada movimiento tenga documento origen, costo y trazabilidad.
- Detectar si frontend, API o base de datos no actualizan disponibilidad de forma consistente.

Preguntas que responde:

- Que entidad calcula disponible vs reservado?
- Que eventos deben recalcular inventario?
- Que validaciones deben ser transaccionales?
- Que reportes dependen del kardex?

Entregables:

- Modelo tecnico de movimientos.
- Reglas de recalculo de existencia.
- Endpoints pendientes de inventario.
- Pruebas criticas de concurrencia y reservas.

### Compras y abastecimiento

#### Agente de negocio: Especialista en abastecimiento

Responsabilidad:

- Definir flujos de proveedores, requisiciones, autorizaciones, ordenes de compra, recepciones y reabastecimiento.
- Validar compras sugeridas desde faltantes, minimos, produccion o solicitudes internas.
- Cuidar tiempos de entrega, condiciones comerciales y autorizaciones.

Preguntas que responde:

- Cuando una necesidad debe convertirse en requisicion?
- Quien autoriza segun monto, centro o urgencia?
- Que pasa con recepciones parciales?
- Como se compara factura contra orden y recepcion?

Dependencias principales:

- Produccion: faltantes de recursos.
- Almacenes: recepciones.
- Gastos: facturas y cuentas por pagar.
- Costos: costo de adquisicion.
- Contabilidad: inventario, proveedor, impuestos y pagos.

#### Agente tecnico: Especialista tecnico de compras

Responsabilidad:

- Revisar entidades de proveedor, requisicion, orden de compra y recepcion.
- Validar integracion con inventario, gastos, costos y contabilidad.
- Detectar endpoints, estados y documentos origen faltantes.

Preguntas que responde:

- Que estado habilita recepcion?
- Que datos se copian de requisicion a orden?
- Que eventos actualizan almacen?
- Que validaciones evitan recibir mas de lo autorizado?

Entregables:

- Flujo tecnico requisicion-orden-recepcion.
- Contratos con almacenes y gastos.
- Lista de validaciones backend.
- Pendientes de UI y API.

### Ventas y clientes

#### Agente de negocio: Especialista comercial

Responsabilidad:

- Definir clientes, cotizaciones, pedidos, reservas, entregas, devoluciones y margen.
- Validar que el flujo comercial pueda operar venta de producto, servicio o producto fabricado bajo pedido.
- Cuidar promesas de entrega, precios, descuentos y rentabilidad.

Preguntas que responde:

- Cuando una cotizacion se convierte en pedido?
- Que condiciones disparan reserva o produccion?
- Como se manejan entregas parciales?
- Como se calcula margen estimado y real?

Dependencias principales:

- Almacenes: reservas y entregas.
- Produccion: ordenes por demanda.
- Costos: margen.
- Contabilidad: ingresos, impuestos, cuentas por cobrar y costo de venta.
- Reportes: demanda y rentabilidad comercial.

#### Agente tecnico: Especialista tecnico de ventas

Responsabilidad:

- Revisar datos de clientes, cotizaciones, pedidos, entregas y margen.
- Validar integraciones con inventario, produccion, costos y contabilidad.
- Detectar faltantes para API, permisos, documentos y reportes.

Preguntas que responde:

- Que entidad bloquea inventario para un pedido?
- Que evento crea una orden de produccion?
- Que datos requiere contabilidad al facturar o entregar?
- Que componentes deben actualizarse si cambia el estado del pedido?

Entregables:

- Mapa tecnico del flujo comercial.
- Contratos con almacenes y produccion.
- Estados y transiciones de pedido.
- Pendientes de API y UI.

### Gastos y cuentas por pagar

#### Agente de negocio: Especialista en gastos y pagos

Responsabilidad:

- Definir carga documental, clasificacion, asignacion, cuentas por pagar, pagos y vencimientos.
- Validar que XML, PDF, comprobantes y anexos soporten auditoria.
- Cuidar asignacion a centros de costos, ordenes, productos, servicios o proyectos.

Preguntas que responde:

- Que documentos respaldan un gasto?
- Como se clasifica un gasto directo, indirecto o administrativo?
- Que autorizacion necesita un pago?
- Como se relaciona un gasto con compras, costos o contabilidad?

Dependencias principales:

- Compras: factura contra orden y recepcion.
- Costos: asignaciones y prorrateos.
- Contabilidad: cuenta por pagar, pago, impuestos y anexos.
- Reportes: gasto por proveedor, centro y periodo.

#### Agente tecnico: Especialista tecnico de gastos

Responsabilidad:

- Revisar estructuras de documentos, proveedores, gastos, vencimientos, pagos y anexos.
- Validar integracion con costos, compras y contabilidad.
- Detectar necesidades de carga de archivos, almacenamiento, extraccion fiscal y conciliacion.

Preguntas que responde:

- Donde se guardan XML/PDF y como se relacionan?
- Que datos fiscales deben extraerse?
- Que estado genera cuenta por pagar?
- Que evento genera asiento contable?

Entregables:

- Modelo tecnico documental.
- Contratos con contabilidad y costos.
- Lista de endpoints para carga y pagos.
- Riesgos de seguridad y auditoria.

### Costos y centros de costos

#### Agente de negocio: Especialista en rentabilidad

Responsabilidad:

- Definir centros de costos, costo estimado, costo real, variaciones y rentabilidad.
- Validar que el sistema explique por que un producto, servicio, orden o cliente gana o pierde margen.
- Cuidar criterios de acumulacion, prorrateo y comparacion.

Preguntas que responde:

- Que costos entran al estimado?
- Que costos entran al real?
- Como se explica una variacion?
- Que indicadores necesita direccion para decidir?

Dependencias principales:

- Produccion: consumos, tiempos, merma y ordenes.
- Almacenes: valuacion de insumos y producto terminado.
- Compras: costos de adquisicion.
- Gastos: asignaciones.
- Ventas: margen.
- Contabilidad: variaciones y costo de venta.

#### Agente tecnico: Especialista tecnico de costos

Responsabilidad:

- Revisar formulas, fuentes de datos, acumulaciones, variaciones y reportes de costos.
- Validar que los calculos sean reproducibles y auditables.
- Detectar campos faltantes para costo estimado, real y margen.

Preguntas que responde:

- Que fuente alimenta cada componente del costo?
- Que calculos deben persistirse y cuales pueden recalcularse?
- Que pasa si falta costo, tiempo o cantidad?
- Que reportes dependen del calculo?

Entregables:

- Mapa de formulas.
- Dependencias por fuente de costo.
- Pruebas de calculo.
- Pendientes de precision y auditoria.

### Reportes e inteligencia operativa

#### Agente de negocio: Especialista en indicadores

Responsabilidad:

- Definir dashboards, indicadores, filtros, dimensiones, alertas y exportaciones.
- Traducir datos operativos en decisiones para duenos, gerentes y responsables de area.
- Priorizar reportes accionables sobre reportes decorativos.

Preguntas que responde:

- Que indicador ayuda a tomar una decision concreta?
- Que filtros necesita cada rol?
- Que alerta debe mostrarse antes de que el problema sea caro?
- Que reporte debe exportarse para junta, auditoria o seguimiento?

Dependencias principales:

- Todos los modulos operativos.
- Administracion: permisos y alcances.
- Contabilidad: periodos y cierres.
- Costos: rentabilidad y variaciones.

#### Agente tecnico: Especialista tecnico de reportes

Responsabilidad:

- Revisar datasets, filtros, permisos, agregaciones, exportaciones y rendimiento.
- Validar consistencia entre datos fuente y visualizaciones.
- Detectar cuando un reporte necesita vista materializada, endpoint especifico o cache.

Preguntas que responde:

- De que entidad sale cada metrica?
- Que filtros deben aplicarse por rol o centro?
- Que calculos se hacen en backend y cuales en frontend?
- Que tan caro sera consultar este reporte?

Entregables:

- Diccionario de metricas.
- Contratos de datos para dashboards.
- Reglas de permisos por reporte.
- Lista de reportes pendientes.

### Contabilidad

#### Agente de negocio: Especialista contable

Responsabilidad:

- Definir catalogo de cuentas, periodos, asientos, polizas, mapeos, anexos y cierres.
- Validar que cada documento origen pueda transformarse en registro contable auditable.
- Cuidar balance, impuestos, naturaleza de cuentas y periodos cerrados.

Preguntas que responde:

- Que asiento corresponde a cada operacion?
- Que documentos deben quedar anexos?
- Que pasa si no existe mapeo contable?
- Como se maneja cierre, reapertura o reverso?

Dependencias principales:

- Ventas: ingresos, impuestos, cuentas por cobrar y costo de venta.
- Gastos: cuentas por pagar y pagos.
- Almacenes: inventario, ajustes y merma.
- Costos: variaciones y producto en proceso.
- Compras: proveedores e impuestos.

#### Agente tecnico: Especialista tecnico contable

Responsabilidad:

- Revisar estructuras de cuentas, periodos, asientos, mapeos y anexos.
- Validar generacion automatica de asientos balanceados.
- Detectar reglas faltantes, cuentas sin mapeo, documentos sin anexo o cierres no protegidos.

Preguntas que responde:

- Que evento genera asiento?
- Que regla de mapeo aplica?
- Que validacion garantiza cargos igual a abonos?
- Que endpoints deben bloquear cambios en periodo cerrado?

Entregables:

- Matriz de mapeos contables.
- Contratos de documentos origen.
- Validaciones de periodo y balance.
- Pendientes de integracion contable.

## Checklist antes de actualizar un modulo

Antes de hacer una modificacion funcional o tecnica:

1. Identificar modulo y submodulo afectado.
2. Consultar agente de negocio correspondiente.
3. Consultar agente tecnico correspondiente.
4. Identificar microfrontend dueno y confirmar que el cambio no pertenece al shell o shared.
5. Identificar microservicio dueno y confirmar que no invade datos de otro servicio.
6. Revisar dependencias con otros modulos.
7. Revisar contratos afectados: API, eventos, permisos, estados, UI y datos.
8. Definir cambios esperados en frontend, API, datos, permisos y reportes.
9. Evaluar blast radius: que puede romperse si cambia este boton, formulario, estado o endpoint.
10. Validar localizacion: todo texto visible nuevo o modificado debe existir en Espanol e Ingles con las mismas variables dinamicas.
11. Ejecutar validaciones tecnicas disponibles.
12. Registrar el cambio en `TRAZABILIDAD.md`.

## Fuentes de referencia

Estas referencias sirven como base conceptual para entrenar a los agentes. No sustituyen la documentacion propia de ERClave; ayudan a mantener criterios profesionales y consistentes.

| Fuente | Uso dentro de ERClave |
|---|---|
| ASCM SCOR Digital Standard | Flujos de cadena operativa: planear, ordenar, comprar, transformar, surtir, devolver y orquestar. |
| COSO Internal Control - Integrated Framework | Controles, autorizaciones, segregacion de funciones, monitoreo y trazabilidad. |
| IFRS Conceptual Framework for Financial Reporting | Criterios para informacion contable y financiera util, verificable y comparable. |
| OWASP Application Security Verification Standard | Controles tecnicos de seguridad para autenticacion, autorizacion, validacion, datos, logs y APIs. |
| Arquitectura ERClave de microservicios y microfrontends | Fronteras por modulo, shell, microfrontends, microservicios, contratos, eventos y estrategia de migracion. |
| Contratos ERClave | Contratos API, eventos y UI que evitan acoplar modulos por implementacion interna. |
| `frontend/i18n/translations.js` | Fuente actual de textos localizables en Espanol e Ingles para el prototipo frontend. |

## Pendientes

- Convertir esta matriz en prompts operativos para agentes reales.
- Crear una ficha individual por agente cuando crezca el proyecto.
- Agregar nivel de prioridad por modulo.
- Definir responsables humanos o automatizados para cada agente.
- Convertir la regla obligatoria de segmentacion en checklist automatizable por PR o revision de cambios.
- Convertir la revision i18n Espanol/Ingles en validacion automatica de paridad de claves y variables.
