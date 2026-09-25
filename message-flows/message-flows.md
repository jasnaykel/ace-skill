# message-flows — Generación de `.msgflow` y `.subflow` como XML/XMI (sin ACE Toolkit)

## Propósito
Obligación del agente al generar desarrollo base desde SCI + ETI: generar **también** los archivos `.msgflow` y `.subflow` como documentos XML/XMI válido (EMF), no solo ESQL. Solo quedan para el ACE Toolkit las operaciones de wizard que producen derivados (import de copybook COBOL → DFDL), la regeneración de `gen/*.msgflow` al compilar y el scaffolding de Policy Projects.

## Regla de generación (heredada de `message-flow-rules.md`)
1. Al generar desarrollo base a partir de SCI/ETI, entregar SIEMPRE:
   - Archivos `.esql` (código ESQL).
   - El `.msgflow` principal en XML/XMI (fachada `MF_<S>.msgflow` y dispatcher REST `gen/<S>.msgflow`).
   - Los subflows en XML/XMI (`InputCatchHandler`, `InputFailureHandler`, `InputTimeoutHandler`, `HealthCheck`, `Validate`, `ValidReply`, `<Operación>`).
   - `restapi.descriptor` y `request.schema.json`.
2. **Nunca** omitir los flujos asumiendo que "solo se requiere ESQL". La automatización cubre TODOS los artefactos de la plantilla corporativa.
3. No inventar tipos de nodo ni prefijos de namespace: validar contra el esquema del ACE (`MessageFlow.xsd` + `MessageFlowUI.xsd`, en `C:\Program Files\IBM\ACE\<version>\common\schemas\MessageFlow`).

## Esqueleto canónico (cabecera fija + árbol)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ecore:EPackage xmi:version="2.0"
  xmlns:xmi="http://www.omg.org/XMI"
  xmlns:ecore="http://www.eclipse.org/emf/2002/Ecore"
  xmlns:eflow="http://www.ibm.com/wbi/2005/eflow"
  xmlns:utility="http://www.ibm.com/wbi/2005/eflow_utility"
  xmlns:ComIbmXX.msgnode="ComIbmXX.msgnode" ...  <!-- uno por tipo de nodo usado -->
  nsURI="<ruta-archivo>.msgflow" nsPrefix="<ruta-archivo_snake>.msgflow">
  <eClassifiers xmi:type="eflow:FCMComposite" name="FCMComposite_1" nodeLayoutStyle="SQUARE">
    <eSuperTypes href="http://www.ibm.com/wbi/2005/eflow#//FCMBlock"/>
    <translation xmi:type="utility:TranslatableString" key="<nombre>" bundleName="<nombre>" pluginId="<proyecto>"/>
    <composition> ... <nodes/> ... <connections/> ... </composition>
    <propertyOrganizer/> <stickyBoard/>
  </eClassifiers>
