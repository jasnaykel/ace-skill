# service-dev — Ciclo completo de desarrollo de servicios IBM ACE (Fábrica BanBif)

## Propósito
Ciclo de desarrollo de servicios IBM ACE desde la generación de plantilla hasta el despliegue en CP4I. Complementa a `generation-workflow` (que convierte SCI/ETI en desarrollo base) con el proceso operativo en Toolkit y la configuración de entorno.

> Stack: IBM ACE 12.0.x · IBM MQ 9.x · CP4I / OpenShift · Azure DevOps · Bitbucket
> Repositorios framework: `core` · `subflows` · `policies` · `core_utils` · `creatorApp-java`

## Cuándo usar este módulo
| Situación | Acción |
|---|---|
| Nuevo servicio atómico desde cero | Seguir todas las fases en orden |
| Nuevo servicio orquestador | Este módulo + `@bian-nomenclature` para el mapeo |
| Solo configurar `valid_cfg_values` | Ir directo a FASE 5 |
| Solo configurar `server.conf.yaml` / MQ local | Ir directo a FASE 4 |
| Solo validar flows en Toolkit | Ir directo a FASE 2 |

---

## FASE 0 — Gate de entrada (insumos obligatorios)
> ⛔ Sin estos documentos **no iniciar**. Coordinar con el Líder Técnico.

- [ ] **DETI** — Documento de Especificaciones Técnicas de Integración
- [ ] **FSS / SCI** — Formato de Solicitud de Servicios con: nombre técnico, operaciones, campos entrada/salida, sistemas backend
- [ ] **Nomenclatura BIAN aprobada** → ver `@bian-nomenclature`
- [ ] **ETI firmado** → arquitectura, seguridad (LDAP/mTLS), infra (URLs por ambiente)

---

## FASE 1 — Generación de plantilla seleccionada

### Fuente canónica
La plantilla no se obtiene desde `Z:\Java` ni desde una copia local preexistente. Seleccionar `IBS` o `HUB` según el servicio y clonar la rama correspondiente. Para ambos dominios, la plantilla está en `app213-terdep-pay-exec-s-ace`:

```cmd
git clone --branch <BRANCH> --single-branch https://github.com/Karinadr/plantillas-AI.git <TEMPLATE_REPO_ROOT>
git -C <TEMPLATE_REPO_ROOT> ls-tree -r --name-only HEAD
<TEMPLATE_ROOT> = <TEMPLATE_REPO_ROOT>\app213-terdep-pay-exec-s-ace
```

Usar únicamente `<TEMPLATE_ROOT>` como fuente de estructura y archivos base. Confirmar el dominio, rama, subdirectorio y commit antes de generar y registrar la versión utilizada. Las rutas locales solo pueden ser el destino temporal del clon, nunca una fuente de verdad distinta.

### Opción A: Techzone (recomendada)
**Paso 1 — Completar el Excel *Template ACE*:**
- Hoja `Datos Generales`: nombre servicio, versión, `num_operaciones` (define cuántas hojas `ItemX` habrá)
- Por cada operación: hoja `Item1`, `Item2`…
  - `Header` → campos de cabecera HTTP
  - `Consumidor` → campos del body de entrada (request)
  - `Productor (Éxito)` → campos del body de salida (response exitoso)
  - `Servicio (Error)` → campos de error
- Columna **Ubicación**: GET con query params → `query`; GET con path params → `path`
- Arreglos/listas: notación `[]` → ej: `Organisation[]/JobTitle`
- Columna **Ejemplo**: opcional; se usa en el OpenAPI y en la collection Postman generada

**Paso 2 — Ejecutar Postman `Generate_APP+Collection`:**
```
URL: https://creator-app-cdt-interop-tools.apps.68f1e891a62483ab9217f05f.am1.techzone.ibm.com/api/projects/create/all
Body: form-data → adjuntar el archivo Excel
```
Descargar el ZIP → descomprimir → importar en Toolkit.

