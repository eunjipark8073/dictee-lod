"""Apply pending edits to Property + relationship CSVs. Idempotent.
usage: patch_csv.py [REL_OUT]   (default: overwrite dictee_relationships_final.csv in place)"""
import csv, io, shutil, sys
from pathlib import Path

DL = Path(r"C:\Users\ejpar\OneDrive\바탕 화면\Downloads")
PROP = DL / "0908_Dictee_.xlsx - Property.csv"
REL = DL / "dictee_relationships_final.csv"
REL_OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else REL

def load(path):
    raw = path.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    rows = list(csv.reader(io.StringIO(text, newline="")))
    while rows and not any(c.strip() for c in rows[-1]):
        rows.pop()
    return rows, bom, nl

def save(path, rows, bom, nl):
    buf = io.StringIO(newline="")
    csv.writer(buf, lineterminator=nl).writerows(rows)
    path.write_bytes((b"\xef\xbb\xbf" if bom else b"") + buf.getvalue().encode("utf-8"))

def backup(p):
    b = p.with_suffix(p.suffix + ".bak")
    if not b.exists():  # keep the original pre-edit backup
        shutil.copy2(p, b)

# 1. Property sheet
rows, bom, nl = load(PROP)
have = {r[1].strip() for r in rows if len(r) > 1}
new_props = [
    ["publisher", "dct:publisher", "Work", "Group", "Dublin Core",
     "Dublin Core dct:publisher. 표준 방향(Work→Agent) 준수: 작품 → 출판 주체(Group)."],
    ["holds", "schema:holds", "Group", "Work", "Schema.org",
     "Schema.org schema:holds. 소장/권리 보유 기관(Group) → 작품(Work)."],
]
if any(r[1] not in have for r in new_props):
    backup(PROP)
    rows += [r for r in new_props if r[1] not in have]
    save(PROP, rows, bom, nl)

# 1b. Entities sheet
ENT = DL / "0908_Dictee_.xlsx - Entities.csv"
rows, bom, nl = load(ENT)
hdr = rows[0]
col = {h: i for i, h in enumerate(hdr)}
changed = False
for r in rows[1:]:
    if r[0] == "dict:group/uc-press":
        new = {"prefLabel (en)": "University of California Press",
               "Primary URI": "https://www.wikidata.org/wiki/Q1816033"}
        for k, v in new.items():
            if r[col[k]] != v:
                r[col[k]] = v; changed = True
if not any(r[0] == "dict:concept/muse-subversion" for r in rows):
    definition = ("Traditional Muses reclaimed as active channels for silenced women across colonial and gendered "
                  "histories. Each Muse no longer represents a single genre but an unstable intersection of colonial "
                  "history, martyrdom, and shamanism. THALIA (Comedy) opens with MELPOMENE (Tragedy) fresco — genre "
                  "expectation deliberately violated.")
    new = [""] * len(hdr)
    for k, v in {"Entity ID": "dict:concept/muse-subversion", "Type": "Concept", "Linked Art Class": "Type",
                 "prefLabel (en)": "Muse Subversion", "prefLabel (ko)": "뮤즈 전복",
                 "Mapping Status": "noExternalAuthority", "Evidence Type": "Modeling",
                 "Definition / Scope Note": definition, "internal_Definition / Scope Note": definition}.items():
        new[col[k]] = v
    # insert after the last concept row (before the OBJECTS section header)
    last_concept = max(i for i, r in enumerate(rows) if r[0].startswith("dict:concept/"))
    rows.insert(last_concept + 1, new); changed = True
if changed:
    backup(ENT)
    save(ENT, rows, bom, nl)

# 2. Relationship instances
rows, bom, nl = load(REL)
header = rows[0]
if "REVISED" not in header:
    header.append("REVISED")
w = len(header)
for r in rows[1:]:
    r += [""] * (w - len(r))

for r in rows[1:]:
    if r[:3] == ["dict:group/tanam-press", "dct:publisher", "dict:work/dictee"]:
        r[0], r[2] = "dict:work/dictee", "dict:group/tanam-press"
        r[5] = "FLIPPED"

