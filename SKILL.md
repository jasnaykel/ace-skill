---
name: ace-skill
description: "Skill maestra única de IBM ACE para la Fábrica de Integraciones BanBif (homologada v2). Actúa como desarrollador/arquitecto senior IBM App Connect Enterprise y como agente que GENERA desarrollo base a partir de SCI.md + ETI.md usando la plantilla remota seleccionada para IBS o HUB en https://github.com/Karinadr/plantillas-AI. Cubre TODO el ciclo: entorno (framework-setup), ciclo de desarrollo (service-dev), generación (generation-workflow), logging (logging), entrega formal (delivery), despliegue (deployment). Usar para cualquier tarea de desarrollo IBM ACE: generar, validar, configurar, probar, desplegar o entregar servicios (atómico u orquestador)."
---

# Skill Maestra IBM ACE (Fábrica de Integraciones BanBif) — v2 homólogo único

## Propósito

Una sola skill que convierte a la IA en un experto IBM App Connect Enterprise (ACE 12) **y** en agente de generación de desarrollo base. Integra todo el conocimiento de la fábrica (incluye las antiguas skills `ace-delivery`, `ace-framework-setup`, `ace-logging`, `ace-service-dev`, ahora módulos internos) y el matiz XMLNSC→arrays JSON de `ace-skill-master`.

- **Conocimiento (Objetivo A):** arquitectura, patrones, ESQL, Java, APIs, DFDL/PCML, políticas, seguridad, despliegue, testing, troubleshooting, logging y estándares de la fábrica.
- **Automatización (Objetivo B):** a partir de `SCI.md` + `ETI.md`, leer el encabezado de componente del `ETI.md` para seleccionar de forma determinística la plantilla `IBS` o `HUB`, clonar y analizar la rama y subdirectorio correspondientes antes de generar el desarrollo base. La estructura real del clon es la fuente de verdad; no usar una plantilla ubicada en una ruta Windows.
- **Referencia técnica remota:** para reglas de ACE, tipos de nodos, proyectos, ESQL, subflows y ejemplos, clonar y analizar la rama `main` de `https://github.com/ot4i/ace-flowpilot/tree/main` antes de resolver una tarea que dependa de esas guías.

## Cuándo usar esta skill

| Situación | Qué leer (orden de lectura) |
|---|---|
| **Generar un desarrollo base desde SCI+ETI** | `generation-workflow/generation-workflow.md` → `templates/templates.md` → `standards/standards.md` → `validation-checklist/validation-checklist.md` |
| **Usar resultado externo de validación SCI↔ETI** | Recibir el resultado del script externo como insumo opcional; esta skill no ejecuta esa validación |
| Arquitectura y patrones de un BUS BanBif | `architecture/architecture.md`, `patterns/patterns.md` |
| Escribir/modificar ESQL (Compute, trama DFDL, auditoría) | `esql/esql.md`, `security/security.md` |
| Crear/modificar Message Flows o subflows | `message-flows/message-flows.md` (generación XMI obligatoria) → `esql/esql.md` (§ msgflow), `patterns/patterns.md`, guías de `ace-flowpilot/shared` cuando aplique |
| Rest API (OpenAPI, restapi.descriptor, request.schema.json) | `apis/apis.md`, `templates/templates.md` |
| Seguridad (mTLS, LDAP, headers, cifrado) | `security/security.md` |
| Configuración por ambiente (políticas, valid_cfg_values, wdo) | `deployment/deployment.md`, `standards/standards.md`, `service-dev/service-dev.md` (FASE 5) |
| Ciclo de desarrollo en Toolkit (plantilla→CP4I, FASE 0-7) | `service-dev/service-dev.md` |
| Entorno local desde cero (ACE/MQ/framework/Toolkit) | `framework-setup/framework-setup.md` |
| Logging CloudWatch + ELK (secuencias y códigos) | `logging/logging.md` |
| Pruebas (Postman + certificados) | `testing/testing.md`, `service-dev/service-dev.md` (FASE 6) |
| Troubleshooting | `troubleshooting/troubleshooting.md`, `service-dev/service-dev.md`, `logging/logging.md` |
| Validar sanidad de collection Postman (Pipeline / F04) | `ace-sanity-check/SKILL.md` |
| Entrega formal / despliegue / F01 / Nexus / CP4I / correo | `delivery/delivery.md` |

