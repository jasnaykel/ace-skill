# validation-checklist — DoD del desarrollo generado y checklist de revisión

## Propósito
Criterios objetivos para declarar un desarrollo base generado como **CORRECTO al 100%**, más la revisión previa a entrega de cualquier artefacto ACE.

## DoD (Definition of Done)

Un desarrollo generado es correcto solo si cumple TODOS estos criterios:

### Cobertura
- [ ] 100% de requisitos del SCI/ETI implementados.
- [ ] **Tabla de trazabilidad completa:** Requisito (SCI/ETI) → Componente generado → Ubicación.

### Fidelidad a la plantilla
- [ ] El inventario de rutas, proyectos y artefactos generados coincide con la plantilla seleccionada; no se usó el inventario de la otra rama.
- [ ] La estructura, capas y proyectos presentes en la plantilla seleccionada se conservaron al 100%; no se agregaron capas ausentes.
- [ ] Los metadatos Eclipse `.project`, si existen, tienen buildSpec/natures exactos de la plantilla seleccionada.
- [ ] Los contratos, OpenAPI, `servers`, fachadas, flujos, subflows, módulos, DFDL/PCML, políticas y pruebas se validan solo si existen en la plantilla seleccionada o los exige el ETI.
- [ ] Los artefactos de flujo existentes se generaron como XML/XMI válido según la topología real de la plantilla y `ace-flowpilot`.
- [ ] Los archivos de lógica de negocio modificados corresponden a archivos existentes en la plantilla seleccionada; no se crearon equivalentes IBS para HUB.
- [ ] Auditoría, ELK, seguridad y manejo de errores conservan el patrón real de la plantilla seleccionada.
- [ ] Desviaciones justificadas y declaradas (si las hubo).

### Estructura y Sintaxis Estática
- [ ] `.esql` sintácticamente válido y estructurado; sin `BROKER SCHEMA` innecesario, `DOUBLE`/`RANDOM`/`CREATE OUTPUTROOT`.
- [ ] Cada routine ESQL nueva o modificada se basa en una routine equivalente que compila en la plantilla; no se inventaron statements para corregir un error.
- [ ] `NEXTSIBLING` aparece solo en statements completos `MOVE ... NEXTSIBLING;` o `MOVE ... NEXTSIBLING NAME '...';`; no existe como función, token aislado ni condición `WHILE`.
- [ ] El recorrido de hermanos repetidos usa la forma canónica `REFERENCE` + `WHILE LASTMOVE(...) DO ... END WHILE` (LASTMOVE avanza por cada ocurrencia); si aparece `MOVE ... NEXTSIBLING;` debe ser un statement completo con `;` y `FIELDVALUE(...)` para escalares.
- [ ] La compilación de ambas capas termina sin `ESQL Parser`, `Builder Referential Error Marker` ni errores referenciales equivalentes.
- [ ] Si existe DFDL, fue validado en el Toolkit sin `DFDL Validation Problem`.
- [ ] Si existe DFDL, su cardinalidad coincide con el copybook/ETI y conserva la estrategia de la plantilla.
- [ ] Si existen grupos DFDL, sus reglas `lengthKind` y `length` coinciden con la plantilla y el esquema validado.
- [ ] Si existen flujos, los `xmi:type` de nodos fueron validados contra `ace-flowpilot` y la plantilla seleccionada.
- [ ] Si existen `.msgflow`/`.subflow`, están bien formados XML/XMI y conservan namespaces, composición e identificadores esperados.
- [ ] Si existe OpenAPI, `request.schema.json` y demás contratos, son consistentes con SCI/ETI y la plantilla seleccionada.


### Manejo de errores
- [ ] El manejo OK/ERROR conserva el patrón real de la plantilla seleccionada.
- [ ] Los handlers y descriptores existentes están conectados conforme a la plantilla seleccionada.
- [ ] Los códigos de error, incluidos códigos IBS o `ELEERR` cuando aplique, fueron mapeados según el ETI y la plantilla seleccionada.

### Seguridad
- [ ] Sin credenciales/tokens/IP/URLs internas hardcodeadas (placeholders y políticas externas).
- [ ] mTLS, Onprem, LDAP y security headers se validan solo si existen en la plantilla seleccionada o los exige el ETI.

### Configuración
- [ ] Las configuraciones por ambiente, wdo, destinos, timeouts y políticas existentes están completas según la plantilla seleccionada y el ETI.
- [ ] Las constantes y códigos de servicio están cargados solo en los archivos de política que existan en la plantilla seleccionada.

### Documentación y pruebas
- [ ] `README.md` generado con la estructura global de `templates/readme-eti-template.md` y datos reales del `SCI.md`, `ETI.md` y la plantilla seleccionada.
- [ ] Encabezado descriptivo en cada componente generado.
- [ ] Colección Postman por ambiente (éxito + escenarios de error).

## Checklist de revisión de artefactos (general, hereda de `ace-flowpilot`)
- [ ] Tipo de proyecto correcto y metadatos Eclipse (`.project`, descriptores) exactos.
- [ ] Nodos con `xmi:type` validado contra esquema; sin inventar atributos.
- [ ] ESQL: tabla de repetibilidad antes de escribir código; comparar con una routine equivalente de la plantilla; usar `REFERENCE` + `WHILE LASTMOVE` + `MOVE ... NEXTSIBLING;`, `FIELDVALUE()` para escalares y la construcción de arrays verificada por la plantilla; nunca inventar `FOR ... AS path[] DO` ni statements `NEXTSIBLING` incompletos.
- [ ] Conectores: esquemas `gen/` y políticas creados; operaciones según guía del conector.
- [ ] Subflows: Input/Output obligatorios; Passthrough si no hay lógica; en Shared Library van en subdirectorio (broker schema), nunca en la raíz.
- [ ] Simplicidad: sin nodos "por si acaso"; flujo directo Input→Reply es válido para echo.
- [ ] Nota de import en ACE Toolkit al crear proyectos nuevos (File > Import > Existing Projects into Workspace).

## Regla final
Si algún criterio del DoD no se cumple o no puede verificarse, NO declarar el desarrollo como completo: listarlo como pendiente.