### Opción B: CreatorApp legado
No usar esta opción para desarrollo IBS o HUB. Solo aplica si el usuario solicita explícitamente ejecutar CreatorApp local para una generación histórica; en ese caso consultar la configuración de `framework-setup/framework-setup.md`.

---

## FASE 2 — Validación en IBM ACE Toolkit

### Importar fuentes
1. Importar repositorios del framework: `core`, `subflows`, `policies`, `core_utils`
2. Importar la plantilla generada (descomprimida)

### Checklist de validación — API Rest
- [ ] HTTPS habilitado en el descriptor del API Rest (pestaña Description → Security → HTTPS ✅)
- [ ] Message Flow usa el framework (nodo principal conectado al core)
- [ ] `HTTP_Input` tiene HTTPS habilitado
- [ ] SubMessageFlow `HealthCheck` → diseño estándar
- [ ] SubMessageFlow `CatchHandler` → llama al **Controlador Error del framework**
- [ ] SubMessageFlow `FailureHandler` → llama al **Controlador Error del framework**
- [ ] SubMessageFlow `TimeOutHandler` → llama al **Controlador Error del framework**
- [ ] SubMessageFlow de cada operación tiene todos los nodos necesarios

### Archivos que debes modificar (solo estos dos)
```
LIB_<NombreServicio>.esql    ← lógica de negocio de la operación
LIB_Constants.esql           ← constantes del servicio (valores fijos)
```
> ⚠️ **NUNCA** modificar: `LIB_CORE_COMMON`, `LIB_CORE_CONTROL`, `LIB_SMF_UTIL` ni ningún archivo del framework.

---

## FASE 3 — DFDL (solo si el backend es AS400 / Mainframe)
Generar desde el Toolkit → New → Message Model → DFDL:
1. Seguir los 8 pasos del wizard usando el copybook real del servicio.
2. Antes de validar, comparar cada grupo repetido con el `OCCURS` del copybook y con la cardinalidad del ETI. No asumir que todos los grupos son de tamaño fijo.
3. Para `occursCountKind="fixed"`, conservar el mismo valor en `minOccurs` y `maxOccurs`. Para `OCCURS ... DEPENDING ON` o `OCCURS *`, conservar la estrategia de ocurrencia variable de la plantilla o declarar BLOQUEO; no convertir el grupo a `fixed` solo para eliminar `CTDV1602E`.
4. Todo **grupo** (`complexType`) se declara con `dfdl:lengthKind="implicit"` (longitud derivada de los hijos, cada uno con su `dfdl:length`). No poner `dfdl:length` en un grupo; el default del formato (`lengthKind="explicit"`) dispara `CTDV1210E` al no tener `length`.
5. **CRÍTICO en paso 8**: los campos de descripción de errores deben ser tipo `characters`, NO `bytes`.
6. Ejecutar la validación DFDL del Toolkit. Si aparece `DFDL Validation Problem`, comparar con el copybook y corregir la cardinalidad o el `lengthKind`; no cambiar valores a ciegas.
7. Registrar el resultado de validación y conservar el XSD validado junto con el servicio.

---

## FASE 4 — Configuración local para pruebas

### 4.1 Crear Integration Server local
Toolkit → New → Integration Server → asignar nombre y puerto.

### 4.2 `server.conf.yaml`
```yaml
RestAdminListener:
    port: 7600
ResourceManagers:
  HTTPConnector:
    ListenerPort: 7800
  JVM:
    jvmDebugPort: 9997
```

### 4.3 Cola de auditoría IBM MQ
```cmd
crtmqm <nameQmgr>
strmqm <nameQmgr>
dspmq                            # debe aparecer como Running

runmqsc <nameQmgr>
  define ql('IB.InternalAudit.REQ.01')
  alter qmgr deadq (SYSTEM.DEAD.LETTER.QUEUE)
  end
```
Agregar en `server.conf.yaml`:
```yaml
defaultQueueManager: '<nameQmgr>'
```

