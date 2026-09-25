# generation-workflow — Flujo operativo del agente (SCI + ETI → desarrollo base)

## Propósito
Procedimiento operativo para que la IA genere **desarrollo base** de un servicio IBM ACE a partir de dos insumos Markdown: `SCI.md` (QUÉ) y `ETI.md` (CÓMO), aplicando la plantilla corporativa sin improvisar estructuras.

## Insumos obligatorios
- `SCI.md` — Formato de Solicitud de Servicios (funcional): campos, reglas de negocio, consumidores, productor.
- `ETI.md` — Especificación Técnica de Integración: mapeo de campos, transformaciones, contratos, endpoints, manejo de errores.
- Plantilla remota seleccionada por dominio `IBS` o `HUB` (ver `templates/templates.md`).
- Skills de soporte: módulos `service-dev`, `logging`, `framework-setup`, `delivery` de esta skill.

> ⛔ Si falta un insumo → **BLOQUEO**. No continuar.

## Paso 0 — Resolver y analizar la plantilla seleccionada
Antes de leer o generar artefactos:

Determinar el dominio exclusivamente desde el encabezado del componente en `ETI.md`:

| Encabezado exacto del ETI | Dominio | Rama | Subdirectorio |
|---|---|---|---|
| `# Componente IBS` | `IBS` | `IBS` | `app213-payexe-prorev-core-upda-s-ops-ace` |
| `# Componente API REST` | `HUB` | `HUB` | `app213-payexe-prorev-hub-upda-s-ops-ace` |

La comparación se hace sobre encabezados Markdown normalizados únicamente en espacios. No inferir la plantilla desde el nombre del servicio, backend, endpoint, protocolo o contenido del `SCI.md`. Si falta el encabezado, no coincide, aparecen los dos encabezados o existen variantes no documentadas, declarar **BLOQUEO** y detener la generación.

```bash
git clone --branch <BRANCH> --single-branch https://github.com/Karinadr/plantillas-AI.git <TEMPLATE_REPO_ROOT>
git -C <TEMPLATE_REPO_ROOT> rev-parse --verify HEAD
git -C <TEMPLATE_REPO_ROOT> ls-tree -r --name-only HEAD
git -C <TEMPLATE_REPO_ROOT> ls-tree -d --name-only HEAD -- <SUBDIRECTORIO_SELECCIONADO>
<TEMPLATE_ROOT> = <TEMPLATE_REPO_ROOT>/<SUBDIRECTORIO_SELECCIONADO>

git clone --branch main --single-branch https://github.com/ot4i/ace-flowpilot.git <FLOWPILOT_ROOT>
git -C <FLOWPILOT_ROOT> rev-parse --verify HEAD
git -C <FLOWPILOT_ROOT> ls-tree -r --name-only HEAD
```

Analizar el árbol del repositorio y de `<TEMPLATE_ROOT>` para localizar las capas `application`, `service`, configuración, `ci` y `test`. Si el subdirectorio seleccionado no existe en la rama seleccionada, declarar **BLOQUEO** y no usar una plantilla de otra rama. Analizar también `<FLOWPILOT_ROOT>` para localizar las guías reales aplicables, por ejemplo `skills/shared`, tipos de nodos, reglas de message flows, subflows y proyectos. Leer los archivos equivalentes antes de copiar o renombrar cualquier artefacto. Registrar encabezado selector, dominio, URL, rama, subdirectorio, commit y ruta temporal de ambos repositorios en el reporte. Si alguno no está disponible, declarar **BLOQUEO** para la parte dependiente y no usar una copia local alternativa.

## Paso 1 — Lectura y análisis
Leer ambos documentos en su totalidad. Extraer en tablas:
- Campos de entrada (fuente, tipo, longitud, obligatorio, formato/regex, transformación).
- Mapeo hacia el backend (trama PCML/RPG) y de respuesta.
- Constantes de catálogo (CT-XXX), códigos de error IBS, LDAP, endpoints, timeouts.

## Paso 2 — Consumir validación SCI↔ETI externa
La consistencia cruzada SCI↔ETI y su reporte son responsabilidad de un script externo. Esta skill:

- No ejecuta los siete chequeos.
- No genera ni replica el reporte de inconsistencias.
- No bloquea la generación por no recibir ese reporte.
- Puede leer un resultado externo si el usuario lo proporciona, únicamente para conocer decisiones o datos ya resueltos.

