# Documentación para pruebas de ERClave en QA

> Las fuentes Markdown describen su corte y ambiente. Los Word son exportaciones candidatas: comprobar [REGISTRO](../manuales_solucion/REGISTRO.md) antes de distribuir; no asumir paridad con cambios Local posteriores.

Revisión documental: 15 de septiembre de 2026.
Versión del sistema descrita: `e57237fe90319f88e1db8ed8d2e686604d2d9c54`.
Aplicación: https://erclave.web.app

Este paquete contiene los siete manuales funcionales y la guía de pruebas de la versión publicada en QA. Explica las responsabilidades de cada área, los pasos de uso y los resultados que el tester debe comprobar. La disponibilidad del despliegue no sustituye la aceptación funcional: los casos están por ejecutar y sus resultados deben registrarse.

**Actualización desplegada:** los manuales incluyen feedback de formularios en los módulos y Backoffice, margen esperado sobre costo sin tope de 100% y evidencia inicial/final de servicios en Producción, con adjuntos optimizados y vencimiento a 365 días. Las mejoras ya están en QA. Los nueve casos correspondientes siguen sujetos a ejecución funcional; registre el SHA realmente probado. Evidencia técnica del release: [plan y resultado](../operaciones/release_qa_20260914.md).

**Smoke parcial:** se comprobó en OP-000003 el formulario nuevo y el rechazo de descripción inicial vacía. La carga automatizada quedó detenida por el permiso de archivos locales de la extensión. No se ha comprobado guardado de evidencia, descarga ni cierre al 100%; estos resultados siguen pendientes y no son fallos confirmados del producto.

**Estado editorial:** fuentes Markdown actualizadas. Consulte [REGISTRO](../manuales_solucion/REGISTRO.md) para conocer el estado de generación y revisión visual de los ocho Word antes de distribuirlos como versión final.

## Contenido y orden de lectura

1. **Guía de pruebas QA**: alcance, preparación, permisos, casos, evidencia y criterio de salida. Comience por este documento.
2. **Administración y Backoffice**: contexto, usuarios, roles y permisos para preparar las pruebas.
3. **Recursos Humanos**: estructura y trabajadores elegibles para las órdenes.
4. **Almacenes e Inventarios**: confirmaciones de entrada/salida, reservas, transferencias y devoluciones.
5. **Compras y Abastecimiento**: requisición, autorización, compra y recepción; el solicitante acepta servicios.
6. **Ventas y Clientes**: emisión/aprobación de cotizaciones, pedidos, entregas y servicios comerciales.
7. **Producción**: reserva, salida previa por Almacén, ejecución y recepción de producto terminado.
8. **Mantenimiento**: solicitud y entrega de refacciones, recuperación, resolución y cierre.

La matriz de ejecución incluida conserva un caso por fila y conserva **Sin ejecutar** hasta concluir el caso; el smoke parcial se documenta en observaciones. Registre Pasa, Falla, Bloqueado o No aplica, junto con evidencia y observaciones. La versión corta `e57237f` identifica el sistema probado; la fecha de este paquete identifica la revisión de los documentos.

## Puntos que deben conocerse antes de probar

- **Devolución de sobrantes de Mantenimiento:** la API existe, pero se detectó por revisión de código una discrepancia en el contenedor donde se monta la bandeja de solicitud. Verifique su acceso en pantalla. Si no aparece, registre la incidencia y marque esa variante Bloqueado; no improvise una entrada manual. Producción y la recepción de devoluciones en Almacén se evalúan por separado.
- **Compra directa:** la API la admite; el formulario actual de órdenes parte de una requisición aprobada. La variante de aceptación por comprador se prueba sólo con una orden directa ya preparada por un medio autorizado.
- **Producto terminado:** consultar y recibir exige permisos específicos de recepción, además de los permisos generales que correspondan.
- **Fixture de evidencia:** OP-000003 y su servicio/receta fueron creados con autorización específica en la sesión QA acordada. Coordine su uso y conserve su historia; esta referencia no autoriza otros tenants o datos.
- **Datos:** no se copiaron datos Local a QA. Los folios históricos mostrados durante desarrollo no son precondiciones que necesariamente existan en QA.
- **Alcance:** no se incluyen facturación, cobranza, devoluciones comerciales a clientes/proveedores ni los módulos futuros indicados en los manuales.

## Uso de los datos y evidencia

Use únicamente las cuentas y el tenant de pruebas autorizados. No cree otras empresas, envíe invitaciones, suspenda usuarios/tenants, elimine registros o induzca fallos en servicios compartidos fuera del alcance acordado. Los casos que carezcan de datos o autorización se registran Bloqueado, con su precondición faltante.

Comparta folios, cantidades, pasos y resultados observables; omita contraseñas, tokens, enlaces vigentes de invitación y datos personales reales. En entradas y salidas compare existencia, reserva, disponible y Kardex antes y después. Reintente la misma tarea cuando el sistema lo permita, sin duplicar documentos.

Los manuales no autorizan una liberación a Producción ni constituyen evidencia de que las pruebas ya hayan pasado.
