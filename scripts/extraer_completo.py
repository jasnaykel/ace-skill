"""
SCI + ETI + copybook -> contrato canonico completo.

Este modulo es lo que quita el analisis a la IA. La IA no vuelve a leer el SCI
y el ETI para deducir campos, longitudes, obligatoriedad y mapeos: eso se
extrae aqui, de forma determinista y con la referencia de origen en cada dato.

Lo que sale de aqui es exactamente lo que la IA antes se pasaba leyendo:

    request.body.campos[]   nombre, tipo, longitud, obligatorio, formato,
                            transformacion y campo backend (ICODIBS, VSERVICIO…)
    response.body.campos[]  lo mismo, incluyendo el array y sus items
    headers                propagacion al backend (VTRX, VCANAL)
    errores                codigo + significado de la hoja Errores
    backend                programa, resolutor, conector, copybook
    dfdl                   cardinalidad de los OCCURS, contrastada con el copybook

Y lo que NO sale, a proposito:

    logica ESQL, contenido de Message Flows, politicas por ambiente,
    auditoria, Postman, README.

Eso lo genera la IA desde la plantilla, como hasta ahora. Aqui solo se
normaliza lo que estaba en los documentos.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts import documentos as doc

_RAIZ = Path(__file__).resolve().parent.parent


# ── copybook ─────────────────────────────────────────────────────────────────

def parsear_copybook(texto: str) -> dict[str, Any]:
    """
    Lee un copybook COBOL: estructuras, campos y cardinalidades.

    Es la fuente de verdad de la estructura fisica. Sirve para dos cosas:
    contrastar que cada mapeo del SCI exista de verdad, y rellenar el nombre de
    las estructuras (`DL1071RI`, `DL1071RIRSP`, `ELEERR`) y los `OCCURS`.
    """
    patron = re.compile(
        r"^\s*(\d+)\s+([A-Za-z0-9_$-]+)"
        r"(?:\s+OCCURS\s+(\d+)\s+TIMES)?"
        r"(?:\s+PIC\s+([^.{}]+))?\s*\.\s*$",
        re.IGNORECASE,
    )
    nivel_actual: list[tuple[int, str]] = []
    raiz: str | None = None
    estructuras: list[dict[str, Any]] = []
    campos: list[dict[str, Any]] = []

    for linea in texto.splitlines():
        encontrado = patron.match(linea)
        if not encontrado:
            continue
        nivel, nombre, occurs, pic = encontrado.groups()
        nivel = int(nivel)
        while nivel_actual and nivel_actual[-1][0] >= nivel:
            nivel_actual.pop()
        padre = nivel_actual[-1][1] if nivel_actual else None

        if nivel == 1:
            raiz = nombre
            continue
        if nivel == 2:
            estructuras.append({
                "nombre": nombre,
                "padre": raiz,
                "campos": 0,
            })
        else:
            if occurs or pic:
                campos.append({
                    "nombre": nombre,
                    "estructura": padre,
                    "nivel": nivel,
                    "longitud": _longitud_pic(pic),
                    "ocurrencias": int(occurs) if occurs else None,
                })
            if estructuras and padre == estructuras[-1]["nombre"]:
                estructuras[-1]["campos"] += 1
        nivel_actual.append((nivel, nombre))

    return {
        "raiz": raiz,
        "estructuras": estructuras,
        "campos": campos,
        "nombres": {c["nombre"] for c in campos} | {e["nombre"] for e in estructuras},
        "ocurrencias": {c["nombre"]: c["ocurrencias"] for c in campos if c["ocurrencias"]},
    }


def _longitud_pic(pic: str | None) -> int | None:
    if not pic:
        return None
    encontrado = re.search(r"X\((\d+)\)", pic, re.IGNORECASE)
    if encontrado:
        return int(encontrado.group(1))
    encontrado = re.search(r"9\((\d+)\)", pic, re.IGNORECASE)
    return int(encontrado.group(1)) if encontrado else None


# ── construccion del contrato ───────────────────────────────────────────────

def extraer_contrato(
    sci: str,
    eti: str,
    *,
    proyecto: str = "banbif",
    copybook: str | None = None,
    copybook_ruta: str | None = None,
) -> dict[str, Any]:
    """
    Arma el contrato completo. Sin copybook es un contrato sin capa backend.

    No inventa: si algo no esta en los documentos, no aparece. Lo que quedo a
    medias se anota en `decisiones.por_verificar` con la ruta exacta del campo,
    para que la revision vaya a mirarlo y no a buscar.
    """
    por_verificar: list[str] = []
    contrato = extract_minimal(sci, eti, proyecto=proyecto)
    contrato.pop("decisiones", None)
    contrato.pop("exposicion", None)

    ident = _identidad(eti, sci, por_verificar)
    contrato["componente"].update(ident)

    exposicion = _exposicion(eti, sci, contrato["componente"], por_verificar)
    contrato["exposicion"] = exposicion

    entrada = doc.bloque_hoja(sci, "DatosEntrada")
    salida = doc.bloque_hoja(sci, "DatosSalida")
    contrato["headers"] = _headers(entrada, salida, por_verificar)
    contrato["request"] = _request(entrada, por_verificar)
    contrato["response"] = _response(salida, por_verificar)
    contrato["errores"] = _errores(sci)

    backend = _backend(sci, por_verificar)
    if copybook:
        backend.update(_capa_copybook(copybook, copybook_ruta, por_verificar))
    if backend:
        contrato["backend"] = backend
        if backend.get("copybook"):
            contrato["dfdl"] = _dfdl(backend, contrato.get("response") or {})
    contrato["reglas"] = _reglas(entrada, salida)
    contrato["configuracion"].update(_configuracion(sci, eti, por_verificar))
    contrato["decisiones"] = {
        "manuales": [],
        "justificaciones": [],
        "por_verificar": sorted(set(por_verificar)),
    }
    return contrato


def _identidad(eti: str, sci: str, por_verificar: list[str]) -> dict[str, Any]:
    """Nombres, código y metadata. Del ETI si se puede; del SCI como respaldo."""
    servicio = doc.seccion(eti, "Información del componente", "Informacion del componente")
    alcance = servicio or eti
    datos = {
        "nombre_tecnico": _valor_tabla(alcance, ("Nombre técnico", "Nombre tecnico")),
        "nombre_servicio": _valor_tabla(alcance, ("Servicio ACE", "Nombre del servicio")),
        "nombre_funcional": _valor_tabla(alcance, ("Nombre funcional", "Funcionalidad")),
        "etiqueta_tecnica": _valor_tabla(alcance, ("Etiqueta técnica", "Etiqueta tecnica")),
        "linea_producto": _valor_tabla(alcance, ("Línea de producto", "Linea de producto")),
        "producto": _valor_tabla(alcance, ("Producto",)),
    }
    for clave, valor in datos.items():
        if not valor:
            por_verificar.append(f"componente.{clave}")
    codigo = _valor_tabla(alcance, ("Código de servicio", "Codigo de servicio"))
    if not codigo:
        por_verificar.append("configuracion.codigo_servicio")
    datos["codigo_servicio"] = codigo
    if not _es_nombre_tecnico(datos.get("nombre_servicio") or ""):
        por_verificar.append("componente.nombre_servicio")
    return datos


def _exposicion(eti: str, sci: str, componente: dict[str, Any], por_verificar: list[str]) -> dict[str, Any]:
    """Base path, metodo, timeout y nombre de la operacion."""
    base, metodo, timeout_cliente, timeout_backend = "", "POST", None, None

    bloque = doc.seccion(eti, "Endpoint")
    if bloque:
        filas = doc.tabla(bloque)
        for fila in filas:
            celdas = [doc.limpiar(c) for c in fila]
            if any(c.upper() in ("DEV", "QAS", "PRD") for c in celdas):
                for celda in celdas:
                    encontrada = re.search(r"(https?://\S+)", celda)
                    if encontrada:
                        ruta = re.sub(r"^https?://[^/]+", "", encontrada.group(1)).rstrip("`")
                        base = ruta.rsplit("/", 1)[0] or "/"
                        metodo = (re.match(r"([A-Z]+)", celda.strip()) or ["", "POST"])[1] if re.match(r"([A-Z]+)", celda.strip()) else "POST"
                        break
                if base:
                    break

    if not base:
        # Respaldo: el SCI publica la ruta en la hoja de impacto funcional.
        encontrado = re.search(r"/v?\d[\w/.-]*", eti + sci)
        if encontrado:
            base = encontrado.group(0).rsplit("/", 1)[0]
            por_verificar.append("exposicion.base_path")
        else:
            por_verificar.append("exposicion.base_path")

    timeouts = _valor_tabla(doc.seccion(eti, "Información del componente") or eti, ("Timeout",))
    if timeouts:
        numeros = re.findall(r"(\d+)\s*s", timeouts)
        if len(numeros) >= 2:
            timeout_cliente, timeout_backend = int(numeros[0]), int(numeros[1])
        elif numeros:
            timeout_backend = int(numeros[0])

    nombre = componente.get("etiqueta_tecnica") or componente.get("nombre_tecnico") or ""
    if not nombre:
        por_verificar.append("exposicion.operaciones[0].nombre")

    return {
        "protocolo": "REST",
        "base_path": base,
        "seguridad_externa": "mtls",
        "operaciones": [{
            "id": _slug(nombre) or "operation",
            "nombre": nombre,
            "metodo": metodo,
            "path": "/" + (base.rsplit("/", 1)[-1] if base else "retrieve"),
            **({"timeout_cliente_s": timeout_cliente} if timeout_cliente else {}),
            **({"timeout_backend_s": timeout_backend} if timeout_backend else {}),
        }],
    }


def _headers(entrada: list[dict], salida: list[dict], por_verificar: list[str]) -> dict[str, Any]:
    """
    Headers de request y response.

    De los headers del SCI sale lo que la IA antes deducía a mano: obligatoriedad,
    longitud, formato y, sobre todo, la propagación al backend (`VTRX`, `VCANAL`).
    """
    request, response = [], []
    for fila in entrada:
        if "headers" not in fila["seccion"].lower():
            continue
        header = _campo_a_header(fila, "SCI:DatosEntrada:Headers REQUEST")
        if not header:
            continue
        if fila["campo_backend"]:
            header["propagacion_backend"] = fila["campo_backend"]
        request.append(header)
    for fila in salida:
        if "headers" not in fila["seccion"].lower():
            continue
        header = _campo_a_header(fila, "SCI:DatosSalida:Headers RESPONSE")
        if header:
            response.append(header)
    if not request:
        por_verificar.append("headers.request")
    if not response:
        por_verificar.append("headers.response")
    return {"request": request, "response": response}


def _campo_a_header(fila: dict[str, Any], origen: str) -> dict[str, Any] | None:
    nombre = fila["nombre"]
    if not nombre or not re.match(r"^[A-Za-z][A-Za-z0-9-]*$", nombre):
        return None
    header: dict[str, Any] = {"nombre": nombre, "tipo": "string", "origen": origen}
    if fila["longitud"] is not None:
        header["longitud"] = fila["longitud"]
    if fila["obligatorio"] is not None:
        header["obligatorio"] = fila["obligatorio"]
    if fila["formato"] and fila["formato"] not in ("-",):
        header["formato"] = fila["formato"]
    return header


def _request(entrada: list[dict], por_verificar: list[str]) -> dict[str, Any]:
    """Headers fuera y body dentro, con los items de array anidados."""
    cuerpo = [f for f in entrada if "headers" not in f["seccion"].lower()]
    campos, raiz = _campos(cuerpo, "SCI:DatosEntrada:Body REQUEST")
    if not campos:
        por_verificar.append("request.body.campos")
    return {"body": {"nombre_raiz": raiz, "campos": campos}}


def _response(salida: list[dict], por_verificar: list[str]) -> dict[str, Any]:
    """
    Cuerpo de respuesta. La hoja trae tambien `Estructura de Errores`, que no
    es parte de la respuesta exitosa: se separa, porque mezclarla produce un
    OpenAPI con StatusCode dentro del 200.
    """
    cuerpo = [
        f for f in salida
        if "headers" not in f["seccion"].lower() and "errores" not in f["seccion"].lower()
    ]
    campos, raiz = _campos(cuerpo, "SCI:DatosSalida:Body RESPONSE")
    if not campos:
        por_verificar.append("response.body.campos")
    return {"body": {"nombre_raiz": raiz, "campos": campos}}


def _campos(filas: list[dict], origen: str) -> tuple[list[dict[str, Any]], str]:
    """
    Convierte filas planas en campos, anidando los items de array.

    El SCI entrega `Raiz/Lista[]/Campo` en filas sueltas. Sin agrupar, el
    contrato tendría 15 campos sueltos en lugar de un array de 15 items, y el
    OpenAPI no podría declarar `maxItems`.
    """
    raiz = ""
    indices: dict[str, dict[str, Any]] = {}
    orden: list[str] = []
    items: dict[str, list[dict[str, Any]]] = {}

    for fila in filas:
        if fila["nombre_raiz"] and not raiz:
            raiz = fila["nombre_raiz"]
        padre = fila["array_padre"] if fila["es_item"] else None
        if padre:
            items.setdefault(padre, []).append(_campo(fila, origen))
            continue
        nombre = fila["nombre"]
        if not nombre or nombre in indices:
            continue
        indices[nombre] = _campo(fila, origen)
        orden.append(nombre)

    campos: list[dict[str, Any]] = []
    for nombre in orden:
        campo = indices[nombre]
        if nombre in items:
            campo["items"] = items[nombre]
        campos.append(campo)
    return campos, raiz


def _campo(fila: dict[str, Any], origen: str) -> dict[str, Any]:
    campo: dict[str, Any] = {
        "nombre": fila["nombre"],
        "tipo": fila["tipo"],
        "origen": origen,
    }
    if fila["nombre_servicio"] and fila["nombre_servicio"] != fila["nombre"]:
        campo["nombre_servicio"] = fila["nombre_servicio"]
    if fila["nombre_bian"]:
        campo["ruta"] = fila["nombre_bian"]
    if fila["longitud"] is not None:
        campo["longitud"] = fila["longitud"]
    if fila["obligatorio"] is not None:
        campo["obligatorio"] = fila["obligatorio"]
    if fila["formato"]:
        campo["formato"] = fila["formato"]
    if fila.get("max_items"):
        campo["max_items"] = fila["max_items"]
    if not fila["expuesto"]:
        campo["expuesto"] = False
    if fila["ejemplo"] and not doc.es_nano(fila["ejemplo"]):
        campo["ejemplo"] = fila["ejemplo"]

    transformacion = fila["transformacion"]
    if transformacion and transformacion != "ninguna":
        campo["transformacion"] = transformacion
        if not _es_clave(transformacion):
            campo["transformacion_nota"] = fila.get("descripcion") or transformacion

    if fila["campo_backend"]:
        backend: dict[str, Any] = {"campo": fila["campo_backend"]}
        if transformacion and transformacion != "ninguna":
            backend["transformacion"] = transformacion
        campo["backend"] = backend
    elif not fila["es_item"]:
        campo["backend"] = {}
    return campo


def _es_clave(valor: str) -> bool:
    return bool(re.fullmatch(r"[a-z_]+", valor))


def _errores(sci: str) -> list[dict[str, Any]]:
    """
    Hoja Errores: `| 9701 | Codigo del cliente errado |`.

    Sin esto, el codigo de error viaja en el comentario de una fila y la IA
    tiene que buscarlo en un documento de 300 lineas.
    """
    texto = doc.hoja(sci, "Errores")
    if not texto:
        return []
    salida = []
    for fila in doc.tabla(texto):
        if len(fila) < 2:
            continue
        codigo, descripcion = doc.limpiar(fila[0]), doc.limpiar(fila[1])
        if not codigo or not codigo[0].isdigit():
            continue
        salida.append({
            "codigo": codigo,
            "significado": descripcion,
            "http": 202,
            "tipo": "negocio",
            "origen": "SCI:Errores",
        })
    return salida


def _backend(sci: str, por_verificar: list[str]) -> dict[str, Any]:
    """Programa, resolutor, conector y timeout. De la hoja Informacion del SCI."""
    texto = doc.hoja(sci, "Información") or doc.hoja(sci, "Informacion")
    if not texto:
        por_verificar.append("backend")
        return {}
    plataforma = _valor_tabla(texto, ("Nombre de la Plataforma",))
    programa = _valor_tabla(texto, ("Nombre del programa",))
    resolutor = _valor_tabla(texto, ("Resolutor",))
    conector = _valor_tabla(texto, ("Conector",))
    if not programa:
        por_verificar.append("backend.programa")
    if not conector:
        por_verificar.append("backend.conector")
    salida: dict[str, Any] = {"tipo": "IBS_RPG" if plataforma == "IBS" else "IBS_RPG"}
    if conector:
        salida["conector"] = conector
    if programa:
        salida["programa"] = programa
    if resolutor:
        encontrado = re.search(r"\(([A-Za-z0-9_]+)\)", resolutor)
        if encontrado:
            salida["programa_resolutor"] = encontrado.group(1)
        else:
            salida["resolutor"] = resolutor
    return salida


def _capa_copybook(
    copybook: str,
    ruta: str | None,
    por_verificar: list[str],
) -> dict[str, Any]:
    """
    Estructuras y cardinalidades del copybook.

    `request` es el nombre de la estructura que se envia al backend, no el
    primero de nivel 01: en `DL1071RI` el nivel 01 se llama igual que la
    estructura de request, y en otros copybooks no. Se resuelve por posicion
    (el segundo grupo de nivel 02) y se deja anotado.
    """
    info = parsear_copybook(copybook)
    raiz = info["raiz"] or ""
    grupos = [e for e in info["estructuras"] if e["nombre"] != raiz]
    request = grupos[0]["nombre"] if grupos else raiz
    response = grupos[1]["nombre"] if len(grupos) > 1 else ""
    error = ""
    for grupo in grupos:
        if "ERR" in grupo["nombre"].upper():
            error = grupo["nombre"]
            break
    if response and error and response == error:
        response = ""
    return {
        "copybook": {
            "ruta": ruta or "",
            "request": request,
            "response": response,
            "error": error,
            "xsd_generado": _xsd_de(ruta) if ruta else "",
            "yaml_control": _yaml_de(ruta) if ruta else "",
        },
        "_nombres": info["nombres"],
        "_ocurrencias": info["ocurrencias"],
    }


def _xsd_de(ruta: str) -> str:
    return str(Path(ruta).with_suffix(".xsd").name)


def _yaml_de(ruta: str) -> str:
    """El `.yaml` de control viene de la plantilla, no del copybook. Se infiere."""
    return str(Path(ruta).with_suffix(".yaml").name)


def _dfdl(backend: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Opciones DFDL y cardinalidad declarada, lista para contrastar con el XSD."""
    copybook = backend.get("copybook") or {}
    cardinalidad = dict(backend.get("_ocurrencias") or {})
    # El array del contrato es la misma cardinalidad que el OCCURS del copybook.
    for campo in ((response.get("body") or {}).get("campos") or []):
        if campo.get("items") and campo.get("max_items"):
            cardinalidad.setdefault(campo["nombre"], campo["max_items"])
    return {
        "script": "scripts/generate_cobol_dfdl_xsd.py",
        "xsd_esperado": copybook.get("xsd_generado", ""),
        "opciones": {
            "codepage": "ISO-8859-1",
            "endian": "Little",
            "string_padding": "%SP;",
            "number_padding": "0",
            "preserve_case": True,
        },
        "cardinalidad": {
            nombre: {"tipo": "fixed", "min": valor, "max": valor}
            for nombre, valor in cardinalidad.items()
            if valor
        },
    }


