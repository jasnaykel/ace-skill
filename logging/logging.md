# logging — Estándar de logging para servicios IBM ACE (CloudWatch + ELK)

## Propósito
Estándar de logging de la fábrica: exactamente qué logs registrar, en qué orden y con qué campos, para cada escenario de éxito y error (servicio atómico y orquestador).

## Cuándo usar este módulo
- Implementar logging en un servicio ACE nuevo.
- Validar que los logs de un servicio son correctos (checklist al final).
- Revisar la secuencia esperada de logs para un escenario.

---

## Estructura de los logs

### CloudWatch — campos base
| Campo | Valores posibles | Descripción |
|---|---|---|
| `componente` | `MAIN`, `BACKEND` | `MAIN` = lógica del servicio propio; `BACKEND` = llamada al servicio de destino |
| `tipo_accion` | `REQUEST`, `RESPONSE`, `DETAIL`, `ERROR` | Tipo del evento |
| `level` | `INFO`, `WARNING`, `ERROR` | Severidad |

### ELK — códigos de evento
| Código | Evento |
|---|---|
| `10` | MAIN REQUEST — entrada al servicio |
| `20` | BACKEND REQUEST — request enviado al backend |
| `30` | BACKEND RESPONSE — response recibido del backend |
| `40` | MAIN RESPONSE — respuesta final del servicio |
| `50` | BACKEND ERROR TÉCNICO / TIMEOUT |
| `60` | MAIN ERROR TÉCNICO (header, body, LDAP) |

---

## 1. Servicio Atómico

### 1.1 Escenarios CloudWatch

#### Éxito
```
MAIN     | REQUEST  | INFO
BACKEND  | REQUEST  | INFO
BACKEND  | RESPONSE | INFO
MAIN     | RESPONSE | INFO
```

#### Error funcional (backend devuelve error de negocio)
```
MAIN     | REQUEST  | INFO
BACKEND  | REQUEST  | INFO
BACKEND  | RESPONSE | INFO     ← el backend responde con error funcional
MAIN     | ERROR    | WARNING  ← warning porque es error esperado de negocio
```

#### Error en campo de entrada — header inválido
```
MAIN     | REQUEST  | INFO
MAIN     | DETAIL   | ERROR    ← detalle del campo inválido
MAIN     | RESPONSE | ERROR
```

#### Error en campo de entrada — body (jsonschema)
```
MAIN     | REQUEST  | INFO
MAIN     | DETAIL   | ERROR
MAIN     | RESPONSE | ERROR
```

#### Error en campo de entrada — body (validación lógica funcional)
```
MAIN     | REQUEST  | INFO
MAIN     | DETAIL   | ERROR
MAIN     | ERROR    | ERROR    ← error en vez de RESPONSE porque es validación interna
```

#### Error LDAP
```
MAIN     | REQUEST  | INFO
MAIN     | DETAIL   | ERROR
MAIN     | RESPONSE | ERROR
```

#### Error técnico (backend no disponible / caído)
```
MAIN     | REQUEST  | INFO
BACKEND  | REQUEST  | INFO
BACKEND  | ERROR    | ERROR    ← backend no respondió
MAIN     | RESPONSE | INFO     ← el servicio responde al cliente con error estándar
```

#### Timeout (backend no responde en tiempo)
```
MAIN     | REQUEST  | INFO
BACKEND  | REQUEST  | INFO
BACKEND  | ERROR    | ERROR
MAIN     | RESPONSE | INFO
```

### 1.2 Escenarios ELK
| Escenario | Secuencia de eventos |
|---|---|
| Éxito | `MAIN:10` → `BACKEND:20` → `BACKEND:30` → `MAIN:40` |
| Error funcional | `MAIN:10` → `BACKEND:20` → `BACKEND:30` → `MAIN:40` |
| Error header | `MAIN:10` → `MAIN:60` → `MAIN:40` |
| Error body (jsonschema) | `MAIN:10` → `MAIN:60` → `MAIN:40` |
| Error body (validación lógica) | `MAIN:10` → `MAIN:60` → `MAIN:40` |
| Error LDAP | `MAIN:10` → `MAIN:60` → `MAIN:40` |
| Error técnico backend | `MAIN:10` → `BACKEND:20` → `BACKEND:50` → `MAIN:40` |
| Timeout backend | `MAIN:10` → `BACKEND:20` → `BACKEND:50` → `MAIN:40` |

