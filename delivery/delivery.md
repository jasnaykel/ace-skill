# delivery — Proceso de entrega formal de servicios IBM ACE (F01, pipeline, Nexus, CP4I)

## Propósito
Proceso de entrega formal de servicios ACE al banco: F01, pipeline Azure DevOps, BAR a Nexus, despliegue CP4I, repositorios y correo formal.

## Cuándo usar este módulo
| Situación | Acción |
|---|---|
| Entregar un servicio ACE finalizado al banco | Seguir todas las fases |
| Solo subir BAR a Nexus | Ir a FASE 2 |
| Solo desplegar en Cloud Pak | Ir a FASE 3 |
| Solo elaborar el F01 | Ir a FASE 1 |

## Requisitos previos para iniciar la entrega
- [ ] Desarrollo ACE finalizado
- [ ] Pruebas unitarias locales completadas (Postman + certificados)
- [ ] **F04** — Documento de evidencias QA (Soaint) firmado por el Líder QA
- [ ] **F01** — Documento de despliegue elaborado
- [ ] Pipeline de validación de fuente pasando en Azure DevOps
- [ ] Código en rama `feature` en Azure DevOps

---

## FASE 1 — Elaborar el F01 (documento de despliegue)
El F01 debe incluir:
- Nombre y versión del servicio
- Descripción funcional
- Artefactos a desplegar (BAR files y versiones)
- Repositorios afectados (Azure DevOps + Bitbucket) con links a los commits
- URLs por ambiente (DEV / QAS / PRD)
- Configuración `valid_cfg_values` por ambiente
- Grupos LDAP por ambiente
- Destinos (destinations) configurados
- Instrucciones de rollback
- Datos de contacto del desarrollador responsable

---

## FASE 2 — Pipeline Azure DevOps y subida a Nexus

### 2.1 Crear pipeline de validación de fuente
En Azure DevOps → Pipelines → New Pipeline (8 pasos de configuración):
1. Seleccionar repositorio
2. Seleccionar template de validación ACE
3. Configurar nombre del pipeline
4. Definir trigger (rama `feature`)
5. Configurar agente de build
6. Agregar paso de compilación ACE
7. Agregar paso de publicación a Nexus
8. Guardar y ejecutar

### 2.2 Verificar pipeline verde
- El pipeline debe pasar sin errores antes de continuar
- Verificar en Nexus que el BAR quedó publicado con la versión correcta

---

## FASE 3 — Despliegue en Cloud Pak (OpenShift / CP4I)

### 3.1 Instalar / verificar utilitario `oc` (OpenShift CLI)
```cmd
oc version
```

### 3.2 Descargar BAR desde Nexus
```cmd
# Descargar el BAR correspondiente a la versión a desplegar
```

### 3.3 Desplegar en Cloud Pak
```cmd
# Login al cluster OpenShift
oc login <URL_CLUSTER> --token=<TOKEN>

# Verificar proyecto / namespace
oc project cp4i-ace

# Subir y desplegar el BAR
# (seguir procedimiento interno del pipeline de despliegue)
```

### 3.4 Verificar el despliegue
- Verificar en CP4I que el Integration Server levantó correctamente
- Ejecutar health check: `GET /v1.0/u/<nombre>/health`
- Revisar logs en CloudWatch que no haya errores de inicio

---

## FASE 4 — Subir fuentes a repositorios

### Repositorio Azure DevOps (Soaint)
Estructura de la rama `feature`:
```
docs/
├── F01_<NombreServicio>_v<version>.docx
└── F04_<NombreServicio>_v<version>.docx
src/
└── <proyecto-ace>/           ← fuentes del servicio
test/
└── <NombreServicio>.postman_collection.json
```

### Repositorio Bitbucket (Banco)
Solo fuentes y Postman; los documentos F01/F04 van a SharePoint.
```
src/
└── <proyecto-ace>/
test/
└── <NombreServicio>.postman_collection.json
```
1. Crear rama `feature/<ID-requerimiento>-<nombre-servicio>` desde `develop`
2. Commit de los archivos correspondientes
3. Crear **Pull Request** de `feature` → `develop`

---

## FASE 5 — Correo formal de entrega al banco

```
Asunto: [ENTREGA] <NombreServicio> v<version> — <ID Requerimiento>

Estimados,

Se realiza la entrega formal del siguiente servicio:

📋 SERVICIOS ENTREGADOS:
- Nombre funcional: <Nombre funcional>
- Nombre técnico: <NombreTecnico>
- Versión: v1.0
- Funcionalidad: <Descripción breve>

📁 DOCUMENTACIÓN (SharePoint):
- F01: <link directo>
- F04: <link directo>

🗂️ REPOSITORIOS:
- Azure DevOps (Soaint): <URL rama feature> — Commit: <hash>
- Bitbucket (Banco): <URL rama feature> — Commit: <hash>
- Repositorio suscripciones APIC: <URL> — Commit: <hash>
- Repositorio scopes OAuth: <URL> — Commit: <hash>

Quedo disponible para cualquier consulta.
Saludos,
<Nombre desarrollador>
```

---

## Checklist final de entrega
- [ ] F01 elaborado y firmado
- [ ] F04 firmado por QA
- [ ] Pipeline Azure DevOps verde
- [ ] BAR publicado en Nexus con versión correcta
- [ ] Despliegue en CP4I verificado (health check OK)
- [ ] Health check responde correctamente en DEV
- [ ] Fuentes en Azure DevOps (Soaint) en rama `feature`
- [ ] Fuentes en Bitbucket (Banco) con Pull Request creado
- [ ] F01 y F04 subidos a SharePoint
- [ ] Correo de entrega enviado con todos los links y commits

## Referencias internas
- `service-dev/service-dev.md` (FASE 7 prepara F01/entrega), `deployment/deployment.md` (despliegue CP4I).
- `standards/standards.md` (BAR naming, config por ambiente).