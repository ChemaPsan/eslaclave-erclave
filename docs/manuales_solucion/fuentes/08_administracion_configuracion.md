# Manual funcional de Administracion: folios y consecutivos

- Audiencia: administradores del tenant
- Alcance por ambiente: Local; no promovido a QA
- Ultima revision: 2026-08-21
- Capacidades cubiertas: catalogo de codigos por tipo documental

## Proposito

El catalogo evita que cada operador invente codigos. La configuracion es independiente por tenant y documento.

## Acceso

Consultar requiere `admin.setting.read`; editar requiere `admin.setting.update`. Reservar un folio desde otro modulo requiere el permiso de alta de ese documento.

## Campos

| Campo | Efecto |
|---|---|
| Prefijo | Texto inicial, por ejemplo REC, OP, ART o COT. |
| Separador | Caracter entre prefijo y numero. |
| Siguiente numero | Proxima reserva; no puede disminuir. |
| Longitud | Digitos con ceros a la izquierda. |
| Administrado | ERClave reserva el siguiente codigo de forma atomica e idempotente. |
| Manual | El operador captura; el modulo valida formato y unicidad. |
| Estatus | Inactivo impide nuevas asignaciones. |

## Procedimiento

Abra **Administracion > Catalogos base > Folios y consecutivos**, localice el tipo, cambie los campos y guarde. Solo afecta altas nuevas; nunca renombra documentos existentes.

Ejemplo: `OP`, separador `-`, siguiente `25` y longitud `6` produce `OP-000025`.

## Catalogos iniciales

Productos/servicios, recetas, ordenes de produccion, maquinaria, almacenes, articulos, movimientos, areas, puestos, empleados, clientes, cotizaciones, pedidos y entregas.

## Validaciones frecuentes

- **No se puede retroceder:** elija un siguiente numero igual o mayor al actual.
- **Codigo manual obligatorio:** capturelo en el formulario origen.
- **Secuencia inactiva/no encontrada:** active o revise la configuracion.

Los reintentos con la misma clave devuelven el mismo resultado. Un folio reservado puede quedar sin documento si la operacion posterior falla; no se reutiliza silenciosamente.

## Cobertura

Catalogo y consumidores UI implementados en Local. Clientes API externos deben integrar la reserva central o usar compatibilidad manual autorizada.
