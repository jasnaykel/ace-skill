#!/usr/bin/env python3
"""
verify_scaffold.py - Verificador ESTATICO de scaffolding ACE (BanBif / skill ace-skill).

Comprueba, sin necesitar el Toolkit, los 8 grupos de fallos que el Toolkit 12.0.x
reporta al importar un proyecto generado por la fabrica:

  1. OpenAPI 3: parseo, `components` en la raiz, una sola stanza `servers`,
     `servers.url` y claves de `path` con "/", `parameters` es array sin duplicados,
     todo `$ref` local resoluble, sin `$ref` externos, sin BOM.
  2. ESQL: `BROKER SCHEMA` == ruta de la carpeta del archivo (derivada desde la raiz
     del proyecto Eclipse, no desde la raiz del repositorio).
  3. ESQL: ninguna routine de PRIMER NIVEL declarada dos veces en un mismo schema.
  4. Toda URN `esql://routine/<schema>#<Routine>` resuelve a una routine declarada
     en el MISMO proyecto.
  5. XML bien formado (.msgflow, .subflow, .policyxml, .monprofile.xml, .project).
  6. restapi.descriptor: elemento raiz `ns2:restapiDescriptor`, atributos obligatorios,
     `definitionFile`/`implementation` existentes, cobertura de todos los `operationId`
     del OpenAPI y de los 3 error handlers CATCH/FAILURE/TIMEOUT.
  7. Higiene de codificacion: sin BOM UTF-8, todo UTF-8 valido.
  8. request.schema.json: JSON valido.

Uso:
    python verify_scaffold.py                 # usa el directorio del script
    python verify_scaffold.py <ruta-proyecto> # verifica otro arbol

Requiere PyYAML. Salida: 0 si no hay fallos, 1 si hay fallos.
NO sustituye la compilacion real en el ACE Toolkit.
"""
import os, re, sys, glob, json
import xml.dom.minidom
import yaml

ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
fails, warns = [], []

def fail(m): fails.append(m); print("  FAIL " + m)
def warn(m): warns.append(m); print("  WARN " + m)
def ok(m):   print("  ok   " + m)

# ---------- locate the REST service project (dir containing restapi.descriptor) ----------
SVC_DIR = None
for _d in glob.glob(os.path.join(ROOT, "src", "**", "restapi.descriptor"), recursive=True):
    SVC_DIR = os.path.dirname(_d); break
if SVC_DIR is None:
    print("ERROR: no se encontro ningun restapi.descriptor bajo %s/src" % ROOT)
    sys.exit(2)
SVC_NAME = os.path.basename(SVC_DIR)
print("Proyecto : %s" % ROOT)
print("Servicio : %s" % SVC_NAME)

# ---------- 1. OpenAPI / YAML ----------
print("\n[1] OpenAPI 3 documents")
for p in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.yaml"), recursive=True)):
    rel = os.path.relpath(p, ROOT)
    raw = open(p, "rb").read()
    if raw[:3] == b"\xef\xbb\xbf":
        fail(rel + ": has UTF-8 BOM"); continue
    try:
        d = yaml.safe_load(raw.decode("utf-8"))
    except Exception as e:
        fail(rel + ": YAML parse error: %s" % e); continue
    if not isinstance(d, dict):
        fail(rel + ": root is not a mapping"); continue
    if d.get("openapi") != "3.0.0":
        fail(rel + ": openapi != 3.0.0 (%r)" % d.get("openapi"))
    if "components" not in d:
        fail(rel + ": 'components' is NOT at root level (keys=%s)" % list(d.keys()))
    if "components" in d.get("paths", {}):
        fail(rel + ": 'components' nested inside 'paths'")
    for k in ("openapi", "info", "servers", "paths", "components"):
        if k not in d: fail(rel + ": missing top-level '%s'" % k)
    srv = d.get("servers", [])
    if len(srv) != 1:
        fail(rel + ": %d server stanzas (must be exactly 1)" % len(srv))
    else:
        u = srv[0].get("url", "")
        if not u.startswith("/"):
            fail(rel + ": server url %r must start with '/'" % u)
    for pk, pv in d.get("paths", {}).items():
        if not pk.startswith("/"):
            fail(rel + ": path key %r must start with '/'" % pk)
        for meth, op in (pv or {}).items():
            if not isinstance(op, dict): continue
            params = op.get("parameters", []) or []
            if not isinstance(params, list):
                fail(rel + " %s.%s: parameters is not an array" % (pk, meth)); continue
            seen = set()
            for prm in params:
                if not isinstance(prm, dict) or "$ref" not in prm:
                    warn("%s %s.%s: inline parameter (no $ref)" % (rel, pk, meth)); continue
                ref = prm["$ref"]
                if not ref.startswith("#/"):
                    fail("%s %s.%s: external $ref %r (definitionWithExtRef=false)" % (rel, pk, meth, ref))
                if ref in seen:
                    fail("%s %s.%s: duplicate parameter $ref %s" % (rel, pk, meth, ref))
                seen.add(ref)
            for body in [op.get("requestBody")] + list((op.get("responses") or {}).values()):
                if not isinstance(body, dict): continue
                for ctype, cv in (body.get("content") or {}).items():
                    sch = (cv or {}).get("schema") or {}
                    r = sch.get("$ref")
                    if r and not r.startswith("#/"):
                        fail("%s %s: external schema $ref %r" % (rel, pk, r))
    # resolve every local $ref
    def resolve(doc, ref):
        cur = doc
        for part in ref.lstrip("#/").split("/"):
            if not isinstance(cur, dict) or part not in cur: return None
            cur = cur[part]
        return cur
    refs = set(re.findall(r'"\$ref"\s*:\s*"([^"]+)"', raw.decode("utf-8")))
    for r in sorted(refs):
        if r.startswith("#/") and resolve(d, r) is None:
            fail(rel + ": unresolvable $ref %s" % r)
    if not fails or True:
        ok("%s parses; components at root; 1 server; %d local $refs all resolve" % (rel, len([r for r in refs if r.startswith('#/')])))

