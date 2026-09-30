"""
Pruebas de la capa contractual.

Cada regla del plan tiene aqui su prueba de romperla. Una regla sin prueba es
una regla que nadie sabe si sigue viva: en seis meses el validador se desactiva
por un refactor y nadie lo nota hasta que un contrato roto llega a generacion.

    python -m pytest tests/ -q
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

_RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_RAIZ))

from scripts.contrato import (  # noqa: E402
    ContractError,
    apply_profile,
    cache_key,
    extract_minimal,
    hash_file,
    load_contract,
    load_profile,
    merge_manual,
    resolve_template,
    to_legacy_parameters,
    to_openapi,
    validate_contract,
)

_EJEMPLO = _RAIZ / "proyectos" / "banbif" / "ejemplos" / "cobranza-libre-pj.contrato.yaml"
_PERFIL = _RAIZ / "proyectos" / "banbif" / "perfil.yaml"


@pytest.fixture
def contrato() -> dict:
    return load_contract(_EJEMPLO)


@pytest.fixture
def perfil() -> dict:
    return load_profile(_PERFIL)


# ── el ejemplo mismo ─────────────────────────────────────────────────────────

def test_ejemplo_referencia_es_valido(contrato):
    assert validate_contract(contrato, check_files=False) == []


def test_ejemplar_proyecta_parametros_que_la_skill_ya_usa(contrato):
    parametros = to_legacy_parameters(contrato)
    assert parametros["servicio"] == "CPS_ProColLis_Corp_Retr_B"
    assert parametros["nombre_funcional"] == "Listado de Cobranza Libre"
    assert parametros["operacion_get"] == "RetrieveCPSDProductCollectionListCorporate"
    assert parametros["codigo_catalogo"] == "CSH012"
    assert parametros["ruta_servicio"] == "v1.0/onprem/b/productcollectionlist/retrieve"
    assert parametros["grupo_ldap"] == "CPS_PROCOLLIS_CORP_RETR"


def test_openapi_publica_la_via_base_completa(contrato):
    """La via base completa va en servers[0].url, no en el path de la operacion."""
    openapi = to_openapi(contrato)
    assert len(openapi["servers"]) == 1
    assert openapi["servers"][0]["url"] == "/v1.0/onprem/b/productcollectionlist/retrieve"
def test_raiz_proyecto_no_es_el_nombre_del_artefacto(contrato):
    """
    `nombre_servicio` es el nombre del artefacto ACE. Usarlo de carpeta produce
    un arbol que no se parece a ningun repositorio de la organizacion.
    """
    parametros = to_legacy_parameters(contrato)
    assert parametros["raiz_proyecto"] != parametros["servicio"]
    assert parametros["raiz_proyecto"] == "app213-payexe-prorev-core-upda-s-ops-ace"


def test_raiz_proyecto_preferida_al_nombre_del_contrato(contrato):
    """`componente.nombre_repo` del ETI manda sobre el subdirectorio plantilla."""
    contrato["componente"]["nombre_repo"] = "app213-procollis-corp-retr-b-ops-ace"
    assert to_legacy_parameters(contrato)["raiz_proyecto"] == "app213-procollis-corp-retr-b-ops-ace"


def test_via_base_no_duplica_el_action_term(contrato):
    """
    El action term puede escribirse en `base_path` o en `operaciones[].path`,
    nunca en los dos. En los dos, la via publicada sale duplicada.
    """
    contrato["exposicion"]["base_path"] = "/v1.0/onprem/b/productcollectionlist/retrieve"
    assert to_openapi(contrato)["servers"][0]["url"] == \
        "/v1.0/onprem/b/productcollectionlist/retrieve"
    assert to_legacy_parameters(contrato)["ruta_servicio"] == \
        "v1.0/onprem/b/productcollectionlist/retrieve"



def test_openapi_omite_detalles_de_backend(contrato):
    """OpenAPI es el contrato HTTP. Un PCML dentro es senal de que se mezclo."""
    texto = yaml.safe_dump(to_openapi(contrato))
    for interno in ("DL1071RI", "IN2100RI", "LISTADOCOBRANZARSP", "ICODIBS", "PCML"):
        assert interno not in texto, f"OpenAPI no debe exponer `{interno}`"


def test_openapi_declara_el_array_con_max_items(contrato):
    esquema = to_openapi(contrato)["components"]["schemas"]["Response"]
    lista = esquema["properties"]["CollectionsFreeList"]
    assert lista["maxItems"] == 40
    assert "PartyIdentification" in lista["items"]["properties"]


def test_openapi_no_declara_campos_no_expuestos(contrato):
    """NumeroRegistrosPorPagina es configurable: no es parte del contrato REST."""
    esquemas = to_openapi(contrato)["components"]["schemas"]
    assert "NumeroRegistrosPorPagina" not in esquemas["Request"]["properties"]


# ── bloqueantes del schema ───────────────────────────────────────────────────

def test_plantilla_sin_commit_es_valida_si_tiene_rama(contrato):
    contrato["plantilla"].pop("commit")
    validate_contract(contrato, check_files=False)


def test_plantilla_sin_rama_bloquea(contrato):
    contrato["plantilla"].pop("rama")
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


def test_plantilla_con_commit_placeholder_bloquea(contrato):
    contrato["plantilla"]["commit"] = "<hash-fijado>"
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


def test_tipo_de_componente_desconocido_bloquea(contrato):
    contrato["componente"]["tipo"] = "microservicio"
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


def test_metodo_http_invalido_bloquea(contrato):
    contrato["exposicion"]["operaciones"][0]["metodo"] = "FETCH"
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


def test_operaciones_requieren_ruta(contrato):
    contrato["exposicion"]["operaciones"][0].pop("path")
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


# ── bloqueantes condicionales ────────────────────────────────────────────────

def test_orquestador_sin_orquestacion_bloquea(contrato):
    contrato["componente"]["tipo"] = "orquestador"
    with pytest.raises(ContractError, match="orquestacion"):
        validate_contract(contrato, check_files=False)


def test_orquestador_con_orquestacion_pasa(contrato):
    contrato["componente"]["tipo"] = "orquestador"
    contrato["orquestacion"] = {
        "componentes": [{"id": "c1", "nombre": "HijoA", "orden": 1}],
        "timeout_total_s": 25,
    }
    assert validate_contract(contrato, check_files=False) == []


def test_backend_as400_sin_copybook_bloquea(contrato):
    contrato["backend"].pop("copybook")
    with pytest.raises(ContractError, match="copybook"):
        validate_contract(contrato, check_files=False)


# ── copybook opcional (SCI y ETI son los unicos obligatorios) ────────────────

def test_servicio_rest_sin_copybook_es_valido(contrato):
    """Un servicio que no consume trama COBOL no declara copybook y es valido."""
    contrato["backend"] = {"tipo": "REST", "timeout_s": 16}
    contrato.pop("dfdl", None)
    contrato.pop("artefactos_backend", None)
    assert validate_contract(contrato, check_files=False) == []


def test_orquestador_sin_copybook_es_valido(contrato):
    """El caso real de 158: orquesta servicios REST y no tiene trama propia."""
    contrato["componente"]["tipo"] = "orquestador"
    contrato["componente"]["dominio"] = "ORQ"
    contrato["orquestacion"] = {"componentes": [], "timeout_total_s": 25}
    contrato.pop("backend", None)
    contrato.pop("dfdl", None)
    contrato.pop("artefactos_backend", None)
    assert validate_contract(contrato, check_files=False) == []


def test_openapi_de_servicio_sin_copybook_no_trae_dfdl(contrato):
    """Sin copybook el OpenAPI se genera igual: la capa DFDL no lo afecta."""
    contrato["backend"] = {"tipo": "REST"}
    contrato.pop("dfdl", None)
    doc = to_openapi(contrato)
    assert doc["openapi"].startswith("3.")
    assert "Request" in doc["components"]["schemas"]


def test_as400_sin_xsd_declarado_bloquea(contrato):
    contrato["backend"]["copybook"].pop("xsd_generado")
    contrato.pop("dfdl")
    with pytest.raises(ContractError, match="XSD"):
        validate_contract(contrato, check_files=False)


def test_campo_expuesto_sin_mapeo_bloquea(contrato):
    contrato["request"]["body"]["campos"][1].pop("backend")
    with pytest.raises(ContractError, match="sin mapeo backend"):
        validate_contract(contrato, check_files=False)


def test_campo_no_expuesto_no_exige_mapeo(contrato):
    no_expuesto = contrato["request"]["body"]["campos"][3]
    assert no_expuesto["expuesto"] is False
    no_expuesto.pop("backend")
    assert validate_contract(contrato, check_files=False) == []


def test_dos_operaciones_con_el_mismo_metodo_bloquea(contrato):
    segunda = copy.deepcopy(contrato["exposicion"]["operaciones"][0])
    segunda["id"] = "otra"
    segunda["path"] = "/otro"
    contrato["exposicion"]["operaciones"].append(segunda)
    with pytest.raises(ContractError, match="duplicadas"):
        validate_contract(contrato, check_files=False)


# ── reglas de artefactos backend ─────────────────────────────────────────────

def test_contrato_declara_que_artefacto_consume_ctrllengthcpy(contrato):
    """La confusion .yaml vs .xsd rompe en runtime, no en el Toolkit."""
    control = contrato["artefactos_backend"]["control_length"]
    assert control["ruta"].endswith(".yaml")
    assert contrato["configuracion"]["wdo"]["filename_pattern"] == "DL1071RI.yaml"


def test_perfil_advierte_que_el_yaml_no_se_sustituye(perfil):
    nota = perfil["artefactos_backend"]["control_length"]["nota"]
    assert "NO se sustituye por el .xsd" in nota


# ── perfiles y plantillas ────────────────────────────────────────────────────

def test_perfil_banbif_tiene_las_tres_plantillas(perfil):
    assert {"ace-bus-rest", "ace-orquestador", "ach"} <= set(perfil["plantillas"])


def test_perfil_protege_las_librerias_del_framework(perfil):
    assert "LIB_CORE_CONTROL" in perfil["ace"]["artefactos_protegidos"]


def test_plantilla_se_toma_del_contrato_si_esta_completa(contrato, perfil):
    assert resolve_template(contrato, perfil)["commit"] == contrato["plantilla"]["commit"]


def test_plantilla_se_resuelve_desde_el_perfil_si_falta(contrato, perfil):
    contrato["plantilla"] = {}
    resuelta = resolve_template(contrato, perfil)
    assert resuelta["tipo"] == "ace-bus-rest"
    assert resuelta["subdirectorio"].endswith("app213-payexe-prorev-core-upda-s-ops-ace")


def test_perfil_sin_rama_para_generacion_bloquea(contrato, perfil):
    """Sin rama no se puede resolver la plantilla."""
    contrato["plantilla"] = {}
    perfil["plantillas"]["ace-bus-rest"].pop("rama")
    with pytest.raises(ContractError):
        resolve_template(contrato, perfil)


def test_plantilla_orchestrator_se_elige_por_tipo(contrato, perfil):
    contrato["plantilla"] = {}
    contrato["componente"]["tipo"] = "orquestador"
    contrato["orquestacion"] = {"componentes": [], "timeout_total_s": 25}
    assert resolve_template(contrato, perfil)["tipo"] == "ace-orquestador"


def test_plantilla_ach_se_elige_por_backend(contrato, perfil):
    contrato["plantilla"] = {}
    contrato["backend"]["tipo"] = "ACH"
    assert resolve_template(contrato, perfil)["tipo"] == "ach"


def test_apply_profile_no_pisa_lo_que_el_contrato_ya_dijo(contrato, perfil):
    contrato["plantilla"]["commit"] = "a" * 40
    resultado = apply_profile(contrato, perfil)
    assert resultado["plantilla"]["commit"] == "a" * 40


# ── extraccion SCI/ETI ───────────────────────────────────────────────────────

SCI = """# 147_BUS_listado_cobranza_libre

