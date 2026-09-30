"""
Parser de los documentos del cliente (SCI/ETI en Markdown).

Este modulo es la pieza que quita el analisis a la IA: en vez de que el modelo
lea el SCI y el ETI completos y deduzca campos, mapeos y cardinalidades, los
scripts lo hacen aqui de forma determinista y con la referencia de origen en
cada dato.

Por que tablas y no "leer el documento":

- El SCI volcado a Markdown trae una tabla por hoja. Buscar "Nombre tecnico"
  sobre el texto plano coge el valor de otra hoja: en el 147 devolvia
  `Capa` y `Flujo y reglas de Orquestacion` como nombre de servicio.
- Dentro de la tabla, buscar por nombre de columna es seguro. Buscar por
  posicion no lo es: la hoja de entrada tiene 19 columnas y la de salida 20.
  Si una hoja gana una columna, todo lo que se lee por indice se desplaza.

Por eso las columnas se resuelven por nombre, y cada dato guarda su
referencia (`SCI:DatosEntrada:Body REQUEST`) para la trazabilidad.
"""
from __future__ import annotations

import re
from typing import Any

NANOS = {"nan", "", "none", "n/a", "-", "null"}


def es_nano(valor: str | None) -> bool:
    return (valor or "").strip().lower() in NANOS


def limpiar(valor: str | None) -> str:
    """Quita el ruido de un volcado de Excel a Markdown."""
    texto = (valor or "").strip()
    texto = re.sub(r"[*`]+", "", texto)
    return texto.strip()


def dividir_fila(linea: str) -> list[str]:
    """Divide una fila de tabla Markdown respetando el pipe escapado."""
    cuerpo = linea.strip()
    if cuerpo.startswith("|"):
        cuerpo = cuerpo[1:]
    if cuerpo.endswith("|"):
        cuerpo = cuerpo[:-1]
    partes, actual, escapado = [], [], False
    for caracter in cuerpo:
        if escapado:
            actual.append(caracter)
            escapado = False
            continue
        if caracter == "\\":
            actual.append(caracter)
            escapado = True
            continue
        if caracter == "|":
            partes.append("".join(actual))
            actual = []
            continue
        actual.append(caracter)
    partes.append("".join(actual))
    return [p.strip() for p in partes]


def hoja(markdown: str, nombre: str) -> str:
    """Recorta la hoja `## Hoja: <nombre>` completa."""
    patron = rf"^#{{1,4}}\s+.*?Hoja:\s*{re.escape(nombre)}\s*$"
    match = re.search(patron, markdown, re.IGNORECASE | re.MULTILINE)
    if not match:
        return ""
    resto = markdown[match.end():]
    fin = re.search(r"^#{1,4}\s+\S|^---\s*$", resto, re.MULTILINE)
    return resto[: fin.start()] if fin else resto


def seccion(markdown: str, *titulos: str) -> str:
    """Recorta una seccion por titulo de encabezado Markdown."""
    for titulo in titulos:
        patron = rf"^#{{1,4}}\s+.*?{re.escape(titulo)}.*?$"
        match = re.search(patron, markdown, re.IGNORECASE | re.MULTILINE)
        if not match:
            continue
        resto = markdown[match.end():]
        fin = re.search(r"^#{1,4}\s+\S|^---\s*$", resto, re.MULTILINE)
        return resto[: fin.start()] if fin else resto
    return ""


def tabla(markdown: str) -> list[list[str]]:
    """Devuelve las filas de la primera tabla, ya divididas."""
    filas = []
    for linea in markdown.splitlines():
        limpio = linea.strip()
        if not limpio.startswith("|"):
            if filas:
                break
            continue
        if re.fullmatch(r"\|[\s:\-|]+\|", limpio):
            continue
        filas.append(dividir_fila(limpio))
    return filas


def normalizar(texto: str) -> str:
    """
    Colapsa espacios y quita acentos de un nombre de columna.

    El volcado de Excel no es estable en el espaciado: la misma columna sale
    `Campo BIAN` en la hoja de entrada y `Campo  BIAN` (dos espacios) en la de
    salida. Buscar por patron exacto sobre el nombre crudo hacia fallar segun
    la hoja, que es la peor forma de fallar: funciona con un documento y no con
    el siguiente.
    """
    plano = (texto or "").strip().lower()
    plano = re.sub(r"\s+", " ", plano)
    return re.sub(r"[áéíóúüñ]", lambda m: m.group(0).replace("á", "a").replace("é", "e")
                  .replace("í", "i").replace("ó", "o").replace("ú", "u")
                  .replace("ü", "u").replace("ñ", "n"), plano)


