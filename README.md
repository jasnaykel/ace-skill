# ace-skill

## Guia para principiantes

Esta guia explica que es `ace-skill`, para que sirve y como utilizarla aunque no tengas conocimientos de informatica, IBM ACE o inteligencia artificial.

---

## 1. Que es ace-skill

`ace-skill` es un conjunto de instrucciones para que la IA pueda actuar como desarrollador de integraciones IBM App Connect Enterprise.

La skill le indica a la IA:

- Como leer los documentos funcionales y tecnicos de un servicio.
- Como elegir la plantilla correcta del servicio.
- Como crear flujos de integracion, contratos, transformaciones y configuraciones.
- Como aplicar seguridad, auditoria, manejo de errores y logging.
- Como crear pruebas Postman.
- Como validar que la estructura generada sea compatible con IBM ACE.
- Como documentar el servicio en un README tecnico.

En palabras simples: la skill es un manual de trabajo que la IA consulta para construir un servicio ACE siguiendo el estandar de la fabrica de integraciones.

La skill no es IBM ACE, no es un servidor y no reemplaza IBM ACE Toolkit. La skill genera y valida archivos; la compilacion y el despliegue final deben realizarse en el entorno ACE correspondiente.

---

## 2. Que es IBM ACE

IBM App Connect Enterprise, conocido como IBM ACE, es una plataforma que conecta sistemas diferentes.

Por ejemplo, un servicio ACE puede:

1. Recibir una solicitud de una aplicacion movil.
2. Validar los datos recibidos.
3. Transformar JSON a SOAP, XML o una estructura de backend.
4. Invocar un sistema bancario.
5. Transformar la respuesta.
6. Devolver una respuesta al consumidor.
7. Registrar auditoria y errores.

La skill ayuda a generar los archivos que representan ese proceso.

---

## 3. Que puede hacer la skill

La skill puede ayudar a:

- Generar un desarrollo base desde documentos SCI y ETI.
- Crear servicios atomicos de IBS.
- Crear servicios atomicos de HUB.
- Crear servicios orquestadores de negocio.
- Crear o modificar flujos ACE.
- Crear archivos ESQL.
- Crear contratos OpenAPI y JSON Schema.
- Crear subflows y handlers de error.
- Crear configuraciones DEV, QAS y PRD.
- Crear policies de usuario y Active Directory.
- Crear workdir overrides.
- Crear colecciones Postman.
- Revisar la estructura de un servicio existente.
- Detectar que faltan archivos o configuraciones.
- Preparar una entrega para Toolkit, pipeline o despliegue.

---

## 4. Que no hace automaticamente

La skill no debe considerarse un boton de despliegue automatico.

Por seguridad y control, la IA no debe:

- Inventar datos que no esten en el SCI, ETI o plantilla.
- Inventar credenciales.
- Inventar certificados.
- Inventar contrasenas LDAP.
- Publicar servicios en produccion sin autorizacion.
- Compilar realmente en ACE Toolkit si no tiene ese entorno disponible.
- Reemplazar archivos del framework compartido sin autorizacion.
- Usar una plantilla IBS para un servicio HUB.
- Usar una plantilla atomica para un servicio orquestador.

Cuando falte informacion importante, la respuesta correcta es `BLOQUEO` o `PENDIENTE`, no una suposicion.

---

## 5. Archivos que necesitas entregar

Para generar un servicio desde cero normalmente necesitas dos documentos.

### SCI

El SCI describe **que necesita el negocio**.

Suele contener:

- Nombre funcional.
- Tipo de componente.
- Capa del servicio.
- Consumidores.
- Productor o backend.
- Campos de entrada.
- Campos de salida.
- Campos obligatorios.
- Reglas de negocio.
- Ejemplos.

Ejemplo de nombre:

```text
SCI_BUS_Pagar_Recaudacion_HUB.md
```

### ETI

El ETI describe **como debe construirse tecnicamente** el servicio.

Suele contener:

- Nombre tecnico.
- Ruta BIAN.
- Metodo HTTP.
- Headers.
- Request y response.
- Mapeo hacia el backend.
- Endpoints por ambiente.
- Timeout.
- Seguridad.
- Auditoria.
- Manejo de errores.
- Informacion de despliegue.

