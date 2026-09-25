# testing — Pruebas de servicios ACE (Postman + certificados + escenarios)

## Propósito
Preparar y ejecutar pruebas unitarias e integrales de un servicio: requests Postman por ambiente, escenarios de éxito/error y verificación de logs (ELK/CloudWatch).

## Material de prueba (convención)
- Columna Postman por ambiente en `test/`: `<Servicio>.postman_collection.json` con carpetas DEV/QAS/PRD y `MTLS`/`Onprem`.
- Certificados OpenShift/CP4I para Invocations TLS (importar en ACE Toolkit) — ver `ace-service-dev` FASE 6.
- Pre-request scripts para headers canónicos: `bif-consumer-id`, `bif-correlation-id`, `time-stamp` (UTC).

## Escenarios mínimo obligatorios
| Escenario | Caso | Resultado esperado |
|---|---|---|
| Éxito funcional | Request válido contra backend OK | HTTP 200 + `TotalNumberOfRecords`/`ResultCode` del backend |
| Error funcional | Request válido, backend responde código IBS de negocio (ej. 0815) | HTTP 200 (o status definido) con código en body — confirmar regla del servicio |
| Error de validación | Request con campo inválido (longitud/regex) o header faltante | HTTP 202 (capa entrada) con `faultFormat` JSON |
| Error técnico | Backend caído / timeout | HTTP 503/502 con `status`, `detail`; logging ELK código 5x |
| Health / readiness | GET health | 200 OK, `status: UP` |

## Validación de logging (integrar con `ace-logging`)
- Escenario de éxito → logs CloudWatch (códigos 10/20) y ELK `tipo_accion` correctos.
- Escenario de error → código 30/40/50 en la secuencia correcta del diagrama.
- Verificar que `IsErrorFuncional` solo prende tras `HTTP 200` (T1) y que la auditoría llegue a la cola MQ (T2: `lblAudit` → `CTRLAUDIT`).

## Cómo probar con Toolkit
1. Crear Integration Server local (bar) con recursos mínimos (`user.jar`, `Monitoring.monprofile`, políticas).
2. Cola MQ local de auditoría y `server.conf.yaml` con el LTPA/seguridad correspondiente.
3. Importar certificados del ambiente y ejecutar la colección Postman hacia el puerto del server.
4. Revisar console logs y archivos de eventos; verificar DataFrame en `CTRLERROR`.

## Referencias
- Skill `ace-service-dev` (FASE 6), `ace-logging` (escenarios).
- Repo C: `test/Reversar_Pago-...postman_collection.json`.