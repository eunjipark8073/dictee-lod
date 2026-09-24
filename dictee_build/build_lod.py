"""Build dictee_lod_v2.jsonld + dictee_graph_v2.html from Entities/Property/relationship CSVs."""
import csv, json, os, sys
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent
# inputs live in the folder above dictee_build/ when that folder is self-contained; else fall back to Downloads
DL = HERE.parent if (HERE.parent / "dictee_relationships_final.csv").exists() \
    else Path(r"C:\Users\ejpar\OneDrive\바탕 화면\Downloads")
ENT = DL / "0908_Dictee_.xlsx - Entities.csv"
PROP = DL / "0908_Dictee_.xlsx - Property.csv"
REL = Path(os.environ.get("DICTEE_REL", DL / "dictee_relationships_final.csv"))
OUT_DIR = Path(os.environ.get("DICTEE_OUT", DL))
OUT_LD = OUT_DIR / "dictee_lod_v2.jsonld"
OUT_HTML = OUT_DIR / "dictee_graph_v2.html"

EMPTY = {"", "—", "-"}

def clean(v):
    v = (v or "").strip()
    return "" if v in EMPTY else v

def uris(v):
    return [u.strip() for u in clean(v).split(";") if u.strip()]

# ---------- property schema ----------
props = {}
with open(PROP, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.reader(f))
for r in rows[4:]:
    if len(r) >= 6 and r[1].strip():
        props[r[1].strip()] = {"label": r[0].strip(), "domain": r[2].strip(), "range": r[3].strip(),
                               "source": r[4].strip(), "note": r[5].strip()}

# Domain/range constraints (entityType sets) derived from the Property sheet
ANY = None
CONSTRAINTS = {
    "dict:sharesNameWith": ({"Person"}, {"Person"}),
    "dict:performsAs": ({"Person"}, {"Person"}),
    "dict:performsMediation": ({"Person"}, {"Person"}),
    "dict:hasExchangeableIdentity": ({"Person"}, {"Person"}),
    "dict:hasPostcolonialParallel": (ANY, ANY),
    "dict:mythologicalParallelOf": ({"Person"}, {"Person"}),
    "dict:silences": ({"Event", "Concept"}, {"Person"}),
    "dict:isRecurrenceOf": ({"Event"}, {"Event"}),
    "dict:prefigures": ({"Object", "Concept"}, {"Concept"}),
    "dict:subverts": (ANY, {"Concept"}),
    "dict:requiresExcavationBy": ({"Concept"}, {"Person", "Concept"}),
    "dict:embodiesPunctuation": ({"Person"}, {"Concept"}),
    "dict:critiques": ({"Person"}, {"Concept"}),
    "dict:hasFamilyRelation": ({"Person"}, {"Person"}),
    "dct:creator": ({"Work"}, {"Person"}),
    "dict:hasNarrator": ({"Work"}, {"Person"}),
    "schema:mentions": (ANY, ANY),
    "dct:publisher": ({"Work"}, {"Group"}),
    "schema:holds": ({"Group"}, {"Work"}),
    "skos:broader": ({"Concept", "Object"}, {"Concept"}),
}

RANGE_ALLOWS_LA_TYPE = {"dict:embodiesPunctuation", "dict:subverts"}

def norm_pred(p):
    p = p.strip()
    return "dict:" + p[len("dict:rel/"):] if p.startswith("dict:rel/") else p