Ejemplo de nombre:

```text
ETI_162_BUS_Pagar_Recaudacion_HUB.md
```

Si falta el SCI o el ETI, la generacion debe detenerse.

### 5.1 El copybook es opcional

El SCI y el ETI siempre son obligatorios. El **copybook no**.

El copybook es la descripcion de la trama que un servicio envia o recibe de un
programa COBOL o RPG. No todos los servicios lo usan.

| Tipo de servicio | Copybook |
|---|---|
| Servicio atomico que consume una trama IBS con programa RPG | **Si, obligatorio** |
| Servicio orquestador que coordina otros servicios | **No aplica** |
| Servicio que solo consume o expone REST | **No aplica** |

Un servicio sin copybook **no esta incompleto**. En ese caso la skill no crea la
capa DFDL: no genera `IBMdefined/`, `importFiles/`, el `.xsd` del PCML ni el
`.yaml` de control de longitud.

Inventar un copybook para "completar" un servicio que no lo tiene es un error,
no una mejora. Si el ETI indica que hay trama COBOL y el copybook no esta
disponible, la respuesta correcta es `BLOQUEO`.

---

## 6. Como se elige la plantilla

La eleccion se realiza usando un encabezado exacto dentro del ETI. No se debe elegir por intuicion, nombre del backend o nombre de la carpeta.

### Servicio atomico IBS

El ETI debe contener:

```markdown
# Componente IBS
```

La skill usa:

```text
Rama: IBS
Plantilla: app213-payexe-prorev-core-upda-s-ops-ace
```

### Servicio atomico HUB

El ETI debe contener:

```markdown
# Componente API REST
```

La skill usa:

```text
Rama: HUB
Plantilla: app213-payexe-prorev-hub-upda-s-ops-ace
```

### Servicio orquestador

El ETI debe contener:

```markdown
# Componente Orquestador
```

La skill usa:

```text
Rama: ORQ
Plantilla: app213-payinfass-agrdeblis-retr-b-ops-ace
```

Un orquestador normalmente coordina uno o mas servicios atomicos. Por ejemplo, puede validar una solicitud, consultar un servicio IBS, decidir una ruta e invocar despues un servicio HUB.

Si el encabezado no existe o es ambiguo, la skill debe informar `BLOQUEO` y solicitar que se corrija el ETI.

### 6.1 La plantilla se resuelve por rama, no por commit

La skill clona la plantilla usando el **repositorio y la rama** del dominio, y
trabaja sobre la version mas reciente de esa rama.

```text
Rama IBS  ->  rama IBS  ->  app213-payexe-prorev-core-upda-s-ops-ace
Rama HUB  ->  rama HUB  ->  app213-payexe-prorev-hub-upda-s-ops-ace
Rama ORQ  ->  rama ORQ  ->  app213-payinfass-agrdeblis-retr-b-ops-ace
```

Por que por rama y no por commit:

| Opcion | Comportamiento |
|---|---|
| Commit fijo | La plantilla queda congelada. Una mejora publicada despues no llega al servicio. |
| Rama | La plantilla se actualiza sola. La mejora publicada aplica sin tocar el contrato ni el prompt. |

El commit no se borra del reporte: se registra como evidencia de **con que
version se genero** el servicio. Es informacion de salida, no una entrada que
bloquee futuras generaciones.

Si el subdirectorio de la plantilla no existe en la rama indicada, la skill
informa `BLOQUEO`. Nunca debe sustituirse por la plantilla de otra rama ni por
una copia local antigua.

---

## 7. Como pedir una generacion

No necesitas escribir codigo. Debes indicar a la IA donde estan los documentos y que deseas generar.

### Prompt recomendado

```text
Usando la skill ace-skill, genera el desarrollo base completo del servicio.

SCI:
D:\ruta\SCI_Servicio.md

ETI:
D:\ruta\ETI_Servicio.md

Genera los archivos en:
D:\ruta\mi-proyecto

No inventes datos. Si falta informacion, declara BLOQUEO.
Valida la estructura, crea el README tecnico global y entrega la tabla de trazabilidad.
```

### Si los documentos estan en Downloads

