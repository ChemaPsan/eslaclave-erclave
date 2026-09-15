from argparse import ArgumentParser
from pathlib import Path

import runpy


def build(source: Path, target: Path) -> None:
    root = Path(__file__).resolve().parents[4]
    renderer = runpy.run_path(str(root / "tools" / "build-functional-document.py"))
    renderer["build"](source, target)


def main() -> None:
    parser = ArgumentParser(description="Genera un manual DOCX desde su fuente Markdown.")
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    args = parser.parse_args()
    build(args.source, args.target)


if __name__ == "__main__":
    main()