def resolver_columnas(filas: list[list[str]], indice: int) -> dict[str, int]:
    """
    Mapa nombre-de-columna -> indice, leyendo la fila de encabezado real.

    El volcado de Excel produce dos filas de encabezado: la primera con
    `Unnamed: 0`, `Unnamed: 1`… y la segunda con los nombres verdad. Se leen
    ambas y se ignoran los `Unnamed`.
    """
    if indice >= len(filas):
        return {}
    mapa: dict[str, int] = {}
    for posicion, nombre in enumerate(filas[indice]):
        limpio = normalizar(nombre)
        if limpio and not limpio.startswith("unnamed"):
            mapa.setdefault(limpio, posicion)
    return mapa


def celda(fila: list[str], columnas: dict[str, int], nombre: str) -> str:
    """Valor de una celda por nombre de columna. `""` si no existe la columna."""
    indice = columnas.get(normalizar(nombre))
    if indice is None or indice >= len(fila):
        return ""
    return limpiar(fila[indice])


def columna_por_patron(columnas: dict[str, int], patron: str) -> str | None:
    """Busca una columna por regex sobre el nombre normalizado."""
    expresion = re.compile(patron)
    for nombre in columnas:
        if expresion.search(nombre):
            return nombre
    return None


def es_booleano(valor: str) -> bool | None:
    """`SI`/`NO` del SCI a tri-estado. `None` = no informado."""
    texto = (valor or "").strip().lower()
    if texto in ("si", "sí", "yes", "s"):
        return True
    if texto in ("no", "n"):
        return False
    return None


def longitud(valor: str) -> int | str | None:
    """
    Longitud del SCI: puede venir como `36` o como `[1,9]`.

    Un rango se conserva tal cual. Reducirlo a un entero seria inventar: `[1,9]`
    significa "de 1 a 9 digitos", no "9".
    """
    texto = (valor or "").strip()
    if es_nano(texto):
        return None
    rango = re.fullmatch(r"\[\s*(\d+)\s*,\s*(\d+)\s*\]", texto)
    if rango:
        return f"[{rango.group(1)},{rango.group(2)}]"
    if texto.isdigit():
        return int(texto)
    return None


def tipo_dato(valor: str) -> str:
    """Normaliza el tipo del SCI a los tipos del contrato."""
    texto = (valor or "").strip().lower()
    if texto in ("numeric", "numérico", "numerico", "number", "int", "integer"):
        return "numeric"
    if texto in ("boolean", "bool", "lógico", "logico"):
        return "boolean"
    return "string"


def nombre_bian(valor: str) -> tuple[str | None, str | None]:
    """
    `Raiz/DatosSalida/Campo` -> (raiz, nombre).

    Devuelve (None, None) cuando el campo no se expone al consumidor, que es el
    caso de "No se mapea, dato configurable".
    """
    texto = (valor or "").strip()
    if es_nano(texto) or re.match(r"^no se mapea", texto, re.IGNORECASE):
        return None, None
    partes = [p for p in texto.split("/") if p]
    if not partes:
        return None, None
    if len(partes) == 1:
        return None, partes[0]
    return partes[0], partes[-1]


def es_item(valor: str) -> bool:
    """`Lista[]/Campo` marca que el campo es un elemento de un array."""
    return "/[]/" in (valor or "")


def array_padre(valor: str) -> str | None:
    """`Raiz/Lista[]/Campo` -> `Lista`."""
    partes = [p for p in (valor or "").split("/") if p]
    for indice, parte in enumerate(partes[:-1]):
        if parte.endswith("[]"):
            return parte[:-2]
    return None


def cardinalidad(valor: str) -> int | None:
    """`Lista [40] El tamaño debe ser configurable...` -> 40."""
    encontrado = re.search(r"\[(\d+)\]", valor or "")
    return int(encontrado.group(1)) if encontrado else None


def no_expuesto(comentario: str, bian: str) -> bool:
    """El SCI dice "no debe ser expuesto" en el comentario; se respeta."""
    texto = f"{comentario} {bian}".lower()
    return "no debe ser expuesto" in texto or "no se mapea" in texto


def transformacion(valor: str) -> str:
    """
    Convierte la transformacion en prosa del SCI a una clave estable.

    El SCI escribe "Se completa con ceros a la izquierda" y
    "Backend --> Servicio yyyyMMdd --> yyyy-MM-dd". Se mapean a claves que la
    IA puede aplicar sin volver a leer la frase, y se conserva el texto original
    en `nota` para que no se pierda nada.
    """
    texto = (valor or "").strip()
    bajo = texto.lower()
    if es_nano(texto):
        return "ninguna"
    if "ceros a la izquierda" in bajo or "completar" in bajo and "ceros" in bajo:
        return "completar_con_ceros_izquierda"
    if "yyyymmdd" in bajo and "yyyy-mm-dd" in bajo:
        return "yyyyMMdd_a_yyyy-MM-dd"
    if "flag" in bajo or ("'1': true" in bajo) or ("true, 0" in bajo.replace("true,0", "true, 0")):
        return "flag_binario_a_booleano"
    return texto


