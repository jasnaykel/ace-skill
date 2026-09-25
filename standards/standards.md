# standards — Estándares y convenciones de la fábrica

## Propósito
Reglas de nombrado, estructura y configuración que todo desarrollo generado debe cumplir (Regla 3 de la skill maestra).

## Nomenclatura
| Elemento | Convención | Ejemplo |
|---|---|---|
| Aplicación fachada | `APP_<Servicio>` | `APP_PayExe_ProRev_Core_Upda_S` |
| Flujo fachada | `MF_<Servicio>.msgflow` | `MF_PayExe_ProRev_Core_Upda_S.msgflow` |
| Flujo generado REST | `gen/<Servicio>.msgflow` (no editar) | `gen/PayExe_ProRev_Core_Upda_S.msgflow` |
| Lógica de negocio | `LIB_<Servicio>.esql` | `LIB_PayExe_ProRev_Core_Upda_S.esql` |
| Constantes | `LIB_Constants.esql` (`C_*`) | `C_OPERATION_RQ`, `C_PLP_SERVICE` |
| Utilidades | `LIB_Util.esql` | `getErrorCode`, `copyHttpHeadersFromInput` |
| Compute modules | `SMF_<Servicio>_<Etapa>` | `SMF_PayExe_ProRev_Core_Upda_PrepInvocacion` |
| Utilidades de flujo | `MF_<Servicio>_<Util>` | `MF_PayExe_ProRev_Core_Upda_CheckIfReplied` |
| Policy project | `PLP_<Servicio>` · políticas `PL_*` | `PLP_...:PL_UserDefined`, `:PL_ActiveDirectory` |
| Workdir override | `wdo-<servicio-hyphen>.txt` | `wdo-payexe-prorev-core-upda-s.txt` |
| Handlers | `<Servicio>Input{Catch,Failure,Timeout}Handler` | — |
| BAR | `BAR-<Num>-<Servicio>-v<v>.bar` | `BAR-153-PayExe-ProRev-Core-Upda-S-v1-0.bar` |
| Capas | sufijos `-s` (sistema), `-b` (negocio), `-x` (experiencia) | — |

## Estructura de proyectos
- **Application:** `.project` con 2 natures; `application.descriptor` con `<sharedLibraryReference>` (LIB_CORE_CONTROL, LIB_CORE_COMMON, LIB_SMF_UTIL); `.settings/org.eclipse.core.resources.prefs`.
- **REST Service (v1.0/service):** `.project` (3 natures) + `restapi.descriptor` + OpenAPI + `gen/*.msgflow` + subflow por operación; `faultFormat="JSON"`.
- **Policy:** `.project` (nature de políticas) + `policy.descriptor`; políticas SIEMPRE en policy project.
- Subflows en Shared Library van en subdirectorio (broker schema), nunca en la raíz.

## Reglas de desarrollo (siempre)
| Regla | Valor |
|---|---|
| Timeouts | backend `16 s` · servidor `17 s` · cliente `16–18 s` |
| Protocolo backend | `TLSv1.3` |
| Instancias WDO | mínimo `10` (`additionalInstances`) |
| Conector AS400 | inicia en `N` |
| Exposición | `mTLS` (externa) + `Onprem` (interna) |
| Framework | **nunca** modificar `LIB_CORE_*` ni `LIB_SMF_*` |
| Logging | CloudWatch + ELK según `ace-logging` (códigos 10/20/30/40/50/60) |
| Error de campo | HTTP 202 en capa entrada; error funcional ≠ técnico |

## Configuración por ambiente (`valid_cfg_values.yaml`)
- `service`: `<CodigoBIAN>` + `version: v1.0`.
- `ldap`: grupos por ambiente (`..._GD`, `..._GQ`, `..._GP`).
- `wdo.default.app`: `mTLS.useHTTPS=yes`, `Onprem.useHTTPS=no`, timeouts, URLSpecifiers `/v1.0/mtls|<tipo>|...` y `/v1.0/onprem/...`, `UDP_URL_APIREST`, `UDP_OPERACION_GET`.
- `wdo.default.rest`: `HTTP Input.useHTTPS=yes`, `timeoutForClient`, `CTRLINICIAL.UDP_USE_CCAS400`, `UDP_OPERACION_GET`.
- `destinations`: primero `health` (CentralizedConnector health), luego backends con `srv_info.{TECHNICAL_SRV_NAME, PROGRAM, PCML, TIMEOUT}`.

## BIAN
Path canónico: `v1.0/s/<servicedomain>/<controlrecord>/<subqualifier>/<actionterm>` (ej. `v1.0/s/paymentexecution/procedurereverse/core/update`), expuesto con prefijos `mtls` y `onprem`.

## Referencias
- Detalle: `Documentacion_Skills_IBM_ACE.md`, `Informe_Ejecucion_Prompt_Maestro_IBM_ACE.md` (workspace `Documents\AI`).
- Guías de artefactos: `ace-flowpilot` (`skills/shared/*.md`).