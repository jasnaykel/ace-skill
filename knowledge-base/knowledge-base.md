# knowledge-base — Glosario y conocimiento consolidado

## Propósito
Base de conocimiento transversal: glosario, decisiones de arquitectura y referencias rápidas.

## Glosario abreviado
| Término | Significado |
|---|---|
| SCI | Formato de Solicitud de Servicios (documento funcional; QUÉ) |
| ETI | Especificación Técnica de Integración (documento técnico; CÓMO) |
| DFDL | Data Format Description Language (parseo de tramas) |
| PCML | Program Call Markup Language (llamada a programas RPG/AS400) |
| ELEERR | Estructura de error del backend (PECODE/PERROR/PEMNSG/PEFLD/PEROW/PEWF) |
| Backend Centralizado | Conector CP4I que invoca RPG/AS400 (Program `IN2100RI`, PCML `RE0058RI`) |
| Refactor de Runtime | Normalización de rutas de runtime al nombre del servicio (`<S>`) |
| wdo | `workdiroverride` (overrides por nodo/ambiente) |
| WDO instance | Motor con instancias (regla: 10) |
| mTLS/Onprem | Doble vía de entrada (externa con certificado / interna) |
| LDAP GD/GQ/GP | Grupos de Active Directory por ambiente (Desarrollo/QA/Prod) |
| CT-XXX | Constantes de catálogo del SCI (p. ej. CT-001 = "R ") |
| cod_servicio | Código validado contra `ServiceType` (patrón CSH001) |
| getLBL_AUDIT/getLBL_ELK | Labels de auditoría y observabilidad (MQ local / CloudWatch) |
| faultFormat | Formato JSON de errores de REST API |

## Decisiones de arquitectura registradas
- El atómico BUS **no conoce consumidores**; el orquestador/Transformador-X resuelve la lógica de negocio del consumidor.
- Las librerías del framework (`LIB_CORE_*`, `LIB_SMF_*`) son **intocables**.
- Convención de timeouts: backend 16 s / servidor 17 s / cliente 16–18 s (excepto decisión explícita del ETI).
- Pipeline del repo genera el monprofile; la compilación BAR/publicación Nexus viven en la fábrica.
- Respuesta única al consumidor (CheckIfReplied) y errores de campo en HTTP 202.

## Preguntas frecuentes (FAQ) — extracto
- **¿Echo el `TransactionReference`?** No siempre: la respuesta trae el valor del backend (`OUR02TRX`). Confirmar en el ETI.
- **¿Puedo editar `gen/*.msgflow`?** No; se regenera desde el Toolkit.
- **¿`FullName` es obligatorio?** En el caso 153, NO (opcional; `request.schema.json` lo deja fuera de `required`).
- **¿Cómo se resuelve el "Transaccion Duplicada" (0815)?** Confirmar regla del servicio (HTTP 200 con código en body vs rama de error). Ver reporte de consistencia D2.
- **¿Qué hago si el ETI pide timeout 25 s?** Pedir decisión: 16–18 s es el estándar de fábrica (reporte D1).

## Fuentes
- Reportes del Prompt Maestro (workspace `Documents\AI`).
- Repositorio plantilla IBS `https://github.com/Karinadr/plantillas-AI/tree/IBS` y repositorio técnico `ace-flowpilot` `https://github.com/ot4i/ace-flowpilot/tree/main`.
- Skills propias (`ace-delivery`, `ace-framework-setup`, `ace-logging`, `ace-service-dev`).
