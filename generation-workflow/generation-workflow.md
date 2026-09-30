# generation-workflow — Flujo operativo del agente (SCI + ETI → desarrollo base)

## Propósito
Procedimiento operativo para que la IA genere **desarrollo base** de un servicio IBM ACE a partir de dos insumos Markdown: `SCI.md` (QUÉ) y `ETI.md` (CÓMO), aplicando la plantilla corporativa sin improvisar estructuras.

## Insumos obligatorios
- `SCI.md` — Formato de Solicitud de Servicios (funcional): campos, reglas de negocio, consumidores, productor.
- `ETI.md` — Especificación Técnica de Integración: mapeo de campos, transformaciones, contratos, endpoints, manejo de errores.
- Plantilla remota seleccionada por dominio `IBS`, `HUB` u `ORQ` (ver `templates/templates.md`).
- Skills de soporte: módulos `service-dev`, `logging`, `framework-setup`, `delivery` de esta skill.

> ⛔ Si falta un insumo → **BLOQUEO**. No continuar.

## Insumo condicional: copybook
- `SCI.md` y `ETI.md` son **siempre obligatorios**. Sin uno de los dos no hay generación.
- El **copybook es opcional** y solo aplica cuando el servicio realmente consume una trama COBOL/RPG.

| Caso | Copybook |
|---|---|
| Backend `IBS_RPG` (trama propia con copybook) | **Obligatorio**. Sin `backend.copybook.ruta` → BLOQUEO. |
| Orquestador que coordina servicios REST y no consume trama propia | **No aplica**. No declararlo ni inventarlo. |
| Servicio que solo consume o expone REST, sin COBOL | **No aplica**. |

La decisión se toma desde el ETI, según qué consume el servicio. Un servicio sin
copybook **no** es un servicio incompleto: es un servicio sin capa DFDL. En ese
caso el contrato no declara `backend.copybook`, ni `dfdl`, ni `artefactos_backend`,
y no se generan `IBMdefined/`, `importFiles/`, `<PCML>.xsd` ni el `.yaml` de
`CTRLLENGTHCPY`. Inventar un copybook para "completar" el desarrollo es un defecto,
no una mejora.

## Paso 0 — Resolver y analizar la plantilla seleccionada
Antes de leer o generar artefactos:

Determinar el dominio exclusivamente desde el encabezado del componente en `ETI.md`:

| Encabezado exacto del ETI | Dominio | Rama | Subdirectorio |
|---|---|---|---|
| `# Componente IBS` | `IBS` | `IBS` | `app213-payexe-prorev-core-upda-s-ops-ace` |
| `# Componente API REST` | `HUB` | `HUB` | `app213-payexe-prorev-hub-upda-s-ops-ace` |
| `# Componente Orquestador` | `ORQ` | `ORQ` | `app213-payinfass-agrdeblis-retr-b-ops-ace` |

La comparación se hace sobre encabezados Markdown normalizados únicamente en espacios. No inferir la plantilla desde el nombre del servicio, backend, endpoint, protocolo, capa o contenido del `SCI.md`. Si falta el encabezado, no coincide, aparecen dos selectores o existen variantes no documentadas, declarar **BLOQUEO** y detener la generación.

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

Analizar el árbol del repositorio y de `<TEMPLATE_ROOT>` para localizar las capas `application`, `service`, configuración, `ci` y `test`. Para `ORQ`, verificar además que la plantilla corresponda a capa de negocio (`-b`) y exponga flujos de coordinación de servicios atómicos. Si el subdirectorio seleccionado no existe en la rama seleccionada, declarar **BLOQUEO** y no usar una plantilla de otra rama. Analizar también `<FLOWPILOT_ROOT>` para localizar las guías reales aplicables, por ejemplo `skills/shared`, tipos de nodos, reglas de message flows, subflows y proyectos. Leer los archivos equivalentes antes de copiar o renombrar cualquier artefacto. Registrar encabezado selector, dominio, URL, rama, subdirectorio, commit y ruta temporal de ambos repositorios en el reporte. Si alguno no está disponible, declarar **BLOQUEO** para la parte dependiente y no usar una copia local alternativa.

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

### 4.0 — Elegir el modo: legacy o contrato

Hay dos modos. **Ninguno reemplaza al otro.**

