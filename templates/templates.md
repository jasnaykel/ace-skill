# templates — Plantillas corporativas (fuente de verdad estructural)

## Propósito
Definir cómo usar el repositorio plantilla para generar desarrollos, qué contiene y cómo normalizarlo antes de reutilizarlo.

## Selección de plantilla
El agente debe seleccionar exactamente una plantilla según el encabezado del `ETI.md`. La rama y el subdirectorio deben permanecer aislados; nunca combinar archivos entre `IBS` y `HUB`.

| Dominio | URL | Rama | Subdirectorio de plantilla |
|---|---|---|---|
| `IBS` | `https://github.com/Karinadr/plantillas-AI/tree/IBS/app213-payexe-prorev-core-upda-s-ops-ace` | `IBS` | `app213-payexe-prorev-core-upda-s-ops-ace` |
| `HUB` | `https://github.com/Karinadr/plantillas-AI/tree/HUB/app213-payexe-prorev-hub-upda-s-ops-ace` | `HUB` | `app213-payexe-prorev-hub-upda-s-ops-ace` |

### Encabezados selectores del ETI
| Encabezado Markdown del ETI | Plantilla que debe utilizarse |
|---|---|
| `# Componente IBS` | Fila `IBS` de la matriz anterior |
| `# Componente API REST` | Fila `HUB` de la matriz anterior |

No seleccionar por semejanza semántica ni por datos encontrados en otra sección. Si el encabezado no coincide exactamente después de normalizar espacios, detener el flujo con **BLOQUEO**.

Para `IBS`, el servicio de referencia es el BUS atómico que consume el RPG `RE0058RI` mediante Backend Centralizado. Para `HUB`, no asumir contratos, backend, códigos ni convenciones IBS: leer el contenido real de la plantilla `HUB`.

## Resolución de Plantilla (Git-First)
Antes de iniciar la generación:
1. Determinar el dominio exclusivamente con el encabezado selector del `ETI.md`, según la tabla anterior. No usar la solicitud, el `SCI.md`, el nombre del servicio ni una inferencia técnica para elegir la plantilla.
2. Clonar el repositorio en una carpeta temporal del dominio mediante:
   ```bash
   git clone --branch <BRANCH> --single-branch https://github.com/Karinadr/plantillas-AI.git <TEMPLATE_REPO_ROOT>
   git -C <TEMPLATE_REPO_ROOT> rev-parse --verify HEAD
   git -C <TEMPLATE_REPO_ROOT> ls-tree -r --name-only HEAD
   git -C <TEMPLATE_REPO_ROOT> ls-tree -d --name-only HEAD -- <SUBDIRECTORIO_SELECCIONADO>
   ```
3. Resolver `<TEMPLATE_ROOT>` como `<TEMPLATE_REPO_ROOT>/<SUBDIRECTORIO_SELECCIONADO>` y analizar tanto el árbol del repositorio como el subdirectorio real.
4. Registrar dominio, URL, rama, subdirectorio y commit utilizado. Todos los archivos y estructuras generados deben basarse con un 100% de fidelidad en `<TEMPLATE_ROOT>`. No inventar nombres de carpetas, de subflows ni de convenciones. No buscar archivos en otros workspaces o rutas fuera del clon de la plantilla seleccionada.
5. Si el comando de verificación no encuentra el subdirectorio seleccionado, declarar **BLOQUEO** y solicitar que se publique la plantilla en esa rama. No sustituirla automáticamente por la plantilla histórica de IBS ni por archivos de otra rama.

## Repositorio técnico complementario
La plantilla seleccionada se complementa con las guías técnicas de `ace-flowpilot`:
- **URL:** `https://github.com/ot4i/ace-flowpilot/tree/main`
- **Rama:** `main`
- **Clonado:** `git clone --branch main --single-branch https://github.com/ot4i/ace-flowpilot.git <FLOWPILOT_ROOT>`
- **Uso:** analizar el árbol real y consultar solo los archivos aplicables. Registrar el commit; no asumir rutas ni inventar contenido si una guía no existe.

## Documentación global
`templates/readme-eti-template.md` es la plantilla documental corporativa global para todos los desarrollos `IBS` y `HUB`. La estructura del README no cambia por rama; sus datos, backend, componente, contratos, endpoints, seguridad y demás valores deben completarse desde el `SCI.md`, `ETI.md` y la plantilla seleccionada.

