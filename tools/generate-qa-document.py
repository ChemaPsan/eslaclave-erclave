"""Generate the QA guide from its canonical source using the shared layout."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]

if __name__ == '__main__':
    build = runpy.run_path(str(ROOT / 'tools/build-functional-document.py'))['build']
    build(ROOT / 'docs/qa/guia_pruebas_qa_mvp.md', ROOT / 'docs/qa/guia_pruebas_qa_mvp.docx')
