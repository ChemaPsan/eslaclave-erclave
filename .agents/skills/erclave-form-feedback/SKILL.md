---
name: erclave-form-feedback
description: Crear o corregir formularios ERClave y su feedback de validación, errores de negocio y fallos técnicos. Usar al modificar capturas, serialización de payloads, controles condicionales, clientes de errores o componentes compartidos de formularios de cualquier módulo, incluyendo módulos futuros.
---

# Formularios corregibles por el usuario

Leer `docs/arquitectura/feedback_operativo_y_errores.md` desde la raíz del repositorio. Aplicar este contrato a formularios modales, inline, asistentes, partidas dinámicas y Backoffice dentro del alcance del cambio.

## Identificar el recorrido real

- Inventariar los formularios afectados, su módulo, submit, cliente API, esquema backend y manejador de errores. Un cambio compartido requiere revisar todos sus consumidores en Administración, Producción, Almacenes, Compras, Ventas, RH y Mantenimiento, más Backoffice y módulos futuros que lo consuman.
- Comparar required, límites, tipos, valores cero y reglas condicionales entre controles y contrato. No inventar restricciones ni trasladar autorización o reglas críticas fuera del backend.
- Seguir la respuesta rechazada desde el cliente hasta la pantalla. Conservar código estable y detalles estructurados; no reducir el objeto a un mensaje antes de resolver sus campos.

No aplicar automáticamente un máximo de 100 a todo porcentaje. Distinguir proporción sobre un total de utilidad sobre costo; al retirar un límite revisar también Pydantic, OpenAPI, precisión/constraints PostgreSQL y la tarjeta de lectura. Conservar las reglas no afectadas y probar valores por encima del límite anterior.

## Resolver sin adivinar

- Asociar rutas de payload a controles mediante nombres exactos o un mapa explícito por formulario. Normalizar prefijos de transporte conocidos, como `body`, conservando índices de arrays: `items[1].quantity` debe señalar la cantidad de la segunda partida, nunca la primera por coincidencia parcial.
- Revisar aliases, campos anidados, IDs ocultos de lookups, listas que se reordenan y campos serializados con otro nombre. Marcar el control visible que permite corregir el valor; mantener la identidad estable del registro.
- Resolver causas mediante `error.code`, tipo de validación y metadatos estructurados permitidos. Nunca deducir el campo buscando palabras en `error.message`, textos traducidos o diagnósticos libres. No mostrar trazas, payloads ni el texto técnico del servidor.
- Un error sin ruta resoluble permanece como error general accionable. No decir «revisa los campos marcados» si ninguno pudo marcarse. Un fallo técnico, permiso, concurrencia o dato no editable no implica que la captura sea incorrecta; indicar el siguiente paso seguro y referencia de soporte cuando exista.

Cuando un schema legado entregue `ValueError` sin código estructurado, admitir únicamente equivalencias literales finitas verificadas contra el schema en `VALIDATION_RULES`. Cada equivalencia declara código estable y rutas relativas; no usar heurísticas, substrings ni texto libre. Validar paridad ES/EN y referencias del catálogo.

## Permitir corregir

- Mostrar el requisito y cómo corregirlo junto al campo; resumir errores múltiples con navegación a controles resolubles. Usar etiquetas de negocio y localización ES/EN con las mismas variables.
- Añadir indicador textual y visual, `aria-invalid` y asociación mediante `aria-describedby` sin borrar descripciones previas. Enviar foco al primer control inválido visible y habilitado; si no existe, al resumen accesible. Al corregir o reabrir, limpiar exclusivamente marcas y referencias creadas por el feedback.
- Respetar `hidden`, controles deshabilitados y condiciones de negocio. No enfocar ni exigir controles que no aplican. Los errores sobre requisitos no editables explican dónde resolverlos.
- Conservar valores, selecciones y partidas tras un rechazo; restaurar únicamente el estado operativo confirmado cuando corresponda. No cerrar, resetear ni anunciar éxito en el camino de error. Reintentar no duplica operaciones ni salta permisos.

Capturar el formulario propietario antes de esperar red/autenticación y caducar interacciones sin petición. No atribuir un error al formulario que se abrió después. Si cambian valores o filas mientras llega un rechazo, conservar el borrador actual sin marcarlo con errores de una captura anterior. No persistir contraseñas ni borradores sensibles.

Para capturas con adjuntos, comprobar límites tanto en navegador como servidor, formato real, asociación por tenant/registro, conservación tras errores y descarga privada. Probar optimización y vencimiento conforme a la política vigente del módulo; no confundir expiración de acceso con borrado físico ni eliminar el texto histórico junto con un adjunto.

## Evidencia de regresión

Ejecutar `npm run validate:form-feedback`, `npm run test:form-feedback`, `npm run validate:error-feedback`, validaciones i18n/documentales aplicables y `npm run verify`. Los chequeos de texto o presencia de funciones no demuestran comportamiento.

Agregar o actualizar pruebas conductuales negativas sobre el recorrido real de los formularios afectados: rechazo local y de servidor; varios errores; ruta anidada y segunda partida; error de negocio conocido; ruta/código desconocido; permiso y red/5xx. Comprobar mensaje accionable, control correcto, foco, ARIA, conservación de captura, limpieza al corregir y ausencia de éxito o doble envío. Verificar ES/EN, controles condicionales y CSS computado de `hidden` en navegador.

Para un cambio transversal registrar evidencia por formulario y módulo; cubrir todos los consumidores afectados, no inferir cobertura completa de un solo formulario o de probar el helper. Distinguir pruebas con respuestas simuladas de integración real y UAT. Documentar cualquier recorrido no ejecutado, con causa; no declarar validación total mientras queden pendientes.

Mantener la matriz/evidencia del cambio, documentación y trazabilidad según `AGENTS.md`. Esta skill no autoriza despliegues ni mutaciones remotas. La verificación debe respetar las fronteras de ambientes del proyecto.