</ecore:EPackage>
```
- `nsURI`/`nsPrefix`: `<archivo>.msgflow` (o `gen/<archivo>.msgflow` / `gen_<archivo>.msgflow`); en subflow `<archivo>.subflow`.
- `pluginId`: `APP_<S>` para la fachada, `<S>` para el servicio.
- `nodeLayoutStyle`: `SQUARE` en los flujos reales del Repo C (fachada y subflows de control); `RECTANGLE` es válido (dispatcher `gen` usa RECTANGLE). Mantener el patrón del Repo C.

## Tabla de tipos de nodo (validados contra ace-flowpilot y Repo C)
| Nodo | `xmi:type` | Atributos clave |
|---|---|---|
| HTTP Input | `ComIbmWSInput.msgnode:FCMComposite_1` | `URLSpecifier` **con `/` inicial**; `useHTTPS="true"` para mTLS; `parseQueryString`, `messageDomainProperty="JSON"`, `faultFormat="JSON"`. Terminales: `out`, `failure`, `timeout`, `catch`. |
| HTTP Reply | `ComIbmWSReply.msgnode:FCMComposite_1` | — |
| HTTP Request | `ComIbmWSRequest.msgnode:FCMComposite_1` | `URLSpecifier` destino, `httpMethod`, `protocol`, `timeoutForServer`, `messageDomainProperty="JSON"`. Terminales: `out`, `failure`, `error`. |
| Compute | `ComIbmCompute.msgnode:FCMComposite_1` | `computeExpression="esql://routine/ace.esb.<sistema>.<s>#<ModuloCompute>.Main"`, `computeMode` (`all`, `destinationAndMessage`, `message`). |
| Route To Label | `ComIbmRouteToLabel.msgnode:FCMComposite_1` | — |
| Label | `ComIbmLabel.msgnode:FCMComposite_1` | `labelName` (lblError, lblAudit, lblELK, lblEncrypt, lblDecrypt, operaciones). |
| Validate | `ComIbmValidate.msgnode:FCMComposite_1` | `domain="JSON"`, `checkDomain`, `checkSet`, `validateMaster="contentAndValue"`. Terminal: `match`, `failure`. |
| Reset Content Descriptor | `ComIbmResetContentDescriptor.msgnode:FCMComposite_1` | `messageDomain="JSON"`, `resetMessageDomain`, `messageSet="{Message model}"`. |
| Pass through | `ComIbmPassthru.msgnode:FCMComposite_1` | — |
| Try Catch | `ComIbmTryCatch.msgnode:FCMComposite_1` | Terminales: `InTerminal.in`, `OutTerminal.try`, `OutTerminal.catch`. |
| Throw | `ComIbmThrow.msgnode:FCMComposite_1` | — |
| Trace | `ComIbmTrace.msgnode:FCMComposite_1` · Log → `ComIbmLog.msgnode` | — |
| Subflow (referencia) | `<Subflow>.subflow:FCMComposite_1` (en broker schema: `ace_esb_core_ope_<X>.subflow:FCMComposite_1`) | `xmlns:<prefijo>.subflow="<ruta>.subflow"`. Terminales `InTerminal.Input`/`Output`, `Output_1`, etc. |
| Subflow In | `eflow:FCMSource` | IDs usuales: `Input` o `InTerminal.Input_1`. |
| Subflow Out | `eflow:FCMSink` | IDs usuales: `Output` o `OutTerminal.Output_1`. |

> **Trampa HTTP:** los nodos "HTTP Input / HTTP Reply / HTTP Request" del Toolkit se serializan con prefijo **`ComIbmWS*`**, NUNCA `ComIbmHTTP*` (esto causa "Message node cannot be located"). El Repo C lo confirma.
> **Reconciliación con `message-flow-rules.md`:** sus plantillas citan `ComIbmRESTInput/ComIbmRESTReply` y `ComIbmSubFlowIn/ComIbmSubFlowOut`. Esos nombres NO son los que emite el Toolkit para flujos HTTP/REST reales: el wizard usa `ComIbmWS*` y `eflow:FCMSource/FCMSink`. Se conserva del archivo la **obligación** de generar flujos y los atributos de nodo; los `xmi:type` se toman de los valores validados (`node-types.md` + Repo C).

## Conexiones
```xml
<connections xmi:type="eflow:FCMConnection" xmi:id="FCMConnection_N"
  targetNode="FCMComposite_X" sourceNode="FCMComposite_Y"
  sourceTerminalName="OutTerminal.out" targetTerminalName="InTerminal.in"/>