# ---------- entities ----------
entities = OrderedDict()
with open(ENT, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        eid, etype = r["Entity ID"].strip(), r["Type"].strip()
        if not eid.startswith("dict:") or not etype:
            continue  # section header rows
        node = OrderedDict()
        node["@id"] = eid
        node["@type"] = clean(r["Linked Art Class"]) or etype
        node["_label"] = clean(r["prefLabel (en)"])
        node["identified_by"] = [
            {"type": "Name", "content": clean(r["prefLabel (en)"]), "language": "en"},
            {"type": "Name", "content": clean(r["prefLabel (ko)"]), "language": "ko"},
        ]
        node["dictrel:entityType"] = etype
        node["dictrel:documentedIn"] = ["dictee"]
        primary, status = clean(r["Primary URI"]), clean(r["Mapping Status"])
        close = uris(r["closeMatch URI"])
        if primary:
            if status == "closeMatch":
                close = [primary] + close  # closeMatch status ≠ owl:sameAs
            else:
                node["equivalent"] = [{"id": primary}]
        node["dictrel:mappingStatus"] = status
        if close:
            node["skos:closeMatch"] = [{"id": u} for u in close]
        broader = uris(r["broader URI"])
        if broader:
            node["skos:broader"] = [{"id": u} for u in broader]
        refs = []
        if clean(r["Definition / Scope Note"]):
            refs.append({"type": "LinguisticObject", "content": clean(r["Definition / Scope Note"]),
                         "classified_as": "description"})
        if clean(r["internal_Definition / Scope Note"]):
            refs.append({"type": "LinguisticObject", "content": clean(r["internal_Definition / Scope Note"]),
                         "classified_as": "scope_note"})
        node["referred_to_by"] = refs
        if clean(r["Evidence Type"]):
            node["dict:evidenceType"] = clean(r["Evidence Type"])
        if clean(r["Chapter(s)"]):
            node["dict:chapter"] = [c.strip() for c in clean(r["Chapter(s)"]).split(",") if c.strip()]
        if clean(r["Page References"]):
            node["dict:pageReference"] = clean(r["Page References"])
        entities[eid] = node

# ---------- relationships ----------
issues, pred_count = [], Counter()
with open(REL, encoding="utf-8-sig", newline="") as f:
    rels = [r for r in csv.DictReader(f) if r["subject_uri"].strip()]
for i, r in enumerate(rels, start=1):
    # unquoted commas in a note spill into REVISED / extra columns — refuse rather than truncate silently
    if None in r or clean(r.get("REVISED")) not in ("", "ADDED", "FLIPPED"):
        sys.exit(f"row {i}: malformed CSV row (unquoted comma in note?): {r}")
    s, p, o = r["subject_uri"].strip(), norm_pred(r["relationship_property_uri"]), r["object_uri"].strip()
    for x in (s, o):
        if x not in entities:
            sys.exit(f"row {i}: unknown entity {x}")
    pred_count[p] += 1
    edge = OrderedDict([("id", o), ("dictrel:documentedIn", ["dictee"])])
    if clean(r["page_ref"]):
        edge["dict:pageRef"] = clean(r["page_ref"])
    if clean(r["note"]):
        edge["dict:note"] = clean(r["note"])
    if clean(r.get("REVISED")):
        edge["dictrel:revised"] = clean(r["REVISED"])
    st, ot = entities[s]["dictrel:entityType"], entities[o]["dictrel:entityType"]
    if p not in CONSTRAINTS:
        edge["dictrel:schemaStatus"] = "undeclared"
        issues.append(f"row {i}: {p} not declared in Property sheet ({s} -> {o})")
    else:
        dom, rng = CONSTRAINTS[p]
        # "Concept or Type" ranges also accept any entity whose Linked Art class is Type
        type_ok = p in RANGE_ALLOWS_LA_TYPE and entities[o]["@type"] == "Type"
        if (dom and st not in dom) or (rng and ot not in rng and not type_ok):
            edge["dictrel:schemaViolation"] = True
            issues.append(f"row {i}: {p} domain/range mismatch {st}->{ot}")
    entities[s].setdefault(p, []).append(edge)

# ---------- write JSON-LD ----------
graph = []
for n in entities.values():
    n = OrderedDict(n)
    n.pop("_label", None)
    graph.append(n)
doc = OrderedDict([
    ("@context", [
        "https://linked.art/ns/v1/linked-art.json",
        {
            "dict": "https://dictee-lod.wikibase.cloud/entity/",
            "dictrel": "https://dictee-lod.wikibase.cloud/prop/direct/",
            "skos": "http://www.w3.org/2004/02/skos/core#",
            "schema": "https://schema.org/",
            "dct": "http://purl.org/dc/terms/",
        },
    ]),
    ("dct:created", datetime.now(timezone.utc).isoformat()),
    ("dct:source", [ENT.name, PROP.name, REL.name]),
    ("@graph", graph),
])
OUT_LD.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

# ---------- write HTML ----------
connected = set()
for n in entities.values():
    for k, v in n.items():
        if isinstance(v, list) and v and isinstance(v[0], dict) and str(v[0].get("id", "")).startswith("dict:"):
            connected.add(n["@id"]); connected.update(e["id"] for e in v)
isolated = [e for e in entities if e not in connected]

schema_for_html = {k: {"label": v["label"], "domain": v["domain"], "range": v["range"]} for k, v in props.items()}
tpl = (HERE / "graph_template.html").read_text(encoding="utf-8")
d3 = (HERE / "d3.min.js").read_text(encoding="utf-8")
html = (tpl.replace("/*__D3__*/", d3)
           .replace("/*__DATA__*/null", json.dumps(doc, ensure_ascii=False).replace("</", "<\\/"))
           .replace("/*__SCHEMA__*/null", json.dumps(schema_for_html, ensure_ascii=False).replace("</", "<\\/")))
OUT_HTML.write_text(html, encoding="utf-8")

print(f"entities: {len(entities)}  ({Counter(n['dictrel:entityType'] for n in entities.values())})")
print(f"relations: {len(rels)}  predicates: {len(pred_count)}")
for p, c in pred_count.most_common():
    print(f"  {c:3d}  {p}")
print(f"isolated ({len(isolated)}): {isolated}")

# connected components (undirected)
adj = {e: set() for e in entities}
for n in entities.values():
    for k, v in n.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            for e in v:
                if e.get("id") in adj:
                    adj[n["@id"]].add(e["id"]); adj[e["id"]].add(n["@id"])
seen, comps = set(), []
for e in entities:
    if e in seen or not adj[e]:
        continue
    stack, comp = [e], []
    seen.add(e)
    while stack:
        x = stack.pop(); comp.append(x)
        for y in adj[x] - seen:
            seen.add(y); stack.append(y)
    comps.append(sorted(comp))
comps.sort(key=len, reverse=True)
print(f"connected components (excluding isolated): {len(comps)}  sizes={[len(c) for c in comps]}")
for c in comps[1:]:
    print("  minor component:", c)
KOREA_FAMILY = ["dict:person/cha-theresa", "dict:person/huh-hyungsoon", "dict:person/cha-hyungsang",
                "dict:person/cha-haksang", "dict:person/yu-gwansoon", "dict:person/empress-myeongseong",
                "dict:event/march-first-1919", "dict:event/april-19-1960", "dict:event/korean-war-1950",
                "dict:event/gwangju-1980", "dict:event/japanese-colonization", "dict:event/gojong-funeral-1919",
                "dict:event/cha-family-exile-1962", "dict:object/korea-map"]
where = {x: i for i, c in enumerate(comps) for x in c}
print("korea history/family cluster in one component:",
      len({where.get(x) for x in KOREA_FAMILY}) == 1, {x.split('/')[-1]: where.get(x) for x in KOREA_FAMILY})
print("schema issues:", *issues, sep="\n  ") if issues else print("schema issues: none")
print("wrote", OUT_LD, "and", OUT_HTML)
