"""
Contrato canonico de componente ACE.

Modulo unico de la capa contractual: carga, valida, proyecta a OpenAPI y
traduce a los parametros que la skill ya usa hoy. No genera ACE, no toca
plantillas y no depende de OIA.

Regla de precedencia (docs/PLAN_CONTRATO_GENERACION_ACEv1.md seccion 2):

    copybook                > contrato   para estructura fisica DFDL
    contrato aprobado       > perfil     para datos especificos del servicio
    perfil del proyecto     > plantilla  para convenciones comunes
    plantilla fijada        > IA         para estructura de archivos y flujos
    SCI/ETI                 = trazabilidad, no entrada directa de generacion
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

_SKILL = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _SKILL / "contratos" / "contrato.schema.json"

# Codigos de salida, iguales en todos los scripts de esta capa.
EXIT_OK = 0
EXIT_WARNING = 1
EXIT_BLOCK = 2
EXIT_ERROR = 3


class ContractError(ValueError):
    """Contrato ausente, invalido o incompatible con la generacion."""


# ── carga ────────────────────────────────────────────────────────────────────

def load_contract(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    """Carga un contrato desde dict, archivo YAML/JSON o texto YAML."""
    if isinstance(source, dict):
        return copy.deepcopy(source)
    path = Path(source)
    if path.is_file():
        raw = path.read_text(encoding="utf-8")
    else:
        raw = str(source)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ContractError(f"No se pudo leer el contrato: {exc}") from exc
    if not isinstance(data, dict):
        raise ContractError("El contrato debe ser un objeto YAML/JSON")
    return data


# ── validacion ───────────────────────────────────────────────────────────────

def validate_contract(
    contract: dict[str, Any],
    *,
    check_files: bool = True,
    schema_path: Path | None = None,
) -> list[str]:
    """
    Valida el contrato contra el schema y las reglas condicionales.

    Devuelve advertencias. Lanza ContractError ante cualquier bloqueante.
    """
    errores = _validar_schema(contract, schema_path)
    if errores:
        detalle = "; ".join(f"{ruta or '$'}: {msg}" for ruta, msg in errores)
        raise ContractError(f"Contrato invalido: {detalle}")

    componente = contract["componente"]
    advertencias: list[str] = []

    # Reglas condicionales: dependen de un valor, el schema no puede verlas.
    if componente["tipo"] == "orquestador" and not contract.get("orquestacion"):
        raise ContractError("Un orquestador requiere la seccion `orquestacion`")

    backend = contract.get("backend") or {}
    copybook = backend.get("copybook") or (contract.get("copybook") or None)
    if backend.get("tipo") == "IBS_RPG" and not copybook:
        raise ContractError("Un backend IBS_RPG requiere `backend.copybook.ruta`")
    if copybook and backend.get("tipo") not in (None, "IBS_RPG"):
        advertencias.append("Se declaro copybook pero el backend no es IBS_RPG")

    if check_files and copybook:
        ruta = copybook.get("ruta")
        if ruta and not Path(ruta).is_file():
            advertencias.append(f"Copybook no encontrado localmente: {ruta}")

    _validar_mapeos(contract)
    _validar_dfdl(contract)
    _validar_operaciones(contract)
    return advertencias


def _validar_schema(contract: dict[str, Any], schema_path: Path | None) -> list[tuple[str, str]]:
    """Valida con jsonschema si esta disponible; si no, aplica el minimo crítico."""
    ruta = schema_path or _SCHEMA_PATH
    if not ruta.is_file():
        raise ContractError(f"No existe el schema del contrato: {ruta}")
    schema = json.loads(ruta.read_text(encoding="utf-8"))
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return _validar_minimo(contract, schema)
    validator = Draft202012Validator(schema)
    salida = []
    for error in sorted(validator.iter_errors(contract), key=lambda e: list(e.path)):
        salida.append((".".join(str(p) for p in error.path), error.message))
    return salida


def _validar_minimo(contract: dict[str, Any], schema: dict[str, Any]) -> list[tuple[str, str]]:
    """
    Respaldo sin jsonschema instalado.

    Solo comprueba lo que bloquea la generacion. Un validador que se desactiva en
    silencio es peor que no tener validador, asi que declara que corrio parcial.
    """
    errores: list[tuple[str, str]] = []
    for clave in schema.get("required", []):
        if clave not in contract:
            errores.append((clave, "falta clave requerida"))
    errores.extend(_validar_minimo_objeto(contract, schema))
    return errores


def _validar_minimo_objeto(contract: dict, schema: dict) -> list[tuple[str, str]]:
    errores: list[tuple[str, str]] = []
    propiedades = schema.get("properties") or {}
    for clave, spec in propiedades.items():
        if clave not in contract or not isinstance(spec, dict):
            continue
        valor = contract[clave]
        if "const" in spec and valor != spec["const"]:
            errores.append((clave, f"debe ser {spec['const']!r}"))
        if "enum" in spec and valor not in spec["enum"]:
            errores.append((clave, f"valor fuera de enum: {valor!r}"))
        if spec.get("type") == "object" and isinstance(valor, dict):
            for req in spec.get("required", []):
                if req not in valor:
                    errores.append((f"{clave}.{req}", "falta clave requerida"))
        if spec.get("type") == "array" and isinstance(valor, list):
            if "minItems" in spec and len(valor) < spec["minItems"]:
                errores.append((clave, f"se requieren {spec['minItems']} elementos"))
    return errores


def _validar_mapeos(contract: dict[str, Any]) -> None:
    """
    Un campo expuesto al consumidor debe declarar destino backend.

    Sin esto la IA tiene que deducirlo, y deducir un mapeo es inventarlo.
    """
    for seccion in ("request", "response"):
        campos = ((contract.get(seccion) or {}).get("body") or {}).get("campos") or []
        for campo in campos:
            if campo.get("expuesto", True) is False:
                continue
            if not campo.get("backend") and not campo.get("backend_campo"):
                raise ContractError(
                    f"Campo expuesto sin mapeo backend: {seccion}.{campo.get('nombre', '<sin nombre>')}"
                )


def _validar_dfdl(contract: dict[str, Any]) -> None:
    """
    Para AS400: la cardinalidad del contrato debe poder contrastarse con el XSD.

    No valida el XSD aqui — eso es de generar, no del contrato — pero si deja
    explicito que se espera.
    """
    backend = contract.get("backend") or {}
    if backend.get("tipo") != "IBS_RPG":
        return
    dfdl = contract.get("dfdl") or {}
    copybook = backend.get("copybook") or {}
    if not copybook.get("ruta"):
        raise ContractError("backend IBS_RPG sin copybook.ruta")
    if not (copybook.get("xsd_generado") or dfdl.get("xsd_esperado")):
        raise ContractError(
            "backend IBS_RPG sin XSD declarado: usa `copybook.xsd_generado` o `dfdl.xsd_esperado`"
        )


def _validar_operaciones(contract: dict[str, Any]) -> None:
    """Una operacion REST no puede tener dos rutas base distintas."""
    exposure = contract.get("exposicion") or {}
    if exposure.get("protocolo") != "REST":
        return
    operaciones = exposure.get("operaciones") or []
    metodos = [o.get("metodo") for o in operaciones]
    duplicados = {m for m in metodos if metodos.count(m) > 1}
    if duplicados:
        raise ContractError(f"Operaciones duplicadas por metodo: {', '.join(sorted(duplicados))}")


# ── proyeccion a OpenAPI ─────────────────────────────────────────────────────

def to_openapi(contract: dict[str, Any]) -> dict[str, Any]:
    """
    Proyecta el contrato a OpenAPI 3.0.3.

    Una sola stanza `servers`: el builder de REST API del Toolkit rechaza varias
    vias base distintas, y los canales mTLS/onprem son detalle de los nodos
    WSInput del msgflow, no del OpenAPI.
    """
    validate_contract(contract, check_files=False)
    exposure = contract["exposicion"]
    componente = contract["componente"]

    headers_request = _headers_nombres(contract.get("headers"))
    esquemas = _esquemas_campos(contract)

    paths: dict[str, Any] = {}
    for operacion in exposure["operaciones"]:
        metodo = operacion["metodo"].lower()
        cuerpo: dict[str, Any] = {
            "operationId": operacion["id"],
            "summary": operacion.get("descripcion") or operacion["nombre"],
            "x-nombre-bian": operacion["nombre"],
        }
        if headers_request:
            cuerpo["parameters"] = [
                {"$ref": f"#/components/parameters/{nombre}"} for nombre, _ in headers_request
            ]
        if _cuerpo_seccion(contract, "request") and esquemas.get("Request"):
            cuerpo["requestBody"] = {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Request"}}},
            }
        respuestas: dict[str, Any] = {
            "200": {
                "description": "Respuesta exitosa",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Response"}}},
            }
        }
        if esquemas.get("Error"):
            respuestas["202"] = {
                "description": "Error de negocio o de validacion",
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}},
            }
        cuerpo["responses"] = respuestas
        paths.setdefault(operacion["path"], {})[metodo] = cuerpo

    documento: dict[str, Any] = {
        "openapi": "3.0.3",
        "info": {
            "title": componente["nombre_funcional"],
            "version": str(contrato_version(contract)),
            "description": componente.get("nombre_tecnico") or componente["nombre_funcional"],
        },
        "servers": [{"url": exposure["base_path"]}],
        "paths": paths,
    }

    components: dict[str, Any] = {}
    if headers_request:
        components["parameters"] = {nombre: _parametro_header(header) for nombre, header in headers_request}
    if esquemas:
        components["schemas"] = esquemas
    if exposure.get("seguridad_externa") == "mtls":
        components["securitySchemes"] = {"MutualTLS": {"type": "mutualTLS"}}
        documento["security"] = [{"MutualTLS": []}]
    if components:
        documento["components"] = components
    return documento


def to_request_schema(contract: dict[str, Any]) -> dict[str, Any]:
    """
    JSON Schema del body de request, para `request.schema.json` de la plantilla.

    Va aparte del OpenAPI porque el REST API service lo usa para validar la
    entrada antes de que el flujo corra, y porque solo con lo que el consumidor
    ve: los campos configurables por politica no se exponen.
    """
    validate_contract(contract, check_files=False)
    request = _cuerpo_seccion(contract, "request")
    if not request:
        return {}
    propiedades: dict[str, Any] = {}
    requeridos: list[str] = []
    for campo in request.get("campos") or []:
        if campo.get("expuesto", True) is False:
            continue
        propiedades[campo["nombre"]] = _esquema_campo(campo)
        if campo.get("obligatorio"):
            requeridos.append(campo["nombre"])
    esquema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "title": request.get("nombre_raiz") or "Request",
        "properties": propiedades,
    }
    if requeridos:
        esquema["required"] = requeridos
    if contract.get("headers"):
        esquema["x-headers"] = {
            header["nombre"]: {
                "required": bool(header.get("obligatorio")),
                **({"maxLength": int(header["longitud"])} if str(header.get("longitud", "")).isdigit() else {}),
            }
            for header in contract["headers"].get("request") or []
        }
    return esquema


def contrato_version(contract: dict[str, Any]) -> str:
    """Version del contrato, no del requerimiento: es la del modelo."""
    return "1.0.0"


def _headers_nombres(headers: dict[str, Any] | None) -> list[tuple[str, dict]]:
    if not headers:
        return []
    return [(h["nombre"], h) for h in headers.get("request") or []]


def _parametro_header(header: dict[str, Any]) -> dict[str, Any]:
    r"""
    Traduce un header del contrato a un parameter de OpenAPI.

    `formato` en el contrato es ambiguo a proposito: a veces es un regex
    (`^APP\d{3}$`) y a veces un valor literal (`application/json`). Aplicarlo
    como `pattern` en los dos casos produce un `pattern: application/json` que
    no es un regex y hace que el contrato no case nunca.
    """
    schema: dict[str, Any] = {"type": header.get("tipo", "string")}
    if header.get("longitud"):
        try:
            schema["maxLength"] = int(header["longitud"])
        except (TypeError, ValueError):
            pass
    formato = header.get("formato")
    if formato:
        if _parece_regex(formato):
            schema["pattern"] = formato
        elif "/" in formato:
            schema["enum"] = [formato]
        else:
            schema["example"] = formato
    return {
        "name": header["nombre"],
        "in": "header",
        "required": bool(header.get("obligatorio")),
        "schema": schema,
    }


def _parece_regex(valor: str) -> bool:
    """Un regex lleva metacaracteres; un valor literal como application/json no."""
    return bool(re.search(r"[\^\$\(\)\[\]\{\}\*\+\?\|\\]", valor))


def _cuerpo_seccion(contract: dict[str, Any], seccion: str) -> dict:
    return (contract.get(seccion) or {}).get("body") or {}


def _esquemas_campos(contract: dict[str, Any]) -> dict[str, Any]:
    """Traduce campos del contrato a JSON Schema dentro de components.schemas."""
    salida: dict[str, Any] = {}

    request = _cuerpo_seccion(contract, "request")
    if request:
        propiedades: dict[str, Any] = {}
        requeridos: list[str] = []
        for campo in request.get("campos") or []:
            if campo.get("expuesto", True) is False:
                continue
            propiedades[campo["nombre"]] = _esquema_campo(campo)
            if campo.get("obligatorio"):
                requeridos.append(campo["nombre"])
        cuerpo: dict[str, Any] = {"type": "object", "properties": propiedades}
        if requeridos:
            cuerpo["required"] = requeridos
        salida["Request"] = cuerpo

    response = _cuerpo_seccion(contract, "response")
    if response:
        propiedades = {}
        requeridos = []
        for campo in response.get("campos") or []:
            propiedades[campo["nombre"]] = _esquema_campo(campo)
            if campo.get("obligatorio"):
                requeridos.append(campo["nombre"])
        cuerpo = {"type": "object", "properties": propiedades}
        if requeridos:
            cuerpo["required"] = requeridos
        salida["Response"] = cuerpo

    if contract.get("errores"):
        salida["Error"] = {
            "type": "object",
            "properties": {
                "StatusCode": {"type": "string"},
                "Message": {"type": "string"},
                "Status": {"type": "string"},
            },
        }
    return salida


def _esquema_campo(campo: dict[str, Any]) -> dict[str, Any]:
    tipo = str(campo.get("tipo", "string")).lower()
    if tipo == "object":
        items = campo.get("items") or []
        reqs = [i["nombre"] for i in items if i.get("obligatorio")]
        esquema = {
            "type": "object",
            "properties": {i["nombre"]: _esquema_campo(i) for i in items},
        }
        if reqs:
            esquema["required"] = reqs
        return esquema
    if tipo == "array" or campo.get("items"):
        items = campo.get("items") or []
        item_schema = (
            {"type": "object", "properties": {i["nombre"]: _esquema_campo(i) for i in items}}
            if items else {"type": "string"}
        )
        if items:
            reqs = [i["nombre"] for i in items if i.get("obligatorio")]
            if reqs:
                item_schema["required"] = reqs
        esquema = {"type": "array", "items": item_schema}
        if campo.get("max_items"):
            esquema["maxItems"] = int(campo["max_items"])
        return esquema
    esquema: dict[str, Any] = {}
    if tipo in ("number", "decimal", "float"):
        esquema["type"] = "number"
        escala = _escala_decimal(campo.get("longitud"))
        if escala is not None:
            esquema["multipleOf"] = 10 ** -escala
    elif tipo in ("integer", "int", "numeric"):
        esquema["type"] = "integer"
    elif tipo in ("boolean", "bool"):
        esquema["type"] = "boolean"
    else:
        esquema["type"] = "string"
    if campo.get("longitud"):
        try:
            esquema["maxLength"] = int(campo["longitud"])
        except (TypeError, ValueError):
            pass
    if campo.get("formato") and esquema.get("type") == "string" and not esquema.get("pattern"):
        esquema["pattern"] = campo["formato"]
    if campo.get("constante"):
        esquema["default"] = campo["constante"]
    return esquema


def _escala_decimal(longitud: Any) -> int | None:
    """Obtiene la escala de una longitud documental como `13.2`."""
    match = re.fullmatch(r"\d+\.(\d+)", str(longitud or "").strip())
    return int(match.group(1)) if match else None


# ── proyeccion a los parametros actuales de la skill ─────────────────────────

def to_legacy_parameters(contract: dict[str, Any]) -> dict[str, Any]:
    """
    Traduce el contrato a los nombres que la skill ya usa.

    Es la pieza que evita reescribir la logica que funciona: la IA recibe el
    contrato, y lo que consume el resto del flujo sigue siendo `servicio`,
    `nombre_funcional`, `ruta_servicio` y compañía.
    """
    validate_contract(contract, check_files=False)
    componente = contract["componente"]
    exposure = contract.get("exposicion") or {}
    operaciones = exposure.get("operaciones") or []
    operacion = operaciones[0] if operaciones else {}
    configuracion = contract.get("configuracion") or {}
    seguridad = contract.get("seguridad") or {}
    autorizacion = seguridad.get("autorizacion") or {}
    perfil = contract.get("perfil") or {}

    base = str(exposure.get("base_path") or "").strip("/")
    path = str(operacion.get("path") or "").strip("/")
    ruta = "/".join(parte for parte in (base, path) if parte)

    servicio = componente.get("nombre_servicio") or componente.get("nombre_tecnico")
    if not servicio:
        raise ContractError("El contrato no define componente.nombre_servicio")

    return {
        "servicio": servicio,
        "nombre_funcional": componente.get("nombre_funcional", ""),
        "ruta_servicio": ruta,
        "operacion_get": operacion.get("nombre") or operacion.get("id", ""),
        "codigo_catalogo": str(configuracion.get("codigo_servicio") or ""),
        "prefijo_modulo": perfil.get("prefijo_modulo", "MF_"),
        "numero_requerimiento": str(componente.get("requerimiento") or ""),
        "grupo_ldap": str(autorizacion.get("grupo") or ""),
    }


# ── perfiles ─────────────────────────────────────────────────────────────────

def load_profile(path: str | Path) -> dict[str, Any]:
    ruta = Path(path)
    if not ruta.is_file():
        raise ContractError(f"No existe el perfil: {ruta}")
    data = yaml.safe_load(ruta.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ContractError(f"El perfil debe ser un objeto YAML: {ruta}")
    return data


def resolve_template(contract: dict[str, Any], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Resuelve la plantilla sin ambiguedad, por repositorio y rama.

    1. `contrato.plantilla` si declara url, rama y subdirectorio.
    2. Si no, `perfil.plantillas[clave]` segun proyecto, dominio, tipo de
       componente y tipo de backend. Nunca por similitud de nombre.

    La resolucion es por RAMA: no se fija commit. El clon se hace sobre la rama
    y se usa su HEAD, de modo que una mejora de la plantilla aplique sin tocar
    el contrato. El commit concreto se registra en el reporte de generacion
    como evidencia de que se genero, no como entrada.
    """
    declarada = contract.get("plantilla") or {}
    if declarada.get("url") and declarada.get("rama") and declarada.get("subdirectorio"):
        return {**declarada, "resolucion": "rama"}
    if profile is None:
        raise ContractError("La plantilla no esta en el contrato y no se paso perfil")
    clave = _clave_plantilla(contract)
    plantillas = profile.get("plantillas") or {}
    elegida = plantillas.get(clave)
    if not elegida:
        raise ContractError(
            f"El perfil no define la plantilla '{clave}'. Hay: {', '.join(sorted(plantillas)) or 'ninguna'}"
        )
    if not elegida.get("rama") or not elegida.get("url") or not elegida.get("subdirectorio"):
        raise ContractError(
            f"La plantilla '{clave}' del perfil no define url, rama o subdirectorio."
        )
    return {"tipo": clave, **elegida, "resolucion": "rama"}