def _reglas(entrada: list[dict], salida: list[dict]) -> dict[str, Any]:
    """
    Transformaciones, en forma de tabla.

    La IA las necesитaba para el ESQL (`preparar trama`, `armaRpta`) y antes
    las leia frase por frase del SCI. Aqui quedan como pares origen-destino.
    """
    transformaciones = []
    vistos = set()
    for filas in (entrada, salida):
        for fila in filas:
            transformacion = fila["transformacion"]
            if not transformacion or transformacion == "ninguna" or not fila["campo_backend"]:
                continue
            clave = (fila["nombre"], fila["campo_backend"], transformacion)
            if clave in vistos:
                continue
            vistos.add(clave)
            regla: dict[str, Any] = {
                "origen": fila["nombre_bian"] or fila["nombre"],
                "destino": fila["campo_backend"],
                "expresion": transformacion,
            }
            if not _es_clave(transformacion):
                regla["nota_sci"] = fila.get("descripcion") or transformacion
            transformaciones.append(regla)
    return {"transformaciones": transformaciones}


def _configuracion(sci: str, eti: str, por_verificar: list[str]) -> dict[str, Any]:
    """
    Constantes y destinos.

    El SCI no trae URLs de backend: salen de la politica del proyecto, asi que
    aqui van como `${VARIABLE}`. Inventar una URL es peor que dejarla pendiente.
    """
    salida: dict[str, Any] = {"constantes": {}}
    codigo = _valor_tabla(doc.seccion(eti, "Información del componente") or eti, ("Código de servicio",))
    if codigo:
        salida["codigo_servicio"] = codigo
    return salida