```text
Usando ace-skill, desarrolla el servicio utilizando:

SCI: C:\Users\<usuario>\Downloads\SCI_Servicio.md
ETI: C:\Users\<usuario>\Downloads\ETI_Servicio.md

Genera el proyecto en:
D:\jasna\Trabajo\Trabajo IBM\Azure\IA IBM\mi-servicio
```

### Si ya existe un proyecto

```text
Usando ace-skill, revisa y completa este proyecto:

D:\ruta\proyecto-ace

Usa como referencia:
SCI: D:\ruta\SCI.md
ETI: D:\ruta\ETI.md

No borres cambios existentes. Indica que archivos modificas y valida el resultado.
```

### Para generar solo documentacion

```text
Usando ace-skill, genera o completa el README tecnico global del servicio a partir de:

SCI: D:\ruta\SCI.md
ETI: D:\ruta\ETI.md

No modifiques codigo ni configuraciones.
```

---

## 8. Que ocurre durante la generacion

La IA debe seguir este proceso:

1. Leer el SCI y el ETI completos.
2. Revisar que ambos documentos existan.
3. Leer el encabezado selector del ETI.
4. Seleccionar IBS, HUB u ORQ.
5. Descargar o clonar la plantilla remota correcta.
6. Revisar el contenido real de la plantilla.
7. Revisar las guias tecnicas de `ace-flowpilot` cuando sean necesarias.
8. Construir el proyecto sin mezclar plantillas.
9. Parametrizar nombres, rutas, contratos y configuraciones.
10. Crear los flujos y subflows.
11. Crear los archivos ESQL permitidos.
12. Crear policies y configuraciones por ambiente.
13. Crear la coleccion Postman.
14. Crear el README tecnico global.
15. Ejecutar validaciones estaticas.
16. Entregar un resumen, pendientes, bloqueos y trazabilidad.

---

## 9. Estructura de salida esperada

Un servicio ACE normalmente contiene una estructura similar a esta:

```text
mi-servicio/
  README.md
  azure-pipelines.yml
  ci/
    valid_cfg_values.yaml
    Monitoring.json
  src/
    application/
      APP_<Servicio>/
    v1.0/
      service/
        <Servicio>/
      configuration/
        DEV/
        QAS/
        PRD/
  test/
    <Servicio>.postman_collection.json
```

Los nombres exactos dependen de la plantilla seleccionada. La skill no debe inventar una estructura diferente si la plantilla ya define una.

---

## 10. Ambientes

Los servicios normalmente tienen tres ambientes:

| Ambiente | Significado |
|---|---|
| DEV | Desarrollo |
| QAS | Certificacion o pruebas |
| PRD | Produccion |

Cada ambiente puede tener valores diferentes para:

- URL del backend.
- Timeout.
- Grupo LDAP.
- Certificados.
- Policies.
- Cantidad de instancias.
- Rutas de entrada.

Las credenciales, tokens y certificados no deben guardarse directamente en el codigo fuente.

---

## 11. Archivos importantes

### ESQL

Los archivos `.esql` contienen logica de transformacion, validacion, preparacion de requests y construccion de respuestas.

No se deben modificar las librerias compartidas `LIB_CORE_*` ni `LIB_SMF_*`.

### Message flow

Los archivos `.msgflow` representan el flujo principal de mensajes.

### Subflow

Los archivos `.subflow` representan bloques reutilizables, como:

- Validacion.
- HealthCheck.
- Respuesta valida.
- Manejo de Catch.
- Manejo de Failure.
- Manejo de Timeout.

### Policy

Las policies contienen configuraciones externas al codigo, como destinos y grupos de seguridad.

### WDO

Los archivos `wdo-*.txt` permiten sobrescribir valores del flujo por ambiente.

### Postman

La coleccion Postman permite probar el servicio con solicitudes de exito y error.

### README tecnico

El `README.md` de la raiz debe ser el documento ETI tecnico completo del servicio. No debe ser un README corto de marketing ni el README heredado de otra plantilla.

---

## 12. Que significa un BLOQUEO

`BLOQUEO` significa que la IA no debe continuar porque falta informacion necesaria o existe una contradiccion.

Ejemplos:

