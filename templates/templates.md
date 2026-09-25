# templates — Plantilla corporativa (fuente de verdad estructural)

## Propósito
Definir cómo usar el repositorio plantilla para generar desarrollos, qué contiene y cómo normalizarlo antes de reutilizarlo.

## Repositorio plantilla canónico
- **URL de Repositorio:** `https://github.com/Karinadr/plantillas-AI/tree/IBS`
- **Rama:** `IBS`
- **Servicio de referencia:** `153_BUS_PayExe_ProRev_Core_Upda_S` — BUS atómico que consume el RPG `RE0058RI` (IBS) vía Backend Centralizado (`IN2100RI`).
- **Uso:** El agente debe clonar este repositorio y rama de forma local en un directorio temporal para usarlo como la única fuente de verdad y estructura.

## Resolución de Plantilla (Git-First)
Antes de iniciar la generación:
1. Clonar de forma local la plantilla mediante:
   ```bash
   git clone --branch IBS --single-branch https://github.com/Karinadr/plantillas-AI.git <TEMPLATE_ROOT>
   git -C <TEMPLATE_ROOT> rev-parse --verify HEAD
   git -C <TEMPLATE_ROOT> ls-tree -r --name-only HEAD
   ```
2. Usar `<TEMPLATE_ROOT>` como el directorio de referencia y analizar su árbol real antes de generar.
3. Registrar el commit utilizado. Todos los archivos y estructuras generados deben basarse con un 100% de fidelidad en este repositorio clonado. No inventar nombres de carpetas, de subflows ni de convenciones. No buscar archivos en otros workspaces o rutas fuera del clon de esta plantilla.

## Repositorio técnico complementario
La plantilla IBS se complementa con las guías técnicas de `ace-flowpilot`:
- **URL:** `https://github.com/ot4i/ace-flowpilot/tree/main`
- **Rama:** `main`
- **Clonado:** `git clone --branch main --single-branch https://github.com/ot4i/ace-flowpilot.git <FLOWPILOT_ROOT>`
- **Uso:** analizar el árbol real y consultar solo los archivos aplicables. Registrar el commit; no asumir rutas ni inventar contenido si una guía no existe.

## Estructura que define la plantilla (patrón fijo)
```
src/application/APP_<S>/        Fachada: .project (Eclipse), MF_<S>.msgflow (mTLS+Onprem→LDAP→HTTP Request interno),
                                LIB_APP_<S>.esql (UDP_URL_APIREST), MF_<S>_ApplySecurityHeaders.esql
src/v1.0/service/<S>/           REST service: .project (Eclipse), <S>.yaml (OpenAPI), restapi.descriptor,
                                request.schema.json, gen/<S>.msgflow (no editar),
                                HealthCheck|Validate|ValidReply|<Operación>.subflow,
                                <S>Input{Catch,Failure,Timeout}Handler.subflow,
                                <PCML>.{cpy,yaml,xsd} + importFiles/ + IBMdefined/ + log/,
                                ace/esb/<s>/**/{LIB_Constants,LIB_<S>,LIB_Util,SMF_<S>,MF_<S>}.esql
src/v1.0/configuration/{DEV,QAS,PRD}/   policyproject/PLP_<S>/{PL_UserDefined, PL_ActiveDirectory,
                                        Monitoring.monprofile.xml} + workdiroverride/wdo-<s>.txt
ci/                             valid_cfg_values.yaml + Monitoring.json
test/                           <S>.postman_collection.json
azure-pipelines.yml             pipeline por plantillas common_components
```

## Blueprint estricto (Regla Fundamental de Fidelidad — heredada de `template-blueprint.md`)
- El agente **NUNCA** inventa estructuras de carpetas, nombres de archivos, subflows ni convenciones: todo desarrollo generado replica con **100% de exactitud** la arquitectura y distribución de la plantilla.
- Árbol obligatorio (por capa):
  - `src/application/APP_<S>/`: `<S>.yaml` (fachada), `MF_<S>.msgflow`, `application.descriptor`, **`.project`**, `ace/esb/<path>/{MF_<S>_ApplySecurityHeaders, LIB_APP_<S>}.esql`.
  - `src/v1.0/service/<S>/`: subflows `ValidReply`, `Validate`, `<S>`, `<S>Input{Catch,Failure,Timeout}Handler`, `HealthCheck`; `restapi.descriptor`, `request.schema.json`, `<BackendProgram>.{yaml,xsd,cpy}`, `<S>.yaml` (OpenAPI), **`.project`**, `ace/esb/<path>/{SMF_<S>, MF_<S>, LIB_Util, LIB_<S>, LIB_Constants}.esql`, `gen/<S>.msgflow`, artefactos DFDL `IBMdefined/`, `importFiles/`, `log/`.
  - `src/v1.0/configuration/{DEV,QAS,PRD}/` (policyproject `PLP_<S>` + wdo) y `test/<S>.postman_collection.json`.
- **Metadatos Eclipse (`.project`) obligatorios en ambas capas**, replicados exactamente de la plantilla (buildSpec + natures):
  - `APP_<S>/.project`: natures `applicationNature` + `messageBrokerProjectNature`; 19 build commands (applibbuilder, …, sin `javabuilder` ni `StandardBrokerModelBuilder`).
  - `<S>/.project` (REST service): 3 natures (`restapi.ui.Nature` + las 2 anteriores) con build commands de REST API (restApiBuilder, restApiDefinitionsBuilder, policybuilder, dfdl builders, esql builder, msgflow builder, …).
