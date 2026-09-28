#!/usr/bin/env python3
"""Validate the global ACE README ETI contract before delivery."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    "## 1.",
    "## 2.",
    "## 3.",
    "## 4.",
    "## 5.",
    "## 6",
    "# 7 ",
    "# 8 ",
    "# 9 ",
    "# 10 ",
    "# 11 ",
    "# 12 ",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--domain", choices=("IBS", "HUB", "ORQ"), required=True)
    args = parser.parse_args()

    readme = Path(args.root) / "README.md"
    errors: list[str] = []
    if not readme.is_file():
        errors.append("README.md is missing at repository root")
    else:
        text = readme.read_text(encoding="utf-8")
        first_line = text.splitlines()[0] if text.splitlines() else ""
        if not re.fullmatch(r"# \d+_BUS_[a-z0-9_]+", first_line):
            errors.append("first line must match '# <ID>_BUS_<NombreFuncionalSnake>'")
        for section in REQUIRED_SECTIONS:
            if not any(line.startswith(section) for line in text.splitlines()):
                errors.append(f"missing ETI section: {section}")
        if "{{" in text or "}}" in text:
            errors.append("README contains unresolved template placeholders")
        for field in ("L\u00ednea de Producto", "Producto", "Nombre funcional", "Nombre t\u00e9cnico"):
            if field not in text:
                errors.append(f"missing component information field: {field}")
        if args.domain == "HUB" and "IBS (APP037)" in text:
            errors.append("HUB README contains the IBS producer default")

    if errors:
        for error in errors:
            print(f"BLOQUEO DOCUMENTAL: {error}", file=sys.stderr)
        return 1
    print("README ETI OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
