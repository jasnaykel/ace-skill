# kafka — Eventos / Kafka (breadcrumb)

## Propósito
Punto de entrada futura para integraciones por eventos. **Estado: NO cubierto** por la plantilla ni por las guías del Repo B (roadmap de `ace-flowpilot` lo tiene como TODO).

## Posición en la fábrica
- Hoy el patrón dominante es **síncrono REST (BUS)**; la integración por eventos (Apache Kafka) en la fábrica de integraciones BanBif no está documentada en los repositorios analizados.
- Cuando un SCI/ETI solicite una integración por eventos, la skill debe **declarar BLOQUEO de conocimiento** y pedir: topología de tópicos (productor/consumidor), formatos de mensaje (avro/json), conectores esperados (Kafka) y políticas de snapshot/offsets.

## Qué NO hacer
- No generar flujos Kafka sin guías verificadas (conectores, propiedades del nodo `KafkaConsumer`/`KafkaProducer`, estructura de clúster).
- No inventar nombres de tópicos ni grupos de consumidores.

## Recomendación
Actualizar este módulo cuando exista documentación oficial de la mesa sobre integraciones por eventos (conectores, topologías, convenciones de tópicos).

## Referencias
- `<FLOWPILOT_ROOT>`: `backlog/roadmap.md` (TODO Kafka) y `skills/shared/connectors/` si existe `Kafka*.md` (conector Discovery) en el directorio real de 138 conectores.