Leer SCI y ETI para extraer los datos necesarios para parametrizar el desarrollo. Si durante la generación falta un dato técnico indispensable, declarar un **BLOQUEO de información de generación**, sin convertirlo en un reporte de consistencia SCI↔ETI.

## Paso 3 — Contraste con la plantilla
Resolver para el nuevo servicio `<Servicio>`:

| Acción | Qué |
|---|---|
| **Copiar** (patrón fijo) | 2 capas (fachada + service), subflows (HealthCheck, Validate, ValidReply, `<Operación>`, handlers Catch/Failure/Timeout), módulos `SMF_<S>_<Paso>`/`MF_<S>`, auditoría `getLBL_AUDIT()` + `lblAudit/lblELK`, seguridad mTLS/Onprem + LDAP, DFDL/PCML, `ci/` |
| **Renombrar** | `APP_<S>`, `MF_<S>.msgflow`, `LIB_<S>.esql`, `LIB_Constants.esql`, `SMF_<S>`, `<S>.yaml`, subflows, wdo, `PLP_<S>`, `C_PLP_SERVICE=<PLP_<S>>:PL_UserDefined`, `BROKER SCHEMA ace.esb.<s>...` |
| **Parametrizar** (desde SCI/ETI) | `cod_servicio`, constantes CT-XXX, contrato OpenAPI + `request.schema.json` (campos/longitudes/regex/obligatoriedad), mapeo `prepareDataRequestDFDL` y `armaRpta*_OK/_ERROR`, destinos (URLDEST/TIMEOUT/PROTOCOLO/METODO/PROGRAM/PCML), LDAP GD/GQ/GP, timeouts, `UDP_OPERACION_GET`, monitoreo, Postman |

## Paso 4 — Generación
Generar el desarrollo base completo:
1. `src/application/APP_<S>/` (fachada mTLS+Onprem): **`<S>.yaml` (OpenAPI de la fachada: UNA stanza `servers` con vía base `/v1.0/s/...` + schemas del contrato; los canales mTLS/onprem SOLO como descripción)** + **`.project`** + `application.descriptor` + **`MF_<S>.msgflow` generado como XMI** (`message-flows/message-flows.md`).
2. `src/v1.0/service/<S>/` (contrato + **`.project`** + **`gen/<S>.msgflow` + subflows generados como XMI** + DFDL/PCML (`IBMdefined/`, `importFiles/`, `log/`) + ESQL por capas).
3. `src/v1.0/configuration/{DEV,QAS,PRD}/` (políticas `PL_UserDefined`, `PL_ActiveDirectory`, `Monitoring` + wdo).
4. `ci/valid_cfg_values.yaml` + `ci/Monitoring.json`.
5. `test/` Postman.

> ⛔ Los `.project` deben replicar buildSpec/natures exactos de la plantilla (los `.esql` y artefactos DFDL se sirven desde la plantilla como base, normalizando solo residuos y sin renombrar rutinas/módulos). Los `.msgflow`/`.subflow` NO se difieren al Toolkit: se entregan como XML/XMI válido (ver `message-flows/message-flows.md`). Solo quedan para el Toolkit: import DFDL (→`.xsd`+`importFiles/`+`IBMdefined/`+`log/`), regeneración de `gen/*.msgflow` al compilar y scaffolding de Policy Projects.

### 4.1 — Gate de verificación estructural y sintáctica (obligatorio)

Antes de declarar generado el desarrollo, comprobar de manera estática que no se introduzcan desviaciones estructurales:

1. Localizar la routine equivalente de la plantilla que ya compila. Copiar su estructura y cambiar solo campos, paths y valores verificados contra SCI/ETI. Si no existe una routine equivalente o el copybook no permite determinar la cardinalidad, declarar BLOQUEO.
2. Para cada `.esql` nuevo o modificado, comprobar la sintaxis antes de integrarlo:
   - `NEXTSIBLING` solo puede aparecer dentro de `MOVE ... NEXTSIBLING;` o `MOVE ... NEXTSIBLING NAME '...';`.
   - No generar `NEXTSIBLING(...)`, `NEXTSIBLING;` aislado, `WHILE ... NEXTSIBLING DO` ni una sentencia `MOVE` sin `;`.
   - Para hermanos repetidos usar la forma de la routine compilada: `REFERENCE` + `WHILE LASTMOVE(...) DO` + `MOVE ... NEXTSIBLING`.
   - No inventar un `FOR ... AS path[] DO` ni cambiar el tipo/cardinalidad de un campo para resolver un error de compilación.
