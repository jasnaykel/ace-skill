"""
Adaptador SCI + ETI -> contrato canonico.

Es una guia de lectura, no un parser de Excel. El SCI y el ETI llegan ya
convertidos a Markdown; extraer de un .xlsx entero es otro trabajo, con su
propia validacion. Este script fija **que** se extrae y **como se nombra** en
el contrato, para que la extraccion sea la misma siempre.

    python scripts/extraer_contrato.py SCI.md ETI.md -o contrato.yaml
    python scripts/extraer_contrato.py SCI.md ETI.md -o contrato.yaml --modo actualizar

No inventa. Lo que no se demuestra del documento queda vacio y el validador
bloquea: un contrato incompleto que aparenta estar completo es peor que uno
que dice lo que le falta.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from scripts.contrato import (  # noqa: E402
    EXIT_BLOCK,
    EXIT_ERROR,
    EXIT_WARNING,
    apply_profile,
    extract_minimal,
    hash_file,
    load_contract,
    load_profile,
    merge_manual,
    validate_contract,
)

_SKILL = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="SCI + ETI -> contrato canonico")
    parser.add_argument("sci", type=Path)
    parser.add_argument("eti", type=Path)
    parser.add_argument("-o", "--salida", type=Path, default=Path("contrato.yaml"))
    parser.add_argument("--perfil", type=Path, default=_SKILL / "proyectos" / "banbif" / "perfil.yaml")
    parser.add_argument("--modo", choices=["crear", "actualizar"], default="crear")
    parser.add_argument("--sin-perfil", action="store_true")
    args = parser.parse_args()

    for documento in (args.sci, args.eti):
        if not documento.is_file():
            print(f"[extraer] ERROR: no existe {documento}", file=sys.stderr)
            return EXIT_ERROR

    try:
        contrato = extract_minimal(
            args.sci.read_text(encoding="utf-8"),
            args.eti.read_text(encoding="utf-8"),
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[extraer] ERROR leyendo documentos: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.modo == "actualizar" and args.salida.is_file():
        try:
            contrato = merge_manual(load_contract(args.salida), contrato)
        except Exception as exc:  # noqa: BLE001
            print(f"[extraer] ERROR leyendo contrato previo: {exc}", file=sys.stderr)
            return EXIT_ERROR

    if not args.sin_perfil and args.perfil.is_file():
        try:
            contrato = apply_profile(contrato, load_profile(args.perfil))
        except Exception as exc:  # noqa: BLE001
            print(f"[extraer] ERROR aplicando perfil: {exc}", file=sys.stderr)
            return EXIT_ERROR

    contrato["fuentes"] = {
        "sci": {"archivo": str(args.sci), "sha256": hash_file(args.sci)},
        "eti": {"archivo": str(args.eti), "sha256": hash_file(args.eti)},
    }

    args.salida.write_text(
        yaml.safe_dump(contrato, sort_keys=False, allow_unicode=True, width=100),
        encoding="utf-8",
    )
    print(f"[extraer] contrato escrito en {args.salida}")

    # Valida despues de escribir: el archivo existe aunque falte informacion, y
    # quien viene a completarlo necesita verlo.
    try:
        advertencias = validate_contract(contrato, check_files=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[extraer] BLOQUEANTE: {exc}", file=sys.stderr)
        print("[extraer] completa el contrato antes de generar", file=sys.stderr)
        return EXIT_BLOCK
    for aviso in advertencias:
        print(f"[extraer] ADVERTENCIA: {aviso}", file=sys.stderr)
    return EXIT_WARNING if advertencias else 0


if __name__ == "__main__":
    raise SystemExit(main())