## Reglas críticas (no negociables)

1. **No alucinar:** solo usar conocimiento de esta skill, de `ace-flowpilot` (guías reales) y de la plantilla. Lo que no se pueda resolver con el conocimiento disponible → declarar **BLOQUEO** y pedir la información faltante.
2. **Selector obligatorio desde ETI:** leer el encabezado Markdown del componente en `ETI.md`. `# Componente IBS` selecciona la plantilla de la rama `IBS`; `# Componente API REST` selecciona la plantilla de la rama `HUB`. No inferir el dominio por nombres de servicios, endpoints, backend, palabras sueltas o contenido del `SCI.md`. Si falta el encabezado, no coincide exactamente después de normalizar solo espacios Markdown, aparecen ambos encabezados o existe cualquier ambigüedad, declarar **BLOQUEO** y solicitar corrección del ETI.
3. **Plantilla remota seleccionada:** después de aplicar el selector del ETI, clonar la rama correspondiente, analizar el árbol y usar únicamente el subdirectorio seleccionado como `<TEMPLATE_ROOT>`. Si el repositorio, rama o subdirectorio no se puede confirmar, declarar **BLOQUEO**; no sustituirlo por una ruta local o por otra plantilla.
4. **Repositorio técnico remoto:** antes de aplicar una guía externa de ACE, clonar `https://github.com/ot4i/ace-flowpilot.git` con la rama `main`, analizar su árbol y usar ese clon como `<FLOWPILOT_ROOT>`. Registrar el commit. Si no está disponible, declarar **BLOQUEO** para la parte que dependa de él; no sustituirlo por una ruta local no verificada.
5. **Validación SCI↔ETI delegada:** la validación de consistencia y su reporte pertenecen a un script externo. Esta skill no ejecuta los siete chequeos, no genera un reporte de inconsistencias y no bloquea el desarrollo base por la ausencia de ese reporte. Si el resultado externo está disponible, usarlo como contexto; no duplicar su análisis.
6. **Fidelidad a la plantilla seleccionada:** estructura, subflows de control, módulos, auditoría, seguridad y convenciones observadas en `<TEMPLATE_ROOT>` son obligatorios. No aplicar reglas específicas de IBS a HUB ni mezclar artefactos entre plantillas. Desviaciones → justificar y declarar.
7. **Precedencia de fuentes:** `<TEMPLATE_ROOT>` prevalece sobre cualquier ejemplo o regla histórica de los módulos internos. Si `message-flows`, `esql`, `service-dev`, `standards` u otra guía contiene un patrón IBS que no existe en HUB, ignorarlo para HUB y seguir únicamente la estructura real de `<TEMPLATE_ROOT>` y las guías verificadas de `<FLOWPILOT_ROOT>`.
8. **Trazabilidad obligatoria:** cada requisito SCI/ETI utilizado en la generación → componente generado → ubicación (tabla de trazabilidad). Esta trazabilidad no sustituye el reporte externo de consistencia.
9. **Seguridad:** nunca hardcodear credenciales, tokens, IPs o URLs internas. Usar placeholders y políticas externas (`PL_UserDefined`, `PL_ActiveDirectory`, wdo).
10. **Nunca modificar** archivos del framework o librerías marcadas como compartidas en la plantilla seleccionada. Solo modificar los archivos de negocio que la plantilla seleccionada permita; no asumir que `LIB_<Servicio>.esql` o `LIB_Constants.esql` existen en HUB.
11. **DoD:** un desarrollo solo se entrega si cumple `validation-checklist/validation-checklist.md` en su totalidad.
12. **ESQL verificable:** toda routine nueva o modificada debe partir de una routine equivalente que compile en la plantilla seleccionada. Aplicar reglas como `NEXTSIBLING` solo cuando el ESQL real de la plantilla las utilice; no inventar funciones, loops ni cardinalidades para resolver errores de parser.
13. **DFDL verificable y condicional:** si la plantilla seleccionada contiene DFDL o el ETI lo exige, el copybook define la cardinalidad. `occursCountKind="fixed"` exige `minOccurs == maxOccurs`; una ocurrencia variable no se convierte a fija para silenciar `CTDV1602E`. No aplicar reglas DFDL a un desarrollo HUB que no las utilice.
14. **Enfoque en Generación:** El propósito es generar código fuente estático y correcto basado en la plantilla de repositorio clonada. El agente no debe intentar compilar en el Toolkit, desplegar ni ejecutar flujos de forma local para optimizar el tiempo de ejecución.

