# mq — IBM MQ en servicios ACE (colas, listeners y auditoría local)

## Propósito
Conocimiento mínimo de MQ para configurar el entorno local y la cola de auditoría que usan los servicios de la fábrica.

## Uso en el flujo típico
- **Auditoría:** la auditoría (`getLBL_AUDIT()` → label `lblAudit` → `CTRLAUDIT`) publica en una **cola MQ local** (SMF); en local se define una cola `Q.LOCAL.AUDITORIA` (configuración local, ver `ace-framework-setup` FASE 4 y 5 y `ace-service-dev` FASE 4).
- **Invocaciones síncronas a Backend/otros servicios VAN por HTTP** (Backend Centralizado), NO por MQ (excepto integraciones legadas específicas).

## Configuración local mínima
- Cola local de auditoría (ej. `Q.LOCAL.AUDITORIA`) con `server.conf.yaml` referenciando el queue manager local.
- Queue manager de desarrollo (MQ 9.x) instalado por `ace-framework-setup`.

## Guía rápida de comandos (línea de comandos)
```sh
# crear cola local (runmqsc)
DEFINE QLOCAL(Q.LOCAL.AUDITORIA) REPLACE
# ver colas
DISPLAY QLOCAL(*) ALL
```

## Recomendaciones
- No usar MQ para orquestaciones ligeras; el patrón de la fábrica es REST.
- Si un servicio requiere consumir/escribir MQ (integración legada), respetar naming de colas y configurarlas por ambiente (wdo/`valid_cfg_values`).

## Referencias
- `ace-framework-setup` (MQ 9.x), `ace-service-dev` (cola de auditoría local), `ace-logging` (colas en escenarios).