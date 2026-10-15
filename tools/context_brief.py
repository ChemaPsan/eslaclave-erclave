"""Read-only, dependency-free orientation for an ERClave working tree."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", "-c", "core.quotePath=false", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return result.stdout.rstrip("\r\n") if result.returncode == 0 else "no disponible"


def first_section(source: str) -> tuple[str, str]:
    headings = list(re.finditer(r"(?m)^## (.+)$", source))
    if not headings:
        return "sin sección", ""
    start = headings[0].end()
    end = headings[1].start() if len(headings) > 1 else len(source)
    return headings[0].group(1), source[start:end].strip()


def status_paths(status: str) -> list[str]:
    paths = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.append(path.replace("\\", "/"))
    return paths


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable local facts")
    args = parser.parse_args()

    status = git("status", "--short", "--untracked-files=all")
    paths = status_paths(status) if status != "no disponible" else []
    scopes = dict(sorted(Counter(path.split("/", 1)[0] for path in paths).items()))
    state_heading, state_summary = first_section(read("docs/contexto/ESTADO_ACTUAL.md"))
    pending_heading, pending_summary = first_section(read("docs/contexto/PENDIENTES.md"))
    trace_ids = re.findall(r"(?m)^### (CHG-\d{3})$", read("TRAZABILIDAD.md"))
    qa_sha_match = re.search(r"QA está desplegado en `([0-9a-f]{40})`", read("docs/contexto/ESTADO_ACTUAL.md"))
    qa_rows = [line for line in read("docs/qa/MATRIZ_EJECUCION_QA.md").splitlines() if line.startswith("| QA-")]
    qa_statuses = dict(sorted(Counter(line.split("|")[3].strip() for line in qa_rows).items()))
    result = {
        "kind": "local_documentary_context",
        "remote_verified": False,
        "branch": git("branch", "--show-current"),
        "head": git("rev-parse", "--short", "HEAD"),
        "latest_traceability": trace_ids[-1] if trace_ids else None,
        "documented_qa_sha": qa_sha_match.group(1) if qa_sha_match else None,
        "changed_files": len(paths),
        "changed_scopes": scopes,
        "qa_case_statuses_documented": qa_statuses,
        "state_heading": state_heading,
        "state_summary": state_summary,
        "pending_heading": pending_heading,
        "pending_summary": pending_summary,
        "tools": {name: bool(shutil.which(name)) for name in ("git", "node", "npm", "python")},
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    print("ERClave: contexto documental local (sin consulta QA)")
    print(f"Rama/HEAD: {result['branch']} / {result['head']}")
    print(f"Último cambio: {result['latest_traceability'] or 'no disponible'}")
    print(f"QA documentado: {result['documented_qa_sha'] or 'no disponible'} (sin verificación remota)")
    print(f"Árbol local: {len(paths)} archivos; scopes {scopes}")
    print(f"Matriz QA documentada: {qa_statuses} (sin ejecución nueva)")
    print(f"Herramientas: {result['tools']}")
    print(f"Estado: {state_heading}\n{state_summary}")
    print(f"Pendientes: {pending_heading}\n{pending_summary}")


if __name__ == "__main__":
    main()
