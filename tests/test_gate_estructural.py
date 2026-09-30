"""
Pruebas del gate estructural de la generacion.

El gate existe por un motivo concreto: el servicio 147 genero ESQL que no
compilaba y el error no aparecio hasta el Toolkit. Estas pruebas existen para
que eso no vuelva a pasar en silencio.

Cada prueba toma el fragmento que rompio una regla real y comprueba que el gate
lo detecta; y toma la forma correcta y comprueba que NO la marca. Un gate que
solo detecta errores y marca todo lo demas como roto termina ignorandose.

    python -m pytest tests/ -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parent.parent
_GATE = _RAIZ / "scripts" / "gate_estructural.py"

# ESQL que compila, tomado de LIB_CORE_COMMON (FormatServiceErrorsForEnvironment).
# Si el gate marca esto, el gate esta roto, no el codigo.
ESQL_BUENO = """
BROKER SCHEMA a.b.c
PATH a.b.common;

CREATE PROCEDURE armaLista(IN refEnv REFERENCE, IN refDfdlOut REFERENCE, IN refJsonOut REFERENCE)
BEGIN
\tDECLARE refItem REFERENCE TO refDfdlOut.LISTADOCOBRANZARSP;
\tDECLARE refJsonItem REFERENCE TO refJsonOut.CollectionsFreeList.Item;

\tCREATE LASTCHILD OF refJsonOut IDENTITY(JSON.Array)CollectionsFreeList;

\tWHILE LASTMOVE(refItem) DO
\t\tIF isNotEmpty(refItem.OCODCLI) THEN
\t\t\tSET refJsonItem.PartyIdentification = TRIM(CAST(refItem.OCODCLI AS CHARACTER));
\t\t\tMOVE refJsonItem NEXTSIBLING;
\t\tEND IF;

