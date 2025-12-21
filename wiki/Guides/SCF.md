# SCF and CRML

The **Secure Controls Framework (SCF)** is a comprehensive catalog of controls that maps to many other frameworks (NIST, ISO, CIS, etc.). CRML supports importing SCF data from its standard Excel format into CRML Control Catalogs.

## Importing SCF Catalogs

CRML provides a CLI command to ingest SCF Excel files (`.xlsx`). This converts the flat spreadsheet into a structured, validated CRML `ControlCatalog`.

### Prerequisites

You need the `scf` optional dependency (which installs `openpyxl`):

```bash
pip install "crml-lang[scf]"
```

### Usage

```bash
crml-lang scf-import-catalog <input.xlsx> <output.yaml>
```

**Example:**

```bash
crml-lang scf-import-catalog ./Secure_Controls_Framework_2025.xlsx ./scf-catalog.yaml
```

The command automatically detects the relevant worksheet (looking for "SCF" and year "20xx") and the header row.

## Mapping Rules

The import process applies the following normative mapping rules to translate SCF columns into CRML fields:

| SCF Column | CRML Field | Transformation Rule |
|---|---|---|
| **SCF #** | `id` | Relabeled with `scf:` namespace. Spaces removed.<br>Example: `AC-1` &rarr; `scf:AC-1` |
| **Control Question** | `title` | Copied as-is. Used as the short human-readable summary. |
| **Domain** | `tags` | The domain is added as a tag.<br>Example: `Security & Privacy Governance` &rarr; `tags: ["Security & Privacy Governance"]` |
| **Control Description** | (Omitted) |  Omitted to avoid embedding copyrighted text. |

### Identifier Namespacing

CRML requires globally unique control IDs. Since "AC-1" is common across frameworks (NIST, ISO), SCF controls are automatically prefixed with `scf:` to prevent collisions.

- Input: `AC-1`
- CRML Output: `scf:AC-1`

## CMM Maturity Levels (Simulation)

When creating assessments against an SCF catalog, you can use the `scf_cmm_level` field in `Assessment` entries. The CRML Engine maps these maturity levels to quantitative effectiveness scores:

| CMM Level | Description | Simulated Effectiveness |
|---|---|---|
| **0** | Not Performed | 0% (0.00) |
| **1** | Performed Informally | 10% (0.10) |
| **2** | Planned & Tracked | 25% (0.25) |
| **3** | Well-Defined | 50% (0.50) |
| **4** | Quantitatively Controlled | 75% (0.75) |
| **5** | Continuously Improving | 90% (0.90) |

**Example Assessment:**
```yaml
assessments:
  - id: "scf:AC-1"
    scf_cmm_level: 3  # Maps to 0.50 effectiveness
```