| Nombre funcional | Listado de Cobranza Libre |
| Nombre técnico | `BUS_CPS_ProductCollectionList_Corporate_Retrieve` |
| Nombre del servicio | `CPS_ProColLis_Corp_Retr_B` |
| Código de servicio | `CSH012` |
"""

ETI = """
## 2. Información del componente

| Concepto | Valor |
| --- | --- |
| Relative Service Name | `retrieve-collections-free-pj` |
| Nombre funcional | Listado de Cobranza Libre |
| Nombre técnico | `BUS_B_CPSD_ProductCollectionList_Corporate_Retrieve` |
| Etiqueta técnica | `BUS_CPS_ProColLis_Corp_Retr_B` |
| Servicio ACE | `CPS_ProColLis_Corp_Retr_B` |
| Código de servicio | `CSH012` |
| Linea de producto | Cash Management |

## 4. Endpoint

| DEV | `POST https://retrieve-collections-free-pj.apps.example/v1.0/onprem/b/productcollectionlist/retrieve` |
"""


def test_extraccion_minima_solo_toma_lo_demostrable():
    contrato = extract_minimal(SCI, ETI)
    assert contrato["componente"]["nombre_servicio"] == "CPS_ProColLis_Corp_Retr_B"
    assert contrato["componente"]["nombre_tecnico"] == "BUS_B_CPSD_ProductCollectionList_Corporate_Retrieve"
    assert contrato["componente"]["nombre_funcional"] == "Listado de Cobranza Libre"
    assert contrato["componente"]["requerimiento"] == "147"
    assert contrato["configuracion"]["codigo_servicio"] == "CSH012"
    assert contrato["exposicion"]["base_path"] == "/v1.0/onprem/b/productcollectionlist"
    assert contrato["exposicion"]["operaciones"][0]["path"] == "/retrieve"


def test_extraccion_no_deja_dudas_en_un_eti_limpio():
    contrato = extract_minimal(SCI, ETI)
    assert contrato["decisiones"]["por_verificar"] == []


# ── regresiones de extraccion ────────────────────────────────────────────────
# Estas tres existen porque fallaron con documentos reales. El SCI volcado a
# Markdown trae una tabla por hoja y varias se llaman igual; buscar sobre el
# texto plano cogía el valor de otra hoja.

SCI_VOLCADO = """# 147_BUS_listado_cobranza_libre

