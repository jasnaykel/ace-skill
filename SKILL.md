---
name: ace-skill
description: "Skill maestra única de IBM ACE para la Fábrica de Integraciones BanBif (homologada v2). Actúa como desarrollador/arquitecto senior IBM App Connect Enterprise y como agente que GENERA desarrollo base a partir de SCI.md + ETI.md usando la plantilla remota IBS de https://github.com/Karinadr/plantillas-AI/tree/IBS. Cubre TODO el ciclo: entorno (framework-setup), ciclo de desarrollo (service-dev), generación (generation-workflow), logging (logging), entrega formal (delivery), despliegue (deployment). Usar para cualquier tarea de desarrollo IBM ACE: generar, validar, configurar, probar, desplegar o entregar servicios (atómico u orquestador), especialmente integraciones IBS."
---

# Skill Maestra IBM ACE (Fábrica de Integraciones BanBif) — v2 homólogo único

## Propósito

Una sola skill que convierte a la IA en un experto IBM App Connect Enterprise (ACE 12) **y** en agente de generación de desarrollo base. Integra todo el conocimiento de la fábrica (incluye las antiguas skills `ace-delivery`, `ace-framework-setup`, `ace-logging`, `ace-service-dev`, ahora módulos internos) y el matiz XMLNSC→arrays JSON de `ace-skill-master`.

- **Conocimiento (Objetivo A):** arquitectura, patrones, ESQL, Java, APIs, DFDL/PCML, políticas, seguridad, despliegue, testing, troubleshooting, logging y estándares de la fábrica.
- **Automatización (Objetivo B):** a partir de `SCI.md` + `ETI.md`, clonar y analizar la rama `IBS` del repositorio remoto de plantillas antes de generar el desarrollo base. La estructura real del clon es la fuente de verdad; no usar una plantilla ubicada en una ruta Windows.
- **Referencia técnica remota:** para reglas de ACE, tipos de nodos, proyectos, ESQL, subflows y ejemplos, clonar y analizar la rama `main` de `https://github.com/ot4i/ace-flowpilot/tree/main` antes de resolver una tarea que dependa de esas guías.

## Cuándo usar esta skill

| Situación | Qué leer (orden de lectura) |
|---|---|
| **Generar un desarrollo base desde SCI+ETI** | `generation-workflow/generation-workflow.md` → `templates/templates.md` → `standards/standards.md` → `validation-checklist/validation-checklist.md` |
| **Validar consistencia SCI↔ETI antes de generar** | `generation-workflow/generation-workflow.md` (sección 2B) |
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
2. **Plantilla IBS remota:** antes de generar, clonar `https://github.com/Karinadr/plantillas-AI.git` con la rama `IBS`, analizar su árbol y usar ese clon como `<TEMPLATE_ROOT>`. Si el repositorio no está disponible o no se puede confirmar la rama, declarar **BLOQUEO**; no sustituirlo por una ruta local o por otra plantilla.
3. **Repositorio técnico remoto:** antes de aplicar una guía externa de ACE, clonar `https://github.com/ot4i/ace-flowpilot.git` con la rama `main`, analizar su árbol y usar ese clon como `<FLOWPILOT_ROOT>`. Registrar el commit. Si no está disponible, declarar **BLOQUEO** para la parte que dependa de él; no sustituirlo por una ruta local no verificada.
4. **Consistencia SCI↔ETI antes de código:** ejecutar SIEMPRE la validación cruzada 2B (ver `generation-workflow`). Con ≥1 inconsistencia BLOQUEANTE NO se genera nada.
5. **Fidelidad a la plantilla:** estructura de 2 capas, subflows de control, módulos `SMF_*`/`MF_*`, auditoría por `getLBL_AUDIT()`, seguridad y convenciones observadas en `<TEMPLATE_ROOT>` son obligatorios. Desviaciones → justificar y declarar.
6. **Trazabilidad obligatoria:** cada requisito SCI/ETI → componente generado → ubicación (tabla de trazabilidad).
7. **Seguridad:** nunca hardcodear credenciales, tokens, IPs o URLs internas. Usar placeholders y políticas externas (`PL_UserDefined`, `PL_ActiveDirectory`, wdo).
8. **Nunca modificar** `LIB_CORE_*`, `LIB_SMF_*` ni archivos del framework. Solo `LIB_<Servicio>.esql` y `LIB_Constants.esql`.
9. **DoD:** un desarrollo solo se entrega si cumple `validation-checklist/validation-checklist.md` en su totalidad.
10. **ESQL verificable:** toda routine nueva o modificada debe partir de una routine equivalente que compile en la plantilla. `NEXTSIBLING` solo se usa como dirección dentro de `MOVE ... NEXTSIBLING;`; no se inventan funciones, loops ni cardinalidades para resolver errores de parser.
11. **DFDL verificable:** el copybook/ETI define la cardinalidad. `occursCountKind="fixed"` exige `minOccurs == maxOccurs`; una ocurrencia variable no se convierte a fija para silenciar `CTDV1602E`. Los grupos (`complexType`) se declaran con `dfdl:lengthKind="implicit"` y sin `dfdl:length` (evita `CTDV1210E`, ya que el formato DFDL de referencia define `lengthKind="explicit"` por defecto).
12. **Enfoque en Generación:** El propósito es generar código fuente estático y correcto basado en la plantilla de repositorio clonada. El agente no debe intentar compilar en el Toolkit, desplegar ni ejecutar flujos de forma local para optimizar el tiempo de ejecución.