```
- Flujo principal: `OutTerminal.out` → `InTerminal.in`.
- Terminales de error: `OutTerminal.failure`.`OutTerminal.error`.`OutTerminal.timeout`.`OutTerminal.catch`.
- Salidas de subflow: `OutTerminal.Output` / `OutTerminal.Output_1`; entrada de subflow: `InTerminal.Input` / `InTerminal.Input_1`.
- `bendPoints` opcional para ajustar el trazado.

## Plantillas por artefacto (patrón del Repo C)
### A. Application fachada — `MF_<S>.msgflow`
Dos `ComIbmWSInput` (mTLS `/v1.0/mtls/<s>...*` con `useHTTPS="true"`; Onprem `/v1.0/onprem/<s>...*`) → `CTRLAUTH` (`SMF_BUS_CORE_SRV_CTRLAUTHAPPV2`, `securityProfileName="{PLP_<S>}:PL_ActiveDirectory"`, UDPs de servicio) → `PreparaRequest` (Compute `SMF_Params.Main`) → HTTP Request interno (`URLSpecifier=<UDP_URL_APIREST>…@path_params`) → `EnsuranceHeaders` (Compute `MF_<S>_ApplySecurityHeaders.Main`) → `ComIbmWSReply`. Ramas `failure/timeout/catch` de los Inputs y `failure/error/out` del Request → `lblError` → `CTRLERROR`; labels `lblAudit`→`CTRLAUDIT`, `lblDecrypt`→`DECRYPT`, `lblELK`→`CTRLELK`. `UDP_URL_APIREST` declarado como `eStructuralFeatures` + `propertyOrganizer` (propiedad configurable).

### B. Dispatcher REST — `gen/<S>.msgflow`
`ComIbmWSInput` (`URLSpecifier="/v1.0/s/...*"`, JSON, faultFormat) → `CTRLINICIAL` (`SMF_BUS_CORE_SRV_CTRLINICIALV2`, `UDP_CODSERVICIO`, `UDP_NOMSERVICIO`, `UDP_USE_CCAS400="S"`) → `RouteToLabel` → por operación un `ComIbmLabel` + nodo `xmi:type="<Operación>.subflow:FCMComposite_1"` (HealthCheck, UpdatePaymentExecutionProcedureReverseCore, …) → `ValidReply` → `ComIbmWSReply`. Handlers del Input: `failure`→InputFailureHandler, `timeout`→InputTimeoutHandler, `catch`→InputCatchHandler. Labels transversales: `lblEncrypt`→`ENCRYPTSRV`, `lblDecrypt`→`DECRYPTSRV`, `lblAudit`→`CTRLAUDIT`, `lblELK`→`CTRLELK`; error→`CTRLERROR` (`UDP_CODSERVICIO`, `UDP_OPERACION_GET`, `UDP_NOMSERVICIO`). `stickyBoard` con la nota "automatically generated… do not edit".

### C. Subflow de operación — `<Operación>.subflow`
`FCMSource` → `Validate` (subflow, `messageSet="request.schema.json"`) → `CTRLLENGTHCPY` (`SMF_BUS_CORE_SRV_CTRLLENGTHCPY`; `inputDirectory` (wdo), `filenamePattern="<PCML>.yaml"`, `UDP_SCHEMA_RSP`, `UDP_SCHEMA_ERR`, `UDP_PCML`) → `PrepInvocacion` (Compute `SMF_<S>_PrepInvocacion.Main`) → `ConectorCentralizado` (`ComIbmWSRequest`, destino centralizado) → `PrepRespSrv` (Compute `SMF_<S>_PrepRespSrv.Main`) → `FCMSink`. Ramas: `failure` de PrepInvocacion y `failure/error` del Request → `ControlarError` (Compute `SMF_<S>_ControlarError.Main`); `failure` de PrepRespSrv → `ControlarException` (Compute `SMF_<S>_ControlarException.Main`) → `FCMSink`.

### D. Subflows de soporte
- `HealthCheck.subflow`: `FCMSource` → `SMF_ESB_UTIL_HEALTH_CHECK_IBS` (`UDP_PLP_SERVICE_HEALTH_CHECK="{PLP_<S>}:PL_UserDefined"`, `UDP_OPERACION_GET`) → `FCMSink`.
- `Validate.subflow`: `FCMSource` → `RCD` (Reset Content Descriptor JSON, `messageSet` promovido vía `attributeLinks`) → `Validate` (`validateMaster="contentAndValue"`, match→out) → `FCMSink`.
- `ValidReply.subflow`: `FCMSource` → `CheckIfReplied` (Compute `MF_<S>_CheckIfReplied.Main`) → `ApplySecurityHeaders` (Compute `MF_<S>_ApplySecurityHeaders.Main`) → `FCMSink`.
- `*Input{Catch,Failure,Timeout}Handler.subflow`: `FCMSource` → `CTRLERROR` (subflow framework, UDPs de servicio) → `FCMSink`.

## Reglas operativas
- **Simplicidad:** mínimo de nodos trazables; un enlace directo Input→Reply es válido para echo/passthrough. Sin nodos "por si acaso".
- `computeExpression`: si el `.esql` está en broker schema, usar `esql://routine/ace.esb.<sistema>.<s>#<Modulo>.Main` (referencia al MODULE, no al archivo).
- Subflows del framework (LIB_CORE_COMMON/CONTROL, SMF_ESB_UTIL): únicamente referenciarlos; NUNCA copiar su contenido ni modificarlos (`ace/esb/core/ope/...`, `ace/esb/smf/util/...`).
- Tras generar, la compilación en el Toolkit puede regenerar `gen/<S>.msgflow` (se sobrescribe) — comportamiento esperado; el desarrollo base ya lo incluye.
- Al resolver un atributo desconocido: buscar la descripción en `MessageFlowUI.xsd` → obtener el id de propiedad → nombre real en `MessageFlow.xsd` → tipo/dato/default.

## Referencias
- `<FLOWPILOT_ROOT>/skills/shared/`: `node-types.md` (mapa canónico), `message-flow-rules.md`, `ExampleApplication/Example.msgflow`, `ExampleAPI/gen/ExampleAPI.msgflow`, `ExampleAPI/*.subflow`.
- Repo C (plantilla): implementación real de los 9 flujos del servicio 153.
- Archivo determinante descargado: `message-flow-rules.md` (obligación XMI) + `template-blueprint.md` (formato XMI obligatorio de todo flujo).