- Falta el SCI.
- Falta el ETI.
- El ETI no tiene encabezado selector.
- La plantilla ORQ no existe en la rama indicada.
- El backend no esta definido.
- Falta el contrato de entrada o salida.
- Falta el mapeo de campos.
- La plantilla no contiene la estructura necesaria.
- Faltan `.project` obligatorios.
- El README tecnico global esta incompleto.

Cuando aparezca un bloqueo, debes proporcionar la informacion solicitada y volver a ejecutar la generacion.

---

## 13. Como interpretar la respuesta de la IA

Una respuesta correcta debe indicar:

### Generado

Archivos y carpetas que fueron creados o modificados.

### Validado

Comprobaciones que se ejecutaron, por ejemplo:

- JSON valido.
- XML valido.
- Rutas correctas.
- Nombres coherentes.
- Policies presentes.
- README presente.

### Pendiente

Acciones que necesitan ACE Toolkit, certificados, credenciales, datos de infraestructura o aprobacion.

### Bloqueos

Problemas que impiden continuar.

### Trazabilidad

Tabla que relaciona cada requisito del SCI/ETI con el archivo que lo implementa.

---

## 14. Validacion del README tecnico

La skill incluye un validador para comprobar el README global:

```text
C:\Users\%USERNAME%\.agents\skills\ace-skill\scripts\validate_readme_eti.py
```

Uso para IBS:

```powershell
python C:\Users\%USERNAME%\.agents\skills\ace-skill\scripts\validate_readme_eti.py --root D:\ruta\proyecto --domain IBS
```

Uso para HUB:

```powershell
python C:\Users\%USERNAME%\.agents\skills\ace-skill\scripts\validate_readme_eti.py --root D:\ruta\proyecto --domain HUB
```

Uso para ORQ:

```powershell
python C:\Users\%USERNAME%\.agents\skills\ace-skill\scripts\validate_readme_eti.py --root D:\ruta\proyecto --domain ORQ
```

El validador comprueba que:

- Exista `README.md` en la raiz.
- La primera linea tenga el formato correcto.
- Existan las secciones ETI principales.
- No queden placeholders.
- Existan datos del componente.
- No se use por error el productor IBS por defecto en un servicio HUB.

---

## 15. Recomendaciones para trabajar con la IA

- Indica siempre las rutas completas de los archivos.
- Di claramente si quieres generar, revisar, corregir o documentar.
- Pide que no se inventen datos.
- Pide que se informen los bloqueos antes de continuar.
- Conserva los documentos SCI y ETI junto con el proyecto.
- No compartas contrasenas ni certificados privados en el chat.
- Revisa los pendientes antes de solicitar un despliegue.
- Para cambios grandes, pide primero un analisis y despues la implementacion.

---

## 16. Ejemplos de solicitudes frecuentes

### Revisar un proyecto

```text
Usando ace-skill, revisa la sanidad estructural de D:\ruta\proyecto-ace.
No modifiques archivos. Reporta errores, riesgos y pendientes.
```

### Completar configuracion

```text
Usando ace-skill, desarrollame el siguiente servicio , se le pasa el documento ETI Y SCI.
```

### Preparar pruebas

```text
Usando ace-skill, revisa y completa la coleccion Postman del servicio D:\ruta\proyecto-ace.
Incluye escenarios exitosos y errores de validacion.
```

### Preparar entrega

```text
Usando ace-skill, prepara el reporte de entrega del servicio D:\ruta\proyecto-ace.
Incluye checklist DoD, bloqueos, pendientes y tabla de trazabilidad.
```

---

## 17. Ubicacion de la skill

La skill instalada se encuentra en:

```text
C:\Users\%USERNAME%\.agents\skills\ace-skill
```

El archivo principal de instrucciones es:

```text
C:\Users\%USERNAME%\.agents\skills\ace-skill\SKILL.md
```

Este README es una guia para la persona usuaria. `SKILL.md` contiene las reglas internas que debe seguir la IA.

---

### 18 Opcion A: copiar la carpeta al agente

Si tu otra IA utiliza una carpeta de skills, copia `ace-skill` completa dentro de esa carpeta.

Ejemplo generico:

```text
<carpeta-de-skills-del-agente>/ace-skill
```

