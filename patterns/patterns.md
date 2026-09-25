# patterns — Patrones de diseño del BUS y de servicios ACE

## Propósito
Catálogo de patrones recurrentes de la fábrica que todo desarrollo generado o manual debe seguir.

## Patrón 1 — Servicio atómico BUS REST (fachada + service)
- **Subflows obligatorios** de un servicio REST con operaciones:
  - `HealthCheck.subflow` → al destino `health` (backend health check).
  - `Validate.subflow` → JSON Schema (`request.schema.json`) + validaciones Business-Side (XPath a `InputRoot.JSON`).
  - `ValidReply.subflow` → responden UNA sola vez al consumidor (con `localEnvironment.RESTReply` y HTTP status).
  - `<Operación>.subflow` → la lógica de negocio: `Validate → CTRLLENGTHCPY → PrepInvocacion → Conector Centralizado (HTTP Request) → PrepRespSrv`.
  - `Input{Catch,Failure,Timeout}Handler.subflow` → CTRLERROR (error HTTP con `faultFormat`).
- **Regla:** no enviar respuesta en más de un punto del flujo (no duplicar Reply).

## Patrón 2 — Pre/Post invocación a Backend Centralizado
```json
// request al Conector (JSON)
{
  "Header": "Json",
  "Data": {
    "CentralizedConnector": {
      "NamePcml": "RE0058RI",
      "Message": "<trama DFDL serializada>",
      "LengthOut": "000000000100",
      "LengthErr": "000000000100"
    }
  }
}
```
- `prepareDataRequestDFDL` arma el árbol DFDL con los campos del request (usa `CT-CERELEM` = "INR02PREFIJO"/campos reales).
- `STRUCTURE_DFDL_RE0058RI(...)` + `StructureDataDFDL` montan el registro; `convertDfdlToChar` lo serializa.
- La respuesta se deserializa con `convertCharToDfdlV2` y se lee la estructura `RE0058RIRSP` + `ELEERR` (PECODE/PERROR/PEMNSG/PEFLD/PEROW/PEWF).

## Patrón 3 — Determinación de éxito/error (PrepararRespuestaSrv)
- `HTTP 200` + código éxito (`getCOD_EXITO()`) ⇒ respuesta **OK** → `armaRpta*_OK`.
- En otro caso ⇒ rama de **error** → `ControlarError` → `armaRpta*_ERROR`, HTTP status según tipo (error funcional ≠ técnico).
- Errores de campo (validación) se responden con **HTTP 202** en la capa de entrada.

## Patrón 4 — Auditoría y observabilidad
- Auditoría: `PROPAGATE TO LABEL getLBL_AUDIT() DELETE NONE` con el mensaje JSON de auditoría (`prepararMensajeAuditoriaV2`). Requiere conexión del label `lblAudit` → `CTRLAUDIT`.
- ELK: `PROPAGATE TO LABEL getLBL_ELK()` con `tipo_accion`, códigos 10/20/30/40/50/60 (ver skill `ace-logging`).

## Patrón 5 — Seguridad de entrada
- Application fachada con 2 listeners: `mTLS` (useHTTPS=yes, TLSv1.3) y `Onprem` (useHTTPS=no).
- `ApplySecurityHeaders` (Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Referrer-Policy, Permissions-Policy, X-XSS-Protection).
- Autenticación: `CTRLAUTHAPP` + LDAP (`securityProfileName` del `PL_ActiveDirectory`).

## Anti-patrones (NO hacer)
- Meter lógica de negocio del consumidor en el atómico.
- Editar `gen/*.msgflow` (regenerado por el Toolkit).
- Responder en múltiples puntos o no responder (CheckIfReplied).
- Copiar hardcodes de ejemplo (URLs, credenciales, `localhost`).

## Referencias
- Repo C: subflows y ESQL reales (`SMF_<S>`, `MF_<S>`, `LIB_<S>`).
- `ace-flowpilot`: `skills/shared/message-flow-rules.md`, `subflow-rules.md`, `review-checklist.md`.