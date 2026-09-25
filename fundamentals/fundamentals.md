# fundamentals — Fundamentos IBM App Connect Enterprise (ACE)

## Propósito
Conocimiento base de ACE 12 para poder interpretar proyectos, configuraciones y errores antes de tocar código.

## Conceptos clave
- **Integration Node (Broker):** unidad de ejecución; contiene Integration Servers.
- **Integration Server:** ejecuta Applications/Shared Libraries; en CP4I un servidor = un pod.
- **Integration Service (REST):** exponer API REST con OpenAPI; genera el dispatcher `gen/*.msgflow`.
- **Applications / Shared Libraries / REST APIs / Policy Projects / Static Libraries:** los 5 tipos de proyectos ACE.
  - Application: unidad desplegable, contiene flujos y recursos.
  - Shared Library: código reutilizable (ESQL, subflows, Java, copys) que comparten varias aplicaciones.
  - Policy Project: no se despliega; contiene políticas de configuración.
- **Message Flow (.msgflow):** grafo de nodos (lógica) con propiedades en `xmi:type`.
- **ESQL (.esql):** lenguaje procedural para Compute/Transform; broker schema `ace.esb.<sistema>.<s>`.
- **Java:**
  - JavaCompute: nodo Compute con clase Java.
  - Maven/Maven Central para dependencias externas (vía `ace-maven-compile`).
- **DFDL/PCML:** descripción de tramas binarias/texto plano (AS400/COBOL) para parsear el backend.

## Mecánica del ACE Toolkit
- Importar proyectos: **File > Import > Existing Projects into Workspace**.
- Perspectivas: Integration Development, Debug, Git, Java.
- Verificación de esquemas de nodos: abrir `MessageFlow.xsd`/`MessageFlowUI.xsd` (versión ACE) para validar atributos `xmi:type`.

## Entorno local (resumen — ver skill `ace-framework-setup`)
- IBM ACE 12.0.x + IBM MQ 9.x; clonar framework (`core`, `subflows`, `policies`, `core_utils`, `creatorApp-java`, rama `dev`) y, para desarrollo `IBS` o `HUB`, clonar la plantilla seleccionada desde `https://github.com/Karinadr/plantillas-AI`; colección Postman.

## Versiones
- ACE 12.x / 13.x cambian rutas de XSD y nodos. Preguntar la versión del entorno si la tarea depende de esquemas de nodos (ver `<FLOWPILOT_ROOT>/skills/shared/ace-versions.md`).

## Referencias
- `<FLOWPILOT_ROOT>`: `skills/shared/ace-projects.md` (metadatos exactos), `ace-versions.md`, `node-types.md`.
- Skills propias: `ace-framework-setup`, `ace-service-dev`.
