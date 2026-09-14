"""Regenerate only the seven implemented module manuals."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    build = runpy.run_path(str(ROOT / 'tools/build-functional-document.py'))['build']
    for source in sorted((ROOT / 'docs/manuales_solucion/fuentes').glob('[0-9]*.md')):
        build(source, ROOT / 'docs/manuales_solucion/word' / (source.stem + '.docx'))
