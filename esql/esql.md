# esql — ESQL (Compute, tramas DFDL, auditoría) y Message Flows

## Propósito
Reglas y recetario para escribir o modificar ESQL dentro de los módulos de la plantilla, y para leer/crear `.msgflow`/`.subflow`.

## Layout de archivos (patrón del Repo C)
```
LIB_Constants.esql   → CREATE FUNCTION/constantes C_* (UDP_URL_APIREST, C_OPERATION_RQ, getCOD_EXITO, etc.)
LIB_Util.esql        → utilidades: getErrorCode, copyHttpHeadersFromInput, C8OPxxx (formato), splitCade
LIB_<Servicio>.esql  → lógica de negocio + armado de trama DFDL (armaMensajeTo_AS400*, prepareDataRequestDFDL,
                       prepareCallToCentralizedBackend, convertDfdlToChar, armaRpta*_OK/_ERROR, FormatLoanAmount,
                       validarMensaje, auditoría)
SMF_<S>.esql         → módulos Compute (SMF_<S>_PrepInvocacion, SMF_<S>_PrepRespSrv, SMF_<S>_ControlarError,
                       SMF_<S>_ControlarException) — cada uno es un Compute node
MF_<S>.esql          → utilidades de flujo: MF_<S>_CheckIfReplied, MF_<S>_ApplySecurityHeaders
```
Todos bajo `BROKER SCHEMA ace.esb.<sistema>.<s>`.

## Reglas ESQL (heredadas de `ace-flowpilot/esql-guidelines.md`)
- Preferir funciones sobre procedimientos; `Environment.Schema` para buenas prácticas (no variables globales).
- **No**: `BROKER SCHEMA` en cada archivo (definir según el módulo), `DOUBLE`, `RANDOM`, `CREATE OUTPUTROOT`.
- JSON → XMLNSC: con `CREATE LASTCHILD OF OutputRoot DOMAIN 'JSON'` y `ContentType 'application/json'`.
- La fuente primaria para un mapeo es la rutina equivalente que ya compila en la plantilla corporativa. Copiar esa routine, conservar sus statements y cambiar únicamente los nombres/contratos verificados en SCI/ETI. No inventar una routine ESQL nueva cuando la plantilla ya tiene el patrón.
- Antes de generar un bloque, identificar el path real de entrada, el tipo de cada campo y la cardinalidad. Si el path o la cardinalidad no están documentados, declarar BLOQUEO.

### Navegación XMLNSC y statement `MOVE`
`NEXTSIBLING` es una dirección del statement `MOVE`; no es una función. En el ESQL generado debe aparecer únicamente dentro de una instrucción completa y terminada con `;`:

```sql
MOVE xmlNode NEXTSIBLING;
MOVE xmlNode NEXTSIBLING NAME 'ChildName';
```

No generar estas formas:
- `NEXTSIBLING(...)` o `NEXTSIBLING;` como instrucción independiente.
- `WHILE xmlNode NEXTSIBLING DO`; la condición de recorrido es `WHILE LASTMOVE(xmlNode) DO`.
- `MOVE xmlNode NEXTSIBLING` sin punto y coma seguido de otra instrucción.
- `FOR ... AS path[] DO` para reemplazar un recorrido XMLNSC que la plantilla resuelve con `REFERENCE`, `WHILE LASTMOVE` y `MOVE`.

El recorrido repetido se realiza sobre una referencia declarada al primer hijo real, se procesa el elemento actual y se mueve la referencia al hermano al final de cada iteración. La forma exacta (`[1]`, `NAME`,`*` o helper de la plantilla) debe copiarse de una routine compilada del mismo tipo de dato; no inventar una variante por analogía.

### Reglas de transformación JSON/XMLNSC
- Crear el dominio JSON una sola vez con `CREATE LASTCHILD OF OutputRoot DOMAIN 'JSON' ContentType 'application/json'`.
- Leer escalares con `FIELDVALUE(...)`.
- Para listas, conservar la construcción de array que usa la routine equivalente de la plantilla. `IDENTITY (JSON.Array)` solo se añade cuando esa routine y el dominio de salida lo requieren.
- No concatenar cadenas para representar listas ni cambiar la cardinalidad para hacer que compile.
- Después de cada routine nueva o modificada, verificar la sintaxis de forma estática para asegurar que sea correcta.