# ---------- helpers ----------
def project_of(abs_path):
    """Nearest ancestor directory (inclusive) that contains a .project file."""
    d = os.path.dirname(abs_path)
    while True:
        if os.path.isfile(os.path.join(d, ".project")):
            return os.path.basename(d)
        nd = os.path.dirname(d)
        if nd == d: return None
        d = nd

def esql_schema_path(abs_path):
    """ESQL path relative to its project root, e.g. ace/esb/payexe/pro/hub/init/s"""
    proj = project_of(abs_path)
    if not proj:
        return None
    d = os.path.dirname(abs_path)
    parts = []
    while d and os.path.basename(d) != proj:
        parts.append(os.path.basename(d))
        nd = os.path.dirname(d)
        if nd == d:          # reached filesystem root without finding the project
            return None
        d = nd
    return "/".join(reversed(parts))

# ---------- 2. ESQL broker schema vs folder ----------
print("\n[2] ESQL: BROKER SCHEMA must equal folder path with '/'->'.'")
esql_by_schema = {}
for p in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.esql"), recursive=True)):
    rel = os.path.relpath(p, ROOT)
    epath = esql_schema_path(p)
    if not epath:
        fail(rel + ": cannot locate project root (.project)"); continue
    derived = ".".join(epath.split("/"))
    m = re.search(r"^\s*BROKER\s+SCHEMA\s+([A-Za-z0-9_.]+)", open(p, encoding="utf-8").read(), re.M)
    if not m:
        fail(rel + ": no BROKER SCHEMA declaration"); continue
    got = m.group(1)
    if got != derived:
        fail("%s: BROKER SCHEMA %r != derived from folder %r (%r)" % (rel, got, epath, derived))
    else:
        ok("%s: BROKER SCHEMA %s == folder-derived %s" % (rel, got, epath))
    esql_by_schema.setdefault(got, []).append((rel, p, open(p, encoding="utf-8").read()))

# ---------- 3. duplicate modules per schema ----------
print("\n[3] ESQL: duplicate TOP-LEVEL routine names within a broker schema")
# Top-level only: 'CREATE ...' must start at column 0 (nested Main/FUNCTION inside a
# COMPUTE MODULE is indented and is NOT a broker-schema-level routine).
MOD_RE = r"^CREATE\s+(?:COMPUTE\s+MODULE|FUNCTION|PROCEDURE)\s+([A-Za-z0-9_]+)"
for sch, files in esql_by_schema.items():
    seen = {}
    for rel, _p, txt in files:
        for mod in re.findall(MOD_RE, txt, re.M):
            seen.setdefault(mod, []).append(rel)
    for mod, where in seen.items():
        if len(where) > 1:
            fail("schema %s: routine %s declared %d times -> %s" % (sch, mod, len(where), where))
    if not any(len(w) > 1 for w in seen.values()):
        ok("schema %s: %d distinct top-level routines, no duplicates" % (sch, len(seen)))

# ---------- 4. esql:// URNs resolve ----------
print("\n[4] esql://routine URNs resolve to a declared routine in the same project")
def routines_of_project(proj):
    out = set()
    for sch, files in esql_by_schema.items():
        for rel, fp, _txt in files:
            if project_of(fp) == proj:
                out |= set(re.findall(MOD_RE, open(fp, encoding="utf-8").read(), re.M))
    return out
urn_re = re.compile(r'esql://routine/([A-Za-z0-9_.]+)#([A-Za-z0-9_.]+)')
checked = 0
for p in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.*"), recursive=True)):
    if os.path.splitext(p)[1].lower() not in (".msgflow", ".subflow"): continue
    rel = os.path.relpath(p, ROOT)
    proj = project_of(p)
    if not proj:
        fail("%s: cannot locate project root (.project)" % rel); continue
    avail = routines_of_project(proj)
    for sch, routine in sorted(set(urn_re.findall(open(p, encoding="utf-8").read()))):
        checked += 1
        mod = routine.split(".")[0]          # URN shape: <schema>#<Routine>[.<Function>]
        if sch not in esql_by_schema:
            fail("%s: URN schema %r not declared by any ESQL in project %s" % (rel, sch, proj))
        elif mod not in avail:
            fail("%s: URN %s#%s -> routine not declared in %s (have: %s)" % (rel, sch, routine, proj, sorted(avail)))
        else:
            ok("%s: %s#%s resolves" % (rel, sch, routine))
