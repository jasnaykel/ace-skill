# java — JavaCompute y artefactos Java en ACE

## Propósito
Escribir o modificar clases JavaCompute y dependencias Java respetando el estilo y las guías de la fábrica.

## Cuándo usar JavaCompute
- Transformaciones complejas difíciles en ESQL.
- Integración con librerías Java externas (crypto, parsers).
- En la plantilla de la fábrica el patrón dominante es **ESQL**; usar Java solo cuando se justifique (nunca recetas por defecto).

## Estructura y entregables
- Proyecto Java / componente dentro de la librería o aplicación correcta (p. ej. `Shared-Static Library` con `<library>.library.descriptor`).
- Clase que extiende `com.ibm.broker.plugin.MbJavaCompute` (o `MbNode` para JavaCompute avanzado).
- `evaluate(MbMessageAssembly inAssembly, MbMessageAssembly outAssembly)` como punto de entrada.

## Convenciones
- Nombrado de clases PascalCase; métodos camelCase; sin magic numbers en el código.
- Preferir código corto y directo: si requiere >50 líneas de parseo, evaluar ESQL/DFDL.
- Lanzar `MbUserException`/`MbException` controladas; NO dejar excepciones crudas que rompan el compute node sin diagnóstico.
- Compilar con Maven (guias de `ace-flowpilot` Java) y empaquetar el `.jar` dentro del BAR como `user.jar`.

## Guardrails
- No mezclar lógica de negocio del consumidor en Java del atómico.
- No hardcodear credenciales/claves (usar `setdbparams`, `userDefined`, políticas).
- No llamar a recursos externos sin timeout.

## Referencias
- `ace-flowpilot`: `skills/ace-java-compute/SKILL.md`, `skills/shared/java-guidelines.md`.