Despues reinicia el agente para que detecte la nueva skill.

Importante: copia la carpeta completa, no solo `SKILL.md`. Los modulos internos son necesarios para cumplir las reglas.

### 18.1 Opcion B: cargar el archivo SKILL.md

Si tu otra IA no tiene carpeta de skills, puedes pegarle el contenido del archivo:

```text
C:\Users\%USERNAME%\.agents\skills\ace-skill\SKILL.md
```

Instruccion sugerida:

```text
A partir de ahora sigue las reglas del documento que te pegare como manual de trabajo.
Si te pido generar un servicio IBM ACE, primero lee el manual completo y luego
leelos los modulos internos de la carpeta de la skill antes de crear archivos.
```

Si la IA no puede leer archivos de tu disco, tendras que copiar tambien el contenido de los modulos que necesite, por ejemplo:

```text
generation-workflow/generation-workflow.md
templates/templates.md
templates/readme-eti-template.md
validation-checklist/validation-checklist.md
standards/standards.md
```

### 18.2 Opcion C: usar la skill desde un chat sin archivos

En este caso la IA no tendra la carpeta. deberas pegarle las instrucciones y los documentos del servicio.

Ejemplo de mensaje completo:

```text
Actua como desarrollador IBM ACE senior. Estas son mis reglas de trabajo:

1. Necesito un SCI y un ETI. Si falta alguno, detenete e informa BLOQUEO.
2. Elige la plantilla segun el encabezado del ETI:
   - "# Componente IBS" usa la plantilla IBS.
   - "# Componente API REST" usa la plantilla HUB.
   - "# Componente Orquestador" usa la plantilla ORQ.
3. No inventes datos, URLs, credenciales ni certificados.
4. Genera el README tecnico global completo.
5. Entrega checklist DoD, bloqueos, pendientes y tabla de trazabilidad.

Aqui esta mi SCI:
<pegar SCI>

Aqui esta mi ETI:
<pegar ETI>
```

### 18.3 Compatibilidad con otras IAs

La skill esta escrita en Markdown, YAML, XML, JSON y ESQL, por lo que puede leerse en la mayoria de IAs.

| Tipo de IA | Como usarla | Limitaciones |
|---|---|---|
| Agente con acceso a archivos | Copia la carpeta de skills | Debe poder crear archivos y ejecutar comandos |
| Chat con carga de archivos | Sube `SKILL.md` y modulos | No podra clonar plantillas si no tiene red |
| Chat sin archivos | Pega las reglas y el SCI/ETI | Sin validaciones automaticas |
| IA sin escritura de archivos | Solo analisis y revision | No podra generar el proyecto |

### 18.4 Requisitos para que la IA pueda seguir la skill

- Poder leer archivos de texto.
- Poder crear y editar archivos.
- Poder ejecutar comandos si se validan scripts.
- Tener acceso a internet para descargar las plantillas.
- Respetar la instruccion de declarar BLOQUEO en vez de inventar.

Si tu IA no cumple alguno de estos requisitos, informale que la skill no aplica del todo y acuerda manualmente que partes se cumpliran.

### 18.5 Verificar que la otra IA Following the rules worked

Pide a la otra IA que te confirme:

```text
Antes de empezar, enumera:
1. Que archivos de la skill leiste.
2. Que plantilla seleccionaste y por que.
3. Que datos del SCI y ETI usaste.
4. Que archivos generaste.
5. Que pendientes quedan.
```

Si la respuesta no menciona la plantilla seleccionada, el README tecnico o el DoD, es probable que la IA no haya leido la skill completa.

### 18.6 Instalar la skill en otro equipo

Para compartir la skill con otra persona o equipo:

1. Comprime la carpeta `ace-skill` completa.
2. Enviala por el medio aprobado en tu organizacion.
3. Indica que debe descomprimirse dentro de la carpeta de skills del agente.
4. Verifica que exista el archivo `SKILL.md` en la ruta final.
5. Pide una prueba generating un servicio pequeno.

No se deben compartir certificados, llaves privadas ni credenciales junto con la skill.

---

## 19. Capa de contratos: del SCI y ETI al contrato