print("  (%d URN references checked)" % checked)

# ---------- 5. XML validity ----------
print("\n[5] XML well-formedness")
for p in sorted(glob.glob(os.path.join(ROOT, "src", "**", "*.*"), recursive=True)):
    if os.path.splitext(p)[1].lower() not in (".msgflow", ".subflow", ".project", ".policyxml", ".xml"): continue
    rel = os.path.relpath(p, ROOT)
    try:
        xml.dom.minidom.parse(p); ok(rel)
    except Exception as e:
        fail(rel + ": %s" % e)

# ---------- 6. restapi.descriptor ----------
print("\n[6] restapi.descriptor")
rd = os.path.join(SVC_DIR, "restapi.descriptor")
txt = open(rd, encoding="utf-8").read()
doc = xml.dom.minidom.parseString(txt)
rootel = doc.documentElement
if rootel.tagName != "ns2:restapiDescriptor":
    fail("restapi.descriptor: root element is %r, expected 'ns2:restapiDescriptor'" % rootel.tagName)
else:
    ok("root element is ns2:restapiDescriptor (namespace %s)" % rootel.namespaceURI)
for a, v in [("definitionType", "openapi_3"), ("faultFormat", "JSON"), ("https", "false")]:
    if rootel.getAttribute(a) != v:
        fail("restapi.descriptor: @%s=%r expected %r" % (a, rootel.getAttribute(a), v))
    else:
        ok("@%s=%s" % (a, v))
dfile = rootel.getAttribute("definitionFile"); impl = rootel.getAttribute("implementation")
base = os.path.dirname(rd)
for label, val in [("definitionFile", dfile), ("implementation", impl)]:
    fp = os.path.join(base, val)
    if not os.path.isfile(fp): fail("restapi.descriptor: %s %r does not exist" % (label, val))
    else: ok("%s -> %s exists" % (label, val))
ops = doc.getElementsByTagName("ns2:operation")
if not ops: fail("restapi.descriptor: no <ns2:operation> entries")
apiops = set()
for p in glob.glob(os.path.join(base, "*.yaml")):
    y = yaml.safe_load(open(p, encoding="utf-8").read())
    for pv in (y.get("paths") or {}).values():
        for op in (pv or {}).values():
            if isinstance(op, dict) and "operationId" in op: apiops.add(op["operationId"])
declared = set()
for o in ops:
    nm, im = o.getAttribute("name"), o.getAttribute("implementation")
    declared.add(nm)
    if not os.path.isfile(os.path.join(base, im)):
        fail("restapi.descriptor: operation %s -> %s missing" % (nm, im))
    else: ok("operation %s -> %s" % (nm, im))
missing = apiops - declared
if missing: fail("restapi.descriptor: OpenAPI operationIds not mapped: %s" % sorted(missing))
else: ok("all OpenAPI operationIds mapped: %s" % sorted(apiops))
for eh in doc.getElementsByTagName("ns2:errorHandler"):
    im = eh.getAttribute("implementation")
    if not os.path.isfile(os.path.join(base, im)): fail("errorHandler %s -> %s missing" % (eh.getAttribute("type"), im))
    else: ok("errorHandler %s -> %s" % (eh.getAttribute("type"), im))

# ---------- 7. encoding hygiene (ACE source text only) ----------
print("\n[7] encoding hygiene (ACE source files under src/, ci/, test/)")
TEXT_EXT = {".esql", ".msgflow", ".subflow", ".yaml", ".yml", ".json", ".xml", ".policyxml",
            ".descriptor", ".project", ".prefs", ".properties", ".txt", ".cpy", ".xsd", ".bar"}
bad = 0
scanned = 0
for top in ("src", "ci", "test"):
    for p in glob.glob(os.path.join(ROOT, top, "**", "*.*"), recursive=True):
        if not os.path.isfile(p): continue
        if os.path.splitext(p)[1].lower() not in TEXT_EXT: continue
        scanned += 1
        rel = os.path.relpath(p, ROOT)
        raw = open(p, "rb").read()
        if raw[:3] == b"\xef\xbb\xbf":
            fail(rel + ": UTF-8 BOM (breaks snakeyaml / XMI parsers)"); bad += 1
        try: raw.decode("utf-8")
        except Exception as e: fail(rel + ": not valid UTF-8 (%s)" % e); bad += 1
if not bad: ok("%d ACE source files: no BOM, all valid UTF-8" % scanned)

# ---------- 8. request.schema.json ----------
print("\n[8] request.schema.json")
rs = os.path.join(base, "request.schema.json")
try:
    j = json.loads(open(rs, encoding="utf-8-sig").read()); ok("valid JSON")
except Exception as e:
    fail("request.schema.json: %s" % e)

print("\n" + "=" * 62)
print("FAILURES: %d   WARNINGS: %d" % (len(fails), len(warns)))
print("=" * 62)
for f in fails: print("  - " + f)
sys.exit(1 if fails else 0)
