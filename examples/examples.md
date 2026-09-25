# examples — Casos reales de la fábrica

## Propósito
Casos de referencia verificados que la skill puede citar como ejemplos de patrones, mapeos y decisiones.

## Ejemplo principal: `BUS_Reversar_Pago_IBS` (153)
- **SCIENTÍFICO:** SCI (`SCI_SRV_ReversarPagoIBS.md`) + ETI (`ETI_153_BUS_Reversar_Pago_IBS.md`). La consistencia SCI↔ETI se valida fuera de esta skill mediante el script externo.
- **Implementación real (plantilla):** rama `IBS` del repositorio `https://github.com/Karinadr/plantillas-AI/tree/IBS`.
- **Plantilla HUB:** rama `HUB`, subdirectorio `app213-terdep-pay-exec-s-ace`; no reutilizar automáticamente contratos ni lógica específica de IBS.

### Datos duros extraídos
| Aspecto | Valor |
|---|---|
| Backend | RPG `RE0058RI` (IBS APP037) vía `IN2100RI` (Backend Centralizado) |
| Código BIAN | `BUS_S_PaymentExecution_ProcedureReverse_Core_Update` |
| Operación | `UpdatePaymentExecutionProcedureReverseCore` |
| Path BIAN | `v1.0/s/paymentexecution/procedurereverse/core/update` |
| Endpoints | `…/update-reverse-payment-collections-ibs.apps.onprem.ocphipdes…` (DEV), `/v1.0/mtls/…` |
| 27 campos | mapeo completo SCI → PCML `INR02*`/`IOR02*`/`INR03*`/`OUR03*`/`INR05*` |
| Constantes | CT-001..CT-048 (política `PL_UserDefined`) |
| LDAP | `PAYEXE_PROREV_CORE_UPDA_{GD,GQ,GP}` |
| Error IBS | `ELEERR` PECODE/PERROR/PEMNSG; caso 0815 "Transaccion Duplicada" |
| Respuesta MAIN | `ResultCode/ResultMessage/TotalNumberOfRecords/TransactionReference` |

### Mapeo de referencia (ejemplos)
- `ServiceType=CSH001` → `VSERVIC` → validación `cod_servicio`.
- `TransactionReference=20250214193238` → `INR02TRX`; respuesta `TransactionReference` = valor del backend (`OUR02TRX`).
- montos 13,2 → String 15 (ceros a la derecha) → `INR03MONT/MRED/MTOT`.

## Cómo usar
- Como plantilla de contrato/mapeo cuando la tarea sea de un BUS atómico REST.
- Como referencia de decisiones ya resueltas por el proceso externo cuando el usuario las proporcione.

## Backlog de ejemplos futuros
- Orquestador (invoca 2+ atómicos) — no presente aún.
- Integración por eventos (Kafka) — pendiente de documentación.