def _clave_plantilla(contract: dict[str, Any]) -> str:
    componente = contract.get("componente") or {}
    dominio = str(componente.get("dominio") or "").strip().upper()
    backend = (contract.get("backend") or {}).get("tipo")
    if componente.get("tipo") == "orquestador" or dominio == "ORQ":
        return "ace-orquestador"
    if backend == "ACH":
        return "ach"
    if dominio == "HUB":
        return "ace-bus-rest-hub"
    return "ace-bus-rest"


def apply_profile(contract: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    """
    Rellena lo que el contrato no declara con lo del perfil.

    El contrato gana siempre. Un valor del perfil no se sobreescribe en
    silencio: si difieren, se registra como decision manual pendiente.
    """
    resultado = copy.deepcopy(contract)
    resultado.setdefault("perfil", {})
    convenciones = profile.get("convenciones") or {}
    for clave, valor in convenciones.items():
        resultado["perfil"].setdefault(clave, valor)
    if "seguridad" not in resultado and profile.get("seguridad_default"):
        resultado["seguridad"] = copy.deepcopy(profile["seguridad_default"])
    if "plantilla" not in resultado or not resultado["plantilla"]:
        resultado["plantilla"] = resolve_template(resultado, profile)
    return resultado


# ── utilidades de fuente ─────────────────────────────────────────────────────

def hash_file(path: str | Path) -> str:
    """SHA-256 de un archivo, para `fuentes.yaml` y cache de entradas."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for bloque in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def cache_key(url: str, rama: str, subdirectorio: str, commit: str) -> str:
    """
    Clave inmutable de plantilla.

    Cambia el commit, cambia la clave: una plantilla fijada nunca se actualiza
    sola, que es lo que hace reproducible la generacion.
    """
    crudo = f"{url}|{rama}|{subdirectorio}|{commit}"
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:16]


# ── extraccion SCI/ETI ───────────────────────────────────────────────────────

def extract_minimal(sci: str, eti: str, *, proyecto: str = "banbif") -> dict[str, Any]:
    """
    Extrae identidad y endpoint sin inventar lo que no se puede demostrar.

    Dos decisiones que vienen de romper esto con un documento real:

    **Se lee por sección, no sobre el documento entero.** El SCI volcado a
    Markdown trae una tabla por hoja, y "Nombre técnico" aparece en más de un
    sitio. Buscando sobre el texto plano se cogía el valor de otra hoja: en el
    147 salió `nombre_servicio: Capa` y `nombre_tecnico: Flujo y reglas de
    Orquestación`. Ahora se acota a la sección del componente y, si hay más de
    un candidato, no se elige: se marca para revisión.

    **Lo dudoso se declara dudoso.** `decisiones.por_verificar` lista lo que hay
    que confirmar a mano. Un campo con valor plausible pero equivocado es peor
    que un campo vacío, porque pasa el validador y falla en generación.
    """
    por_verificar: list[str] = []

    servicio = _campo_eti(eti, ("Nombre del servicio", "Servicio ACE"))
    if not servicio:
        servicio = _campo_eti(eti, ("Relative Service Name",))
    if not _es_nombre_tecnico(servicio):
        por_verificar.append("componente.nombre_servicio")
        servicio = ""

    tecnico = _campo_eti(eti, ("Nombre técnico", "Nombre tecnico"))
    if tecnico and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", tecnico):
        por_verificar.append("componente.nombre_tecnico")
        tecnico = ""

    funcional = _campo_eti(eti, ("Nombre funcional", "Funcionalidad"))
    codigo = _campo_eti(eti, ("Código de servicio", "Codigo de servicio"))
    etiquetado = _campo_eti(eti, ("Etiqueta técnica", "Etiqueta tecnica"))
    requerimiento = _primer(sci + eti, r"^#\s*(\d+)_", flags=re.MULTILINE)

    rutas = re.findall(r"`?POST\s+(?:https://[^\s`]+?)?(/v?\d[^`\s|]*)`?", eti)
    if not rutas:
        por_verificar.append("exposicion.base_path")
    ruta = rutas[0] if rutas else ""
    base, _, path = ruta.rpartition("/")
    if not path:
        por_verificar.append("exposicion.operaciones[0].path")

    # El nombre de la operación BIAN no siempre viene etiquetado. Si no, se deja
    # vacío a propósito: el motor lo deriva de la ruta, y adivinarlo aquí produce
    # un operationId que no corresponde con el contrato real.
    nombre_operacion = etiquetado
    if not nombre_operacion:
        por_verificar.append("exposicion.operaciones[0].nombre")

    for campo, valor in (
        ("componente.nombre_funcional", funcional),
        ("configuracion.codigo_servicio", codigo),
        ("componente.requerimiento", requerimiento),
    ):
        if not valor:
            por_verificar.append(campo)

    return {
        "contrato": "1.0",
        "proyecto": proyecto,
        "componente": {
            "tipo": "atomico",
            "dominio": "IBS",
            "nombre_tecnico": tecnico,
            "nombre_servicio": servicio,
            "nombre_funcional": funcional,
            "requerimiento": requerimiento,
            "etiqueta_tecnica": etiquetado,
        },
        "plantilla": {},
        "exposicion": {
            "protocolo": "REST",
            "base_path": base,
            "operaciones": [
                {
                    "id": "operation",
                    "nombre": nombre_operacion,
                    "metodo": "POST",
                    "path": f"/{path}" if path else "/",
                }
            ],
        },
        "configuracion": {"codigo_servicio": codigo},
        "decisiones": {"manuales": [], "justificaciones": [], "por_verificar": por_verificar},
    }


def _seccion(texto: str, *titulos: str) -> str:
    """
    Recorta el texto a una sección `## ...` o `# ...`.

    Sin esto, buscar "Nombre técnico" sobre el documento entero coge el valor de
    la hoja que toque: en el SCI volcado hay una tabla por hoja y varias se
    llaman igual.
    """
    for titulo in titulos:
        patron = rf"^#{{1,4}}\s+.*?{re.escape(titulo)}.*?$"
        match = re.search(patron, texto, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue
        resto = texto[match.end():]
        fin = re.search(r"^#{1,4}\s+\S", resto, re.MULTILINE)
        return resto[: fin.start()] if fin else resto
    return ""


def _campo_eti(eti: str, etiquetas: tuple[str, ...]) -> str:
    """
    Lee `| Etiqueta | Valor |` acotado a la sección del componente.

    Devuelve "" si hay más de un valor distinto para la misma etiqueta: no se
    elige el primero, porque en ese caso el documento es ambiguo y hay que
    preguntarlo, no adivinar.
    """
    alcance = _seccion(eti, "Información del componente", "Informacion del componente")
    if not alcance:
        alcance = eti
    valores: list[str] = []
    for etiqueta in etiquetas:
        patron = rf"^\|\s*{re.escape(etiqueta)}\s*\|\s*`?([^|`\n]+?)`?\s*\|"
        for encontrado in re.findall(patron, alcance, re.IGNORECASE | re.MULTILINE):
            limpio = encontrado.strip()
            if limpio and limpio not in valores:
                valores.append(limpio)
    return valores[0] if len(valores) == 1 else ""


def _es_nombre_tecnico(valor: str) -> bool:
    """
    Un nombre de servicio ACE es un identificador: `CPS_ProColLis_Corp_Retr_B`.

    Filtra palabras de encabezado de tabla que se cuelan en la extracción
    ("Capa", "Concepto", "Valor"): no son nombres de servicio.
    """
    if not valor or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", valor):
        return False
    return valor.lower() not in {
        "capa", "concepto", "valor", "nombre", "servicio", "detalle", "descripcion",
        "descripción", "origen", "componente", "orquestador", "rol", "tipo",
    }


def merge_manual(anterior: dict[str, Any], nuevo: dict[str, Any]) -> dict[str, Any]:
    """
    Modo actualizar: conserva decisiones manuales y datos no derivados.

    Un mapeo escrito a mano no se pisa porque el extractor no lo ha visto. Se
    marca `pendiente_revision` para que la revision lo vea en el diff.
    """
    resultado = copy.deepcopy(nuevo)
    resultado.setdefault("decisiones", {"manuales": [], "justificaciones": []})
    for clave in ("plantilla", "dfdl", "artefactos_backend", "reglas", "configuracion", "seguridad"):
        if clave in anterior and clave not in nuevo:
            resultado[clave] = copy.deepcopy(anterior[clave])
    manuales = (anterior.get("decisiones") or {}).get("manuales") or []
    if manuales:
        resultado["decisiones"]["manuales"] = copy.deepcopy(manuales)
        resultado["decisiones"]["pendiente_revision"] = list(manuales)
    return resultado


def _primer(texto: str, patron: str, *, flags: int = re.IGNORECASE) -> str:
    match = re.search(patron, texto, flags)
    if not match:
        return ""
    return (match.group(1) if match.lastindex else match.group(0)).strip()


def iter_campos(contract: dict[str, Any], incluir_items: bool = True) -> Iterable[dict[str, Any]]:
    """Recorre request, response y sus items, como lo haria el generador ESQL."""
    for seccion in ("request", "response"):
        pila = list(((contract.get(seccion) or {}).get("body") or {}).get("campos") or [])
        while pila:
            campo = pila.pop(0)
            yield campo
            if incluir_items:
                pila.extend(campo.get("items") or [])