\t\tMOVE refItem NEXTSIBLING;
\tEND WHILE;
END;
"""


def _correr(tmp_path: Path, esql: str) -> subprocess.CompletedProcess:
    (tmp_path / "ace" / "esb").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ace" / "esb" / "LIB_TEST.esql").write_text(esql, encoding="utf-8")
    (tmp_path / "README.md").write_text("plantillas-AI", encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(_GATE), str(tmp_path), "a.b.c"],
        capture_output=True,
        text=True,
    )


def test_el_gate_deja_pasar_la_forma_compilada(tmp_path):
    """Si esto falla, el gate marca como erroneo codigo que ya compila en IBS."""
    resultado = _correr(tmp_path, ESQL_BUENO)
    salida = resultado.stdout + resultado.stderr
    assert "IDENTITY" not in salida
    assert "bucle infinito" not in salida
    assert "desbalanceado" not in salida


def test_detecta_identity_en_un_set(tmp_path):
    """
    Error real del 147: `SET refJsonOut.X IDENTITY(JSON.Array)`.

    En ESQL el modificador IDENTITY solo existe en CREATE FIELD y
    CREATE LASTCHILD OF. En un SET el parser aborta con
    "Syntax error. Valid options include: = NAME NAMESPACE TYPE VALUE".
    """
    roto = ESQL_BUENO.replace(
        "CREATE LASTCHILD OF refJsonOut IDENTITY(JSON.Array)CollectionsFreeList;",
        "SET refJsonOut.CollectionsFreeList IDENTITY(JSON.Array);",
    )
    resultado = _correr(tmp_path, roto)
    salida = resultado.stdout + resultado.stderr
    assert "IDENTITY" in salida
    assert resultado.returncode == 2


def test_detecta_bucle_sin_avance_incondicional(tmp_path):
    """
    Error real del 147: el MOVE ... NEXTSIBILING solo estaba en la rama ELSE,
    asi que con un registro con datos el bucle no avanzaba nunca.
    """
    roto = ESQL_BUENO.replace(
        "\t\t\tMOVE refJsonItem NEXTSIBLING;\n\t\tEND IF;\n\n\t\tMOVE refItem NEXTSIBLING;",
        "\t\tEND IF;\n\tELSE\n\t\t\tMOVE refItem NEXTSIBLING;\n\t\tEND IF;",
    )
    assert roto != ESQL_BUENO, "el fixture no se sustituyo: la prueba no probaria nada"
    resultado = _correr(tmp_path, roto)
    salida = resultado.stdout + resultado.stderr
    assert "bucle infinito" in salida
    assert resultado.returncode == 2


def test_detecta_if_desbalanceado(tmp_path):
    resultado = _correr(tmp_path, ESQL_BUENO.replace("END IF;", ""))
    salida = resultado.stdout + resultado.stderr
    assert "desbalanceado" in salida
    assert resultado.returncode == 2


def test_detecta_while_desbalanceado(tmp_path):
    resultado = _correr(tmp_path, ESQL_BUENO.replace("END WHILE;", ""))
    salida = resultado.stdout + resultado.stderr
    assert "desbalanceado" in salida
    assert resultado.returncode == 2


def test_end_while_no_cuenta_como_while(tmp_path):
    """
    `END WHILE` contiene la palabra `WHILE`. Sin el lookbehind, el conteo sale
    desbalanceado siempre y el gate marca como roto un archivo correcto.
    """
    resultado = _correr(tmp_path, ESQL_BUENO)
    salida = resultado.stdout + resultado.stderr
    assert "WHILE/END WHILE desbalanceado" not in salida


def test_detecta_call_a_routine_inexistente(tmp_path):
    """Una routine inventada no falla al generar: falla al compilar."""
    resultado = _correr(
        tmp_path,
        ESQL_BUENO.replace("isNotEmpty(", "isNotEmpty(").replace(
            "\tDECLARE refItem REFERENCE TO refDfdlOut.LISTADOCOBRANZARSP;",
            "\tCALL prepararMensajeAuditoriaV2QueNoExiste();\n\n"
            "\tDECLARE refItem REFERENCE TO refDfdlOut.LISTADOCOBRANZARSP;",
        ),
    )
    salida = resultado.stdout + resultado.stderr
    assert "routine no definida" in salida
    assert resultado.returncode == 2


@pytest.mark.parametrize(
    "residuo",
    ["payexe", "prorev", "RE0058", "termdeposit", "UpdatePaymentExecution"],
)
def test_detecta_residuos_de_la_plantilla(tmp_path, residuo):
    (tmp_path / "ace" / "esb").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ace" / "esb" / "A.yaml").write_text(f"url: {residuo}\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("plantillas-AI", encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, str(_GATE), str(tmp_path)],
        capture_output=True,
        text=True,
    )
    salida = resultado.stdout + resultado.stderr
    assert "residuo de plantilla" in salida
    assert resultado.returncode == 2


def test_el_readme_puede_citar_la_plantilla(tmp_path):
    """
    El README DEBE citar la plantilla de origen: ahi el nombre es evidencia de
    trazabilidad, no un residuo. Por eso los .md quedan fuera del barrido.
    """
    (tmp_path / "ace" / "esb").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ace" / "esb" / "A.esql").write_text(ESQL_BUENO, encoding="utf-8")
    (tmp_path / "README.md").write_text(
        "# svc\nplantillas-AI rama IBS app213-payexe-prorev-core-upda-s-ops-ace\n",
        encoding="utf-8",
    )
    resultado = subprocess.run(
        [sys.executable, str(_GATE), str(tmp_path)], capture_output=True, text=True
    )
    salida = resultado.stdout + resultado.stderr
    assert "residuo de plantilla" not in salida


def test_avisa_si_falta_la_plantilla_en_el_readme(tmp_path):
    (tmp_path / "ace" / "esb").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ace" / "esb" / "A.esql").write_text(ESQL_BUENO, encoding="utf-8")
    (tmp_path / "README.md").write_text("# svc\nsin fuente\n", encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, str(_GATE), str(tmp_path)], capture_output=True, text=True
    )
    salida = resultado.stdout + resultado.stderr
    assert "no declara la plantilla de origen" in salida


def test_no_se_da_por_valido_un_gate_sin_referencias(tmp_path):
    """
    Un gate al que no se le pasa nada verificable debe decirlo, no pasar en
    silencio: un gate que se desactiva solo es peor que no tener gate.
    """
    (tmp_path / "ace" / "esb").mkdir(parents=True, exist_ok=True)
    (tmp_path / "ace" / "esb" / "A.esql").write_text(ESQL_BUENO, encoding="utf-8")
    (tmp_path / "README.md").write_text("plantillas-AI", encoding="utf-8")
    resultado = subprocess.run(
        [sys.executable, str(_GATE), str(tmp_path)], capture_output=True, text=True
    )
    salida = resultado.stdout + resultado.stderr
    assert "gate no pudo validar nada" in salida
    assert resultado.returncode == 2
