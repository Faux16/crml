# Excel workflows: control definitions and mappings

CRML supports authoring **control definitions** (control catalogs) and **control-to-control mappings** (control relationships packs) in a strict XLSX workbook format.

This is intended for workflows where subject-matter experts maintain controls/mappings in Excel, while tools/engines consume CRML YAML.

---

## Install XLSX support

The XLSX import/export feature lives in `crml_lang` and requires the optional dependency `openpyxl`.

```bash
pip install "crml-lang[xlsx]"
```

---

## Recommended workflow (round-trip)

### 1) Generate a template workbook (or export existing YAML)

You can generate an empty workbook with the correct sheet names and headers:

```bash
python -m crml_lang.mapping export-xlsx --out controls-and-mappings.xlsx
```

Or export existing CRML YAML documents into a workbook:

```bash
python -m crml_lang.mapping export-xlsx \
  --out controls-and-mappings.xlsx \
  --control-catalog examples/control_catalogs/control-catalog.yaml \
  --control-relationships examples/control_relationships/cisv8-mappings.yaml
```

Windows note: if your system uses `py` instead of `python`, use `py -m crml_lang.mapping ...`.

---

### 2) Edit in Excel

Open the workbook and edit only the rows in these sheets:

- `control_catalogs` (control definitions)
- `control_relationships` (control mappings)

You may ignore the other sheets if you don’t need them.

Important rules:

- Do not rename sheets.
- Do not delete the `_meta` sheet.
- Keep the first header row intact (it is usually hidden). The workbook uses **two header rows**:
  - Row 1: machine keys (hidden)
  - Row 2: human labels (visible)

If you create new columns, rename columns, or delete the hidden header row, import will fail.

---

## Sheet: `control_catalogs` (control definitions)

Each non-empty row defines one control entry and is grouped into documents by `doc_*` fields + `catalog_id`.

Required fields for a usable row:

- `doc_name` (Document name)
- `framework` (Framework)
- `control_id` (Control id)

Common fields:

- `title`, `url`
- `tags_json` (JSON array, e.g. `["hardening","baseline"]`)
- `defense_in_depth_layers_json` (JSON array, allowed values: `prevent`, `detect`, `respond`, `recover`)

Optional structured locator (`ref_*`):

- `ref_standard` + `ref_control` are required together if either is used
- `ref_requirement` is optional

Notes:

- Keep `id` values stable (e.g. `cisv8:4.2`, `org:edr`). These are what portfolios/assessments reference.
- Avoid embedding copyrighted standard text in titles/descriptions.

---

## Sheet: `control_relationships` (control mappings)

Each non-empty row defines one **source → target** mapping and is grouped into documents by `doc_*` fields + `pack_id`.

Required fields:

- `doc_name`
- `source_id`
- `target_id`
- `overlap_weight` (number in `[0,1]`)

Optional fields:

- `relationship_type` (enum): `overlaps_with`, `mitigates`, `supports`, `equivalent_to`, `parent_of`, `child_of`, `backstops`
- `confidence` (number in `[0,1]`)
- `overlap_dimensions_json` (JSON map, e.g. `{ "coverage": 0.9 }`)
- `groupings_json` (JSON array of objects)
- `references_json` (JSON array of objects)
- `description`, `overlap_rationale`

Practical tip:

- Keep rows for the same `source_id` adjacent (e.g. sort by `doc_name`, then `pack_id`, then `source_id`). This keeps the imported YAML grouped 1→N in a clean way.

---

## Import back to CRML YAML

```bash
python -m crml_lang.mapping import-xlsx \
  --in controls-and-mappings.xlsx \
  --out-dir imported/ \
  --overwrite
```

This writes one YAML file per imported document into `imported/`.

Validation (optional but recommended):

- If you have `crml` CLI installed: `crml validate imported/<file>.yaml`
- Or validate from Python using `crml_lang.validate_*` helpers.

---

## Using the imported YAML in portfolios

Portfolios reference control catalogs and relationship packs by path:

```yaml
portfolio:
  control_catalogs:
    - imported/my-catalog-control-catalog.yaml
  control_relationships:
    - imported/my-mappings-control-relationships.yaml
```
