# apis — REST APIs (OpenAPI, restapi.descriptor, request.schema.json)

## Propósito
Crear o modificar Integration Services REST de la fábrica: contrato OpenAPI, descriptor, validación de request y manejo de respuestas/errores.

## Componentes de un Integration Service REST (`src/v1.0/service/<S>`)
| Archivo | Función |
|---|---|
| `<S>.yaml` | OpenAPI 3.0: paths, request/response schemas, headers, `faultFormat: JSON` |
| `restapi.descriptor` | Descriptor del servicio: operaciones → subflows → `errorHandlers` (Catch/Failure/Timeout) |
| `request.schema.json` | JSON Schema de entrada: campos, tipos, longitudes, patrones, `required` (usado por Validate) |
| `gen/<S>.msgflow` | Dispatcher generado por el Toolkit (NO editar) |
| `<Operación>.subflow` | Lógica de la operación (Validate → … → Respuesta) |
| `<S>Input{Catch,Failure,Timeout}Handler.subflow` | Manejo de errores HTTP |

## Convenciones de contrato (basadas en el caso 153)
- **Headers:** `Content-Type` (obligatorio), `Time-Stamp` (UTC, 24 chars), `Bif-Correlation-Id` (UUID), `Bif-Consumer-Id` (`[A-Z]{3}\d{3}`), `Bif-Mdw-Id`, `Host-Id`, `Branch-Code`, `Country-Code`, `User-Id`, `Device-Id`.
- **Body BIAN:** campos con tipos/longitudes/regex del SCI (ej. `ServiceType [a-zA-Z0-9]{6}`, montos `own decimal 13,2` serializados como string 15 con ceros a la derecha, fechas `[0-9]{8,14}`).
- **Obligatoriedad:** solo lo que el SCI marque como obligatorio va en `required` (campo opcional NO).
- **Respuesta éxito:** `ResultCode`/`ResultMessage` (del backend), `TotalNumberOfRecords` (integer, CAST de `OUR02TOTRE`), `TransactionReference`.
- **Error:** JSON `faultFormat` con `type`, `title`, `status`, `detail`, `instance` + sección `Message[]`/`StatusCode`/`Message`. Errores de campo → HTTP 202.

## Respuesta correcta (patrón de la plantilla)
```json
{
  "TotalNumberOfRecords": 1,
  "TransactionReference": "20250214193232",
  "ResultCode": "0815",
  "ResultMessage": "Transaccion Duplicada"
}
```
Si el backend responde `HTTP 200` con código éxito → OK; si no → respuesta de error `status` según `getErrorCode()`.

## Validación en el flujo
- `Validate.subflow`: aplica `request.schema.json` y valida el mensaje (longitud, campos) antes de llamar al backend.
- `ValidReply.subflow` / `CheckIfReplied`: garantizan una única respuesta al consumidor.

## Referencias
- Repo C: `<S>.yaml` (OpenAPI), `request.schema.json`, `restapi.descriptor`, subflows Validate/ValidReply.
- `<FLOWPILOT_ROOT>`: `skills/shared/ace-projects.md` (§ REST API), `ExampleAPI/`.
