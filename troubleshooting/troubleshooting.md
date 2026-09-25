# troubleshooting — Troubleshooting de servicios ACE

## Propósito
Diagnóstico estructurado de fallas típicas en servicios BUS de la fábrica (runtime CP4I / Toolkit).

## Síntomas y causas típicas
| Síntoma | Causa probable | Verificación / fix |
|---|---|---|
| Errores de validación inconsistentes | `request.schema.json` con `required` mal puesto | Alinear obligatoriedad con SCI/ETI; validar longitudes/regex |
| Respuesta de error "de lógica" | `IsErrorFuncional` condicionado solo a `HTTP 200` | T1: verificar condición de estado antes de marcar error funcional |
| Auditoría no llega | Cola MQ local no configurada o label `lblAudit` sin conexión → `CTRLAUDIT` | T2: conectar `lblAudit` al nodo; verificar `server.conf.yaml` (cola) |
| `cod_servicio` no coincide | Política `PL_UserDefined` con `cod_servicio` distinto del `ServiceType` | Comparar `C_PLP_SERVICE` y `cod_servicio` con el valor del SCI/ETI |
| Bodies PRD distintos | URLs/PCML apuntan a otro ambiente | Revisar `srv_info` (PROGRAM/PCML) y wdo por ambiente |
| Mensaje "trama no válida" del backend | `CTRLLENGTHCPY.inputDirectory` con prefijo `153_`/copybook ajeno | Normalizar rutas de runtime a `<S>` y verificar longitud `C8OPLEN` |
| Timeout en llamada al backend | timeoutForServer < tiempo real del backend | Ajustar `TIMEOUT` (16–18 s estándar) en política/valid_cfg |
| Error mTLS/HTTPS | Certificado/keystore no cargado o `useHTTPS` mal configurado | Importar cert OpenShift; revisar wdo mTLS/Onprem |
| Dispatcher REST no regenera | Editaron `gen/*.msgflow` a mano | Regenerar desde el Toolkit; no editar |
| ELK sin eventos | `getLBL_ELK()` sin conexión o niveles 40/50 mal disparados | Verificar códigos 10–60 con `ace-logging` |

## Secuencia de diagnóstico
1. Revisar logs CloudWatch del pod / EventLog en Toolkit.
2. Identificar nodo y paso (etapas Compute `SMF_*`).
3. Verificar políticas del ambiente y `valid_cfg_values`.
4. Repetir con Postman el escenario fallido (headers canónicos).
5. Revisar auditoría (cola MQ) y ELK (logs) para la transacción (`bif-correlation-id`).

## Reglas
- No cambiar el framework (`LIB_CORE_*`/`LIB_SMF_*`) para "arreglar" un error.
- Documentar la causa raíz y la solución en el backlog del servicio.

## Errores de generación ESQL/DFDL

### `Incorrect function or procedure name "NEXTSIBLING" or argument count` o error en la línea siguiente
1. Abrir el `.esql` generado y localizar la sentencia completa que contiene `NEXTSIBLING`.
2. Confirmar que la forma sea `MOVE <reference> NEXTSIBLING;` o `MOVE <reference> NEXTSIBLING NAME '<child>';`.
3. Eliminar cualquier uso de `NEXTSIBLING` como función, token aislado o condición de `WHILE`.
4. Verificar que el `REFERENCE` esté declarado y que el statement tenga punto y coma.
5. Sustituir el bloque por la routine equivalente que compila en la plantilla y reaplicar solo el mapeo SCI/ETI.
6. Verificar la sintaxis estática antes de continuar. No agregar casts, funciones o cambios de cardinalidad para forzar el silenciado de la validación estructural.

### `CTDV1602E: occursCountKind fixed requiere minOccurs y maxOccurs iguales`
1. Identificar el grupo repetido en el XSD y abrir el `OCCURS` equivalente del copybook.
2. Si es `OCCURS` fijo, conservar el mismo valor en `minOccurs` y `maxOccurs`.
3. Si es `OCCURS ... DEPENDING ON` o `OCCURS *`, no convertirlo a `fixed`; aplicar la estrategia de la plantilla o declarar BLOQUEO.
4. Verificar de forma estática la consistencia del esquema DFDL.

### `CTDV1210E: lengthKind explicit exige la propiedad length`
1. Revisar el elemento señalado: si es un **grupo** (`<xsd:complexType>`, p. ej. `LISTADOCOBRANZARSP`), nunca debe llevar `dfdl:length`; su longitud se calcula de los hijos.
2. El formato DFDL de referencia (`CobolDataFormat` en `IBMdefined/CobolDataDefinitionFormat.xsd`) define `lengthKind="explicit"` como default: si un grupo queda sin `dfdl:lengthKind` explícito, hereda `explicit` sin `length` y la validación falla.
3. Corregir declarando el grupo con `dfdl:lengthKind="implicit"` (mismo patrón que `DL1071RI`, `DL1071RIRSP` y `ELEERR` en la plantilla):
   ```xml
   <xsd:element dfdl:lengthKind="implicit" maxOccurs="40" minOccurs="40" name="LISTADOCOBRANZARSP">
   ```
4. Ejecutar nuevamente la validación DFDL del Toolkit.

## Referencias
- `logging/logging.md` (T1/T2), `service-dev/service-dev.md` (troubleshooting), `delivery/delivery.md` (CP4I).
- `esql/esql.md` y `generation-workflow/generation-workflow.md` (gate de compilación).