```text
modo legacy   (predeterminado, sigue siendo el que funciona)
  SCI + ETI + plantilla (+ copybook si el ETI define trama)  →  la IA lee y genera

modo contrato  (optativo, capa de preparación)
  SCI + ETI → contrato.yaml → validar → paquete → la IA genera
```

**Usa legacy cuando:** el usuario pide generar, hay un contrato válido y ya
probado, o la migración aún no ha llegado a paridad en ese servicio.

**Usa contrato cuando:** el usuario lo pide, o existe un `contrato.yaml`
validado para ese servicio. En ese caso el flujo es:

```bash
python scripts/validar_contrato.py contrato.yaml     # 0 = seguir, 2 = BLOQUEO
python scripts/generate_cobol_dfdl_xsd.py <cpy> <xsd> # fuera del contrato
python scripts/generar_openapi.py contrato.yaml -d paquete/
```

Y la IA recibe el `paquete/`: `artefactos.yaml`, `contrato.resuelto.yaml`,
`parametros.json`, `openapi.yaml`, `request.schema.json`, más la plantilla
clonada sobre su rama (commit no fijado). Prompt de ejecución en
`contratos/README.md`.

En modo contrato, `parametros.json` alimenta **la misma lógica que ya
funciona**: no se reescribe ni el motor ESQL ni la parametrización de la
plantilla. Lo que cambia es de dónde salen los datos, no quién los usa.

Mientras no haya paridad demostrada en dos servicios atómicos, el modo
contrato **no bloquea por defecto**: se usa con `validar_contrato.py --shadow`
para medir cuántos bloqueantes da antes de que bloqueen.

### 4.0.1 — Paso 4 sin modo (compartido por los dos)

**Carpeta raíz del repositorio.** El árbol se genera en una carpeta llamada
`raiz_proyecto`, que es el **nombre del repositorio de la organización**, tomado de
la sección "Repositorio de fuentes" del ETI (p. ej. `app213-payman-agrdeb-coll-init-b-ops-ace`).

⛔ **No** usar `componente.nombre_servicio` (`PayMan_AgrDeb_Coll_Init_B`) como nombre
de carpeta: ese es el nombre del artefacto ACE, no del repositorio, y produce un
árbol que no se parece a ningún repositorio de la plantilla. En modo contrato el
nombre llega ya resuelto en `paquete/parametros.json.raiz_proyecto` y
`paquete/artefactos.yaml.raiz_proyecto`; no volver a derivarlo. La raíz **no** es el
nombre del subdirectorio de la plantilla: ese es el repositorio de la plantilla, que
se clona aparte como `<TEMPLATE_ROOT>`.

Generar el desarrollo base completo:
1. `src/application/APP_<S>/` (fachada mTLS+Onprem): **`<S>.yaml` (OpenAPI de la fachada: UNA stanza `servers` con vía base `/v1.0/s/...` + schemas del contrato; los canales mTLS/onprem SOLO como descripción)** + **`.project`** + `application.descriptor` + **`MF_<S>.msgflow` generado como XMI** (`message-flows/message-flows.md`).
2. `src/v1.0/service/<S>/` (contrato + **`.project`** + **`gen/<S>.msgflow` + subflows generados como XMI** + DFDL/PCML (`IBMdefined/`, `importFiles/`, `log/`, **`<PCML>.xsd`**) + ESQL por capas).
3. `src/v1.0/configuration/{DEV,QAS,PRD}/` (políticas `PL_UserDefined`, `PL_ActiveDirectory`, `Monitoring` + wdo).
4. `ci/valid_cfg_values.yaml` + `ci/Monitoring.json`.
5. `test/` Postman.

> ⛔ Los `.project` deben replicar buildSpec/natures exactos de la plantilla. Los `.msgflow`/`.subflow` NO se difieren al Toolkit: se entregan como XML/XMI válido. El XSD DFDL es obligatorio **solo si el servicio tiene copybook** (backend `IBS_RPG`): generarlo con ACE Toolkit o, si no es posible invocar el importador, con `scripts/generate_cobol_dfdl_xsd.py`; después validarlo en ACE Toolkit. Nunca entregar solo el copybook y el reporte de importación. Si el ETI no define trama propia, no se generan XSD ni artefactos DFDL y eso **no** es un incumplimiento.

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
   - No ejecutar reemplazos globales sobre `xmi:id`, `sourceNode`, `targetNode` ni terminales. Cada nodo debe conservar un `xmi:id` único y toda conexión debe resolver exactamente a un nodo existente.
   - Validar que no existan dos conexiones con la misma pareja `sourceNode/sourceTerminalName` y `targetNode/targetTerminalName`.
   - Resolver cada `esql://routine/<schema>#<module>.<routine>` contra un ESQL físico del proyecto o de una shared library declarada; una referencia inexistente es bloqueante.