## Hoja: Orquestador

| Rol | Tipo de Componente | Funcionalidad |
| --- | --- | --- |
| Orquestador | <Completar> | Flujo y reglas de Orquestación |

## Hoja: Información

| Concepto | Valor |
| --- | --- |
| Capa | B |
| Nombre funcional | Listado de Cobranza Libre |
| Nombre técnico | `BUS_B_CPSD_ProductCollectionList_Corporate_Retrieve` |
| Servicio ACE | `CPS_ProColLis_Corp_Retr_B` |
"""

ETI_VOLCADO = """
## 2. Información del componente

| Concepto | Valor |
| --- | --- |
| Capa | B |
| Nombre funcional | Listado de Cobranza Libre |
| Nombre técnico | `BUS_B_CPSD_ProductCollectionList_Corporate_Retrieve` |
| Etiqueta técnica | `BUS_CPS_ProColLis_Corp_Retr_B` |
| Servicio ACE | `CPS_ProColLis_Corp_Retr_B` |
| Código de servicio | `CSH012` |

## 4. Endpoint

| DEV | `POST https://x.example/v1.0/onprem/b/productcollectionlist/retrieve` |
"""


def test_extraccion_no_coge_el_valor_de_otra_hoja():
    """`Flujo y reglas de Orquestación` y `Capa` salían como nombre de servicio."""
    contrato = extract_minimal(SCI_VOLCADO, ETI_VOLCADO)
    assert contrato["componente"]["nombre_servicio"] == "CPS_ProColLis_Corp_Retr_B"
    assert contrato["componente"]["nombre_tecnico"] == "BUS_B_CPSD_ProductCollectionList_Corporate_Retrieve"
    assert "Capa" not in contrato["componente"]["nombre_servicio"]


def test_extraccion_rechaza_encabezado_de_tabla_como_nombre():
    contrato = extract_minimal("# 147_X", "| Servicio ACE | Capa |")
    assert contrato["componente"]["nombre_servicio"] == ""
    assert "componente.nombre_servicio" in contrato["decisiones"]["por_verificar"]


def test_etiqueta_ambigua_no_se_elige():
    """Dos valores distintos para la misma etiqueta: se pregunta, no se adivina."""
    eti = """
