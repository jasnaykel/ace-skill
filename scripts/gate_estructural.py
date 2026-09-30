"""
Gate estructural del desarrollo generado: comprueba lo que el Toolkit comprobaria
en el momento de differ, pero sinneed de Toolkit.

No sustituye al Toolkit. Falla rapido y sin falsos negativos en los casos que si
se pueden verificar de forma estatica:

1. Todo `esql://routine/<schema>#<modulo>.Main` resuelve contra un
   `CREATE (COMPUTE|FUNCTION) MODULE` real, en el schema declarado.
2. Todo `.msgflow` / `.subflow` / `*.descriptor` es XML bien formado.
3. No hay dos conexiones con la misma pareja
   source/sourceTerminal -> target/targetTerminal.
4. Cada `xmi:id` de nodo es unico.
5. No quedan residuos del esquema de la plantilla renombrada.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

RAIZ = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
SCHEMA_ESPERADO = sys.argv[2] if len(sys.argv) > 2 else None
RESIDUOS = [
    "payexe", "prorev", "RE0058", "UpdatePaymentExecution",
    "termdeposit", "InitiateTermDeposit",
]

fallos: list[str] = []
avisos: list[str] = []


# ── 1. modulos ESQL declarados ───────────────────────────────────────────────
modulos: set[tuple[str, str]] = set()
schemas_declarados: set[str] = set()
for esql in RAIZ.rglob("*.esql"):
    texto = esql.read_text(encoding="utf-8", errors="replace")
    for schema in re.findall(r"BROKER\s+SCHEMA\s+([A-Za-z0-9_.]+)", texto, re.IGNORECASE):
        schemas_declarados.add(schema)
    for nombre in re.findall(
        r"CREATE\s+(?:COMPUTE|FUNCTION)?\s*MODULE\s+([A-Za-z0-9_]+)", texto, re.IGNORECASE
    ):
        modulos.add((esql.name, nombre))

# Los .esql viven en un directorio cuyo nombre final es el ultimo segmento del
# schema, asi que se puede resolver sin depender del nombre del archivo.
modulos_por_schema: dict[str, set[str]] = {}
for esql in RAIZ.rglob("*.esql"):
    texto = esql.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"BROKER\s+SCHEMA\s+([A-Za-z0-9_.]+)", texto, re.IGNORECASE)
    if not match:
        fallos.append(f"ESQL sin BROKER SCHEMA: {esql.relative_to(RAIZ)}")
        continue
    schema = match.group(1)
    for nombre in re.findall(
        r"CREATE\s+(?:COMPUTE|FUNCTION)?\s*MODULE\s+([A-Za-z0-9_]+)", texto, re.IGNORECASE
    ):
        modulos_por_schema.setdefault(schema, set()).add(nombre)

# ── 2. referencias esql://routine ────────────────────────────────────────────
XMI = "{http://www.omg.org/XMI}id"
referencias = 0
for flujo in list(RAIZ.rglob("*.msgflow")) + list(RAIZ.rglob("*.subflow")):
    texto = flujo.read_text(encoding="utf-8", errors="replace")
    for schema, modulo in re.findall(
        r"esql://routine/([A-Za-z0-9_.]+)#([A-Za-z0-9_]+)", texto
    ):
        referencias += 1
        if schema not in schemas_declarados:
            fallos.append(
                f"{flujo.relative_to(RAIZ)}: schema '{schema}' no existe en ningun ESQL"
            )
        elif modulo not in modulos_por_schema.get(schema, set()):
            fallos.append(
                f"{flujo.relative_to(RAIZ)}: routine '{schema}#{modulo}' no existe"
            )

if referencias == 0:
    fallos.append("No se encontro ninguna referencia esql://routine: el gate no pudo validar nada")

# ── 3. XML bien formado, xmi:id unicos, conexiones duplicadas ────────────────
for xml in list(RAIZ.rglob("*.msgflow")) + list(RAIZ.rglob("*.subflow")) + list(
    RAIZ.rglob("*.descriptor")
):
    rel = xml.relative_to(RAIZ)
    try:
        arbol = ET.parse(xml).getroot()
    except ET.ParseError as exc:
        fallos.append(f"{rel}: XML mal formado -> {exc}")
        continue

    ids: list[str] = []
    for elemento in arbol.iter():
        valor = elemento.get(XMI)
        if valor is not None:
            ids.append(valor)
    repetidos = {i for i in ids if ids.count(i) > 1}
    if repetidos:
        fallos.append(f"{rel}: xmi:id duplicados -> {', '.join(sorted(repetidos))}")

    conexiones: list[tuple[str, str, str, str]] = []
    for elemento in arbol.iter():
        if not elemento.tag.endswith("connections"):
            continue
        for hijo in elemento:
            conexiones.append(
                (
                    hijo.get("sourceNode", ""),
                    hijo.get("sourceTerminalName", ""),
                    hijo.get("targetNode", ""),
                    hijo.get("targetTerminalName", ""),
                )
            )
    duplicadas = {c for c in conexiones if conexiones.count(c) > 1}
    if duplicadas:
        fallos.append(f"{rel}: conexiones duplicadas -> {duplicadas}")

    # Cada sourceNode y targetNode debe existir como nodo.
    declarados = {e.get(XMI) for e in arbol.iter() if e.get(XMI) is not None}
    for origen, terminal_origen, destino, _ in conexiones:
        if origen and origen not in declarados:
            fallos.append(f"{rel}: sourceNode '{origen}' no existe")
        if destino and destino not in declarados:
            fallos.append(f"{rel}: targetNode '{destino}' no existe")

# ── 4. residuos de la plantilla renombrada ───────────────────────────────────
# Los .md quedan fuera del barrido: el README debe CITAR la plantilla de origen
# como trazabilidad, y ahi el nombre de la plantilla es la evidencia, no un
# residuo. En cambio, en README si se exige que aparezcan la URL y el commit.
for archivo in RAIZ.rglob("*"):
    if not archivo.is_file() or archivo.suffix.lower() in {
        ".jpg", ".png", ".docx", ".zip", ".jks", ".md",
    }:
        continue
    texto = archivo.read_text(encoding="utf-8", errors="replace")
    for marca in RESIDUOS:
        if marca in texto:
            fallos.append(f"{archivo.relative_to(RAIZ)}: residuo de plantilla '{marca}'")

readme = RAIZ / "README.md"
if not readme.is_file():
    fallos.append("Falta README.md en la raiz del repositorio")
else:
    texto_readme = readme.read_text(encoding="utf-8", errors="replace")
    if "{{" in texto_readme or "}}" in texto_readme:
        fallos.append("README.md: quedan placeholders {{...}} sin resolver")
    if "plantillas-AI" not in texto_readme:
        fallos.append("README.md: no declara la plantilla de origen")

# ── 5. llamadas ESQL: ninguna routine puede quedar inventada ─────────────────
# Una llamada a una routine inexistente no falla al generar el repositorio:
# falla al compilar en el Toolkit. Se comprueba contra las routines definidas en
# este repo mas las librerias compartidas que la plantilla referencia.
COMPARTIDAS = {
    # LIB_CORE_COMMON
    "getDOMINIO_JSON", "getDOMINIO_DFDL", "getDOMINIO_JSON", "getDATA",
    "getHTTP_RES_H", "getHTTP_REQ_H", "getCARACTER_VACIO", "getCOD_EXITO",
    "getCONST_REST", "getCONST_BACKEND", "getCONST_REQUEST", "getCONST_RESPONSE",
    "getCONST_MAIN", "getCONST_ERROR", "getSTATUS_INFO", "getSTATUS_ERROR",
    "getTYPE_LIBRARY_NOT_ATM", "getCODE_APP_BUS", "getLBL_AUDIT",
    "getTIP_RSPTA_2", "getCOD_ERROR_202", "getMSJ_ERROR", "getMSJ_ERROR_DFDL",
    "StructureReqDFDL", "convertDfdlToChar", "convertCharToDfdlV2",
    "prepareCallToCentralizedBackend", "prepararMensajeAuditoriaV2",
    "prepararRespuestaAuditoria", "prepararHeaderRespuestaBus_V2",
    "prepararBodyRespuestaBus_IBS_V2", "prepararBodyRespuestaErrorBus_HTTPV2",
    "PrepareRespPropertiesStatus", "setConfAuditBackend", "setErrorCampo",
    "FormatServiceErrorsForEnvironment", "AppendToServiceErrors",
    "FormatLoanAmount", "ValidateDecimalFormat", "obtenerMensajeError",
    "obtenerCodMsjErrorREST", "manejoErroresGenericoV2", "crearResponseStatus",
    "preparaMensageAPIREST", "GetSecret", "SMF_ESB_COMMON",
}

definidas: set[str] = set()
llamadas: list[tuple[str, str, str]] = []
for esql in RAIZ.rglob("*.esql"):
    texto = esql.read_text(encoding="utf-8", errors="replace")
    rel = esql.relative_to(RAIZ)
    definidas.update(
        re.findall(
            r"CREATE\s+(?:COMPUTE\s+MODULE|PROCEDURE|FUNCTION)\s+([A-Za-z0-9_]+)",
            texto,
            re.IGNORECASE,
        )
    )
    for nombre in re.findall(r"\bCALL\s+([A-Za-z0-9_]+)\s*\(", texto, re.IGNORECASE):
        llamadas.append((str(rel), nombre, texto))

# Nombres de modulo usados como routine en los .msgflow tambien son validos.
for flujo in list(RAIZ.rglob("*.msgflow")) + list(RAIZ.rglob("*.subflow")):
    texto = flujo.read_text(encoding="utf-8", errors="replace")
    for _schema, modulo in re.findall(
        r"esql://routine/([A-Za-z0-9_.]+)#([A-Za-z0-9_]+)", texto
    ):
        definidas.add(modulo)

for rel, nombre, _ in llamadas:
    if nombre in definidas or nombre in COMPARTIDAS:
        continue
    fallos.append(f"{rel}: CALL a routine no definida ni compartida -> {nombre}")

# ── 5b. sintaxis ESQL basica ─────────────────────────────────────────────────
# Esto NO sustituye al parser del Toolkit, pero cubre los tres fallos que se
# repiten al generar sin referencia compilada:
#
#   1. `IDENTITY(JSON.Array)` pegado a un SET. En ESQL el modificador IDENTITY
#      solo existe en CREATE FIELD / CREATE LASTCHILD OF. En un SET el parser
#      espera `= NAME NAMESPACE TYPE VALUE` y aborta con "Syntax error".
#   2. Bloques BEGIN/WHILE/IF desbalanceados.
#   3. Bucles `WHILE LASTMOVE(...)` sin `MOVE ... NEXTSIBLING` incondicional,
#      que no se ven al leer el codigo pero son un bucle infinito en runtime.
SIN_COMENTARIOS = re.compile(r"--[^\n]*")


def _sin_comentarios(texto: str) -> str:
    return SIN_COMENTARIOS.sub("", texto)


def _luego_de(texto: str, inicio: int, patron: re.Pattern) -> int:
    match = patron.search(texto, inicio)
    return match.start() if match else -1


for esql in RAIZ.rglob("*.esql"):
    crudo = esql.read_text(encoding="utf-8", errors="replace")
    texto = _sin_comentarios(crudo)
    rel = esql.relative_to(RAIZ)

    # 1. IDENTITY fuera de CREATE
    for match in re.finditer(r"^\s*SET\s+[^;]*?IDENTITY\s*\(", texto, re.MULTILINE | re.IGNORECASE):
        fallos.append(
            f"{rel}: 'IDENTITY(...)' solo es valido en CREATE FIELD / CREATE "
            f"LASTCHILD OF, no en SET -> {match.group(0).strip()[:70]}"
        )

    # 2. Bloques balanceados
    def contar(patron: str) -> int:
        return len(re.findall(patron, texto, re.IGNORECASE))

    # Los patrones se nombran aparte: dentro de una expresion f-string no puede
    # haber un backslash, y `r'\bIF\b'` es exactamente eso.
    #
    # El lookbehind `(?<!END )` no es cosmetico: `END WHILE` contiene la palabra
    # `WHILE` y `END IF` contiene `IF`, asi que sin el los conteos salen
    # desbalanceados siempre y el gate marca como error un archivo correcto.
    PAT_IF = r"(?<!END )\bIF\b"
    PAT_END_IF = r"\bEND\s+IF\b"
    PAT_WHILE = r"(?<!END )\bWHILE\b"
    PAT_END_WHILE = r"\bEND\s+WHILE\b"
    PAT_CASE = r"(?<!END )\bCASE\b"
    PAT_END_CASE = r"\bEND\s+CASE\b"

    ifs = contar(PAT_IF)
    end_ifs = contar(PAT_END_IF)
    if ifs != end_ifs:
        fallos.append(
            f"{rel}: IF/END IF desbalanceado ({ifs} IF frente a {end_ifs} END IF)"
        )

    whiles = contar(PAT_WHILE)
    end_whiles = contar(PAT_END_WHILE)
    if whiles != end_whiles:
        fallos.append(
            f"{rel}: WHILE/END WHILE desbalanceado "
            f"({whiles} WHILE frente a {end_whiles} END WHILE)"
        )

    cases = contar(PAT_CASE)
    end_cases = contar(PAT_END_CASE)
    if cases != end_cases:
        fallos.append(
            f"{rel}: CASE/END CASE desbalanceado ({cases} CASE frente a {end_cases} END CASE)"
        )

    # 3. Todo WHILE LASTMOVE debe avanzar de forma incondicional
    posicion = 0
    while True:
        cabecera = re.compile(r"\bWHILE\s+LASTMOVE\s*\(", re.IGNORECASE).search(texto, posicion)
        if not cabecera:
            break
        fin = _luego_de(texto, cabecera.end(), re.compile(r"\bEND\s+WHILE\s*;", re.IGNORECASE))
        if fin == -1:
            break
        cuerpo = texto[cabecera.end():fin]
        # NEXTSIBLING tiene que estar fuera de todo IF y fuera del ELSE: si solo
        # aparece dentro de una rama, hay recorrido que no avanza y el bucle no
        # termina. Por eso ELSE tambien aumenta la profundidad.
        profundidad = 0
        advances_incondicional = False
        for sentencia in re.split(r";", cuerpo):
            s = sentencia.strip()
            if not s:
                continue
            if re.match(r"^(ELSE)?IF\b", s, re.IGNORECASE):
                profundidad += 1
            elif re.match(r"^ELSE\b", s, re.IGNORECASE):
                profundidad += 1
            elif re.match(r"^END\s+IF\b", s, re.IGNORECASE):
                profundidad = max(0, profundidad - 1)
            elif re.search(r"\bNEXTSIBLING\b", s, re.IGNORECASE) and profundidad == 0:
                advances_incondicional = True
        if not advances_incondicional:
            fallos.append(
                f"{rel}: el bucle WHILE LASTMOVE de la linea "
                f"{texto[:cabecera.start()].count(chr(10)) + 1} no hace "
                f"'MOVE ... NEXTSIBLING' incondicional: bucle infinito en runtime"
            )
        posicion = fin + 1

# ── 6. .project obligatorios ─────────────────────────────────────────────────
for relativo in (
    "src/application/APP_CPS_ProColLis_Corp_Retr_B/.project",
    "src/v1.0/service/CPS_ProColLis_Corp_Retr_B/.project",
    "src/v1.0/configuration/DEV/policyproject/PLP_CPS_ProColLis_Corp_Retr_B/.project",
    "src/v1.0/configuration/QAS/policyproject/PLP_CPS_ProColLis_Corp_Retr_B/.project",
    "src/v1.0/configuration/PRD/policyproject/PLP_CPS_ProColLis_Corp_Retr_B/.project",
):
    if not (RAIZ / relativo).is_file():
        fallos.append(f"Falta el .project requerido: {relativo}")

# ── 7. schema esperado ───────────────────────────────────────────────────────
if SCHEMA_ESPERADO and SCHEMA_ESPERADO not in schemas_declarados:
    fallos.append(f"El schema esperado '{SCHEMA_ESPERADO}' no esta declarado en ningun ESQL")

# ── salida ───────────────────────────────────────────────────────────────────
print(f"ESQL con schema : {sorted(schemas_declarados)}")
print(f"Modulos ESQL    : {sum(len(v) for v in modulos_por_schema.values())}")
print(f"Referencias     : {referencias}")
for aviso in avisos:
    print(f"AVISO: {aviso}")
if fallos:
    print()
    for fallo in sorted(set(fallos)):
        print(f"BLOQUEANTE: {fallo}")
    print(f"\n{len(set(fallos))} bloqueantes")
    raise SystemExit(2)
print("\nOK: gate estructural superado")
