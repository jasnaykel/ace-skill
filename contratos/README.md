# contrato — Capa contractual (SCI + ETI → contrato → generación)

## Qué es y qué no es

El contrato es la **capa de preparación** de la generación. No reemplaza a la
plantilla ni a la lógica que ya funciona: la prepara.

```text
ANTES (sigue valiendo)
  SCI + ETI + plantilla (+ copybook si el ETI define trama)  →  la IA lee y genera

AHORA (modo contrato)
  SCI + ETI → contrato.yaml → validar → OpenAPI + parametros + manifiesto
            → la IA recibe el paquete y genera
```

El flujo legacy **no se borra**. Sigue siendo el modo por defecto hasta que la
comparación de regresión demuestre paridad. Ver `generation-workflow.md` §4.2.

## SCI y ETI obligatorios; copybook opcional

`SCI.md` y `ETI.md` son **obligatorios**: sin uno de los dos no se genera nada.
El **copybook es opcional** y solo aplica cuando el servicio consume una trama
COBOL/RPG propia.

| Caso | Copybook |
|---|---|
| Backend `IBS_RPG` | **Obligatorio**. Sin `backend.copybook.ruta` → BLOQUEO. |
| Orquestador que coordina servicios REST | **No aplica**. No declararlo. |
| Servicio que solo expone o consume REST | **No aplica**. |

Cuando no aplica, el contrato no declara `backend.copybook`, `dfdl` ni
`artefactos_backend`, y no se generan `IBMdefined/`, `importFiles/`, `<PCML>.xsd`
ni el `.yaml` de `CTRLLENGTHCPY`. Declarar un copybook inexistente es un defecto.

## Precedencia (no negociable)

```
copybook              > contrato   para estructura física DFDL (si existe)
contrato aprobado     > perfil     para datos específicos del servicio
perfil del proyecto   > plantilla  para convenciones comunes
plantilla fijada      > IA         para estructura de archivos y flujos
SCI/ETI               = trazabilidad, no entrada directa de generación
```

Si el contrato contradice al copybook, la generación se detiene. La regla solo
aplica cuando el copybook existe.

## Los tres archivos del backend NO son intercambiables

| Artefacto | Función | Quién lo produce |
|---|---|---|
| `DL1071RI.cpy` | fuente COBOL | el cliente |
| `DL1071RI.xsd` | modelo DFDL | `scripts/generate_cobol_dfdl_xsd.py` |
| `DL1071RI.yaml` | `CTRLLENGTHCPY.filenamePattern` | la plantilla |

Sustituir el `.yaml` por el `.xsd` en el WDO **rompe en runtime**, no en el
Toolkit. Antes de tocar `filenamePattern`, leer el WDO y el subflow de la
plantilla. Está declarado en `contrato.artefactos_backend` para que la IA no
tenga que acordarse.

## Uso

```bash
# 1. Extraer (SCI/ETI ya en Markdown). Genera un contrato mínimo, sin inventos.
python scripts/extraer_contrato.py SCI.md ETI.md -o contrato.yaml

# 2. Completar el contrato a mano: request, response, mapeos, copybook, dfdl.
#    El validador dice qué falta, campo por campo.

# 3. Validar. --shadow mide antes de bloquear.
python scripts/validar_contrato.py contrato.yaml --shadow
python scripts/validar_contrato.py contrato.yaml            # ya bloquea

# 4. XSD desde el copybook (fuera del contrato)
python scripts/generate_cobol_dfdl_xsd.py DL1071RI.cpy DL1071RI.xsd

# 5. Paquete para la IA
python scripts/generar_openapi.py contrato.yaml -d paquete/
```

Códigos de salida, iguales en los tres scripts:

```
0 correcto · 1 advertencias · 2 bloqueante · 3 error técnico
```

## Qué produce el paso 5

| Archivo | Para qué |
|---|---|
| `openapi.yaml` | contrato HTTP; **una sola** stanza `servers` |
| `request.schema.json` | validación de entrada del REST API service |
| `parametros.json` | los nombres que la skill ya usa → no se reescribe la lógica |
| `artefactos.yaml` | qué copiar, parametrizar o generar. Nunca reescribir un fijo |
| `contrato.resuelto.yaml` | contrato con perfil aplicado y plantilla resuelta |

## Reglas de la extracción

`extract_minimal` **no inventa**. Toma solo lo demostrable del documento
(nombres, código de servicio, endpoint, requerimiento). Los mapeos y las
transformaciones no se extraen: se documentan a mano, porque adivinarlos es
peor que no tenerlos.

El contrato que sale de la extracción es **incompleto a propósito**, y el
validador lo dice. Un contrato incompleto que aparenta estar completo es peor
que uno que admite lo que le falta.

## Modo actualizar

```bash
python scripts/extraer_contrato.py SCI.md ETI.md -o contrato.yaml --modo actualizar
```

Conserva `plantilla`, `dfdl`, `artefactos_backend`, `reglas`, `configuracion`
y `seguridad` del contrato anterior, más `decisiones.manuales`. Esas quedan
marcadas en `decisiones.pendiente_revision` para que la revisión las vea.

## Prompt para la IA

Cuando el paquete esté validado, la IA recibe:

```text
Genera el desarrollo base desde el paquete de contexto.

Lee en este orden: artefactos.yaml, contrato.resuelto.yaml, parametros.json,
openapi.yaml, request.schema.json, y despues la plantilla en el commit fijado.

- `copiar_sin_modificar` y `protegidos`: se copian. No se reescriben ni se
  "mejoran". LIB_CORE_*, LIB_SMF_* y los .project no se tocan.
- `parametrizar`: se toma la estructura de la plantilla y se cambian solo los
  valores del contrato. No se reconstruyen.
- `generar_desde_contrato` y `generar`: se producen desde el contrato.

No inventes campos, rutas, mapeos, políticas ni nombres.
No sustituyas el .yaml de CTRLLENGTHCPY por el .xsd; lee el WDO primero.
El XSD lo produce el script, no tú.
Si falta un dato, reporta BLOQUEO con el campo exacto que falta.
Declara pendiente lo que requiera compilación en ACE Toolkit.
```

## Selección y resolución de plantilla

La plantilla se resuelve por **repositorio y rama** asociada al dominio (`IBS`, `HUB`, `ORQ`), tomando siempre el último commit (`HEAD`) de la rama correspondiente en el momento de procesar la generación. No se congela un commit fijo en los contratos para permitir que cualquier mejora de la plantilla aplique de inmediato.

| Dominio | Rama | Subdirectorio |
|---|---|---|
| `IBS` | `IBS` | `app213-payexe-prorev-core-upda-s-ops-ace` |
| `HUB` | `HUB` | `app213-payexe-prorev-hub-upda-s-ops-ace` |
| `ORQ` | `ORQ` | `app213-payinfass-agrdeblis-retr-b-ops-ace` |

El perfil y el validador garantizan que la URL, la rama y el subdirectorio existan. En tiempo de generación, el clon se realiza apuntando a la rama (`git clone --branch <BRANCH> --single-branch ...`) y el HEAD resultante se toma dinámicamente como versión de trabajo.

## Pruebas

```bash
python -m pytest tests/ -q
```

37 pruebas. Cada regla del plan tiene la suya de romperla: commit placeholder,
orquestador sin orquestación, AS400 sin copybook, campo sin mapeo, operaciones
duplicadas, plantilla sin commit, `minOccurs != maxOccurs`, `.yaml` vs `.xsd`.

Una regla sin prueba es una regla que nadie sabe si sigue viva.
