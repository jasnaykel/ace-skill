"""
Pruebas de `clonar_referencia.py`.

Cubren lo que la skill decide antes de tocar la red: que comandos se construyen
y que archivos se declaran como lectura. La red no se prueba aqui a proposito:
una prueba que depende de GitHub falla cuando GitHub falla, y esa no es la
falla que hay que vigilar.

    python -m pytest tests/ -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ))

from scripts.clonar_referencia import (  # noqa: E402
    FLOWPILOT_EXCLUYE,
    FLOWPILOT_INCLUYE,
    PLANTILLAS,
    construir_args_clone,
    construir_args_sparse,
    descubrir_guias,
    inventario,
    listar_subdirs,
)

_RAIZ = Path(__file__).resolve().parent.parent


def test_clon_es_superficial_y_de_una_sola_rama(tmp_path):
    args = construir_args_clone("https://x.git", "IBS", tmp_path)
    assert "--depth" in args and args[args.index("--depth") + 1] == "1"
    assert "--single-branch" in args
    assert args[-1] == str(tmp_path)


def test_clon_no_trae_historial_completo(tmp_path):
    """La skill nunca consulta el historial: Depth 1 siempre."""
    assert "--depth" in construir_args_clone("https://x.git", "IBS", tmp_path)
    assert "--depth" in construir_args_clone("https://x.git", "IBS", tmp_path, sparse=True)


def test_clon_usa_partial_clone_para_no_traer_blobs(tmp_path):
    args = construir_args_clone("https://x.git", "IBS", tmp_path)
    assert "--filter=blob:none" in args


def test_partial_clone_es_conmutable(tmp_path):
    """No todos los servidores lo soportan: se puede apagar."""
    args = construir_args_clone("https://x.git", "IBS", tmp_path, filtro_blobs=False)
    assert "--filter=blob:none" not in args
    assert "--depth" in args


def test_sparse_apagado_por_defecto(tmp_path):
    """Medido: la segunda invocacion cuesta mas de lo que ahorra."""
    assert "--sparse" not in construir_args_clone("https://x.git", "IBS", tmp_path)
    assert "--sparse" in construir_args_clone("https://x.git", "IBS", tmp_path, sparse=True)


def test_sparse_checkout_lleva_los_subdirectorios(tmp_path):
    args = construir_args_sparse(tmp_path, ["app213-x", "src"])
    assert args[-3:] == ["set", "app213-x", "src"]


def test_cada_dominio_apunta_a_su_rama_y_subdirectorio():
    esperadas = {
        "IBS": ("IBS", "app213-payexe-prorev-core-upda-s-ops-ace"),
        "HUB": ("HUB", "app213-payexe-prorev-hub-upda-s-ops-ace"),
        "ORQ": ("ORQ", "app213-payinfass-agrdeblis-retr-b-ops-ace"),
    }
    assert PLANTILLAS == esperadas


def test_inventario_lista_el_arbol_completo(tmp_path):
    """La plantilla se lee al 100%: el inventario no puede filtrar archivos."""
    base = tmp_path / "app213-plantilla"
    (base / "src" / "v1.0" / "service" / "Svc").mkdir(parents=True)
    (base / "src" / "v1.0" / "service" / "Svc" / "restapi.descriptor").write_text("x", encoding="utf-8")
    (base / "src" / "v1.0" / "service" / "Svc" / "ace").mkdir()
    (base / "src" / "v1.0" / "service" / "Svc" / "ace" / "LIB_svc.esql").write_text("x", encoding="utf-8")
    (base / "docs").mkdir()
    (base / "docs" / "notas.txt").write_text("x", encoding="utf-8")

    arbol = inventario(tmp_path)
    assert arbol["total"] == 3
    assert len(arbol["archivos"]) == 3
    assert "app213-plantilla/docs/notas.txt" in arbol["archivos"]
    assert arbol["por_extension"][".esql"] == 1
    assert arbol["por_extension"][".txt"] == 1


def test_plantilla_no_reduce_el_ambito_de_lectura():
    """La regla: 100% de la plantilla. Un allowlist aqui cuela residuos."""
    import inspect

    from scripts import clonar_referencia

    fuente = inspect.getsource(clonar_referencia.clonar)
    assert "lectura" in fuente
    assert 'lecturas_sugeridas' not in fuente
    assert 'LECTURAS_PLANTILLA' not in fuente


def test_flowpilot_descubre_guias_por_patron(tmp_path):
    """Ahi si aplica filtrar: la skill dice consultar solo lo aplicable."""
    (tmp_path / "skills" / "shared" / "connectors").mkdir(parents=True)
    (tmp_path / "backlog").mkdir()
    (tmp_path / "Images").mkdir()
    (tmp_path / "SKILL.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "shared" / "node-types.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "ace-esql" ).mkdir()
    (tmp_path / "skills" / "ace-esql" / "SKILL.md").write_text("x", encoding="utf-8")
    (tmp_path / "skills" / "shared" / "connectors" / "zohocrm.md").write_text("x", encoding="utf-8")
    (tmp_path / "backlog" / "roadmap.md").write_text("x", encoding="utf-8")
    (tmp_path / "Images" / "ACE_Bob10.png").write_bytes(b"x")

    guias = descubrir_guias(tmp_path)
    assert "SKILL.md" in guias
    assert "skills/shared/node-types.md" in guias
    assert "skills/ace-esql/SKILL.md" in guias
    assert "skills/shared/connectors/zohocrm.md" not in guias
    assert "backlog/roadmap.md" not in guias
    assert "Images/ACE_Bob10.png" not in guias


def test_una_guia_nueva_aparece_sola(tmp_path):
    """El motivo de descubrir en vez de enumerar: no hay que actualizar la skill."""
    (tmp_path / "skills" / "shared").mkdir(parents=True)
    (tmp_path / "skills" / "shared" / "nueva-guia.md").write_text("x", encoding="utf-8")
    assert "skills/shared/nueva-guia.md" in descubrir_guias(tmp_path)


def test_no_hay_lista_fija_de_guias():
    """Si alguien re-introduce una lista enumerada, estas pruebas lo detectan."""
    import inspect

    from scripts import clonar_referencia

    fuente = inspect.getsource(clonar_referencia)
    assert "LECTURAS_FLOWPILOT" not in fuente


def test_exclusiones_son_por_categoria_no_por_archivo():
    """Si se excluye por nombre de archivo, un directorio nuevo deja de entrar."""
    for patron in FLOWPILOT_EXCLUYE:
        assert "*" not in patron, patron
    assert any("*" in patron for patron in FLOWPILOT_INCLUYE)


def test_listar_subdirs_ayuda_a_diagnosticar_bloqueo(tmp_path):
    (tmp_path / "app213-plantilla").mkdir()
    (tmp_path / ".git").mkdir()
    assert listar_subdirs(tmp_path) == ["app213-plantilla"]


def test_el_gate_no_fija_el_valor_de_https():
    """IBS y ORQ publican https="true"; HUB publica "false". Fijarlo rompe fidelidad."""
    # Se lee el archivo: importarlo ejecutaria el script y abortaria con sys.exit.
    fuente = (_RAIZ / "scripts" / "verify_scaffold.py").read_text(encoding="utf-8")
    assert '"https", "false"' not in fuente
    assert '_https in ("true", "false")' in fuente