### JSON de entrada (root JSON) — sin `BROKER SCHEMA`
```sql
CREATE LASTCHILD OF OutputRoot DOMAIN 'JSON' ContentType 'application/json';
CREATE FIELD OutputRoot.JSON.Data.CentralizedConnector.NamePcml VALUE 'RE0058RI';
```

## Tramas DFDL/PCML
- El copybook COBOL y el contrato del ETI son la fuente de cardinalidad. No corregir un XSD solo para silenciar `CTDV1602E`.
- Revisar cada grupo y elemento repetido: `OCCURS` fijo, `OCCURS ... DEPENDING ON`, `OCCURS *` y grupos opcionales. El XSD debe conservar la semántica del copybook.
- Cuando `occursCountKind` sea `fixed`, `minOccurs` y `maxOccurs` deben representar el mismo valor fijo. Si el copybook define una lista variable o no permite determinar el límite, usar la estrategia DFDL del template o declarar BLOQUEO; no forzar ambos valores a `1`.
- Los **grupos** (elementos `complexType`, p. ej. `LISTADOCOBRANZARSP`) se declaran con `dfdl:lengthKind="implicit"` — su longitud se deriva de los hijos, que sí llevan `dfdl:length=<n>`. NUNCA poner `dfdl:length` en un grupo: el formato DFDL de referencia define `lengthKind="explicit"` por defecto y un grupo sin `lengthKind` explícito dispara `CTDV1210E`.
- Para campos de descripción de errores usar tipo `characters`, nunca `bytes`.
- `CTRLLENGTHCPY.Compute` valida la longitud del mensaje recibido (`C8OPLEN` = `LENGTH(message)`) contra `inputDirectory` del copybook.
- Armado: `prepareDataRequestDFDL` + `StructureDFDL` + `convertDfdlToChar`; lectura: `convertCharToDfdlV2` + navegación `RE0058RIRSP.ELEERR`.

## Auditoría y errores (dentro de ESQL)
```sql
-- auditoría
PROPAGATE TO LABEL getLBL_AUDIT() DELETE NONE;
-- ELK
PROPAGATE TO LABEL getLBL_ELK() DELETE NONE;
-- propagación de error
PROPAGATE TO LABEL getLBL_ERR_LANDING() DELETE NONE;
```
- `prepararMensajeAuditoriaV2(lblTipoACCION, UDP_OPERACION_AC, ...)` genera el JSON de auditoría.
- `getErrorCode()` devuelve el código de error HTTP/builders; `getTIP_RSPTA_2()` el código 202.

## Message Flows (`.msgflow`) y subflows — ver `message-flows/message-flows.md`
- Al generar desarrollo base, los `.msgflow`/`.subflow` se entregan como XML/XMI válido (nunca se omiten ni se difieren al Toolkit). Reglas y plantillas completas: `message-flows/message-flows.md`.
- Estructura XML: `ecore:EPackage → eClassifiers → composition{nodes, connections}`; nodos con atributo `xmi:type` validado (ej. `ComIbmTransform`, `ComIbmWSInput`).
- **Trampa HTTP:** usar `ComIbmWSInput`/`ComIbmWSReply` para HTTP REST (no `ComIbmHTTPInput/Reply`); subflow In/Out con `eflow:FCMSource/FCMSink`.
- Subflows: Input/Output obligatorios; subflows vacíos → Passthrough; nunca en la raíz de una Shared Library.
- `gen/*.msgflow` (dispatcher REST): se genera como XMI en el desarrollo base; el Toolkit lo regenera al compilar (se sobrescribe) → no editarlo a mano en el Toolkit.

## Referencias
- `ace-flowpilot`: `skills/shared/esql-guidelines.md`, `message-flow-rules.md`, `node-types.md`, `subflow-rules.md`.
- Repo C: ESQL real del servicio 153.