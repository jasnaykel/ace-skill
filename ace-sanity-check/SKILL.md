---
name: ace-sanity-check
description: "Validación de sanidad para la collection Postman de servicios ACE (Bus) en BanBif. Verifica estructura por ambiente y exposición, info, carpetas, headers, requests, payload y rutas conforme al estándar corporativo."
---

# Sanidad ACE - Validación de Collection Postman

Esta skill valida que la collection Postman de un servicio ACE conserve la estructura operable esperada para pruebas por ambiente y tipo de exposición, antes de su entrega (evidencia F04).

## Objetivo

Validar que la collection Postman de un servicio ACE conserve la estructura operable esperada para pruebas por ambiente y tipo de exposición.

## Alcance

- Archivo objetivo: `<ruta-del-test>/*.postman_collection.json`.
- Aplica a collections Postman exportadas en JSON.
- La comparación valida estructura, nombre, descripción, carpetas, requests, headers, payload, métodos y respuestas ejemplo.
- No se validan IDs de Postman, exporter ID, host ni valores concretos de payload.

## Estructura Esperada

```text
<collection>
└── v1.0
    ├── MTLS
    │   ├── DEV
    │   │   ├── Healthcheck
    │   │   └── <Operacion principal>
    │   ├── QAS
    │   │   ├── Healthcheck
    │   │   └── <Operacion principal>
    │   └── PRD
    │       ├── Healthcheck
    │       └── <Operacion principal>
    └── ONPREM
        ├── DEV
        │   ├── Healthcheck
        │   └── <Operacion principal>
        ├── QAS
        │   ├── Healthcheck
        │   └── <Operacion principal>
        └── PRD
            ├── Healthcheck
            └── <Operacion principal>
```

## README.md raíz (base del nombre de la collection)

- El `README.md` en la raíz del repositorio debe existir y ser el **documento ETI completo** del servicio (plantilla `# <ID>_BUS_<nombre>`, `## 1. Alcance`, `## 2. Pre-requisitos`, `## 3. Información del Componente`, ..., `# 12 Historial de Revisiones`).
- La primera línea `# <ID>_BUS_<nombre operacion>` es la fuente para derivar `<ID>` y `<nombre operacion>` de la collection (ver Info Esperado).
- El README ETI y la collection Postman deben derivarse del mismo nombre (`<ID>` y `<nombre operacion>` idénticos).
- La validación de sanidad del pipeline (`/home/aceuser/README.md`) exige que la tabla `## 3. Información del Componente` contenga las filas `| \`Producto\` | valor |` y `| \`Línea de Producto\` | valor |` (ver catálogo de errores, E1).

## Info Esperado

- El nombre del archivo debe cumplir `ACE <ID> <nombre operacion>.postman_collection.json`.
- `<ID>` y `<nombre operacion>` se derivan igual que `info.name`.
- Ejemplo: `ACE 139 Consultar Deudas Recaudaciones Hub.postman_collection.json`.
- `info.schema` debe ser `https://schema.getpostman.com/json/collection/v2.1.0/collection.json`.
- `info.name` debe cumplir `ACE <ID> <nombre operacion>`.
- `<ID>` y `<nombre operacion>` se derivan de la primera línea de `README.md`, quitando `#`, separando por `_` y descartando el token técnico `BUS` cuando exista.
- El primer token numérico es `<ID>`.
- Los tokens restantes forman `<nombre operacion>` separados por espacios, respetando su orden original.
- Ejemplo: `# 139_BUS_Consultar_Deudas_Recaudaciones_Hub` genera `ACE 139 Consultar Deudas Recaudaciones Hub`.
- `info.description` debe iniciar con `Usar credenciales de usuarios AD para cada ambiente.`.

## Carpetas Esperadas

