"""
Contrato -> OpenAPI 3.0.3 + parametros legacy + manifiesto.

    python scripts/generar_openapi.py contrato.yaml -d salida/

Produce, en `salida/`:
    openapi.yaml          una sola stanza servers
    parametros.json       los nombres que la skill ya usa (sin tocar la logica)
    artefactos.yaml       manifiesto de lo que hay que producir, por tipo
    paquete.json          indice del paquete de contexto que recibe la IA

No genera ACE. El XSD tampoco: lo produce `generate_cobol_dfdl_xsd.py` desde el
copybook, y el contrato solo lo referencia.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

from scripts.contrato import (  # noqa: E402
    EXIT_BLOCK,
    EXIT_ERROR,
    ContractError,
    apply_profile,
    load_contract,
    load_profile,
    resolve_template,
    to_legacy_parameters,
    to_openapi,
    to_request_schema,
    validate_contract,
)

_SKILL = Path(__file__).resolve().parent.parent


def manifiesto(contrato: dict) -> dict:
    """
    Que archivos espera la plantilla y cual es fijo, parametrizado o generado.

    Es la pieza que impide a la IA reescribir los 40-50 ficheros que la
    plantilla ya trae. Se deriva del tipo de plantilla, no de una lista escrita
    a mano que se queda vieja.
    """
    tipo = contrato["plantilla"]["tipo"]
    comun = {
        "README.md": "generar",
        "openapi.yaml": "generar_desde_contrato",
        "request.schema.json": "generar_desde_contrato",
        "ci/valid_cfg_values.yaml": "parametrizar",
        "ci/Monitoring.json": "parametrizar",
        "azure-pipelines.yml": "copiar_sin_modificar",
        "test/": "parametrizar",
    }
    if tipo == "ace-bus-rest":
        comun.update({
            "src/application/APP_<S>/.project": "copiar_sin_modificar",
            "src/application/APP_<S>/MF_<S>.msgflow": "copiar_sin_modificar",
            "src/application/APP_<S>/<S>.yaml": "generar_desde_contrato",
            "src/application/APP_<S>/application.descriptor": "copiar_sin_modificar",
            "src/v1.0/service/<S>/.project": "copiar_sin_modificar",
            "src/v1.0/service/<S>/gen/<S>.msgflow": "copiar_sin_modificar",
            "src/v1.0/service/<S>/restapi.descriptor": "copiar_sin_modificar",
            "src/v1.0/service/<S>/ace/esb/**/*.esql": "parametrizar",
            "src/v1.0/configuration/{DEV,QAS,PRD}/policyproject/**": "parametrizar",
            "src/v1.0/configuration/{DEV,QAS,PRD}/workdiroverride/wdo-*.txt": "parametrizar",
        })
    elif tipo == "ach":
        comun.update({"src/": "copiar_sin_modificar"})
    elif tipo == "ace-orquestador":
        comun.update({
            "src/application/APP_<S>/.project": "copiar_sin_modificar",
            "src/v1.0/service/<S>/ace/esb/**/*.esql": "parametrizar",
            "src/v1.0/configuration/{DEV,QAS,PRD}/workdiroverride/wdo-*.txt": "parametrizar",
        })
    return {
        "plantilla": {
            "tipo": tipo,
            "url": contrato["plantilla"].get("url", ""),
            "rama": contrato["plantilla"].get("rama", ""),
            "subdirectorio": contrato["plantilla"].get("subdirectorio", ""),
            "resolucion": "rama",
        },
        "clases": {
            "copiar_sin_modificar": sorted(k for k, v in comun.items() if v == "copiar_sin_modificar"),
            "parametrizar": sorted(k for k, v in comun.items() if v == "parametrizar"),
            "generar_desde_contrato": sorted(k for k, v in comun.items() if v == "generar_desde_contrato"),
            "generar": sorted(k for k, v in comun.items() if v == "generar"),
        },
        "protegidos": ["LIB_CORE_COMMON", "LIB_CORE_CONTROL", "LIB_SMF_UTIL"],
        "backend": contrato.get("artefactos_backend", {}),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Contrato -> OpenAPI + parametros + manifiesto")
    parser.add_argument("contrato", type=Path)
    parser.add_argument("-d", "--destino", type=Path, default=Path("paquete"))
    parser.add_argument("--perfil", type=Path, default=_SKILL / "proyectos" / "banbif" / "perfil.yaml")
    parser.add_argument("--sin-perfil", action="store_true")
    args = parser.parse_args()

    try:
        contrato = load_contract(args.contrato)
        perfil = None
        if not args.sin_perfil and args.perfil.is_file():
            perfil = load_profile(args.perfil)
            contrato = apply_profile(contrato, perfil)
        validate_contract(contrato, check_files=False)
        resolve_template(contrato, perfil)
        openapi = to_openapi(contrato)
        parametros = to_legacy_parameters(contrato)
        request_schema = to_request_schema(contrato)
        artefactos = manifiesto(contrato)
    except ContractError as exc:
        print(f"[openapi] BLOQUEANTE: {exc}", file=sys.stderr)
        return EXIT_BLOCK
    except Exception as exc:  # noqa: BLE001
        print(f"[openapi] ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR

    args.destino.mkdir(parents=True, exist_ok=True)
    _escribir(args.destino / "openapi.yaml",
              yaml.safe_dump(openapi, sort_keys=False, allow_unicode=True, width=100))
    _escribir(args.destino / "request.schema.json",
              json.dumps(request_schema, ensure_ascii=False, indent=2))
    _escribir(args.destino / "parametros.json",
              json.dumps(parametros, ensure_ascii=False, indent=2))
    _escribir(args.destino / "artefactos.yaml",
              yaml.safe_dump(artefactos, sort_keys=False, allow_unicode=True, width=100))
    _escribir(args.destino / "contrato.resuelto.yaml",
              yaml.safe_dump(contrato, sort_keys=False, allow_unicode=True, width=100))

    _verificar_una_stanza(openapi)
    print(f"[openapi] paquete escrito en {args.destino}")
    return 0


def _escribir(ruta: Path, contenido: str) -> None:
    ruta.write_text(contenido if contenido.endswith("\n") else contenido + "\n", encoding="utf-8")


def _verificar_una_stanza(openapi: dict) -> None:
    """
    El builder de REST API del Toolkit rechaza varias vias base distintas con
    "contains several server stanzas with different base paths". Se comprueba
    aqui, no en el Toolkit, donde el error llega tarde.
    """
    servidores = openapi.get("servers") or []
    if len(servidores) > 1:
        raise ContractError(f"OpenAPI con {len(servidores)} stanzas servers; debe tener una")


if __name__ == "__main__":
    raise SystemExit(main())
