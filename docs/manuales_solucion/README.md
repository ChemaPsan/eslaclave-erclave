# Manuales funcionales de la solucion ERClave

Esta biblioteca explica ERClave desde la perspectiva del usuario. No registra actividades de desarrollo, commits ni decisiones de implementacion.

## Organizacion

- `fuentes/`: Markdown versionable y revisable, una fuente por modulo.
- `word/`: documentos DOCX generados para distribucion.
- `REGISTRO.md`: cobertura, revision y pendientes de cada manual.

Los manuales se mantienen con `$erclave-solution-manuals`. Cada cambio funcional visible debe revisar si afecta conceptos, campos, estados, procedimientos, permisos, mensajes o integraciones documentadas.

## Construccion

```powershell
python .agents/skills/erclave-solution-manuals/scripts/build_manual_docx.py docs/manuales_solucion/fuentes/01_produccion.md docs/manuales_solucion/word/01_produccion.docx
```
