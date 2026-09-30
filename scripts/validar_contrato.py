"""
Valida el contrato canonico antes de generar.

    python scripts/validar_contrato.py contrato.yaml
    python scripts/validar_contrato.py contrato.yaml --perfil proyectos/banbif/perfil.yaml
    python scripts/validar_contrato.py contrato.yaml --shadow

Codigos de salida (los mismos en todos los scripts de esta capa):
    0 correcto · 1 advertencias · 2 bloqueante · 3 error tecnico

`--shadow` valida y reporta pero nunca bloquea: es el modo de migracion, para
medir cuantos bloqueantes da el contrato antes de que bloqueen.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.contrato import (  # noqa: E402
    EXIT_BLOCK,
    EXIT_ERROR,
    EXIT_WARNING,
    ContractError,
    apply_profile,
    load_contract,
    load_profile,
    resolve_template,
    validate_contract,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida el contrato canonico")
    parser.add_argument("contrato", type=Path)
    parser.add_argument("--perfil", type=Path, default=Path(__file__).resolve().parent.parent / "proyectos" / "banbif" / "perfil.yaml")
    parser.add_argument("--sin-perfil", action="store_true")
    parser.add_argument("--sin-archivos", action="store_true",
                        help="No exigir que el copybook exista en disco")
    parser.add_argument("--shadow", action="store_true",
                        help="Reporta pero devuelve 0 aunque haya bloqueantes")
    parser.add_argument("--json", dest="json_salida", type=Path)
    args = parser.parse_args()

    def emitir(estado: str, mensaje: str, advertencias: list[str]) -> None:
        resultado = {"estado": estado, "mensaje": mensaje, "advertencias": advertencias}
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
        if args.json_salida:
            args.json_salida.write_text(
                json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    try:
        contrato = load_contract(args.contrato)
        perfil = None
        if not args.sin_perfil and args.perfil.is_file():
            perfil = load_profile(args.perfil)
            contrato = apply_profile(contrato, perfil)
        advertencias = validate_contract(contrato, check_files=not args.sin_archivos)
        resolve_template(contrato, perfil)
    except ContractError as exc:
        emitir("BLOQUEANTE", str(exc), [])
        return 0 if args.shadow else EXIT_BLOCK
    except FileNotFoundError as exc:
        emitir("ERROR", f"No se encontro el archivo: {exc}", [])
        return EXIT_ERROR

    emitir("ADVERTENCIA" if advertencias else "OK", "Contrato valido", advertencias)
    return EXIT_WARNING if advertencias else 0


if __name__ == "__main__":
    raise SystemExit(main())
