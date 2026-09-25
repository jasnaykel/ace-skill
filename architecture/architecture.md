# architecture — Arquitectura de la Fábrica de Integraciones BanBif (IBM ACE) y del BUS

## Propósito
Comprender la topología, los límites de responsabilidad y las decisiones arquitectónicas para desarrollar o generar servicios con la estructura correcta.

## Topología de referencia (patrón dominante del Repo C)

```
Consumidores: APP069 (Recaudaciones), APP061 (Branch), APP204/205 (BxI PN/PJ)
 ├─ canales digitales → API Gateway (APP212 / API Connect) ─────────┐
 └─ Recaudaciones/Branch → Transformador-X (ACE12) ────────────────┤
                                                                    ▼
                            Orquestador ACE12 (APP213) ──────────► Servicio Atómico BUS (APP213 = plantilla)
                                                                    │
                                                                    ▼
                                              Backend Centralizado (CP4I, Conector `IN2100RI`)
                                                                    │
                                                                    ▼
                                              IBS APP037 — RPG RE0058RI
```

- **Orquestación:** el orquestador invoca servicios atómicos (REST). Los atómicos NO conocen consumidores; implementan una operación de negocio completa.
- **Doble vía de exposición:** `mTLS` (externa, canales digitales) + `Onprem` (interna, Transformador-X/Recaudaciones), autenticación LDAP (`CTRLAUTHAPP` + `PL_ActiveDirectory`).

## Capas del atómico BUS (2 capas)
1. **Application fachada** (`APP_<S>`): recibe HTTP (mTLS/Onprem) → autentica (LDAP) → valida security headers → llama internamente al REST Service.
2. **REST Service genérico** (`src/v1.0/service/<S>`): exponen la operación, validan contrato (JSON Schema), construyen y envían la trama al backend (Backend Centralizado), procesan la respuesta y la formatean al consumidor.

## Control de la plataforma (patrón transversal)
- `CTRLINICIAL` → inicialización y configuración (usuario configurado `si-control`, env `UDP_OPERACION_ETP`).
- `CTRLAUTHAPP` → autenticación por LDAP (via `ComIbmSecurityPIP`).
- `CTRLERROR` ≠ auditoría (`CTRLAUDIT`, label `lblAudit`) ≠ observabilidad (`CTRLELK`, label `lblELK`) ≠ cifrado (`ENCRYPTSRV`/`DECRYPTSRV`).
- La auditoría (`getLBL_AUDIT()`) va a una cola MQ local (SMF), ELK va a logs CloudWatch.

## Backend Centralizado (Conector)
- Mensajería: JSON `CentralizedConnector{NamePcml, Message, LengthOut, LengthErr}` enviado por HTTP POST al Conector CP4I (`IN2100RI`).
- La trama se arma como DFDL (`RE0058RI`) y se serializa a caracteres (`convertDfdlToChar`); la respuesta viaja como texto base64/JSON y se deserializa (`convertCharToDfdlV2`).
- `srv_info` define `PROGRAM=IN2100RI`, `PCML=RE0058RI`; la plantilla verifica `timeoutForServer` y el `PROGRAM` en cada invocación.

## Cosas que NO son responsabilidad del atómico
- Transformación de lógica de negocio del consumidor (eso es el Orquestador/Transformador-X).
- Acceso directo a bases de datos relacionales (si aplica, va por otro servicio/backing service).
- Gestión de credenciales físicas del banco (viven en WebSEAL/políticas por ambiente).

## Referencias
- Repo C `app213-payexe-prorev-core-upda-s-ops-ace` (caso real completo).
- Informe del Prompt Maestro: `Informe_Ejecucion_Prompt_Maestro_IBM_ACE.md` (workspace `Documents\AI`), sección 3 y 5.