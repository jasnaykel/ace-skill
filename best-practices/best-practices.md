# best-practices — Buenas prácticas y reglas de desarrollo ACE (fábrica BanBif)

## Propósito
Compendio de reglas transversales que cualquier desarrollo (generado o manual) debe cumplir.

## Reglas de desarrollo (fábrica)
1. **Fidelidad a la plantilla IBS** `https://github.com/Karinadr/plantillas-AI/tree/IBS` (Regla 4 de la skill maestra): analizar el clon y conservar su estructura, subflows, módulos y convenciones.
2. **Consistencia SCI↔ETI antes de código** (Regla 2): siempre validación 2B.
3. **Trazabilidad** (Regla 4): cada requisito → componente → ubicación (tabla).
4. **Seguridad** (Regla 5): nada hardcodeado; políticas externas (ver `security/security.md`).
5. **No tocar el framework** (Regla 6): `LIB_CORE_*`, `LIB_SMF_*`, `gen/*.msgflow` son intocables.
6. **DoD antes de entregar** (Regla 7): `validation-checklist/validation-checklist.md`.

## Convenciones de tiempo y recursos
- Timeout backend ≈ **16 s** (servidor 17, cliente 16–18). Si el ETI dice otro valor → pedir decisión.
- Instancias WDO: 10. Protocolo backend: TLSv1.3. Conector AS400 inicia en `N`.
- BAR: `BAR-<N>-<Servicio>-v<v>.bar`; librerías framework: `LIB_CORE_CONTROL`, `LIB_CORE_COMMON`, `LIB_SMF_UTIL`.

## Colaboración entre skills
| Tarea | Skill |
|---|---|
| Generar desarrollo | `ace-skill` (+ `generation-workflow`) |
| Entorno local | `ace-framework-setup` |
| Desarrollo/plantilla | `ace-service-dev` |
| Logging | `ace-logging` |
| Entrega (F01/CP4I/correo) | `ace-delivery` |
| Guías de artefactos | `<FLOWPILOT_ROOT>` (`skills/shared/*`) |

## Errores que NO cometer
- Inventar nodos/atributos (`xmi:type`) o ESQL sin verificar contra guías/plantilla.
- Copiar residuos de otra plantilla (contratos OpenAPI ajenos, copybooks `DL0743RI`, `.scannerwork`).
- Editar dispatchers o librerías de framework.
- Responder al consumidor en más de un punto del flujo.
- Dejar credenciales/IP/URLs de ejemplo.

## Referencias finales
- Informe del Prompt Maestro (workspace `Documents\AI`): `Informe_Ejecucion_Prompt_Maestro_IBM_ACE.md`, `Reporte_Consistencia_SCI_ETI_...md`, `Documentacion_Skills_IBM_ACE.md`.
- La plantilla IBS (`https://github.com/Karinadr/plantillas-AI/tree/IBS`) y `ace-flowpilot` (`https://github.com/ot4i/ace-flowpilot/tree/main`) como fuentes remotas de verdad, cada una para su propósito.
