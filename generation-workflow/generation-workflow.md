# generation-workflow — Flujo operativo del agente (SCI + ETI → desarrollo base)

## Propósito
Procedimiento operativo para que la IA genere **desarrollo base** de un servicio IBM ACE a partir de dos insumos Markdown: `SCI.md` (QUÉ) y `ETI.md` (CÓMO), aplicando la plantilla corporativa sin improvisar estructuras.

## Insumos obligatorios
- `SCI.md` — Formato de Solicitud de Servicios (funcional): campos, reglas de negocio, consumidores, productor.
- `ETI.md` — Especificación Técnica de Integración: mapeo de campos, transformaciones, contratos, endpoints, manejo de errores.
- Plantilla: `app213-payexe-prorev-core-upda-s-ops-ace` (ver `templates/templates.md`).
- Skills de soporte: `ace-service-dev`, `ace-logging`, `ace-framework-setup`, `ace-delivery`.

> ⛔ Si falta un insumo → **BLOQUEO**. No continuar.

## Paso 1 — Lectura y análisis
Leer ambos documentos en su totalidad. Extraer en tablas:
- Campos de entrada (fuente, tipo, longitud, obligatorio, formato/regex, transformación).
- Mapeo hacia el backend (trama PCML/RPG) y de respuesta.
- Constantes de catálogo (CT-XXX), códigos de error IBS, LDAP, endpoints, timeouts.

## Paso 2 — Validación de consistencia cruzada SCI ↔ ETI (obligatoria)
Ejecutar los 7 chequeos contra ambos documentos (y contra la plantilla como verdad terreno):

1. **Campos huérfanos:** campo que ETI mapea sin fuente en SCI → BLOQUEANTE.
2. **Tipos incompatibles:** origen vs destino con transformación no documentada → BLOQUEANTE.
3. **Requisitos sin implementación:** regla del SCI sin paso en el ETI → BLOQUEANTE (o ADVERTENCIA si opcional).
4. **Endpoints/protocolos:** sistema/cola/API/ruta discrepante → BLOQUEANTE.
5. **Cardinalidad/obligatoriedad:** obligatorio en destino sin origen → BLOQUEANTE.
6. **Nomenclatura:** mismo concepto con nombres distintos sin justificación → ADVERTENCIA.
7. **Ambigüedades:** requisito con ≥2 interpretaciones → ADVERTENCIA (si impide codificar → BLOQUEANTE).

**Salida obligatoria:** tabla `# | Tipo | Documento/Sección | Descripción | Clasificación | Recomendación` + veredicto.
**Regla:** con ≥1 BLOQUEANTE NO generar. Con solo ADVERTENCIAS: solicitarlas al usuario (o usar defaults documentados) antes de generar al 100%.

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

### 4.1 — Gate de compilación ESQL/DFDL (obligatorio)

Antes de declarar generado el desarrollo:

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
   - Ejecutar la validación DFDL del Toolkit.
4. Compilar ambas capas en el ACE Toolkit y guardar el resultado de la compilación. No continuar con un error `ESQL Parser`, `Builder Referential Error Marker` o `DFDL Validation Problem`.
5. Si un cambio falla, volver a la routine/XSD base de la plantilla, reaplicar el mapeo mínimo y volver a validar. No parchear los síntomas con casts, cambios de cardinalidad o statements incompletos.

Sin inventar estructuras. Toda desviación → declararla.

## Paso 5 — Validación (DoD)
Aplicar `validation-checklist/validation-checklist.md` completo, incluir el resultado de compilación ESQL/DFDL y construir la tabla de trazabilidad.

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