# Auditoria contractual - servicio 166

## Estado

`BLOQUEADO`: no se debe regenerar ni entregar el desarrollo ACE hasta resolver
las contradicciones del SCI, ETI y backend.

## Artefactos verificados

- Contrato: `transferencia-tipo-cambio-personalizado.contrato.yaml`
- Paquete OpenAPI generado en temporal: `openapi.yaml`, `request.schema.json`,
  `parametros.json`, `artefactos.yaml`, `contrato.resuelto.yaml`
- XSD fallback generado desde `FX0009RI.cpy`
- Contrato validado con el perfil BanBif IBS
- Pruebas de la skill: `43 passed`
- Los dos XSD comparados parsean como XML

## Bloqueos

1. SCI declara `Consume RPG AS400 = NO`, pero ETI y los artefactos declaran
   `IN007RI -> FX0009RI`, copybook, PCML y conector IBS.
2. SCI declara `TCP (JT400)`, mientras ETI y el desarrollo existente usan REST
   y `CentralizedConnector`.
3. SCI/ETI declaran comunicacion asincrona, pero existe una respuesta HTTP 200
   con payload de resultado y el flujo ACE espera `OUTPUT1`/`ELEERR`.
4. ETI declara `ExchangeRate` como `4.4`, pero `INTEXCRTE` es `PIC 9(5)V9(6)`
   y PCML `length=11 precision=6`.
5. SCI/ETI declaran cuentas de longitud 10, pero `INTFRMACC` e `INTTOACC` son
   `PIC 9(12)` y PCML `length=12`.
6. El PCML fuente usa programa `IN2100RI` con entrada `INPUT`; el PCML del
   repositorio Azure usa programa `FX0009RI` con entrada `FX0009RI`.
7. El README del repositorio Azure clasifica el backend como REST, contrario a
   la ruta RPG/IBS documentada.

## Correcciones del generador

- Los campos `number` ahora generan JSON Schema `type: number`, no `integer`.
- Las longitudes decimales `9.2` y `4.4` generan `multipleOf` adecuado.
- Se mantiene la regla de no inventar mapeos ni resolver automaticamente las
  contradicciones de fuente.

## Decision requerida

Confirmar una unica verdad tecnica para protocolo/backend, sincronismo,
programa PCML, longitudes de cuentas y escala de tipo de cambio. Tras esa
confirmacion se puede parametrizar la plantilla IBS fijada y actualizar el
desarrollo existente de forma trazable.