5. Si un cambio falla, volver a la routine/XSD base de la plantilla, reaplicar el mapeo mínimo y volver a validar la estructura estática. No parchear los síntomas con casts, cambios de cardinalidad o statements incompletos.

Sin inventar estructuras. Toda desviación → declararla.

## Paso 5 — Validación (DoD)
Aplicar `validation-checklist/validation-checklist.md` de forma estática y construir la tabla de trazabilidad.

## Paso 6 — Entrega
Resumen de lo generado, trazabilidad, piezas pendientes (políticas por ambiente, credenciales, URLs reales) y, si aplica, derivar a `ace-delivery` (F01, pipeline, Nexus, CP4I, correo).

## Paso 7 — Generación y gate del README.md (obligatorio y bloqueante)
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

6. Ejecutar el gate documental antes de validar/entregar: comprobar que existen las secciones 1 a 12, que no quedan placeholders `{{...}}`, que los valores corresponden al dominio seleccionado (`IBS`, `HUB` u `ORQ`) y que el nombre de la collection Postman coincide con la primera línea.

   Cuando esté disponible el workspace local, ejecutar `python <ACE_SKILL_ROOT>/scripts/validate_readme_eti.py --root <REPO_ROOT> --domain <IBS|HUB|ORQ>` y conservar el resultado como evidencia. Si el script devuelve código distinto de cero, detener la entrega.

> ⛔ Este README es un artefacto global del desarrollo, no una documentación opcional ni el README que venga dentro de la plantilla remota. Un README resumido, incompleto o heredado de otra operación es un **BLOQUEO DOCUMENTAL** y prohíbe declarar el servicio completo.

> ⛔ Si falta algún dato obligatorio → ADVERTENCIA (usar defaults si existen en el template, si no, comentar).

## Defaults documentados (cuando el SCI/ETI no lo definan)
- Timeouts: backend `16 s`, servidor `17 s`, cliente `16–18 s` (si el ETI difiere, pedir decisión).
- Protocolo backend: `TLSv1.3`.
- Instancias WDO: `10`.
- `MTLS` externa + `Onprem` interna; conector AS400 inicia en `N`.
- Formato de errores: JSON `faultFormat`; error de campo → HTTP 202 en capa entrada.

### 4.1.2 - Gate de proyectos y nombres canonicos

El gate debe verificar literalmente estos cinco archivos: `src/application/APP_<S>/.project`, `src/v1.0/service/<S>/.project`, `src/v1.0/configuration/DEV/policyproject/PLP_<S>/.project`, `src/v1.0/configuration/QAS/policyproject/PLP_<S>/.project` y `src/v1.0/configuration/PRD/policyproject/PLP_<S>/.project`. Si falta uno, detener la entrega y corregir el scaffolding.

Antes de entregar, validar obligatoriamente:

1. Todos los ESQL usan `BROKER SCHEMA` con segmentos separados por punto; el schema declarado coincide con cada `esql://routine`. La ruta física de cada ESQL debe reflejar exactamente esos segmentos: para `ace.esb.payexe.pro.hub.init.s` usar `ace/esb/payexe/pro/hub/init/s/`, tanto en `src/v1.0/service/<S>/` como en `src/application/APP_<S>/`. Una carpeta física compactada como `payexe_pro_hub_init_s` es inválida y bloquea la entrega.
   Ejecutar además un escaneo global de residuos de esquema (por ejemplo `ace.esb.payexe.prorev.hub.upda.s`) en ESQL, msgflow, subflow y descriptores; cualquier coincidencia bloquea la entrega.
2. `APP_<S>/.project` tiene `<projects>` con `LIB_CORE_CONTROL`, `LIB_CORE_COMMON` y `LIB_SMF_UTIL`; `application.descriptor` tiene las mismas referencias. No crear una carpeta fÃ­sica `Referenced Libraries` como sustituto.
3. Cada policy project DEV, QAS y PRD tiene `.project`, `.settings/org.eclipse.core.resources.prefs` exacto y `policy.descriptor` vÃ¡lido.
