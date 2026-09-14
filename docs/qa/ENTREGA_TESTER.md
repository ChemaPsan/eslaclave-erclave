# Documentación para pruebas de ERClave en QA

Revisión documental: 10 de septiembre de 2026.
Versión del sistema descrita: `b63cdad2fbac423c24460e55582ccfc0003e9924`.
Aplicación: https://erclave.web.app

Este paquete contiene los siete manuales funcionales y la guía de pruebas de la versión publicada en QA. Explica las responsabilidades de cada área, los pasos de uso y los resultados que el tester debe comprobar. La disponibilidad del despliegue no sustituye la aceptación funcional: los casos están por ejecutar y sus resultados deben registrarse.

**Actualización del candidato:** los manuales incluyen feedback de formularios en todos los módulos y Backoffice, margen esperado sin tope de 100% y evidencia inicial/final de servicios con adjuntos optimizados y vencimiento a 365 días. Estas mejoras están en Local y **no se declaran liberadas a QA**. Los nueve casos nuevos tienen precondición de promoción; registre el SHA realmente probado. Plan técnico: `../operaciones/release_qa_20260914.md`.

**Estado editorial:** fuentes Markdown actualizadas; ocho Word regenerados y comprobados estructuralmente. La revisión visual de esta edición sigue pendiente por falta de renderizador disponible. No distribuir todavía los Word como versión final.

## Contenido y orden de lectura

1. **Guía de pruebas QA**: alcance, preparación, permisos, casos, evidencia y criterio de salida. Comience por este documento.
2. **Administración y Backoffice**: contexto, usuarios, roles y permisos para preparar las pruebas.
3. **Recursos Humanos**: estructura y trabajadores elegibles para las órdenes.
4. **Almacenes e Inventarios**: confirmaciones de entrada/salida, reservas, transferencias y devoluciones.
5. **Compras y Abastecimiento**: requisición, autorización, compra y recepción; el solicitante acepta servicios.
6. **Ventas y Clientes**: emisión/aprobación de cotizaciones, pedidos, entregas y servicios comerciales.
7. **Producción**: reserva, salida previa por Almacén, ejecución y recepción de producto terminado.
8. **Mantenimiento**: solicitud y entrega de refacciones, recuperación, resolución y cierre.

La matriz de ejecución incluida conserva un caso por fila y comienza con **Sin ejecutar**. Registre Pasa, Falla, Bloqueado o No aplica, junto con evidencia y observaciones. La versión corta `b63cdad` identifica el sistema probado; la fecha de este paquete identifica la revisión de los documentos.

## Puntos que deben conocerse antes de probar

- **Devolución de sobrantes de Mantenimiento:** la API existe, pero se detectó por revisión de código una discrepancia en el contenedor donde se monta la bandeja de solicitud. Verifique su acceso en pantalla. Si no aparece, registre la incidencia y marque esa variante Bloqueado; no improvise una entrada manual. Producción y la recepción de devoluciones en Almacén se evalúan por separado.
- **Compra directa:** la API la admite; el formulario actual de órdenes parte de una requisición aprobada. La variante de aceptación por comprador se prueba sólo con una orden directa ya preparada por un medio autorizado.
- **Producto terminado:** consultar y recibir exige permisos específicos de recepción, además de los permisos generales que correspondan.
- **Datos:** no se copiaron datos Local a QA. Los folios históricos mostrados durante desarrollo no son precondiciones que necesariamente existan en QA.
- **Alcance:** no se incluyen facturación, cobranza, devoluciones comerciales a clientes/proveedores ni los módulos futuros indicados en los manuales.

## Uso de los datos y evidencia

Use únicamente las cuentas y el tenant de pruebas autorizados. No cree otras empresas, envíe invitaciones, suspenda usuarios/tenants, elimine registros o induzca fallos en servicios compartidos fuera del alcance acordado. Los casos que carezcan de datos o autorización se registran Bloqueado, con su precondición faltante.

Comparta folios, cantidades, pasos y resultados observables; omita contraseñas, tokens, enlaces vigentes de invitación y datos personales reales. En entradas y salidas compare existencia, reserva, disponible y Kardex antes y después. Reintente la misma tarea cuando el sistema lo permita, sin duplicar documentos.

Los manuales no autorizan una liberación a Producción ni constituyen evidencia de que las pruebas ya hayan pasado.
