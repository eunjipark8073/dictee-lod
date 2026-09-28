# Dictee LOD — Linked Open Data Model for Theresa Hak Kyung Cha's *Dictee*

A feminist Linked Open Data dataset modelling relational structures in Theresa Hak Kyung Cha's artists' book *Dictee* (Tanam Press, 1982), grounded in a systematic audit of seven MARC catalogue records held across four institutions.

Presented at DH2026, Daejeon, Republic of Korea, July 2026.

---

## Background

Existing bibliographic standards have failed to encode the feminist and postcolonial dimensions of *Dictee* for over forty years. A systematic audit of seven MARC records across four institutions — the Library of Congress, UC Berkeley, MoMA Library, and Kunstbibliothek Berlin — reveals that subject headings such as "Korean Americans," "Feminism and literature," and "Korea — History — Japanese occupation, 1910–1945" have never been applied to this work. This dataset treats that absence not as an oversight but as a structural condition.

To model relations that standard ontologies cannot accommodate, the dataset introduces five custom properties:

| Property | Description |
|---|---|
| `performsMediation` | Speaker empties self to channel a silenced voice |
| `hasExchangeableIdentity` | Identity exchangeable across historical figures |
| `silences` | Structural foreclosure of a subject's voice |
| `isRecurrenceOf` | Event as structural repetition, not mere sequence |
| `hasPostcolonialParallel` | Relation across colonial and gendered histories |

The dataset currently comprises 73 triples, 57 entities, and 25 properties.

---

## Files

| File | Description |
|---|---|
| `Dictee_lod_v2.jsonld` | Dataset (JSON-LD) |
| `Dictee_relationships.csv` | Relationship triples |
| `Dictee_xlsx - Entities.csv` | Entity list with scope notes |
| `Dictee_xlsx - Property.csv` | Property definitions and schema |
| `build_lod.py` | CSV to JSON-LD conversion script |
| `Dictee_graph.html` | Interactive graph visualization (D3.js, JSON-LD embedded) |

---

## Access

**Wikibase instance:** https://dictee-lod.wikibase.cloud  
**Interactive visualization:** https://eunijipark8073.github.io/dictee-lod/dictee_graph_v2.html  
**Zenodo DOI:** [to be added after deposit]

---

## License

This dataset is published under Creative Commons Attribution 4.0 International (CC BY 4.0).  
https://creativecommons.org/licenses/by/4.0/

---

## Citation

Park, Eunji. 2026. *Dictee LOD: A Feminist Linked Open Data Model for Theresa Hak Kyung Cha's Dictee*. [DOI to be added]. Universität der Künste Berlin.

---

## Contributors

- **Eunji Park** (research & concept) — Universität der Künste Berlin  
- **Kumji Park** (technical development) — MCS, University of Illinois Urbana-Champaign

---

## Related Work

- DH2026 presentation slides: https://docs.google.com/presentation/d/1Kc4fGb43WcgzxJlHH-LxlAlCvdI6benYceovtSp9vMw/edit?usp=sharing