### 4.4 Recursos mínimos desplegados (siempre)
| Tipo | Nombre |
|---|---|
| Library | `LIB_CORE_COMMON` |
| Library | `LIB_CORE_CONTROL` |
| Library | `LIB_SMF_UTIL` |
| Policy | `PLP_AS400` |
| Policy | `PLP_LIB_COMMON_CIPHER` |
| Policy | `PolicyLogs` |

### 4.5 Generar y desplegar BAR File
1. Toolkit → New → BAR File → seleccionar Library del servicio → compilar
2. Configurar BAR: desactivar HTTP listener (solo HTTPS para pruebas locales)
3. Drag & drop del `.bar` sobre el Integration Server local
4. Verificar en consola que levanta sin errores

---

## FASE 5 — Archivo `valid_cfg_values` (configuración por ambiente)

### Sección `service`
```yaml
service: "<CodigoBIAN>"      # ej: PayMan_Dis_Natr_Exec_B
version: "v1.0"
```

### Sección LDAP
```yaml
ldap:
  DEV: "<NOMBRE_SERVICIO_GD>"   # grupo AD para DEV
  QAS: "<NOMBRE_SERVICIO_GQ>"   # grupo AD para QAS/UAT
  PRD: "<NOMBRE_SERVICIO_GP>"   # grupo AD para PRD
```

### Sección WDO — app
```yaml
wdo.default.app.additionalInstances: "10"
wdo.default.app.mTLS.useHTTPS: "yes"
wdo.default.app.Onprem.useHTTPS: "no"
wdo.default.app.HTTP Request.timeoutForServer: "17"
wdo.default.app.mTLS.timeoutForClient: "18"
wdo.default.app.Onprem.timeoutForClient: "18"
wdo.default.app.CTRLAUTHAPP.UDP_USE_CCAS400: "S"   # valor por ETI/plantilla 153; ejemplos históricos usan "N"
wdo.default.app.mTLS.URLSpecifier: "/v1.0/mtls/<tipo>/<ruta-bian>*"
wdo.default.app.Onprem.URLSpecifier: "/v1.0/onprem/<tipo>/<ruta-bian>*"
wdo.default.app.UDP_URL_APIREST: "https://localhost:7843/v1.0"
wdo.default.app.UDP_OPERACION_GET: "<NombreOperacionCamelCase>"
```

### Sección WDO — rest
```yaml
wdo.default.rest.additionalInstances: "10"
wdo.default.rest.HTTP Input.useHTTPS: "yes"
wdo.default.rest.HTTP Input.timeoutForClient: "16"
wdo.default.rest.CTRLINICIAL.UDP_USE_CCAS400: "S"   # valor por ETI/plantilla 153
wdo.default.rest.UDP_OPERACION_GET: "<NombreOperacionCamelCase>"
```

### Sección destinations (uno por cada backend)
```yaml
destinations:
  # SIEMPRE el primero: health check del conector centralizado
  - destination:
      name: "health"
      URLDEST: "https://ir-as400-connector-ir.cp4i-ace.svc.cluster.local:7843/v1.0/u/centralizedconnector/health"
      TIMEOUT: "16"
      PROTOCOLO: "TLSv1.3"
      METODO: "GET"
    srv_info:
      TECHNICAL_SRV_NAME: "CentralizedConnector"
      TIMEOUT: "16"

  # Backends adicionales del servicio
  - destination:
      name: "<ALIAS>"          # ej: SERV-PROP-CRED
      URLDEST: "https://<host>:<puerto>/v1.0/<ruta>"
      TIMEOUT: "16"
      PROTOCOLO: "TLSv1.3"
      METODO: "POST"           # GET | POST | PUT | DELETE
    srv_info:
      APP_NAME: "APP037"
      TECHNICAL_SRV_NAME: "<NombreTecnico-s>"
      PROGRAM: "IN2100RI"      # solo AS400
      PCML: "DL1060RI"         # solo AS400
      TIMEOUT: "16"
```

