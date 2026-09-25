# framework-setup — Configuración inicial del entorno local de desarrollo IBM ACE

## Propósito
Configuración del entorno local de desarrollo IBM ACE: instalación de ACE 12 y MQ 9, clonación del framework y preparación del Toolkit. Ejecutar una sola vez por máquina o cuando se renueve el entorno.

## Cuándo usar este módulo
| Situación | Acción |
|---|---|
| Máquina nueva / entorno desde cero | Seguir todas las fases en orden |
| Solo reinstalar IBM MQ | Ir a FASE 2 |
| Solo clonar/actualizar el framework | Ir a FASE 3 |
| Solo configurar las perspectivas del Toolkit | Ir a FASE 4 |

---

## FASE 1 — Instalación de IBM ACE 12.0.x
1. Descargar desde: [Google Drive — IBM ACE 12.0.x](https://drive.google.com/file/d/1wZDfkd03ZRhzpeNII2g1mI49sTdC506g/view?usp=drive_link)
2. Ejecutar el instalador como **administrador**
3. Verificar instalación:
   ```cmd
   mqsiprofile
   mqsilist
   ```
4. Abrir **IBM ACE Toolkit** (Eclipse-based) desde el acceso directo creado

---

## FASE 2 — Instalación de IBM MQ 9.x
1. Descargar desde: [Google Drive — IBM MQ 9.x](https://drive.google.com/file/d/1hdiyF52AgfTrWgY8BQos2hI2g1mI49sTdC506g/view?usp=drive_link)
2. Ejecutar el instalador como **administrador**
3. Verificar instalación:
   ```cmd
   dspmqver
   ```
   Debe mostrar la versión 9.x instalada.

---

## FASE 3 — Clonar repositorios del framework (rama `dev`)
Estos repositorios deben estar siempre actualizados desde Azure DevOps:

| Repositorio | URL Azure DevOps |
|---|---|
| `core` | https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/core |
| `subflows` | https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/subflows |
| `policies` | https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/policies |
| `core_utils` | https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/core_utils |
| `creatorApp-java` | https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/creatorApp-java |

```cmd
git clone https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/core -b dev
git clone https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/subflows -b dev
git clone https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/policies -b dev
git clone https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/core_utils -b dev
git clone https://dev.azure.com/SOAINTCORP/PER_Fabrica_BANBIF/_git/creatorApp-java -b dev
```

> Siempre trabajar sobre la rama **`dev`**. No usar `main` para desarrollo local.

---

## FASE 4 — Importar framework en IBM ACE Toolkit
1. Abrir **IBM ACE Toolkit**
2. File → Import → Existing Projects into Workspace
3. Importar (en este orden):
   - `core`
   - `subflows`
   - `policies`
   - `core_utils`
4. Verificar que no hay errores de compilación en ninguno de los proyectos

---

## FASE 5 — Abrir perspectivas necesarias
En el Toolkit:
1. Window → Perspective → Open Perspective → **Integration Development** (principal)
2. Window → Perspective → Open Perspective → **Debug**
3. Window → Perspective → Open Perspective → **Git**
4. Window → Perspective → Open Perspective → **Java**

---

## FASE 6 — CreatorApp legado (opcional)
Esta fase no es necesaria para generar servicios IBS. La fuente canónica IBS es el repositorio remoto `https://github.com/Karinadr/plantillas-AI/tree/IBS`, que debe clonarse y analizarse según `templates/templates.md`. Solo preparar CreatorApp si se solicita explícitamente una generación histórica local.

Estructura en `Z:\Java\`:
```
Z:\Java\
├── app\          ← copiar: creatorApp-java\src\main\resources\templates\template_api_xxxx
├── template\
└── templates\
    └── docs\
        └── F01\  ← copiar: creatorApp-java\src\main\resources\templates\docs\F01
```
> Solo necesaria para la **Opción B (local)** de generación de plantillas. Con la Opción A (Techzone) no hace falta.

---

## FASE 7 — Importar collection Postman del framework
1. Abrir **Postman**
2. Import → seleccionar la colección de `creatorApp-java\src\main\resources\test`
3. Verificar que aparece la colección con los requests: `Generate_APP+Collection`

---

## Checklist de entorno listo
- [ ] `mqsiprofile` ejecuta sin errores
- [ ] `mqsilist` muestra Integration Nodes (puede estar vacío en primer uso)
- [ ] `dspmqver` muestra IBM MQ 9.x
- [ ] Los 4 proyectos del framework están en el workspace del Toolkit sin errores
- [ ] Las 4 perspectivas están abiertas en el Toolkit
- [ ] Postman tiene importada la collection del framework
- [ ] (Opcional) Carpeta `Z:\Java\` preparada si se usará generación local

## Referencias internas
- `service-dev/service-dev.md` (opción local de CreatorApp, configuración de pruebas locales).
- `fundamentals/fundamentals.md` (mecánica del Toolkit y entorno).