- Debe existir una carpeta de versión `v1.0`.
- Deben existir las carpetas de exposición `MTLS` y `ONPREM` dentro de `v1.0`.
- Cada exposición debe contener los ambientes `DEV`, `QAS` y `PRD`.
- Cada ambiente debe contener exactamente los casos funcionales mínimos: `Healthcheck` y la operación principal del servicio.
- El nombre de la operación principal debe ser `<nombre operacion>` derivado desde la primera línea de `README.md`, usando la misma regla de `info.name` pero sin el prefijo `ACE <ID>`.

## Headers Obligatorios

TODAS las requests (operación principal Y Healthcheck) deben incluir estos 5 headers obligatorios:

```text
Content-Type
Time-Stamp
Bif-Correlation-Id
Bif-Consumer-Id
Bif-Mdw-Id
```

## Headers Opcionales

Estos headers son opcionales (pueden incluirse; el validador no los exige):

```text
Host-Id        # regex ^.{7,15}$
Branch-Code    # regex ^.{5,30}$
Country-Code   # regex ^.{5,30}$
User-Id        # longitud [0,10]
Device-Id      # longitud [5,30]
```

## Header Authorization PROHIBIDO

- **NO debe existir el header `Authorization` en ninguna request.** El validador lo rechaza (`no debe existir header Authorization`).
- La autenticación del canal `ONPREM` se define con el bloque `request.auth` (Basic Auth con `{{ldapUser}}` / `{{ldapPassword}}`), no con un header.

## Estados de Headers por Ambiente

- En `DEV` y `QAS`, los headers obligatorios deben estar habilitados y con valor definido no vacío (`Content-Type` = `application/json`).
- En `DEV` y `QAS`, los headers opcionales, si se incluyen, deben respetar su regex/longitud.
- En `PRD`, todos los headers deben estar habilitados y con valor **vacío** (`"value": ""`) para que operación los complete antes de ejecutar.

## Request Healthcheck

- El request debe llamarse `Healthcheck`.
- El método debe ser `GET`.
- La ruta debe terminar en `health`.
- No debe tener payload, o el payload debe estar vacío.
- **Debe incluir los 5 headers obligatorios** (en `DEV`/`QAS` con valor; en `PRD` vacíos).

## Request Operación Principal

El nombre de la operación principal debe ser `<nombre operacion>` derivado desde la primera línea de `README.md`.

## Payload Esperado

- La operación principal puede usar cualquier método definido por el OpenAPI principal del servicio REST Bus.
- Si el método y el OpenAPI principal definen request body, la collection debe incluir payload.
- Si existe payload, `request.body.mode` debe ser `raw`.
- Si existe payload, `request.body.options.raw.language` debe ser `json`.
- En `DEV` y `QAS`, si existe payload, debe estar definido, no vacío y con datos de prueba.
- En `PRD`, si existe payload, debe respetar la estructura del schema de request del OpenAPI principal del servicio REST Bus.
- En `PRD`, los campos hoja del payload deben tener valor `null`; los objetos y arrays se conservan solo para representar la estructura del contrato.
- Si el OpenAPI principal no define request body para la operación, la collection no debe inventar payload.

## Rutas Esperadas

- `request.url` debe ser objeto Postman, no string.
- `request.url` debe incluir `raw`, `protocol`, `host` como arreglo y `path` como arreglo.
- Si existe una tabla `Endpoint del Componente de Integracion`, cada request debe usar la URL absoluta definida para su carpeta de exposición y ambiente.
- No se deben usar variables de entorno para dominio o host cuando el endpoint está documentado.
- La ruta de `MTLS` debe contener el segmento `mtls`.
- La ruta de `ONPREM` debe contener el segmento `onprem`.
- La ruta debe contener el segmento de versión `v1.0`.
- Solo se valida host exacto cuando existe tabla de endpoints documentada para el servicio.

## Criterios de Aceptación

