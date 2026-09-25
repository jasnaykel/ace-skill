# validation-checklist — DoD del desarrollo generado y checklist de revisión

## Propósito
Criterios objetivos para declarar un desarrollo base generado como **CORRECTO al 100%**, más la revisión previa a entrega de cualquier artefacto ACE.

## DoD (Definition of Done)

Un desarrollo generado es correcto solo si cumple TODOS estos criterios:

### Cobertura
- [ ] 100% de requisitos del SCI/ETI implementados.
- [ ] **Tabla de trazabilidad completa:** Requisito (SCI/ETI) → Componente generado → Ubicación.

### Fidelidad a la plantilla
- [ ] Estructura de 2 capas (Application fachada + REST Service) respetada.
- [ ] Metadatos Eclipse `.project` presentes en AMBAS capas con buildSpec/natures exactos de la plantilla (sin builders inventados).
- [ ] `APP_<S>/<S>.yaml` (OpenAPI de la fachada) presente con el contrato REAL y **UNA sola stanza `servers`** (vía base `/v1.0/s/...`), nunca múltiples stanzas ni el placeholder de otra plantilla.
- [ ] **Flujos generados como XMI** según `message-flows/message-flows.md`: `MF_<S>.msgflow` (fachada), `gen/<S>.msgflow` (dispatcher REST) y subflows obligatorios.
- [ ] Subflows de control presentes: `HealthCheck`, `Validate`, `ValidReply`, `<Operación>.subflow`, `Input{Catch,Failure,Timeout}Handler`.
- [ ] Módulos `SMF_<S>_<Paso>` (PrepInvocacion/PrepRespSrv/ControlarError/ControlarException) y `MF_<S>` (CheckIfReplied/ApplySecurityHeaders).
- [ ] Auditoría/ELK por `PROPAGATE TO LABEL getLBL_AUDIT()` + labels `lblAudit/lblELK`.
- [ ] Desviaciones justificadas y declaradas (si las hubo).

### Compilabilidad
- [ ] `.esql` sintácticamente válido en el ACE Toolkit; sin `BROKER SCHEMA` innecesario, `DOUBLE`/`RANDOM`/`CREATE OUTPUTROOT`.
- [ ] Cada routine ESQL nueva o modificada se basa en una routine equivalente que compila en la plantilla; no se inventaron statements para corregir un error.
- [ ] `NEXTSIBLING` aparece solo en statements completos `MOVE ... NEXTSIBLING;` o `MOVE ... NEXTSIBLING NAME '...';`; no existe como función, token aislado ni condición `WHILE`.
- [ ] El recorrido de hermanos repetidos usa la forma canónica `REFERENCE` + `WHILE LASTMOVE(...) DO ... END WHILE` (LASTMOVE avanza por cada ocurrencia); si aparece `MOVE ... NEXTSIBLING;` debe ser un statement completo con `;` y `FIELDVALUE(...)` para escalares.
- [ ] La compilación de ambas capas termina sin `ESQL Parser`, `Builder Referential Error Marker` ni errores referenciales equivalentes.
- [ ] Cada DFDL derivado de copybook fue validado en el Toolkit sin `DFDL Validation Problem`.
- [ ] La cardinalidad DFDL coincide con el copybook/ETI: `occursCountKind="fixed"` tiene `minOccurs == maxOccurs`; las ocurrencias variables no fueron convertidas a `fixed` para ocultar un error.
- [ ] Los grupos (`complexType`) DFDL llevan `dfdl:lengthKind="implicit"` y sin `dfdl:length`; ningún grupo quedó con `lengthKind="explicit"` sin `length` (evita `CTDV1210E`).
- [ ] `xmi:type` de nodos validado (trampa HTTP: `ComIbmWSInput/Reply`, no `ComIbmHTTP*`; subflow In/Out `eflow:FCMSource/FCMSink`).
- [ ] `.msgflow`/`.subflow` bien formados XML/XMI (cabecera `ecore:EPackage`, `composition{nodes,connections}`, nsURI/nsPrefix correctos).
- [ ] OpenAPI + `request.schema.json` consistentes con el contrato SCI/ETI (longitudes, regex, required).


### Manejo de errores
- [ ] Decisión OK/ERROR en `PrepRespSrv` (HTTP 200 + código éxito → OK; si no → rama error).
- [ ] Handlers Catch/Failure/Timeout conectados al `restapi.descriptor`.
- [ ] Códigos IBS (`ELEERR` PECODE/PERROR/PEMNSG) mapeados según tabla; error funcional ≠ técnico.

### Seguridad
- [ ] Sin credenciales/tokens/IP/URLs internas hardcodeadas (placeholders y políticas externas).
- [ ] Doble vía mTLS + Onprem, LDAP (`PL_ActiveDirectory`), security headers en respuesta.

### Configuración
- [ ] `valid_cfg_values.yaml` y wdo completos por ambiente (LDAP GD/GQ/GP, destinos, timeouts, `UDP_OPERACION_GET`).
- [ ] Constantentes CT-XXX y `cod_servicio` cargados en `PL_UserDefined`.

### Documentación y pruebas
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