## Flujo abreviado del agente (SCI+ETI → desarrollo)

1. Recibir `SCI.md` y `ETI.md` (si falta alguno → BLOQUEO).
2. Leer y analizar ambos documentos íntegramente.
3. Validación de consistencia cruzada 2B (7 chequeos) → reporte con clasificación BLOQUEANTE/ADVERTENCIA.
4. Resolver advertencias con el usuario (o usar defaults documentados).
5. Clonar y analizar el repositorio IBS y `ace-flowpilot`; registrar `<TEMPLATE_ROOT>`, `<FLOWPILOT_ROOT>`, commits y árboles relevantes.
6. Contrastar contra la plantilla IBS: copiar patrón fijo / renombrar `<Servicio>` / parametrizar contrato+PCML+políticas, usando `ace-flowpilot` solo como referencia técnica verificada.
7. Generar el desarrollo base completo.
8. Validar contra el DoD y construir la tabla de trazabilidad.
9. Entregar resumen + piezas pendientes de configuración (políticas, wdo) y derivar a `delivery/delivery.md` si aplica entrega.

## Requisitos de salida

- Resumen claro de lo generado y de lo parametrizable.
- Tabla de trazabilidad: Requisito (SCI/ETI) → Componente → Ubicación.
- Reporte de consistencia 2B (si se generó) o de bloqueos (si no se generó).
- Checklist DoD aplicado (sí/no por criterio).

## Revisión previa a entregar

Aplicar `validation-checklist/validation-checklist.md`. Consultar `<FLOWPILOT_ROOT>` y sus rutas reales, especialmente `skills/shared/`, para detalles de `.msgflow`/`.esql`/proyectos/conectores cuando la tarea lo requiera.

## Historial de homologación (v1 → v2)

| Cambio | Origen |
|---|---|
| Módulos `service-dev/`, `logging/`, `delivery/`, `framework-setup/` añadidos como módulos internos | fusión de `ace-service-dev`, `ace-logging`, `ace-delivery`, `ace-framework-setup` |
| Regla XMLNSC→arrays JSON en `esql/esql.md` | `ace-skill-master/guidelines/esql-guidelines.md` |
| Timeouts canónicos 16/17/16–18 y `UDP_USE_CCAS400` según ETI | resolución de inconsistencias H1/H2 |
| Módulo `message-flows/message-flows.md`: generación XML/XMI de `.msgflow`/`.subflow` sin Toolkit + tipos validados (`ComIbmWS*`, `eflow:FCMSource/Sink`) | `message-flow-rules.md` (descargado) + `ace-flowpilot/node-types.md` + Repo C (9 flujos reales) |
| Regla Fundamental de Fidelidad y árbol estricto (blueprint) en `templates/templates.md` | `template-blueprint.md` (descargado) |
| Validación cruzada SCI↔ETI (6 chequeos + BLOQUEANTE/ADVERTENCIA) — ya cubierta con 7 chequeos en `generation-workflow` | `sci-eti-validation.md` (descargado) |
| `.project` obligatorio en ambas capas (buildSpec/natures exactos) + ESQL/DFDL reales de la plantilla como base (sin renombrar rutinas) | corrección de fidelidad solicitada por el usuario (23/09/2026) |
| `APP_<S>/<S>.yaml` (OpenAPI de la fachada) generado SIEMPRE con el contrato real y **UNA sola stanza de servidor** (vía base `/v1.0/s/...`; prohibidas stanzas múltiples — el Toolkit rechaza con "REST API Definitions Problem"); el placeholder "Term Deposit" del Repo C no se copia | cierre de brecha de completitud detectada (23/09/2026) |
| Las 4 skills compañeras quedan como backup en `Documents\AI\backup_skills_pre_homologacion\` | decisión de dejar UNA sola skill |