> ℹ️ En **error funcional** el ELK sigue la misma secuencia que éxito (el backend respondió).
> El nivel de error se refleja en CloudWatch, no en la secuencia ELK.

---

## 2. Servicio Orquestador (invoca 2 atómicos)

### 2.1 Escenarios CloudWatch

#### Éxito completo
```
MAIN ORQUESTADOR  | REQUEST  | INFO
BACKEND ATOMICO1  | REQUEST  | INFO
  ATOMICO1        | REQUEST  | INFO
  BACKEND1        | REQUEST  | INFO
  BACKEND1        | RESPONSE | INFO
  ATOMICO1        | RESPONSE | INFO
BACKEND ATOMICO1  | RESPONSE | INFO
BACKEND ATOMICO2  | REQUEST  | INFO
  ATOMICO2        | REQUEST  | INFO
  BACKEND2        | REQUEST  | INFO
  BACKEND2        | RESPONSE | INFO
  ATOMICO2        | RESPONSE | INFO
BACKEND ATOMICO2  | RESPONSE | INFO
MAIN ORQUESTADOR  | RESPONSE | INFO
```

#### Error funcional del primer atómico — el flujo se detiene
```
MAIN ORQUESTADOR  | REQUEST  | INFO
BACKEND ATOMICO1  | REQUEST  | INFO
  ATOMICO1        | REQUEST  | INFO
  BACKEND1        | REQUEST  | INFO
  BACKEND1        | RESPONSE | INFO
  ATOMICO1        | ERROR    | WARNING
BACKEND ATOMICO1  | ERROR    | WARNING
MAIN ORQUESTADOR  | ERROR    | WARNING   ← flujo se detiene aquí, no ejecuta atómico 2
```

#### Error de header / body / LDAP (en el orquestador)
```
MAIN ORQUESTADOR  | REQUEST  | INFO
MAIN ORQUESTADOR  | DETAIL   | ERROR
MAIN ORQUESTADOR  | RESPONSE | ERROR
```

#### Error body validación lógica (en el orquestador)
```
MAIN ORQUESTADOR  | REQUEST  | INFO
MAIN ORQUESTADOR  | DETAIL   | ERROR
MAIN ORQUESTADOR  | ERROR    | ERROR
```

#### Error técnico del primer atómico
```
MAIN ORQUESTADOR  | REQUEST  | INFO
BACKEND ATOMICO1  | REQUEST  | INFO
BACKEND ATOMICO1  | ERROR    | ERROR
MAIN ORQUESTADOR  | RESPONSE | INFO
```

#### Timeout del primer atómico
```
MAIN ORQUESTADOR  | REQUEST  | INFO
BACKEND ATOMICO1  | REQUEST  | INFO
BACKEND ATOMICO1  | ERROR    | ERROR
MAIN ORQUESTADOR  | RESPONSE | INFO
```

### 2.2 Escenarios ELK (Orquestador)
| Escenario | Secuencia |
|---|---|
| Éxito | `MAIN-ORC:10` → `BK-AT1:20` → `AT1:10` → `BK1:20` → `BK1:30` → `AT1:40` → `BK-AT1:30` → `BK-AT2:20` → `AT2:10` → `BK2:20` → `BK2:30` → `AT2:40` → `BK-AT2:30` → `MAIN-ORC:40` |
| Error funcional AT1 | `MAIN-ORC:10` → `BK-AT1:20` → `AT1:10` → `BK1:20` → `BK1:30` → `AT1:40` → `BK-AT1:30` → `MAIN-ORC:40` |
| Error header | `MAIN-ORC:10` → `MAIN-ORC:60` → `MAIN-ORC:40` |
| Error body | `MAIN-ORC:10` → `MAIN-ORC:60` → `MAIN-ORC:40` |
| Error LDAP | `MAIN-ORC:10` → `MAIN-ORC:60` → `MAIN-ORC:40` |
| Error técnico AT1 | `MAIN-ORC:10` → `BK-AT1:20` → `BK-AT1:50` → `MAIN-ORC:40` |
| Timeout AT1 | `MAIN-ORC:10` → `BK-AT1:20` → `BK-AT1:50` → `MAIN-ORC:40` |

