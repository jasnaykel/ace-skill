# deployment — Configuración por ambiente, CI/CD y despliegue

## Propósito
Configurar y desplegar un servicio ACE: políticas por ambiente, `valid_cfg_values`, WDO, pipeline Azure DevOps, BAR a Nexus y despliegue CP4I.

## Paquetes por ambiente (convención)
| Ambiente | Configuración | Ejemplo servicio 153 |
|---|---|---|
| DEV | políticas DEV + wdo dev | `src/v1.0/configuration/DEV/` |
| QAS | políticas QAS + wdo qas | `src/v1.0/configuration/QAS/` |
| PRD | políticas PRD + wdo prd | `src/v1.0/configuration/PRD/` |

- Política `PL_UserDefined` (`cod_servicio`, constantes CT-XXX, `destinations` con `srv_info`), `PL_ActiveDirectory` (LDAP GD/GQ/GP), `Monitoring.monprofile.xml`.
- `workdiroverride/wdo-<s>.txt`: instancias (`additionalInstances=10`), `useHTTPS`, timeouts, `URLSpecifiers` (mTLS/onprem), `UDP_OPERACION_GET`, `CTRLLENGTHCPY.inputDirectory`, conector AS400 inicia en `N`.

## `valid_cfg_values.yaml` (fuente de configuración)
- `service`: `<CodigoBIAN>` + `version: v1.0`.
- `ldap`: grupos.
- `wdo.default.app` y `wdo.default.rest`: ver `standards/standards.md` (§ Configuración).
- Es procesado por el pipeline (`ci/` + plantillas `common_components`) para generar los `wdo` y validar consistencia.

## CI/CD (Azure DevOps)
- `azure-pipelines.yml` del Repo C (serverless function en `ci/`): **Validation** (chequea estructura/`valid_cfg_values`) → **ConfigCheck** → **GenerationAndPush** (genera `Monitoring.monprofile.xml` desde `ci/Monitoring.json`).
- La compilación del BAR y la publicación a **Nexus** ocurren en la fábrica (pipeline corporativo), no en el repo del servicio. Frame con LIBs: `LIB_CORE_CONTROL`, `LIB_CORE_COMMON`, `LIB_SMF_UTIL`.
- Naming BAR: `BAR-<N>-<Servicio>-v<v>.bar` (ej. `BAR-153-PayExe-ProRev-Core-Upda-S-v1-0.bar`, repo `dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF`).

## Despliegue CP4I (resumen — ver skill `ace-delivery`)
1. Preparar F01 (doc. de despliegue).
2. Pipeline: build → BAR → Nexus.
3. Desplegar vía utilitario `oc` (CP4I): `oc apply`/ocp config.
4. Subir fuentes a Azure DevOps + Bitbucket del banco.
5. Enviar correo formal de entrega (FASE 5 de `ace-delivery`).

## Regla de configuración
No editar la configuración de runtime directamente en servidores reales; toda la configuración se versiona en `src/v1.0/configuration/*` y se despliega por pipeline/`oc`.

## Referencias
- Skill `ace-delivery` (entrega completa), `ace-framework-setup` (entorno local), `ace-service-dev` (FASE 5).
- Repo C: `azure-pipelines.yml`, `ci/valid_cfg_values.yaml`, `ci/Monitoring.json`.