def _valor_tabla(texto: str, etiquetas: tuple[str, ...]) -> str:
    """
    Valor de la primera etiqueta que aparece en una tabla de dos columnas.

    Devuelve "" si hay mas de un valor distinto: en ese caso el documento es
    ambiguo y se deja que el validador lo marque, en vez de elegir el primero.
    """
    if not texto:
        return ""
    valores: list[str] = []
    for etiqueta in etiquetas:
        patron = rf"^\|\s*{re.escape(etiqueta)}\s*\|\s*([^|\n]*?)\s*\|"
        for encontrado in re.findall(patron, texto, re.IGNORECASE | re.MULTILINE):
            limpio = doc.limpiar(encontrado)
            if doc.es_nano(limpio) or not limpio:
                continue
            if limpio not in valores:
                valores.append(limpio)
    return valores[0] if len(valores) == 1 else ""


def _es_nombre_tecnico(valor: str) -> bool:
    if not valor or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", valor):
        return False
    return valor.lower() not in {
        "capa", "concepto", "valor", "nombre", "servicio", "detalle", "descripcion",
        "descripción", "origen", "componente", "orquestador", "rol", "tipo",
    }


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (texto or "").lower()).strip("_")


def _from_contrato(contrato: dict[str, Any]) -> dict[str, Any]:
    """Quita las claves auxiliares `_nombres` / `_ocurrencias` del contrato."""
    limpio = {k: v for k, v in contrato.items() if not k.startswith("_")}
    backend = limpio.get("backend")
    if isinstance(backend, dict):
        backend.pop("_nombres", None)
        backend.pop("_ocurrencias", None)
    return limpio


from scripts.contrato import extract_minimal  # noqa: E402  (evita ciclo de import)