---

## Checklist de validación de logging
- [ ] Todos los escenarios tienen log `MAIN:REQUEST` (código `10` en ELK)
- [ ] Todos los escenarios tienen log `MAIN:RESPONSE` o `MAIN:ERROR` al final (código `40` en ELK)
- [ ] Errores técnicos de backend usan `BACKEND:ERROR:ERROR` + código `50` ELK
- [ ] Errores de validación interna (header/body/LDAP) usan `MAIN:DETAIL:ERROR` + código `60` ELK
- [ ] Errores funcionales de backend usan `WARNING` en CloudWatch (no `ERROR`)
- [ ] El orquestador detiene el flujo ante error funcional del primer atómico (no llama al segundo)
- [ ] Los logs del ESQL incluyen los campos: `componente`, `tipo_accion`, `level`, `correlationId`, `timestamp`

---

## Troubleshooting de Auditoría y Logs en ACE

### T1. Auditoría de Timeout / Error reportada como `WARNING` / `MAIN|ERROR` en vez de `INFO` / `MAIN|RESPONSE`
- **Problema**: ante un timeout o error técnico en el backend (ej. `TimeoutMillis = 1`), el último log de auditoría V2 de la capa `MAIN` salía con nivel `WARNING` y `tipo_accion = ERROR` (`MAIN|ERROR`), cuando la respuesta final entregada al consumidor debe reportarse como `INFO` y `RESPONSE` (`MAIN|RESPONSE`).
- **Causa**: en el módulo `PrepRespSrv` (`SMF_..._S.esql`), la rama `ELSE` tenía `SET refEnv.Temp.Variable.IsErrorFuncional = TRUE;` de forma incondicional. Durante un timeout el código HTTP no es 200, por lo que forzaba `WARNING`.
- **Solución**: condicionar `IsErrorFuncional` al código HTTP real de la respuesta backend:
  ```esql
  SET refEnv.Temp.Variable.IsErrorFuncional = httpStatusCode = 200;
  ```
  <!-- Homologación: la plantilla 153 de Repo C usa `FIELDVALUE(InputLocalEnvironment.Destination.X-Original-HTTP-Status-Code) = 200` — misma semántica: Timeouts/errores de conexión (no 200) no activan la bandera. Ver `LIB_<S>.esql` `armaRpta*_ERROR`. -->

### T2. Auditoría silenciada o no propagada (`PROPAGATE TO LABEL getLBL_AUDIT()`)
- **Problema**: las llamadas a `PROPAGATE TO LABEL getLBL_AUDIT()` no generan logs ni llegan al subflow de auditoría.
- **Causa**: falta de conexión gráfica (`FCMConnection`) en el `.msgflow` principal del servicio entre el nodo etiqueta (`ComIbmLabel` con `labelName="lblAudit"`) y el subflow de auditoría (`CTRLAUDIT` / `ace_esb_core_ope_SMF_BUS_CORE_SRV_CTRLAUDITV2`).
- **Solución**: conectar `lblAudit` con `CTRLAUDIT` en el `.msgflow`. Para pruebas locales, asegurar que el gestor de colas local (`IIB_local`) y su listener (`LISTENER.TCP` en puerto `1414`) estén iniciados (`strmqm` y `START LISTENER`).

## Referencias internas
- `esql/esql.md` (procedimientos de auditoría `prepararMensajeAuditoriaV2`, labels `lblAudit`/`lblELK`).
- `testing/testing.md` (validación de logging en pruebas), `service-dev/service-dev.md` (FASE 4: cola MQ local).