Ademas del modo directo (la IA lee el SCI y el ETI y genera), existe una **capa
de preparacion**: un archivo `contrato.yaml` que concentra los datos del servicio
y se valida antes de generar.

Esto no reemplaza al modo directo. El modo directo sigue siendo el predeterminado.

### 19.1 Que aporta

El contrato sirve para tres cosas:

1. **Validar antes de generar.** Detecta campos sin mapeo, operaciones duplicadas
   o copybook faltante, sin escribir una sola linea de ACE.
2. **Producir la documentacion.** Genera `openapi.yaml` y `request.schema.json`
   consistentes con el ETI.
3. **Evitar que la IA invente.** La IA recibe datos ya estructurados en vez de
   deducirlos del texto libre.

### 19.2 Flujo de trabajo

```powershell
# 1. Extraer un contrato minimo desde los documentos (no inventa datos)
python C:\Users\jcprieto\.agents\skills\ace-skill\scripts\extraer_contrato.py `
  SCI.md ETI.md -o contrato.yaml

# 2. Completar a mano lo que falte: request, response, mapeos, copybook

# 3. Validar
python C:\Users\jcprieto\.agents\skills\ace-skill\scripts\validar_contrato.py contrato.yaml

# 4. Si el servicio consume trama COBOL, generar el XSD desde el copybook
python C:\Users\jcprieto\.agents\skills\ace-skill\scripts\generate_cobol_dfdl_xsd.py `
  RE0055RI.cpy RE0055RI.xsd

# 5. Generar el paquete para la IA
python C:\Users\jcprieto\.agents\skills\ace-skill\scripts\generar_openapi.py `
  contrato.yaml -d paquete\
```

El paso 4 se omite cuando el servicio no usa copybook.

### 19.3 Archivos que produce

Todos en la carpeta `paquete\`:

| Archivo | Para que sirve |
|---|---|
| `openapi.yaml` | Contrato HTTP del servicio |
| `request.schema.json` | Validacion de entrada del REST API |
| `parametros.json` | Nombres que la IA ya usa, sin reescribir la logica |
| `artefactos.yaml` | Que se copia, que se parametriza y que se genera |
| `contrato.resuelto.yaml` | Contrato con el perfil del proyecto aplicado |

### 19.4 Codigos de salida

Los scripts usan los mismos codigos:

```text
0 correcto  ·  1 advertencias  ·  2 bloqueante  ·  3 error tecnico
```

Un `2` significa que no se debe generar. Debes corregir el contrato o los
documentos y volver a ejecutar.

### 19.5 Ejemplo de solicitud

```text
Usando ace-skill, crea el contrato del servicio 158 a partir de:

SCI: D:\ruta\SCI_SRV_Orquestador Pagar Recaudacion.md
ETI: D:\ruta\README.md

Guarda el contrato y el paquete en:
D:\ruta\contratos\158_BUS_orquestador_pagar_recaudacion

No generes el desarrollo del servicio, solo la parte documental.
```

### 19.6 Validaciones disponibles

| Script | Que comprueba |
|---|---|
| `validar_contrato.py` | Esquema, mapeos, copybook, operaciones duplicadas |
| `generate_cobol_dfdl_xsd.py` | Genera el XSD desde el copybook (solo con copybook) |
| `generar_openapi.py` | Produce el paquete documental |
| `gate_estructural.py` | ESQL, XML, referencias `esql://routine`, residuos de plantilla |
| `verify_scaffold.py` | OpenAPI, `BROKER SCHEMA`, `restapi.descriptor`, codificacion |
| `validate_readme_eti.py` | README tecnico global del servicio |

El gate estructural y el verificador de scaffolding se ejecutan **despues de
generar el proyecto**, no sobre el contrato.

### 19.7 Precedencia cuando las fuentes no coinciden

```text
copybook           > contrato     estructura fisica DFDL (si existe)
contrato aprobado  > perfil       datos del servicio
perfil del proyecto> plantilla    convenciones comunes
plantilla          > IA           estructura de archivos
SCI / ETI          = trazabilidad
```

Si el contrato contradice al copybook, la generacion se detiene. Si el SCI y el
ETI se contradicen entre si, tambien se detiene: es una inconsistencia de
documentacion y se corrige en el origen.