new_rels = [
    ("dict:object/korea-map", "schema:mentions", "dict:event/gwangju-1980", "p.78",
     "분단 지도가 MELPOMENE 챕터에서 광주항쟁 맥락과 연결"),
    ("dict:object/korea-map", "schema:mentions", "dict:person/huh-hyungsoon", "p.78",
     "Korean peninsula division map as the geopolitical condition of Huh Hyungsoon's displacement — born in Manchuria, exiled within Korea during Japanese colonization, displaced to Busan during Korean War, finally exiled to US in 1962. The divided map embodies the structural impossibility of return."),
    ("dict:person/cha-haksang", "schema:mentions", "dict:event/april-19-1960", "p.84",
     "Cha Haksang participated in April 19 Revolution demonstrations. Tutor warning: 'they are killing any student in uniform'"),
    ("dict:event/cha-family-exile-1962", "schema:mentions", "dict:person/cha-theresa", "Biographical",
     "1962 exile: Cha (age 11-12) follows mother to Hawaii then San Francisco"),
    ("dict:event/cha-family-exile-1962", "schema:mentions", "dict:person/huh-hyungsoon", "Biographical",
     "1962 exile: Huh Hyungsoon departs first with son Hak Sung"),
    ("dict:event/gwangju-1980", "schema:mentions", "dict:person/cha-theresa", "p.87",
     "Cha returned to Korea 1980 and witnessed Gwangju aftermath. 'Nothing has changed, we are at a standstill.'"),
    ("dict:event/april-19-1960", "schema:mentions", "dict:person/cha-haksang", "p.84",
     "April Revolution directly connected to Cha family's subsequent exile to US"),
    ("dict:event/cha-family-exile-1962", "dict:isRecurrenceOf", "dict:event/korean-war-1950", "Biographical",
     "Family exile as second displacement after Korean War refuge in Busan"),
    ("dict:person/diseuse", "dict:embodiesPunctuation", "dict:object/punctuation", "p.4",
     "Diseuse internalizes punctuation as bodily condition — 'She would become, herself, demarcations'"),
    ("dict:object/punctuation", "dict:prefigures", "dict:concept/translational-violence", "pp.1-2",
     "Punctuation as colonial language's regulatory infrastructure = material prefiguration of translational violence"),
    ("dict:work/dictee", "dct:publisher", "dict:group/uc-press", "2001 reprint",
     "UC Press published 2001 reprint with BAMPFA"),
    ("dict:object/dreyer-still", "schema:mentions", "dict:person/gertrud", "ERATO",
     "Gertrud (Dreyer 1964) left-page narrative in ERATO split-screen. Name chain: Cha → Thérèse → Joan → Falconetti → Gertrud"),
    ("dict:object/melpomene-fresco", "dict:prefigures", "dict:concept/diasporic-experience", "p.138",
     "Tragedy Muse image opens Comedy chapter — genre subversion visualizes mother-daughter separation (Demeter-Persephone) and incomplete return structuring THALIA"),
    ("dict:object/melpomene-fresco", "dict:subverts", "dict:concept/muse-subversion", "p.138",
     "Comedy chapter opens with Tragedy image — genre expectation violated"),
    ("dict:concept/muse-subversion", "skos:broader", "dict:concept/postcolonial-feminism", "—",
     "Muse subversion operates within postcolonial feminist frame"),
]
existing = {tuple(r[:3]): r for r in rows[1:]}
added = 0
for r in new_rels:
    if r[:3] not in existing:
        rows.append(list(r) + ["ADDED"]); added += 1
    else:  # row already present: sync page/note to the latest wording
        existing[r[:3]][3:5] = r[3:5]

if REL_OUT == REL:
    backup(REL)
save(REL_OUT, rows, bom, nl)
print(f"wrote {REL_OUT.name}: {len(rows) - 1} relations ({added} added this run)")
