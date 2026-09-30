"""
Clona una referencia de trabajo (plantilla o guia) y dice que archivos leer.

    python scripts/clonar_referencia.py --plantilla IBS --dest <DIR>
    python scripts/clonar_referencia.py --flowpilot --dest <DIR>

Que resuelve, y por que existe:

1. La plantilla se resuelve por RAMA, no por commit (regla 21 del SKILL.md), asi
   que el clon debe traer el HEAD de esa rama. `--depth 1` basta y evita
   descargar el historial, que la skill nunca consulta.

2. `git clone --sparse` deja solo los archivos de raiz. Anadir un subdirectorio
   requiere una segunda invocacion (`sparse-checkout set`), y esa segunda ida al
   servidor cuesta mas de lo que ahorra en repos de este tamano. Por eso el
   sparse es opcional y se mide antes de asumirlo.

3. El clon no consume tokens: el gasto de la IA es LEER. Para la plantilla eso
   significa leerla **entera**, porque la fidelidad se copia archivo a archivo
   (regla 3 de `templates.md`). El script entrega el inventario completo para que
   el agente sepa el alcance y no se salte ninguno. Solo en `ace-flowpilot` el
   ambito se reduce a las guias aplicables, porque ahi la propia skill lo dice.

Codigos de salida: 0 correcto · 2 bloqueante · 3 error tecnico.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

PLANTILLAS = {
    "IBS": ("IBS", "app213-payexe-prorev-core-upda-s-ops-ace"),
    "HUB": ("HUB", "app213-payexe-prorev-hub-upda-s-ops-ace"),
    "ORQ": ("ORQ", "app213-payinfass-agrdeblis-retr-b-ops-ace"),
}

PLANTILLAS_URL = "https://github.com/Karinadr/plantillas-AI.git"
FLOWPILOT_URL = "https://github.com/ot4i/ace-flowpilot.git"
FLOWPILOT_RAMA = "main"
FLOWPILOT_DIRS = ["skills"]

# Las guias de ace-flowpilot se DESCUBREN, no se enumeran. Una lista fija se
# queda vieja en cuanto el repositorio publica una guia nueva, y entonces la
# skill deja de leer justo lo que deberia. Los patrones incluyen lo nuevo.
FLOWPILOT_INCLUYE = ["SKILL.md", "skills/*/SKILL.md", "skills/shared/*.md"]
FLOWPILOT_EXCLUYE = ["skills/shared/connectors", "backlog", "Images"]


def construir_args_clone(
    url: str,
    rama: str,
    destino: Path,
    sparse: bool = False,
    filtro_blobs: bool = True,
) -> list[str]:
    """Clon superficial de una sola rama y sin historial.

    `--depth 1` y `--single-branch` son el nucleo: la skill resuelve la plantilla
    por rama y nunca consulta el historial, asi que no se descarga.

    `--filter=blob:none` (partial clone) no trae los blobs hasta que se piden.
    No todos los servidores lo soportan, por eso `clonar` reintenta sin el.
    """
    args = [
        "clone",
        "--branch", rama,
        "--single-branch",
        "--depth", "1",
    ]
    if filtro_blobs:
        args += ["--filter=blob:none"]
    if sparse:
        args.append("--sparse")
    args += [url, str(destino)]
    return args


def construir_args_sparse(destino: Path, subdirs: list[str]) -> list[str]:
    return ["-C", str(destino), "sparse-checkout", "set", *subdirs]


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def ejecutar(args: list[str]) -> None:
    resultado = _git(*args)
    if resultado.returncode != 0:
        raise RuntimeError((resultado.stderr or resultado.stdout).strip())


def clonar_con_reintento(
    url: str,
    rama: str,
    destino: Path,
    sparse: bool,
) -> bool:
    """Clona con partial clone y, si el servidor no lo soporta, reintenta sin el.

    Devuelve si el partial clone se pudo usar, para que quede en el informe.
    """
    try:
        ejecutar(construir_args_clone(url, rama, destino, sparse=sparse, filtro_blobs=True))
        return True
    except RuntimeError:
        if destino.exists():
            shutil.rmtree(destino, ignore_errors=True)
        ejecutar(construir_args_clone(url, rama, destino, sparse=sparse, filtro_blobs=False))
        return False


def inventario(destino: Path) -> dict:
    """Lista el arbol completo de la referencia, agrupado por tipo.

    No es una lista de "lo importante": es el ambito de lectura. La plantilla se
    lee al 100% porque la fidelidad lo exige; narrowingar la lectura es como se
    cuela un residuo de otra plantilla.

    `.git` queda fuera: es metadato del clon, no contenido de la plantilla.
    """
    archivos = sorted(
        str(p.relative_to(destino)).replace("\\", "/")
        for p in destino.rglob("*")
        if p.is_file() and ".git" not in p.relative_to(destino).parts
    )
    por_extension: dict[str, int] = {}
    for relativo in archivos:
        extension = Path(relativo).suffix.lower() or "(sin extension)"
        por_extension[extension] = por_extension.get(extension, 0) + 1
    return {
        "total": len(archivos),
        "por_extension": dict(sorted(por_extension.items(), key=lambda kv: -kv[1])),
        "archivos": archivos,
    }


def descubrir_guias(
    destino: Path,
    incluye: list[str] | None = None,
    excluye: list[str] | None = None,
) -> list[str]:
    """Descubre las guias de `ace-flowpilot` por patron.

    Nada de listas fijas: si el repositorio publica una guia nueva, aparece sola.
    Excluir es por categoria (conectores de terceros, backlog, imagenes), no por
    nombre de archivo, para que un directorio nuevo siga entrando.
    """
    incluye = incluye or FLOWPILOT_INCLUYE
    excluye = excluye or FLOWPILOT_EXCLUYE

    encontradas: set[str] = set()
    for patron in incluye:
        for p in destino.glob(patron):
            if p.is_file():
                encontradas.add(str(p.relative_to(destino)).replace("\\", "/"))

    def excluido(relativo: str) -> bool:
        return any(relativo == e or relativo.startswith(f"{e}/") for e in excluye)

    return sorted(r for r in encontradas if not excluido(r))


def listar_subdirs(destino: Path) -> list[str]:
    """Subdirectorios disponibles en el clon, para diagnosticar un BLOQUEO."""
    return sorted(
        p.name for p in destino.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )


def clonar(
    url: str,
    rama: str,
    destino: Path,
    subdirs: list[str],
    sparse: bool,
    reusar: bool,
    lectura: str,
) -> dict:
    if destino.exists() and any(destino.iterdir()):
        if not reusar:
            raise RuntimeError(f"El destino ya existe y no esta vacio: {destino}. Usa --reusar.")
    elif destino.exists():
        shutil.rmtree(destino)

    if not destino.exists():
        parcial = clonar_con_reintento(url, rama, destino, sparse)
    else:
        parcial = True
    if sparse and subdirs:
        ejecutar(construir_args_sparse(destino, subdirs))

    commit = _git("-C", str(destino), "rev-parse", "HEAD").stdout.strip()
    arbol = inventario(destino)
    faltantes = [d for d in subdirs if not (destino / d).is_dir()]

    informe = {
        "url": url,
        "rama": rama,
        "destino": str(destino),
        "commit": commit,
        "sparse": sparse,
        "partial_clone": parcial,
        "subdirs_requeridos": subdirs,
        "subdirs_faltantes": faltantes,
        "lectura": lectura,
        "archivos_en_disco": arbol["total"],
        "por_extension": arbol["por_extension"],
        "archivos": arbol["archivos"],
    }

    informe["subdirs_disponibles"] = listar_subdirs(destino)
    return informe


def main() -> int:
    parser = argparse.ArgumentParser(description="Clona la referencia de trabajo de la skill")
    origen = parser.add_mutually_exclusive_group(required=True)
    origen.add_argument("--plantilla", choices=sorted(PLANTILLAS), help="Dominio IBS, HUB u ORQ")
    origen.add_argument("--flowpilot", action="store_true", help="Guia tecnica ace-flowpilot")
    parser.add_argument("--dest", type=Path, required=True)
    parser.add_argument("--sparse", action="store_true",
                        help="Dejar en disco solo el subdirectorio. Medido: no ahorra tiempo")
    parser.add_argument("--reusar", action="store_true",
                        help="Reutilizar el clon si el destino ya existe")
    args = parser.parse_args()

    if args.flowpilot:
        url, rama, subdirs = FLOWPILOT_URL, FLOWPILOT_RAMA, FLOWPILOT_DIRS
        lectura = "solo_guias_aplicables"
    else:
        rama, subdirectorio = PLANTILLAS[args.plantilla]
        url, subdirs = PLANTILLAS_URL, [subdirectorio]
        lectura = "todos"

    destino = args.dest
    destino.mkdir(parents=True, exist_ok=True)
    try:
        informe = clonar(url, rama, destino, subdirs, args.sparse, args.reusar, lectura)
    except RuntimeError as exc:
        print(json.dumps({"estado": "ERROR", "detalle": str(exc)}, ensure_ascii=False, indent=2))
        return 3

    if lectura == "solo_guias_aplicables":
        informe["guias_aplicables"] = descubrir_guias(destino)

    if informe["subdirs_faltantes"]:
        print(json.dumps({
            "estado": "BLOQUEANTE",
            "mensaje": "El subdirectorio de la plantilla no existe en esa rama. "
                       "Actualiza PLANTILLAS en el script con el nombre real.",
            "informe": informe,
        }, ensure_ascii=False, indent=2))
        return 2

    print(json.dumps({
        "estado": "OK",
        "aviso": (
            "La plantilla se lee al 100%: la fidelidad lo exige. "
            "El clon solo se optimiza en transferencia, nunca en lectura."
        ) if lectura == "todos" else (
            "Guias aplicables descubiertas por patron: una guia nueva aparece sola."
        ),
        "informe": informe,
    }, ensure_ascii=False, indent=2))
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