3. Para cada DFDL derivado de copybook, comparar el esquema con el copybook y el ETI:
   - `occursCountKind="fixed"` exige `minOccurs` y `maxOccurs` iguales.
   - `OCCURS ... DEPENDING ON` y `OCCURS *` deben conservar la estrategia de ocurrencia variable del template; no convertirlos a `fixed` para silenciar el validador.
   - Todo grupo (`complexType`) lleva `dfdl:lengthKind="implicit"`; no asignar `dfdl:length` a un grupo (el default `lengthKind="explicit"` del formato dispara `CTDV1210E`).
4. Asegurar que las estructuras de los archivos XML de los Message Flows y Subflows se generen de manera que su sintaxis e identificadores coincidan con la estructura lógica esperada.
5. Si un cambio falla, volver a la routine/XSD base de la plantilla, reaplicar el mapeo mínimo y volver a validar la estructura estática. No parchear los síntomas con casts, cambios de cardinalidad o statements incompletos.

Sin inventar estructuras. Toda desviación → declararla.

## Paso 5 — Validación (DoD)
Aplicar `validation-checklist/validation-checklist.md` de forma estática y construir la tabla de trazabilidad.

## Paso 6 — Entrega
Resumen de lo generado, trazabilidad, piezas pendientes (políticas por ambiente, credenciales, URLs reales) y, si aplica, derivar a `ace-delivery` (F01, pipeline, Nexus, CP4I, correo).

## Paso 7 — Generación del README.md (obligatorio)
Generar el README técnico basado en `templates/readme-eti-template.md` y entregarlo en la raíz del repositorio.

**Acciones:**
1. Leer el template: `templates/readme-eti-template.md`.
2. Extraer datos del SCI/ETI:
   - `ID`: Token numérico inicial del nombre del servicio en SCI (ej. "167" de "167_BUS_...").
   - `NombreFuncionalSnake`: `<NombreFuncional>` formateado a snake_case (ej. "actualiza_tipo_cambio_segmentado").
   - `Línea de Producto` y `Producto`: De la sección 3 del ETI (Columnas 2 y 3).
   - `Endpoints`: De la sección 6.7 del ETI (lista de endpoints con protocolo y método).
   - `Programa Backend`: De la sección 6.9 del ETI.
   - `BianPath`: De la sección 5.1 del ETI.
3. Rellenar los placeholders `{{...}}` del template con los datos extraídos.
4. Escribir el resultado en la **raíz** del repositorio: `README.md`.
5. Verificar que la primera línea tenga el formato `# <ID>_BUS_<NombreFuncionalSnake>` (sin emojis ni decoraciones adicionales) y que la sección 3 contenga la tabla de campos.

> ⛔ Si falta algún dato obligatorio → ADVERTENCIA (usar defaults si existen en el template, si no, comentar).

## Defaults documentados (cuando el SCI/ETI no lo definan)
- Timeouts: backend `16 s`, servidor `17 s`, cliente `16–18 s` (si el ETI difiere, pedir decisión).
- Protocolo backend: `TLSv1.3`.
- Instancias WDO: `10`.
- `MTLS` externa + `Onprem` interna; conector AS400 inicia en `N`.
- Formato de errores: JSON `faultFormat`; error de campo → HTTP 202 en capa entrada.

### 4.1.2 - Gate de proyectos y nombres canonicos

Antes de entregar, validar obligatoriamente:

1. Todos los ESQL usan `BROKER SCHEMA` con segmentos separados por punto; el schema declarado coincide con cada `esql://routine`.
2. `APP_<S>/.project` tiene `<projects>` con `LIB_CORE_CONTROL`, `LIB_CORE_COMMON` y `LIB_SMF_UTIL`; `application.descriptor` tiene las mismas referencias. No crear una carpeta fÃ­sica `Referenced Libraries` como sustituto.
3. Cada policy project DEV, QAS y PRD tiene `.project`, `.settings/org.eclipse.core.resources.prefs` exacto y `policy.descriptor` vÃ¡lido.