> ⚠️ **Timeouts (H1 homologación):** los valores canónicos vienen del **ETI/`valid_cfg_values` de cada servicio**. Plantilla 153 → backend `16` / servidor `17` / cliente `16–18`. Ejemplos históricos con `48–49` son genéricos heredados; no usarlos para un servicio real salvo que el ETI lo defina.

---

## FASE 6 — Pruebas unitarias (Postman + certificados OpenShift)
1. Descargar certificados de OpenShift (`.crt` y `.key`)
2. Postman → Settings (⚙️) → Certificates → Add Certificate:
   - **Host**: `<host>:<puerto>`
   - **CRT File**: archivo `.crt`
   - **KEY File**: archivo `.key`
3. Ejecutar requests contra `https://localhost:7800/v1.0/<ruta>`
4. Revisar logs del Integration Server: verificar trazas CloudWatch y eventos ELK (ver módulo `logging`)
5. Validar todos los escenarios: éxito, error funcional, error header, error body, error LDAP, error técnico, timeout

---

## FASE 7 — Pipeline y entrega
1. Crear pipeline de **validación de fuente** en Azure DevOps (8 pasos)
2. Subir BAR a **Nexus**
3. Desplegar en **Cloud Pak** con utilitario `oc` (OpenShift CLI)
4. Elaborar el **F01** y completar la entrega → ver módulo `delivery`

---

## Troubleshooting y Errores Frecuentes en ACE

### 1. Inconsistencia de `cod_servicio` entre ambientes en políticas PolicyProject
- **Error**: `[ERROR] service.cod_servicio no es igual en todos los ambientes para policyproject/.../PL_UserDefined.policyxml: DEV='APP037', PRD='CSH004', QAS='CSH004'`
- **Causa**: los valores de `cod_servicio` en los archivos de políticas (`.policyxml`) difieren entre DEV, QAS y PRD.
- **Solución**: unificar el código de servicio en las políticas de todos los ambientes para que coincidan con el valor definido en DEV.

### 2. Bodies Postman en PRD con objetos anidados vacíos
- **Error**: `[ERROR] v1.0/MTLS/PRD/...: body 'Customer' debe tener valor null en PRD. Actual={"MemberIdentification": null}`
- **Causa**: en PRD, los objetos principales del body de Postman (`Customer`, `Account`, `Transaction`, `Backoffice`) estaban definidos como objetos con propiedades `null`, en lugar de ser directamente `null`.
- **Solución**: configurar dichos objetos con valor literal `null` en la colección Postman de PRD:
  ```json
  "InitiatePaymentExecutionProcedureExchangeTransaction": {
      "Customer": null,
      "Account": null,
      "Transaction": null,
      "ChannelIdentification": null,
      "Backoffice": null
  }
  ```

---

## Reglas de desarrollo (siempre)
| Regla | Detalle |
|---|---|
| Timeouts en segundos | Según ETI (153 → `16` backends, `17` servidor, `16–18` cliente) |
| Protocolo | **TLSv1.3** para todo backend externo |
| Instancias WDO | Mínimo **10** |
| Conector AS400 | Según ETI/plantilla (153 → `S`); ejemplos genéricos usan `N` |
| Exposición doble | `mTLS` (externo seguro) + `Onprem` (interno) |
| Framework | **Nunca** modificar archivos `LIB_CORE_*` ni `LIB_SMF_*` |
| Logging | Siempre implementar CloudWatch + ELK según módulo `logging` |

## Referencias internas
- `generation-workflow/generation-workflow.md` (SCI/ETI → desarrollo base).
- `deployment/deployment.md` (config por ambiente, CI/CD), `delivery/delivery.md` (entrega formal).
- `framework-setup/framework-setup.md` (entorno local).