## Estructura de la plantilla seleccionada
No existe un árbol universal válido para `IBS` y `HUB`. El árbol, archivos, proyectos, subflows, políticas y convenciones del subdirectorio seleccionado son la única estructura obligatoria. La siguiente lista es una guía de artefactos que puede existir en una plantilla, no una estructura para inventar:
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

## Blueprint estricto de la plantilla seleccionada
- El agente **NUNCA** inventa estructuras de carpetas, nombres de archivos, subflows ni convenciones: todo desarrollo generado replica con **100% de exactitud** la arquitectura y distribución de la plantilla seleccionada.
- Si la plantilla seleccionada contiene las siguientes capas, conservarlas así:
  - `src/application/APP_<S>/`: `<S>.yaml` (fachada), `MF_<S>.msgflow`, `application.descriptor`, **`.project`**, `ace/esb/<path>/{MF_<S>_ApplySecurityHeaders, LIB_APP_<S>}.esql`.
  - `src/v1.0/service/<S>/`: subflows `ValidReply`, `Validate`, `<S>`, `<S>Input{Catch,Failure,Timeout}Handler`, `HealthCheck`; `restapi.descriptor`, `request.schema.json`, `<BackendProgram>.{yaml,xsd,cpy}`, `<S>.yaml` (OpenAPI), **`.project`**, `ace/esb/<path>/{SMF_<S>, MF_<S>, LIB_Util, LIB_<S>, LIB_Constants}.esql`, `gen/<S>.msgflow`, artefactos DFDL `IBMdefined/`, `importFiles/`, `log/`.
  - `src/v1.0/configuration/{DEV,QAS,PRD}/` (policyproject `PLP_<S>` + wdo) y `test/<S>.postman_collection.json`.
- **Metadatos Eclipse (`.project`) obligatorios en ambas capas**, replicados exactamente de la plantilla (buildSpec + natures):
  - `APP_<S>/.project`: natures `applicationNature` + `messageBrokerProjectNature`; 19 build commands (applibbuilder, …, sin `javabuilder` ni `StandardBrokerModelBuilder`).
  - `<S>/.project` (REST service): 3 natures (`restapi.ui.Nature` + las 2 anteriores) con build commands de REST API (restApiBuilder, restApiDefinitionsBuilder, policybuilder, dfdl builders, esql builder, msgflow builder, …).
- **Subflows, módulos, DFDL/PCML, ELEERR, mTLS/Onprem, LDAP y OpenAPI** son obligatorios solo si existen en la plantilla seleccionada o si el ETI los exige. No transferir reglas específicas de IBS a HUB.
- **Formato de flujos:** todo `.msgflow`/`.subflow` que exista en la plantilla se genera como XML/XMI válido según `message-flows/message-flows.md`, conservando la topología real de la plantilla.
- La documentación de archivos de ejemplo no autoriza a crear archivos ausentes en la plantilla seleccionada.
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

## Normalización obligatoria de la plantilla seleccionada
- [ ] Reemplazar placeholders, contratos, nombres, rutas, endpoints y valores de ejemplo únicamente en los archivos que existan en `<TEMPLATE_ROOT>`.
- [ ] Eliminar residuos de ejemplo solo cuando estén presentes y se haya confirmado que no forman parte del patrón real de la plantilla seleccionada.
- [ ] Verificar que el contrato, políticas, ESQL, DFDL/PCML, OpenAPI y pruebas coincidan con el servicio real y el ETI.
- [ ] En ESQL, conservar la routine base que compila y cambiar únicamente los campos/contratos verificados; no reconstruir navegación ni arrays desde suposiciones.
- [ ] En DFDL/PCML, comparar el esquema con el copybook real solo si la plantilla seleccionada utiliza ese artefacto.

## Cómo crear el árbol de un nuevo servicio `<Servicio>`
1. Copiar la estructura de `<TEMPLATE_ROOT>` (normalizada).
2. Aplicar el renombrado y la parametrización de `generation-workflow/generation-workflow.md` (Paso 3).
3. Rellenar contrato, mapeos, políticas y wdo desde el SCI/ETI.
4. Conservar el patrón de auditoría/ELK/seguridad que exista en la plantilla seleccionada.
5. Generar los flujos y subflows que existan en la plantilla como XML/XMI según `message-flows/message-flows.md`, replicando su topología real.
6. Generar los `.project`, ESQL, DFDL/PCML, políticas, contratos y pruebas solo cuando existan en la plantilla seleccionada, conservando sus nombres y convenciones.
7. Generar o parametrizar OpenAPI solo si existe en la plantilla seleccionada o lo exige el ETI; conservar sus reglas de `servers` y no imponer una fachada de IBS a HUB.