## 2. Información del componente

| Concepto | Valor |
| --- | --- |
| Nombre funcional | Listado A |
| Nombre funcional | Listado B |
"""
    contrato = extract_minimal("# 147_X", eti)
    assert contrato["componente"]["nombre_funcional"] == ""
    assert "componente.nombre_funcional" in contrato["decisiones"]["por_verificar"]


def test_etiqueta_repetida_con_el_mismo_valor_no_es_ambigua():
    eti = """
## 2. Información del componente

| Concepto | Valor |
| --- | --- |
| Nombre funcional | Listado de Cobranza Libre |
| Nombre funcional | Listado de Cobranza Libre |
"""
    contrato = extract_minimal("# 147_X", eti)
    assert contrato["componente"]["nombre_funcional"] == "Listado de Cobranza Libre"


def test_eti_sin_endpoint_marca_la_ruta_para_verificar():
    contrato = extract_minimal(SCI, "## 2. Información del componente\n")
    assert "exposicion.base_path" in contrato["decisiones"]["por_verificar"]


def test_extraccion_no_inventa_mapeos():
    """La extraccion no toca request/response: se documentan, no se adivinan."""
    contrato = extract_minimal(SCI, ETI)
    assert "request" not in contrato
    assert "response" not in contrato


def test_contrato_incompleto_lo_dice_el_validador():
    contrato = extract_minimal(SCI, ETI)
    contrato["plantilla"] = {}
    with pytest.raises(ContractError):
        validate_contract(contrato, check_files=False)


def test_modo_actualizar_conserva_decisiones_manuales():
    anterior = {
        "contrato": "1.0",
        "plantilla": {"tipo": "ace-bus-rest", "url": "u", "rama": "IBS",
                      "subdirectorio": "s", "commit": "b" * 40},
        "decisiones": {"manuales": ["mapeo_tarjeta"], "justificaciones": []},
    }
    nuevo = {"contrato": "1.0", "componente": {"nombre_servicio": "X"}}
    resultado = merge_manual(anterior, nuevo)
    assert resultado["plantilla"]["commit"] == "b" * 40
    assert resultado["decisiones"]["manuales"] == ["mapeo_tarjeta"]
    assert resultado["decisiones"]["pendiente_revision"] == ["mapeo_tarjeta"]


# ── determinismo y cache ─────────────────────────────────────────────────────

def test_proyeccion_es_determinista(contrato):
    assert to_legacy_parameters(contrato) == to_legacy_parameters(contrato)
    assert to_openapi(contrato) == to_openapi(contrato)


def test_cache_key_cambia_con_el_commit():
    a = cache_key("u", "IBS", "s", "a" * 40)
    b = cache_key("u", "IBS", "s", "b" * 40)
    assert a != b


def test_cache_key_es_estable():
    assert cache_key("u", "IBS", "s", "a" * 40) == cache_key("u", "IBS", "s", "a" * 40)


def test_hash_de_archivo_detecta_cambio(tmp_path):
    archivo = tmp_path / "DL1071RI.cpy"
    archivo.write_text("01 DL1071RI.", encoding="utf-8")
    antes = hash_file(archivo)
    archivo.write_text("01 DL1071RI.  ", encoding="utf-8")
    assert hash_file(archivo) != antes


# ── iteracion de campos ──────────────────────────────────────────────────────

def test_iter_campos_recorre_items(contrato):
    from scripts.contrato import iter_campos
    nombres = {c["nombre"] for c in iter_campos(contrato)}
    assert "CustomerReference" in nombres
    assert "PartyIdentification" in nombres   # dentro del array
    assert "Currency" in nombres




def test_openapi_expone_paths_de_la_plantilla(contrato):
    """La plantilla publica la operacion en `/` y el HealthCheck en `/health`."""
    paths = to_openapi(contrato)["paths"]
    assert set(paths) == {"/", "/health"}
    assert "post" in paths["/"]
    assert paths["/health"]["get"]["operationId"] == "HealthCheck"


def test_openapi_no_declara_security_schemes(contrato):
    """
    `type: mutualTLS` es OpenAPI 3.1. En 3.0.x el importador REST de ACE 12
    lanza NullPointerException en vez de un error legible.
    """
    openapi = to_openapi(contrato)
    assert "securitySchemes" not in (openapi.get("components") or {})
    assert "security" not in openapi


def test_openapi_no_declara_cabeceras_reservadas(contrato):
    """ACE deriva Content-Type/Accept/Authorization del body; declararlas rompe."""
    parametros = (to_openapi(contrato).get("components") or {}).get("parameters") or {}
    declarados = {p["name"].lower() for p in parametros.values()}
    assert not declarados & {"content-type", "accept", "authorization"}


def test_raiz_proyecto_no_es_el_nombre_del_artefacto(contrato):
    """
    `nombre_servicio` es el nombre del artefacto ACE. Usarlo de carpeta produce
    un arbol que no se parece a ningun repositorio de la organizacion.
    """
    parametros = to_legacy_parameters(contrato)
    assert parametros["raiz_proyecto"] != parametros["servicio"]
    assert parametros["raiz_proyecto"] == "app213-payexe-prorev-core-upda-s-ops-ace"


def test_raiz_proyecto_preferida_al_nombre_del_contrato(contrato):
    """`componente.nombre_repo` del ETI manda sobre el subdirectorio plantilla."""
    contrato["componente"]["nombre_repo"] = "app213-procollis-corp-retr-b-ops-ace"
    assert to_legacy_parameters(contrato)["raiz_proyecto"] == "app213-procollis-corp-retr-b-ops-ace"


def test_via_base_no_duplica_el_action_term(contrato):
    """
    El action term puede escribirse en `base_path` o en `operaciones[].path`,
    nunca en los dos. En los dos, la via publicada sale duplicada.
    """
    contrato["exposicion"]["base_path"] = "/v1.0/onprem/b/productcollectionlist/retrieve"
    assert to_openapi(contrato)["servers"][0]["url"] == "/v1.0/onprem/b/productcollectionlist/retrieve"
    assert to_legacy_parameters(contrato)["ruta_servicio"] == "v1.0/onprem/b/productcollectionlist/retrieve"
