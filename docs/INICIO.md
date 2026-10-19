# Portal documental de ERClave

[CC-20: aceptación integrada Local preparada](operaciones/cc20_aceptacion_integrada_local.md). Los 16 casos esperan ejecución y evidencia; no equivalen a aceptación QA.

[Guía CC-19 de mapeos y configuración contable opcional](arquitectura/cc19_mapeos_y_configuracion_contable.md): diagrama, insumos por dueño y roles de cuentas a definir. CC-19 sigue sin backfill por falta de datos y equivalencias reales; Accounting sigue apagado.

Este es el punto de entrada en Obsidian. El [índice completo](INDICE_DOCUMENTAL.md) enlaza las fuentes mantenidas, diseños, evidencias históricas y exportaciones pendientes. Abrir esta carpeta dentro del vault ERC existente; no hace falta cambiar su configuración personal.

## Recorrido de trabajo

1. [Inicio de sesión](contexto/INICIO_SESION.md) → [estado por ambiente](contexto/ESTADO_ACTUAL.md).
2. [Decisiones vigentes](contexto/DECISIONES.md) → [pendientes generales](contexto/PENDIENTES.md) → [control por submódulo contable](contexto/CONTROL_CONTABLE.md).
3. [Fichas funcionales](../modulos/README.md) → [dueños de datos](arquitectura/ownership_datos_mvp.md) → [mapa API](arquitectura/apis_mvp.md) → [contratos ejecutables](../contracts/api/README.md).
4. [Manuales](manuales_solucion/README.md) → [estado de publicaciones](manuales_solucion/REGISTRO.md) → [matriz QA](qa/MATRIZ_EJECUCION_QA.md).
5. [Agentes responsables](../AGENTES.md) → [gobierno documental](arquitectura/gobierno_documentacion_viva.md) → [trazabilidad](../TRAZABILIDAD.md).

## Relación organizacional y contable

[Modelo organizacional](arquitectura/cont_02_administracion_organizacional.md) → [sesión y alcances](arquitectura/cont_03_sesion_alcances.md) → [capacidades con Accounting opcional](arquitectura/matriz_capacidades_organizacionales.md) → [centros de costos](arquitectura/cont_05_catalogo_centros.md). La matriz de [CONTROL_CONTABLE](contexto/CONTROL_CONTABLE.md) relaciona maestros, Ventas, Inventario, Producción, RH, Compras y Mantenimiento con implementación, brecha, evidencia y criterio de cierre. El [plan contable](arquitectura/plan_preparacion_contabilidad.md) explica secuencia sin convertir diseño futuro en runtime.

CC-10/11/12 y [CC-14 Inventarios/productores](arquitectura/cont_08_inventario_productores.md) implementados Local. [CC-15 Compras](arquitectura/cont_08_compras_contexto.md) implementado Local CHG-319. CC-16 Mantenimiento implementado Local CHG-320. Siguiente: CC-17/18; consultar INICIO_SESION.

## Lectura del grafo

El índice permite llegar a cada documento y consultar su autoridad. Los enlaces Markdown relativos funcionan en Obsidian y GitHub. Usar el grafo local del control contable, de una ficha o de una decisión para explorar dependencias; el índice global concentra conexiones de catálogo.

Una evidencia histórica demuestra sólo lo observado en su fecha. Un diseño no prueba implementación. Los Word marcados pendientes no sustituyen su fuente Markdown. Local, QA y Producción se consultan separadamente; no se verificaron recursos remotos en esta auditoría.

## Mantenimiento automático

El [registro](documentacion-registro.json) asigna clase, custodio y autoridad a cada archivo. Al crear, mover o borrar documentación actualizar el registro y ejecutar npm run docs:index. npm run validate:documentation, verify y CI detectan archivos sin clasificar, índices desactualizados, enlaces rotos, fuentes históricas sin aviso y cambios en Word/fuentes posteriores a la paridad registrada. Los dueños contrastan las afirmaciones con código, contratos y evidencia; el script no certifica reglas de negocio ni aceptación UAT.

Resultado y brechas: [auditoría documental CHG-311](auditorias/documentacion_2026-10-07.md).