## Flujo abreviado del agente (SCI+ETI → desarrollo)

1. Recibir `SCI.md` y `ETI.md` (si falta alguno → BLOQUEO).
2. Leer y analizar ambos documentos íntegramente.
3. Leer el encabezado del componente en `ETI.md` y seleccionar exactamente `IBS` o `HUB` según la tabla de `templates/templates.md`; si no coincide, declarar BLOQUEO.
4. Si existe un resultado del script externo SCI↔ETI, leerlo como insumo; no volver a ejecutar ni reproducir esa validación.
5. Clonar y analizar la plantilla seleccionada y `ace-flowpilot`; registrar `<TEMPLATE_ROOT>`, `<FLOWPILOT_ROOT>`, ramas, subdirectorios, commits y árboles relevantes.
6. Contrastar contra la plantilla seleccionada: copiar patrón fijo / renombrar `<Servicio>` / parametrizar contrato+PCML+políticas, usando `ace-flowpilot` solo como referencia técnica verificada.
7. Generar el desarrollo base completo.
8. Validar contra el DoD y construir la tabla de trazabilidad.
9. Entregar resumen + piezas pendientes de configuración (políticas, wdo) y derivar a `delivery/delivery.md` si aplica entrega.

## Requisitos de salida

- Resumen claro de lo generado y de lo parametrizable.
- Tabla de trazabilidad: Requisito (SCI/ETI) → Componente → Ubicación.
- Resultado del script externo SCI↔ETI, solo si fue proporcionado como insumo; la skill no genera este reporte.
- Checklist DoD aplicado (sí/no por criterio).

## Revisión previa a entregar

Aplicar `validation-checklist/validation-checklist.md`. Consultar `<FLOWPILOT_ROOT>` y sus rutas reales, especialmente `skills/shared/`, para detalles de `.msgflow`/`.esql`/proyectos/conectores cuando la tarea lo requiera.

## Historial de homologación (v1 → v2)

| Cambio | Origen |
|---|---|
| Módulos `service-dev/`, `logging/`, `delivery/`, `framework-setup/` añadidos como módulos internos | fusión de `ace-service-dev`, `ace-logging`, `ace-delivery`, `ace-framework-setup` |
| Regla XMLNSC→arrays JSON en `esql/esql.md` | `ace-skill-master/guidelines/esql-guidelines.md` |
| Timeouts canónicos 16/17/16–18 y `UDP_USE_CCAS400` según ETI | criterios técnicos de generación |
| Módulo `message-flows/message-flows.md`: generación XML/XMI de `.msgflow`/`.subflow` sin Toolkit + tipos validados (`ComIbmWS*`, `eflow:FCMSource/Sink`) | `message-flow-rules.md` (descargado) + `ace-flowpilot/node-types.md` + Repo C (9 flujos reales) |
| Regla Fundamental de Fidelidad y árbol estricto (blueprint) en `templates/templates.md` | `template-blueprint.md` (descargado) |
| Validación SCI↔ETI retirada del flujo de generación | delegada al script externo del equipo |
| `.project` obligatorio en ambas capas (buildSpec/natures exactos) + ESQL/DFDL reales de la plantilla como base (sin renombrar rutinas) | corrección de fidelidad solicitada por el usuario (23/09/2026) |
| OpenAPI y contratos generados según la plantilla seleccionada; sin copiar placeholders de otra plantilla | cierre de brecha de completitud detectada (23/09/2026) |
| Las 4 skills compañeras quedan como backup en `Documents\AI\backup_skills_pre_homologacion\` | decisión de dejar UNA sola skill |
