# {{ID}}_BUS_{{NombreFuncionalSnake}}
# Especificaciones Técnicas de Servicios - ETI

---

## 1. Alcance del Componente Integración

El presente documento tiene como alcance la especificación técnica del `{{NombreFuncional}}`.<br>
`Nota:` El presente documento has sido elaborado considerando al consumidor `{{CanalConsumidor}}` como sistema inicial de consumo. Sin embargo, la estructura, lineamientos y definiciones aquí descritas permiten que el servicio pueda ser consumido posteriormente por otros sistemas o aplicaciones que cumplan con los mismos criterios de integración.

---

## 2. Pre-requisitos

| Documento                 | Descripción                                                                                              | Repositorio                          | Responsable                                 |
| ------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------- |
| `SCI Aprobado  `        | Formato de solicitud de Servicios                                                                         | [SCI_{{NombreTecnico}}](https://banbifperu.sharepoint.com/)   | Líder de Producto                          |
| `Acta Mesas de Trabajo` | Acta(s) de las Mesas de Trabajo, ejecutadas para un mejor entendimiento de los requerimientos funcionales | N/A | Líder de Producto `<br>`(Generar las MT) |
| `F43 `                  | Formato de Arquitectura                                                                                   | N/A   | Líder de Producto                          |
| `F44`                   | Documento de definición funcional                                                                        | N/A   | Líder de Producto                          |
| `Servicio Base`         | Documento Checklist Servicio Base                                                                         | N/A  | Líder de Producto                          |

---

## 3. Información del Componente

| Concepto                               | Descripción                            |
| -------------------------------------- | --------------------------------------- |
| `Nombre funcional`                   | {{NombreFuncional}}   |
| `Relative Service Name`              | {{RelativeServiceName}}             |
| `Descripción funcional`             | {{DescripcionFuncional}}   |
| `Nombre técnico`                    | {{NombreTecnico}}          |
| `Etiqueta Funcional`                 | {{EtiquetaFuncional}}      |
| `Etiqueta Técnica (Nombre corto)`   | {{EtiquetaTecnica}}       |
| `Tipo de componente de integración` | BUS                       |
| `Capa`                               | Sistema           |
| `Plataforma de despliegue`           | IBM APP Connect Onpremise   |
| `Línea de Producto`                 | {{LineaProducto}}          |
| `Producto`                           | {{Producto}}               |
| `Tamaño Payload IN`                 | 1 KB       |
| `Tamaño Payload OUT`                | 1 KB      |
| `Tiempo de respuesta promedio`       | 500 ms |

---

## 4. Arquitectura

## 4.1	Nivel 1: Diagrama de Contexto

El diagrama representa la integración del servicio `{{NombreFuncional}}` dentro de la arquitectura empresarial de BanBif.<br>
El flujo se inicia desde el canal `{{CanalConsumidor}}`, que actúa como sistema consumidor. Esta realiza una invocación al `API Gateway (APP212)`, implementado con `IBM API Connect` y desplegado en `AWS Cloud - BanBif`<br>
Posteriormente, la solicitud es derivada al motor de integración `ACE12 (APP213)`, implementado sobre `IBM ACE`, el cual contiene la lógica de integración necesaria para la interacción con el backend.<br>
Finalmente, la transacción es enviada al sistema `IBS (APP037)`, que corresponde al `core bancario`, responsable de ejecutar la lógica de negocio del servicio.

![Figura 1. Diagrama de Contexto de la Solución](docs/Diagram/DiagramaContexto.jpg)

Figura 1. Diagrama de Contexto de la Solución

## 4.2	Nivel 2: Diagrama de Contenedor

El diagrama detalla los contenedores que conforman la solución tecnológica para la funcionalidad `{{NombreFuncional}}`, dentro de la arquitectura empresarial de BanBif.<br>
El flujo inicia desde el canal consumidor `{{CanalConsumidor}}`, que actúa como consumidor externo e invoca API. Esta API está publicada en el `API Gateway (APP212)`, gestionado mediante `IBM API Connect`, donde se expone la funcionalidad requerida.<br>
Posteriormente, el API canaliza la solicitud hacia el componente ACE12 (APP213), que opera sobre IBM App Connect Enterprise v12 en modalidad on-premise, donde se ejecuta el Servicio.<br>
Finalmente, el servicio realiza la integración con el backend IBS (APP037) mediante el programa `IN2100RI`, que a su vez invoca al programa `{{ProgramaBackend}}`, encargado de ejecutar la funcionalidad.<br>
El diseño contempla puntos de auditoría tanto para las solicitudes (request) como para las respuestas (response), permitiendo asegurar trazabilidad, monitoreo y control de cada interacción que ocurre dentro del flujo transaccional.

![Figura 2. Diagrama de Contenedor de la Solución](docs/Diagram/DiagramaContenedor.jpg)

Figura 2. Diagrama de Contenedor de la Solución

## 4.3	Nivel 3: Diagrama de Componentes de Software

![Figura 3. Diagrama de Componentes de la Solución](docs/Diagram/DiagramaComponentes.jpg)

Figura 3. Diagrama de Componentes de la Solución

## 4.4	Nivel 4 Diagramas UML

## 4.4.1	Diagrama de Secuencia

![Figura 4. Diagrama de Secuencia de la Solución](docs/Diagram/DiagramSequence.png)

Figura 4. Diagrama de Secuencia de la Solución

## 4.4.2	Diagrama de Proceso

![Figura 5. Diagrama de Proceso de la Solución](docs/Diagram/DiagramProcess.png)

Figura 5. Diagrama de Proceso de la Solución

---

## 5. Especificación BIAN

Detalle de la ubicación del componente de integración desde el contexto BIAN

## 5.1	Definición BIAN

| Definición BIAN       | Valor                                             |
| ---------------------- | ------------------------------------------------- |
| `Business Area`      | Operations and Execution             |
| `Business Domain 1`  | Consumer Services          |
| `Business Domain 2`  | N/A |
| `Service Domain`     | {{ServiceDomain}}            |
| `Functional Pattern` | {{FunctionalPattern}}        |
| `Control Record`     | {{ControlRecord}}            |
| `Behavior Qualifier` | N/A        |
| `Sub Qualifier`      | N/A                     |
| `Action Term`        | Update               |
| `path`               | {{BianPath}}                      |

## 5.2	Semántica Estándar de BIAN

| Concepto                                     | Descripción                                                                        |
| -------------------------------------------- | ----------------------------------------------------------------------------------- |
| `Service Domain` | **Semántica/Swagger BIAN:**<br> https://portal.bian.org/service-domain-api/ |

## 5.3	BOM BIAN

![Figura 6. Diagrama BOM BIAN](docs/Diagram/BOMBIAN.png)

Figura 6. Diagrama BOM BIAN

### Request

```json
{
  "{{OperationRequest}}": {
    "Field1": "Value1"
  }
}
```

### Response: Caso éxito

```json
{
  "{{OperationResponse}}": {
    "ResponseCode": "1",
    "ResponseMessage": "Se realizo la operación correctamente."
  }
}
```

### Response: Caso de error 

```json
{
"type": "{{OperationResponse}}Error:Technical",
"title": "Ocurrió un(os) error(es) técnico(s)",
"status": 400,
"detail": "La solicitud posee una sintaxis incorrecta o falta parametro(s) requerido(s).",
"instance": "urn:BUS:{{OperationRequest}}",
"extensions": {
    "{{OperationResponse}}": {
            "Message": [
              {
                  "StatusCode": "02",
                    "Message": "La longitud del header Content-Type debe estar en el rango [15, 16]",
                    "Status": "ERROR"
              }
            ]
    }
 }
}
```

---

## 6	Implementación de la Solución

## 6.1	Repositorio de fuentes

| Concepto    | Descripción                                                        |
| ----------- | ------------------------------------------------------------------- |
| Repositorio | `https://bitbucket.org/banbifperu/{{RepoSources}}` |

## 6.2	Repositorio de BAR

| Concepto   | Repositorio                                                                                                                                   |
| ---------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Nombre BAR | `{{BarName}}`                                                                                                                       |
| DEV        | https://bif2nexus10.dombif.peru:8443/ |
| QAS        | https://bif3nexus10.dombif.peru:8443/ |
| PRD        | https://bif1nexus10.dombif.peru:8443/ |

## 6.3	Información del Integration Runtime

| Concepto                             | Descripción                                                                                                                                                              |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **BAR Librerías compartidas** | BAR_LIB_CORE_CONTROL, BAR_LIB_CORE_COMMON, BAR_LIB_SMF_UTIL                                                                                                               |
| **Configuraciones**            | `as400-adapter`, `nexus-user`, `policy-logs`, `setdbparams-banbif`, `ace-banbif-keystore.jks`, `ace-banbif-truststore.jks`, `plp-lib-common-cipherv1.1`, `setdbparams-app213` |
| **Nombre IR**                  | quick-start-003                                                                                                                                                     |
| **Recurso DEV/QAS/PRD**        | **RAM** Req: **256m** Limit: **512m** | **CPU** Req: **100m** Limit: **150m** |

## 6.4	Diagrama de componentes de la solución

| Capa                 | Descripción |
| -------------------- | ----------- |
| **Consumidor** | {{CanalConsumidor}} |
| **Servicio**   | **{{NombreTecnico}} (APP213)** <br> Servicio ACE que expone la funcionalidad de **{{NombreFuncional}}**. <br> **LIB_CORE_CONTROL, LIB_CORE_COMMON, LIB_SMF_UTIL**. |
| **Productor**  | **IBS(APP037): {{ProgramaBackend}}** Programa RPG en IBS. |

## 6.5	Diagrama de Despliegue

![Figura 8. Diagrama de Despliegue de la Solución](docs/Diagram/DiagramDeployment.png)

## 6.6 Detalles para API Connect

| Ambiente | Organización Productora | Catálogo | API Product |
| --- | --- | --- | --- |
| Desarrollo | dev | Interno / Externo | No aplica |
| Calidad | qas | Interno / Externo | No aplica |
| Producción | gapi | Interno / Externo | No aplica |

---

## 6.7 Endpoint del Componente de Integración

| Ambiente | Método | Ruta | TIPO | Síncrono / asíncrono |
| -------- | ------- | ---- | ---- | ---------------------- |
| DEV      | POST    | https://{{RelativeServiceName}}.apps.onprem.ocphipdes.dombif.peru/{{BianPath}} | REST/On-premise | Síncrono / Asíncrono |
| QAS      | POST    | https://{{RelativeServiceName}}.apps.onprem.ocphipuat.dombif.peru/{{BianPath}} | REST/On-premise | Síncrono / Asíncrono |
| PRD      | POST    | https://{{RelativeServiceName}}.apps.onprem.ocphip.dombif.peru/{{BianPath}} | REST/On-premise | Síncrono / Asíncrono |

---

## 6.8 Consumidor autorizado del Componente de Integración

| ID | Nombre |
| -- | ------ |
| {{ConsumidorID}} | {{CanalConsumidor}} |

---

## 6.9 Productor del Componente de Integración

| Ambiente | APP APM | Ruta | Alias | TIPO | Síncrono / Asíncrono |
| -------- | ------- | ---- | ----- | ---- | ---------------------- |
| DEV/QA/PRD | APP037 (IBS) | RPG IN2100RI --> {{ProgramaBackend}} | RPG_IBS_{{NombreTecnico}} | RPG | Síncrono / Asíncrono |

---

# 7 Certificación del componente
| Concepto | Valor |
| --- | --- |
| Documento de casos de prueba | |
| Script de Pruebas [Postman] | |

# 8 Seguridad del componente

## 8.1 Protocolos o tipos de autenticación
- **BUS**: MTLS + BASIC AUTH

## 8.5 Autorización de consumo de servicios BUS
| Ambiente | Grupo LDAP |
| --- | -- |
| Desarrollo | {{EtiquetaTecnica}}_GD |
| Certificación | {{EtiquetaTecnica}}_GQ |
| Producción | {{EtiquetaTecnica}}_GP |

## 8.6 Cifrado de campos en entrada/salida
- `Authorization` (Header Request) : RSA 2048 - RSA/ECB/OAEPWITHSHA-256ANDMGF1PADDING

---

# 9 Auditoría del componente
Para revisar los campos, atributos y características de la auditoría, ver el Lineamiento de Auditoría.

---

# 10 Información de infraestructura
- API Connect, App Connect, Solace Event Broker

---

# 11 Glosario
- Capa de Experiencia (`–x`), Capa de Negocio (`–b`), Capa de Sistema (`–s`).

---

# 12 Historial de Revisiones

| Autor | Versión | Fecha | Descripción |
| ----- | ------- | ----- | ----------- |
| Agente IA IBM ACE | v1.0 | {{FechaActual}} | Versión Inicial Generada Automáticamente |
