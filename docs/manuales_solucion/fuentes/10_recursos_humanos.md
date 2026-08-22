# Manual funcional de Recursos Humanos

- Audiencia: responsables de RH y administradores de estructura
- Alcance por ambiente: Local para folios y elegibilidad productiva
- Ultima revision: 2026-08-21
- Capacidades cubiertas: areas, puestos, empleados y relacion con Produccion

## Proposito

RH administra la estructura completa. Un area o puesto no pertenece a Produccion por el simple hecho de existir.

## Regla de Produccion

La casilla **Interviene en produccion** nace desmarcada. Active solo puestos que participan en recetas u ordenes. Produccion muestra un trabajador cuando empleado, puesto y area estan activos y el puesto tiene esa casilla.

## Procedimiento

1. Cree un area general con codigo y nombre.
2. Cree los puestos dentro del area.
3. Marque la casilla productiva solo en puestos operativos productivos.
4. Registre empleados y asigne un unico puesto vigente.

Para un expediente nuevo, CURP requiere 18 caracteres, RFC de persona fisica 13 y NSS exactamente 11 digitos con digito verificador valido. El sistema valida estos datos antes de guardar y los mensajes no repiten el valor personal rechazado. El numero de empleado puede asignarse automaticamente segun Administracion.

Los codigos de area y numeros de empleado pueden asignarse desde Administracion. Cambiar prefijo no modifica historia.

## Integraciones

Produccion consulta una proyeccion minima de trabajadores elegibles y conserva ID estable mas nombre snapshot. No lee datos personales innecesarios ni escribe tablas RH.

## Mensajes frecuentes

- **No hay responsables elegibles:** confirme estatus de empleado, puesto y area, y la casilla productiva.
- **El puesto no aparece en receta:** un puesto general sin casilla productiva no debe aparecer.
- **El NSS debe contener exactamente 11 digitos:** complete los dos digitos faltantes y confirme el digito verificador; no agregue ceros sin revisar el documento fuente.
- **Capacidad laboral insuficiente:** confirme que existe por lo menos un trabajador activo en el puesto exacto requerido por la receta. Ser responsable de una orden no aporta capacidad a otro puesto.

## Limitaciones

No incluye nomina, reclutamiento, documentos, calendarios ni ausencias.