- **Subflows obligatorios** en cada servicio: `InputTimeoutHandler`, `InputFailureHandler`, `InputCatchHandler`, `ValidReply`, `Validate`, `HealthCheck` (+ `<Operación>`).
- **Normas inquebrantables:** NUNCA modificar `LIB_CORE_COMMON`, `LIB_CORE_CONTROL`, `LIB_SMF_UTIL` (ni sus subflows); la lógica de negocio exclusiva va solo en `LIB_<S>.esql` y `LIB_Constants.esql`.
- **Formato de flujos:** todo `.msgflow`/`.subflow` se genera como XML/XMI válido según `message-flows/message-flows.md` (topología de la plantilla).
- **`<S>.yaml` de la fachada (`APP_<S>/`) es OBLIGATORIO y se genera SIEMPRE** como OpenAPI 3.0 (YAML) con el contrato real de la fachada y **UNA sola stanza `servers`** con la vía de acceso base del API: `/v1.0/s/<carpeta>...` (la misma del backend/operación, p. ej. `/v1.0/s/paymentexecution/procedurereverse/core/update`); paths `/` (operación) y `/health` (HealthCheck), parámetros de cabecera Bif y schemas Request/Response/Error del contrato del servicio. ⛔ **NUNCA múltiples stanzas de servidor** (el builder de REST API Definitions del Toolkit rechaza varias vías base —error: "contains several server stanzas with different base paths"): los canales mTLS/onprem son detalle de los nodos WSInput (`URLSpecifier`) del msgflow de fachada, no stanzas del OpenAPI. ⛔ La copia del Repo C es un placeholder de OTRA plantilla ("Term Deposit") → **nunca copiarla tal cual**; regenerar el contenido desde msgflow + contrato.
- Desviación respecto al blueprint/plantilla → justificar y **declarar** (nunca silenciosa).

## Contenido clave a copiar/servir de referencia
| Archivo | Para qué |
|---|---|
| `valid_cfg_values.yaml` | Estructura service/ldap/wdo (app y rest) |
| `PL_UserDefined.policyxml` | `cod_servicio`, CT-XXX, `destinations` (health + main) con `srv_info` |
| `LIB_<S>.esql` | Copiar la routine equivalente que compila y parametrizar solo los campos/paths verificados; conservar la semántica de `NEXTSIBLING`, arrays y DFDL de la plantilla |
| DFDL/XSD derivado del copybook | Conservar la cardinalidad del copybook: `fixed` con `minOccurs == maxOccurs`; ocurrencias variables según la estrategia validada del template |
| `SMF_<S>.esql` | Módulos Compute: PrepInvocacion / PrepRespSrv / ControlarError / ControlarException |
| `MF_<S>.esql` | CheckIfReplied + ApplySecurityHeaders |
| `gen/<S>.msgflow` + subflows | Patrón del dispatcher REST y subflows de control |
| `ci/Monitoring.json` + monprofile | Eventos de monitoreo 10–60 |
| Postman | Requests por ambiente (MTLS/DEV/QAS/PRD, Onprem) |

## Normalización obligatoria antes de reutilizar como plantilla genérica
- [ ] Reemplazar el contenido del `APP_<S>/<S>.yaml` (placeholder "Term Deposit" del Repo C) por la **fachada real** (canales mTLS/onprem del msgflow + schemas del contrato); eliminar residuos: `.cpy` (`DL0743RI`), `.scannerwork/` (SonarQube), funciones sin uso (`isLoanRecordWithData`, `getDateValue`).
- [ ] Reemplazar valores de ejemplo (`localhost` en HTTP Request, URL `svc-078-...`) por placeholders.
- [ ] Quitar prefijo `153_` de rutas de runtime (`CTRLLENGTHCPY.inputDirectory`) → `<S>`.
- [ ] Verificar que el contrato OpenAPI coincida con el servicio real (no otro negocio).
- [ ] En ESQL, conservar la routine base que compila y cambiar únicamente los campos/contratos verificados; no reconstruir navegación `NEXTSIBLING` ni arrays desde suposiciones.
- [ ] En DFDL, comparar el XSD con el copybook real; no forzar `minOccurs == maxOccurs` si el original representa una ocurrencia variable.

## Cómo crear el árbol de un nuevo servicio `<Servicio>`
1. Copiar la estructura de Repo C (normalizada).
2. Aplicar el renombrado y la parametrización de `generation-workflow/generation-workflow.md` (Paso 3).
3. Rellenar contrato, mapeos, políticas y wdo desde el SCI/ETI.
4. Conservar el patrón de auditoría/ELK/seguridad intacto.
5. Generar `MF_<S>.msgflow`, `gen/<S>.msgflow` y los subflows como XML/XMI según `message-flows/message-flows.md` (replicando la topología de Repo C).
6. Generar los `.project` (buildSpec/natures exactos de la plantilla por capa) y copiar los ESQL y artefactos DFDL/PCML reales de la plantilla como base (normalizando residuos, sin cambiar nombres de rutinas/módulos).
7. Generar `APP_<S>/<S>.yaml` (OpenAPI de la fachada) con **UNA sola stanza `servers`** (vía base `/v1.0/s/...` de la operación) y los schemas del contrato del servicio; los canales mTLS/onprem se documentan SOLO como descripción (ver regla de reconciliación arriba).
