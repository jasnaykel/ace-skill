# security — Seguridad de servicios ACE (autenticación, transporte, cifrado)

## Propósito
Aplicar el modelo de seguridad de la fábrica en cualquier servicio generado: doble vía, LDAP, headers y cifrado de credenciales sin hardcodear.

## Capas de seguridad
| Capa | Implementación | Detalle |
|---|---|---|
| Transporte entrada | `mTLS` (externa) + `Onprem` (interna) | `useHTTPS=yes` para mTLS con TLSv1.3; `Onprem.useHTTPS=no` |
| Autenticación | LDAP (Active Directory) | `CTRLAUTHAPP` con Pipeline `ComIbmSecurityPIP`, `securityProfileName` = política `PL_ActiveDirectory`; grupos `*_GD` (desarrollo), `*_GQ` (QA), `*_GP` (prod) |
| Autorización | Grupos | Los grupos LDAP del servicio determinan quién puede invocar (validación del `CTRLAUTHAPP`) |
| Respuesta | Security headers | `ApplySecurityHeaders`: Content-Security-Policy, X-Content-Type-Options, X-Frame-Options, Strict-Transport-Security, Referrer-Policy, Permissions-Policy, X-XSS-Protection |
| Credenciales | Políticas + cifrado | credenciales en `PL_UserDefined` (destinos) o `setdbparams`; nunca en código. ETI §8.6: cifrado RSA-2048 OAEP de campos sensibles (`ENCRYPTSRV`/`DECRYPTSRV` para `Authorization`) |
| Backend | Conector Centralizado | transporte entre ACE y CP4I en canal interno; usuario `si-control` configurado |

## Reglas (no negociables)
1. **Nada hardcodeado:** credenciales, tokens, IPs, URLs de clusters → placeholders + política por ambiente.
2. **Doble vía siempre** para servicios expuestos a canales digitales (mTLS) y a la red interna (Onprem).
3. **LDAP grupos por ambiente** (GD/GQ/GP) en `valid_cfg_values.yaml` y política.
4. **Headers de seguridad** en toda respuesta HTTP (fachada o service).
5. Cifrado de campos sensibles (passwords en `Authorization`) con `ENCRYPTSRV`/`DECRYPTSRV` (OAEP).
6. No exponer detalles de stack traces en respuestas de error (solo `status`, `detail` del `faultFormat`).

## Cifrado en ESQL (patrón)
```sql
-- cifrar
PROPAGATE TO LABEL getLBL_EncryptSrv() DELETE NONE;  -- ENCRYPTSRV
-- descifrar
PROPAGATE TO LABEL getLBL_DecryptSrv() DELETE NONE;  -- DECRYPTSRV
```

## Referencias
- Repo C: `PL_ActiveDirectory.policyxml`, `ApplySecurityHeaders.esql`, wdo `useHTTPS`, `ETI §8.6`.
- `ace-flowpilot`: `skills/ace-project-setup` (seguridad de proyectos).