def bloque_hoja(markdown: str, nombre_hoja: str) -> list[dict[str, Any]]:
    """
    Lee una hoja de datos (`DatosEntrada` / `DatosSalida`).

    Devuelve filas normalizadas. Cada fila lleva la `seccion` heredada: en el
    volcado, la columna `Seccion` viene `nan` en todas las filas menos la
    primera de cada grupo, y sin heredarla se pierde en que grupo estaba cada
    campo.
    """
    texto = hoja(markdown, nombre_hoja)
    if not texto:
        return []
    filas = tabla(texto)
    if len(filas) < 3:
        return []

    # Encabezado real: la ultima fila antes de los datos cuyos nombres no son
    # todos "Unnamed". En la 147 la fila 0 es `MAIN REQUEST | Unnamed: 1…` y la
    # fila 1 es la de los nombres reales.
    indice_encabezado = 0
    for indice in range(min(3, len(filas))):
        nombres = [limpiar(c) for c in filas[indice]]
        con_nombre = [n for n in nombres if n and not n.lower().startswith("unnamed")]
        if len(con_nombre) >= 5:
            indice_encabezado = indice
    columnas = resolver_columnas(filas, indice_encabezado)

    clave_bian = columna_por_patron(columnas, r"Campo BIAN")
    clave_nombre = columna_por_patron(columnas, r"^Campos Servicio$")
    clave_tipo = columna_por_patron(columnas, r"^Tipo Dato$")
    clave_long = columna_por_patron(columnas, r"^Longitud$")
    clave_oblig = columna_por_patron(columnas, r"^Obligatorio$")
    clave_formato = columna_por_patron(columnas, r"^Formato")
    clave_transf = columna_por_patron(columnas, r"^Transformaci")
    clave_ejemplo = columna_por_patron(columnas, r"^Ejemplo$")
    clave_comentario = columna_por_patron(columnas, r"^Comentario$")
    clave_origen = columna_por_patron(columnas, r"^Fuente del dato$")
    clave_lista = columna_por_patron(columnas, r"^Lista$")
    clave_productor = columna_por_patron(columnas, r"^Productor Datos de")

    salida: list[dict[str, Any]] = []
    seccion_actual = ""
    for fila in filas[indice_encabezado + 1:]:
        if not any(limpiar(c) for c in fila):
            continue
        seccion_celda = limpiar(fila[0]) if fila else ""
        if seccion_celda and not es_nano(seccion_celda):
            seccion_actual = seccion_celda
        elif seccion_celda.lower().startswith("unnamed"):
            seccion_celda = ""
        if not seccion_actual:
            continue

        bian = celda(fila, columnas, clave_bian) if clave_bian else ""
        nombre_servicio = celda(fila, columnas, clave_nombre) if clave_nombre else ""
        raiz, nombre = nombre_bian(bian)
        if not nombre and not nombre_servicio:
            continue

        fila_datos: dict[str, Any] = {
            "seccion": seccion_actual,
            "origen_dato": celda(fila, columnas, clave_origen) if clave_origen else "",
            "nombre_bian": bian,
            "nombre_raiz": raiz,
            "nombre": nombre or nombre_servicio,
            "nombre_servicio": nombre_servicio,
            "es_item": es_item(bian),
            "array_padre": array_padre(bian),
            "lista": celda(fila, columnas, clave_lista) if clave_lista else "",
            "descripcion": "",
            "tipo": tipo_dato(celda(fila, columnas, clave_tipo) if clave_tipo else ""),
            "longitud": longitud(celda(fila, columnas, clave_long) if clave_long else ""),
            "obligatorio": es_booleano(celda(fila, columnas, clave_oblig) if clave_oblig else ""),
            "formato": celda(fila, columnas, clave_formato) if clave_formato else "",
            "transformacion": transformacion(celda(fila, columnas, clave_transf) if clave_transf else ""),
            "ejemplo": celda(fila, columnas, clave_ejemplo) if clave_ejemplo else "",
            "comentario": celda(fila, columnas, clave_comentario) if clave_comentario else "",
            "campo_backend": celda(fila, columnas, clave_productor) if clave_productor else "",
        }
        if es_nano(fila_datos["campo_backend"]):
            fila_datos["campo_backend"] = ""
        if es_nano(fila_datos["formato"]) or fila_datos["formato"] in ("-",):
            fila_datos["formato"] = ""
        fila_datos["expuesto"] = not no_expuesto(
            fila_datos["comentario"], fila_datos["nombre_bian"]
        )
        cardinal = cardinalidad(fila_datos["lista"])
        if cardinal:
            fila_datos["max_items"] = cardinal
        salida.append(fila_datos)
    return salida