- Existe exactamente una collection Postman JSON objetivo o se indica explícitamente cuál validar.
- El nombre del archivo cumple `ACE <ID> <nombre operacion>.postman_collection.json` obtenido desde la primera línea de `README.md`.
- La collection parsea como JSON válido.
- `info.name` coincide con `ACE <ID> <nombre operacion>` obtenido desde la primera línea de `README.md`.
- `info.description` inicia con `Usar credenciales de usuarios AD para cada ambiente.`.
- La estructura de carpetas cumple `v1.0 / MTLS|ONPREM / DEV|QAS|PRD`.
- Cada ambiente tiene `Healthcheck` y una operación principal.
- Los headers esperados existen en cada request.
- Los headers están habilitados y vacíos/no vacíos según el ambiente.
- `Healthcheck` usa `GET`.
- `Healthcheck` no lleva payload.
- La operación principal usa el método definido por el OpenAPI principal, body raw JSON cuando aplica.
- Cada request usa `request.url` como objeto Postman con `raw`, `protocol`, `host[]` y `path[]`.
- Si existen endpoints documentados, las URLs de la collection coinciden con la exposición y ambiente de cada carpeta, sin variables de host.
- En `PRD`, headers vacíos y campos hoja del payload con valor `null` cuando apliquen.
- En `PRD`, el payload debe coincidir estructuralmente con el schema de request del OpenAPI principal del servicio REST Bus cuando aplique.

## Validación Manual Mínima

1. Abrir el `.postman_collection.json` como JSON.
2. Obtener `<ID>` y `<nombre operacion>` desde la primera línea de `README.md` y validar el nombre del archivo.
3. Confirmar `info.schema` versión 2.1.0.
4. Validar `info.name` con el mismo `<ID>` y `<nombre operacion>`.
5. Validar que `info.description` inicie con `Usar credenciales de usuarios AD para cada ambiente.`.
6. Recorrer `item` y validar carpetas `v1.0`, `MTLS`, `ONPREM`, `DEV`, `QAS`, `PRD`.
7. Validar headers, estado habilitado y valor vacío/no vacío por ambiente.
8. Validar método, path y ausencia de payload de `Healthcheck`.
9. Validar que `request.url` sea objeto Postman con `raw`, `protocol`, `host[]` y `path[]`.
10. Validar método contra el OpenAPI principal, body raw JSON cuando aplique.
11. Para `PRD`, comparar el payload contra el schema de request del OpenAPI principal del servicio REST Bus y confirmar valores hoja `null`.

## Verificación rápida de JSON válido

```bash
python -c "import json; json.load(open('archivo.postman_collection.json'))"
```

## Catálogo de Errores Frecuentes

### E1. README.md raíz no cumple el ETI (tabla Info del Componente incompleta)

```
[ERROR] No se pudo(eron) leer el/los campo(s) 'Producto' y 'Línea de Producto' desde la tabla '## 3. Información del Componente' en /home/aceuser/README.md. Verifique que la tabla tenga el formato '| `Producto` | valor |' y '| `Línea de Producto` | valor |' antes de continuar.
make[1]: *** [.scripts/makefiles/release.mk:20: release_ace] Error 1
make: *** [.scripts/makefiles/init.mk:2: init] Error 2
```

- **Causa**: el `README.md` en la raíz del repo no es el documento ETI completo (o su sección `## 3. Información del Componente` no tiene las filas `| \`Producto\` | valor |` y `| \`Línea de Producto\` | valor |`). Un README mínimo/marketing sin esa tabla falla la sanidad.
- **Solución**: reemplazar el README.md raíz por el **ETI completo del servicio** (plantilla con las secciones `# <ID>_BUS_<nombre>`, `## 1. Alcance del Componente Integración`, `## 2. Pre-requisitos`, `## 3. Información del Componente`, Arquitectura, BIAN, Implementación, Certificación, Seguridad, Auditoría, Infraestructura, Glosario, Historial de Revisiones). Dentro de `## 3. Información del Componente` debe estar:
  ```markdown
  | `Línea de Producto` | <valor> |
  | `Producto`           | <valor> |
  ```
- **Nota**: la primera línea del README también define el nombre de la collection (`ACE <ID> <nombre operacion>`), así que debe coincidir con `info.name` de la collection Postman (ver sección Info Esperado).
