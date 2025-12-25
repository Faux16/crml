# CRML Schema Field Reference

This page is a **generated** field-by-field reference for the CRML JSON Schemas.

It is generated from the shipped JSON Schema files:

- `crml_lang/src/crml_lang/schemas/` (language document schemas)
- `crml_engine/src/crml_engine/schemas/` (engine-owned runtime config schemas)

The generator script lives at:

- `scripts/generate_schema_field_reference.py`

## Regenerating this page

From the repo root:

```bash
python scripts/generate_schema_field_reference.py
```

Notes:

- The generator updates only the content between the markers below.
- If you edit the Pydantic models in `crml_lang` or `crml_engine`, regenerate schemas first (see [CRML-Schema](CRML-Schema.md)), then regenerate this page.

<!-- BEGIN: GENERATED FIELD REFERENCE -->

Generated on 2025-12-25 by `scripts/generate_schema_field_reference.py`.

This section is auto-generated. Do not hand-edit.

### CRAssessment

Source: `crml_lang/src/crml_lang/schemas/crml-assessment-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_assessment | const | yes | Assessment document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| assessment | object | yes |  | additionalProperties=false |
| assessment.id | anyOf |  | Optional identifier for this assessment catalog (organization-owned). | default=None |
| assessment.framework | string | yes | Free-form framework label for humans/tools (e.g. 'CISv8', 'ISO27001:2022'). |  |
| assessment.assessed_at | anyOf |  | When this assessment catalog was performed/recorded (ISO 8601 date-time). Example: '2025-12-17T10:15:30Z'. | default=None |
| assessment.assessments | array | yes | List of per-control assessment entries. |  |
| assessment.assessments[] | object |  |  | additionalProperties=false |
| assessment.assessments[].id | string | yes | Canonical unique control id in the form 'namespace:key' (no whitespace). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| assessment.assessments[].oscal_uuid | anyOf |  | Optional OSCAL UUID for this control assessment target. This is interoperability metadata only; referencing/joining within CRML should use the canonical 'id'. | default=None |
| assessment.assessments[].ref | anyOf |  | Optional structured locator for mapping to an external standard (e.g. CIS/ISO). This is metadata only; referencing should use the canonical 'id'. | default=None |
| assessment.assessments[].implementation_effectiveness | anyOf |  | Organization-specific implementation strength for this control. Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented. This represents vulnerability likelihood (susceptibility) posture used to mitigate a scenario's baseline threat frequency. | default=None |
| assessment.assessments[].coverage | anyOf |  | Breadth of deployment/application across the organization. This contributes to vulnerability likelihood reduction when applying this control to a scenario. | default=None |
| assessment.assessments[].reliability | anyOf |  | Reliability/uptime of the control as a probability of being effective in a given period. | default=None |
| assessment.assessments[].affects | anyOf |  | Which loss component this assessment affects. Default is 'frequency' (frequency-first). Note: the current reference engine primarily applies controls to frequency (lambda). | default='frequency' |
| assessment.assessments[].scf_cmm_level | anyOf |  | SCF Capability Maturity Model (CMM) level for this control (0..5). Levels: 0=Not Performed, 1=Performed Informally, 2=Planned & Tracked, 3=Well-Defined, 4=Quantitatively Controlled, 5=Continuously Improving. | default=None |
| assessment.assessments[].question | anyOf |  | Optional assessment prompt/question text for this control (tool/community-defined). Useful for questionnaires and evidence collection. | default=None |
| assessment.assessments[].description | anyOf |  | Optional additional description for this assessment entry (tool/community-defined). Avoid embedding copyrighted standard text unless you have rights. | default=None |
| assessment.assessments[].notes | anyOf |  | Free-form notes about this assessment entry. | default=None |

### CRAttackCatalog

Source: `crml_lang/src/crml_lang/schemas/crml-attack-catalog-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_attack_catalog | const | yes | Attack catalog document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| catalog | object | yes |  |  |
| catalog.id | string | yes | Catalog identifier and namespace for all attack ids in this catalog. All catalog.attacks[*].id values must begin with '<catalog.id>:' (e.g. catalog.id='attck' -> 'attck:T1566'). | pattern='^[a-z][a-z0-9_-]{0,31}$'; minLength=1; maxLength=32 |
| catalog.framework | string | yes | Free-form framework label for humans/tools. Example: 'MITRE ATT&CK Enterprise'. |  |
| catalog.attacks | array | yes | List of attack pattern catalog entries. |  |
| catalog.attacks[] | object |  | Portable metadata about an attack id.  Important: do not embed copyrighted framework text here. Keep this to identifiers and tool-friendly metadata. |  |
| catalog.attacks[].id | string | yes | Canonical unique attack id present in this catalog. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| catalog.attacks[].kind | string | yes | Required normalized entry kind for engines and tools. | enum(10) |
| catalog.attacks[].title | anyOf |  | Optional short human-readable title for the attack entry. | default=None |
| catalog.attacks[].url | anyOf |  | Optional URL for additional reference material. | default=None |
| catalog.attacks[].parent | anyOf |  | Optional parent attack id (same catalog namespace). Useful for hierarchical frameworks (e.g. ATT&CK technique -> sub-technique, NIST CSF function -> category -> subcategory). | default=None |
| catalog.attacks[].phases | anyOf |  | Optional list of phase-like ids (same catalog namespace) that this entry is associated with. For ATT&CK, this can point to tactic ids. For kill chains, phases are typically represented as entries themselves. | default=None |
| catalog.attacks[].tags | anyOf |  | Optional extra tags for grouping/filtering. Tags are non-semantic and must not replace 'kind'. | default=None |

### CRAttackControlRelationships

Source: `crml_lang/src/crml_lang/schemas/crml-attack-control-relationships-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_attack_control_relationships | const | yes | Attack-to-control relationships document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| relationships | object | yes | Relationship pack payload.  This is a standalone, shareable dataset that can be community- or org-authored. |  |
| relationships.id | anyOf |  | Optional identifier for this relationships pack (organization/community-owned). | default=None |
| relationships.relationships | array | yes | List of grouped attack-to-control relationship mappings. |  |
| relationships.relationships[] | object |  | Grouped relationship mapping for a single attack pattern id. |  |
| relationships.relationships[].attack | string | yes | Source attack-pattern id (recommended namespace: 'attck'). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| relationships.relationships[].targets | array | yes | List of mapped controls for this attack pattern. | minItems=1 |
| relationships.relationships[].targets[] | object |  | One target control mapped from an attack pattern. |  |
| relationships.relationships[].targets[].control | string | yes | Target control id. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| relationships.relationships[].targets[].relationship_type | string | yes | Relationship type between the attack pattern and the control. | enum='mitigated_by', 'detectable_by', 'respondable_by' |
| relationships.relationships[].targets[].strength | anyOf |  | Optional quantitative strength in [0, 1] indicating how strongly this control mitigates/detects/responds to the attack pattern (tool/community-defined semantics). | default=None |
| relationships.relationships[].targets[].confidence | anyOf |  | Optional confidence score in [0, 1] for this mapping (tool/community-defined). | default=None |
| relationships.relationships[].targets[].description | anyOf |  | Optional description of how/why the control relates to the attack pattern. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| relationships.relationships[].targets[].references | anyOf |  | Optional list of references/citations supporting this mapping. | default=None |
| relationships.relationships[].targets[].tags | anyOf |  | Optional list of tags for grouping/filtering. | default=None |
| relationships.metadata | anyOf |  | Optional free-form metadata for tools (e.g., source dataset name/version). Not interpreted by validators/engines. | default=None |

### CRControlCatalog

Source: `crml_lang/src/crml_lang/schemas/crml-control-catalog-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_control_catalog | const | yes | Control catalog document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| catalog | object | yes |  |  |
| catalog.id | anyOf |  | Optional identifier for this catalog (organization-owned). | default=None |
| catalog.oscal_uuid | anyOf |  | Optional OSCAL UUID for the source catalog (interoperability metadata). CRML tooling should continue to reference the catalog via 'catalog.id' and controls via canonical 'id'. | default=None |
| catalog.framework | string | yes | Free-form framework label for humans/tools. |  |
| catalog.controls | array | yes | List of catalog entries. |  |
| catalog.controls[] | object |  | Portable metadata about a control id.  Important: do not embed copyrighted standard text here. Keep this to identifiers and tool-friendly metadata. |  |
| catalog.controls[].id | string | yes | Canonical unique control id present in this catalog. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| catalog.controls[].oscal_uuid | anyOf |  | Optional OSCAL UUID for this control. This is interoperability metadata only; CRML tools should continue to reference this control via the canonical 'id'. | default=None |
| catalog.controls[].ref | anyOf |  | Optional structured locator to map the id to an external standard. | default=None |
| catalog.controls[].title | anyOf |  | Optional short human-readable title for the control. | default=None |
| catalog.controls[].description | anyOf |  | Optional free-form description text for this control entry. Only include standard/control prose if you have rights to distribute it. | default=None |
| catalog.controls[].url | anyOf |  | Optional URL for additional reference material. | default=None |
| catalog.controls[].tags | anyOf |  | Optional list of tags for grouping/filtering. | default=None |
| catalog.controls[].defense_in_depth_layers | anyOf |  | Optional defense-in-depth layer tags. Allowed values: prevent, detect, respond, recover. | default=None |
| catalog.groups | anyOf |  | Optional hierarchical group structure (e.g., OSCAL groups). Groups reference controls by id via 'control_ids'. | default=None |

### CRControlRelationships

Source: `crml_lang/src/crml_lang/schemas/crml-control-relationships-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_control_relationships | const | yes | Control relationships document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| relationships | object | yes | Relationship pack payload.  This is a standalone, shareable dataset that can be community- or org-authored. |  |
| relationships.id | anyOf |  | Optional identifier for this relationships pack (organization/community-owned). | default=None |
| relationships.relationships | array | yes | List of grouped source-to-target relationship mappings. |  |
| relationships.relationships[] | object |  | Grouped relationship mapping for a single source control id.  Intended use: - A scenario references a (source) control A. - A portfolio implements one or more (target) controls B1..Bn. - This mapping expresses how each target relates to the source, including quantitative overlap metadata. |  |
| relationships.relationships[].source | string | yes | Source control id (often scenario/threat-centric). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| relationships.relationships[].targets | array | yes | List of target relationship mappings for this source control id. | minItems=1 |
| relationships.relationships[].targets[] | object |  | Target-specific relationship metadata for a given relationship source.  This keeps per-target quantitative metadata (e.g., overlap weights) while allowing relationship packs to be authored in a grouped 1:N form. |  |
| relationships.relationships[].targets[].target | string | yes | Target control id (often portfolio/implementation-centric). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| relationships.relationships[].targets[].relationship_type | anyOf |  | Optional relationship type. Values: 'overlaps_with', 'mitigates', 'supports', 'equivalent_to', 'parent_of', 'child_of', 'backstops'. | default=None |
| relationships.relationships[].targets[].overlap | object | yes | Quantitative overlap metadata used for downstream math.  Semantics (recommended): - weight: fraction of source coverage provided by the target in [0, 1] |  |
| relationships.relationships[].targets[].overlap.weight | number | yes | Quantitative overlap/coverage weight in [0, 1]. Recommended semantics: the fraction of the source control's mitigation objective that is covered by the target control. | minimum=0.0; maximum=1.0 |
| relationships.relationships[].targets[].overlap.dimensions | anyOf |  | Optional multidimensional overlap weights (dimension_name -> weight in [0, 1]). Dimension names are tool/community-defined (e.g. 'coverage', 'intent', 'implementation'). | default=None |
| relationships.relationships[].targets[].overlap.rationale | anyOf |  | Optional free-form rationale explaining why the overlap weight(s) were chosen. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| relationships.relationships[].targets[].confidence | anyOf |  | Optional confidence score in [0, 1] for this mapping/relationship (community/org-defined). | default=None |
| relationships.relationships[].targets[].groupings | anyOf |  | Optional taxonomy/grouping tags for this relationship (framework-agnostic). Example: NIST CSF Function classification. | default=None |
| relationships.relationships[].targets[].description | anyOf |  | Optional description of how/why the target relates to the source. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| relationships.relationships[].targets[].references | anyOf |  | Optional list of references/citations supporting this relationship. | default=None |

### CRPortfolioBundle

Source: `crml_lang/src/crml_lang/schemas/crml-portfolio-bundle-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_portfolio_bundle | const |  | Portfolio bundle document version identifier. | const='1.0'; default='1.0' |
| portfolio_bundle | object | yes | Portfolio bundle payload for `CRPortfolioBundle`.  This is intentionally the inlined artifact content; engines should not require filesystem access. |  |
| portfolio_bundle.portfolio | object | yes |  |  |
| portfolio_bundle.portfolio.crml_portfolio | const | yes | Portfolio document version identifier. | const='1.0' |
| portfolio_bundle.portfolio.meta | object | yes |  |  |
| portfolio_bundle.portfolio.meta.name | string | yes | Human-friendly name for this document. |  |
| portfolio_bundle.portfolio.meta.version | anyOf |  | Optional version string for this document. | default=None |
| portfolio_bundle.portfolio.meta.description | anyOf |  | Optional free-form description. | default=None |
| portfolio_bundle.portfolio.meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| portfolio_bundle.portfolio.meta.author | anyOf |  | Optional author/owner. | default=None |
| portfolio_bundle.portfolio.meta.organization | anyOf |  | Optional organization name. | default=None |
| portfolio_bundle.portfolio.meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| portfolio_bundle.portfolio.meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| portfolio_bundle.portfolio.meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| portfolio_bundle.portfolio.meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| portfolio_bundle.portfolio.meta.company_sizes | anyOf |  | Optional list of company size tags (at most one entry for portfolios). | default=None |
| portfolio_bundle.portfolio.meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| portfolio_bundle.portfolio.meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| portfolio_bundle.portfolio.meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| portfolio_bundle.portfolio.portfolio | object | yes |  |  |
| portfolio_bundle.portfolio.portfolio.assets | array |  | List of assets/exposures in the portfolio. |  |
| portfolio_bundle.portfolio.portfolio.assets[] | object |  |  |  |
| portfolio_bundle.portfolio.portfolio.assets[].name | string | yes | Unique asset name within the portfolio. |  |
| portfolio_bundle.portfolio.portfolio.assets[].cardinality | integer | yes | Number of identical asset units represented by this asset entry (>= 1). | minimum=1 |
| portfolio_bundle.portfolio.portfolio.assets[].criticality_index | anyOf |  | Optional criticality index configuration for this asset. | default=None |
| portfolio_bundle.portfolio.portfolio.assets[].tags | anyOf |  | Optional list of tags for grouping/filtering assets. | default=None |
| portfolio_bundle.portfolio.portfolio.controls | anyOf |  | Optional list of controls present in the organization/portfolio. | default=None |
| portfolio_bundle.portfolio.portfolio.control_catalogs | anyOf |  | Optional list of file paths to referenced control catalogs. | default=None |
| portfolio_bundle.portfolio.portfolio.attack_catalogs | anyOf |  | Optional list of file paths to referenced attack catalogs (e.g., MITRE ATT&CK). These are metadata-only catalogs used by tools/engines to resolve attack-pattern ids. | default=None |
| portfolio_bundle.portfolio.portfolio.assessments | anyOf |  | Optional list of file paths to referenced assessment catalogs. | default=None |
| portfolio_bundle.portfolio.portfolio.control_relationships | anyOf |  | Optional list of file paths to referenced control relationships packs (control-to-control mappings). These can be used by tools/engines to resolve scenario control ids to implemented portfolio controls with quantitative overlap metadata. | default=None |
| portfolio_bundle.portfolio.portfolio.attack_control_relationships | anyOf |  | Optional list of file paths to referenced attack-to-control relationships mappings. These can be used by tools/engines to translate attack-pattern ids (e.g., ATT&CK) into relevant controls. | default=None |
| portfolio_bundle.portfolio.portfolio.scenarios | array | yes | List of scenario references included in the portfolio. |  |
| portfolio_bundle.portfolio.portfolio.scenarios[] | object |  |  |  |
| portfolio_bundle.portfolio.portfolio.scenarios[].id | string | yes | Unique scenario id within the portfolio. |  |
| portfolio_bundle.portfolio.portfolio.scenarios[].path | string | yes | Path to the referenced CRML scenario document. |  |
| portfolio_bundle.portfolio.portfolio.scenarios[].weight | anyOf |  | Optional weight used by some portfolio aggregation methods (model-specific). | default=None |
| portfolio_bundle.portfolio.portfolio.scenarios[].binding | object |  |  |  |
| portfolio_bundle.portfolio.portfolio.scenarios[].binding.applies_to_assets | anyOf |  | Optional explicit list of portfolio asset names this scenario applies to. Used for per-asset-unit scenarios to define the exposure set. | default=None |
| portfolio_bundle.portfolio.portfolio.scenarios[].tags | anyOf |  | Optional list of tags for grouping/filtering scenarios. | default=None |
| portfolio_bundle.portfolio.portfolio.semantics | object | yes |  |  |
| portfolio_bundle.portfolio.portfolio.semantics.method | string | yes | Aggregation semantics used to combine scenario losses. | enum='sum', 'mixture', 'choose_one', 'max' |
| portfolio_bundle.portfolio.portfolio.semantics.constraints | object |  |  |  |
| portfolio_bundle.portfolio.portfolio.semantics.constraints.require_paths_exist | boolean |  | If true, referenced file paths must exist during validation. | default=False |
| portfolio_bundle.portfolio.portfolio.semantics.constraints.validate_scenarios | boolean |  | If true, referenced scenario files are schema-validated during portfolio validation. | default=True |
| portfolio_bundle.portfolio.portfolio.semantics.constraints.validate_relevance | boolean |  | If true, perform additional relevance checks between the portfolio organization context (meta.locale/meta.industries/meta.company_sizes/meta.regulatory_frameworks) and the referenced scenarios. Also validates that portfolio control id namespaces align with declared regulatory frameworks. | default=False |
| portfolio_bundle.portfolio.portfolio.relationships | anyOf |  | Optional relationships between scenarios (correlation/conditional). | default=None |
| portfolio_bundle.portfolio.portfolio.dependency | anyOf |  | Optional dependency specification for runtime models (e.g. copulas). | default=None |
| portfolio_bundle.portfolio.portfolio.risk_tolerance | anyOf |  | Optional risk-tolerance threshold for this portfolio. Engines may use this for reporting (and optionally for gating/alerts), but it does not change the portfolio semantics by itself. | default=None |
| portfolio_bundle.portfolio.portfolio.context | object |  | Free-form context object for tools/runtimes (engine-defined). | additionalProperties=true |
| portfolio_bundle.scenarios | array |  | Scenario documents referenced by the portfolio, inlined. |  |
| portfolio_bundle.scenarios[] | object |  |  |  |
| portfolio_bundle.scenarios[].id | string | yes | Scenario id from the portfolio. |  |
| portfolio_bundle.scenarios[].weight | anyOf |  | Optional scenario weight (portfolio semantics dependent). | default=None |
| portfolio_bundle.scenarios[].source_path | anyOf |  | Original scenario path reference (if any). | default=None |
| portfolio_bundle.scenarios[].scenario | object | yes |  | additionalProperties=false |
| portfolio_bundle.scenarios[].scenario.crml_scenario | const | yes | Scenario document version identifier. | const='1.0' |
| portfolio_bundle.scenarios[].scenario.meta | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.meta.name | string | yes | Human-friendly name for this document. |  |
| portfolio_bundle.scenarios[].scenario.meta.version | anyOf |  | Optional version string for this document. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.description | anyOf |  | Optional free-form description. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| portfolio_bundle.scenarios[].scenario.meta.author | anyOf |  | Optional author/owner. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.organization | anyOf |  | Optional organization name. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| portfolio_bundle.scenarios[].scenario.meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| portfolio_bundle.scenarios[].scenario.meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| portfolio_bundle.scenarios[].scenario.evidence | anyOf |  | Optional evidence/provenance section designed for scenarios authored from threat reports/news and for lightweight calibration metadata. | default=None |
| portfolio_bundle.scenarios[].scenario.data | anyOf |  | Optional data source and feature mapping section. | default=None |
| portfolio_bundle.scenarios[].scenario.scenario | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.scenario.frequency | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.basis | string |  | Frequency basis/denominator (e.g. per-organization-year, per-asset-unit-year). | enum='per_organization_per_year', 'per_asset_unit_per_year'; default='per_organization_per_year' |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.model | string |  | Frequency distribution/model identifier (engine-defined). If omitted, defaults to 'poisson'. | default='poisson' |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters.lambda | anyOf |  | Threat-event frequency parameter (e.g. Poisson rate). Interpreted as baseline threat likelihood (threat landscape) before organization-specific vulnerability/control posture is applied. Serialized as 'lambda' in YAML/JSON. | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters.alpha_base | anyOf |  | Frequency model parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters.beta_base | anyOf |  | Frequency model parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters.r | anyOf |  | Frequency model parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.frequency.parameters.p | anyOf |  | Probability parameter for frequency model (0..1). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.scenario.severity.model | string | yes | Severity distribution/model identifier (engine-defined). |  |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters | object | yes |  |  |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.median | anyOf |  | Median loss value (distribution-dependent). Interpreted as threat impact (monetary loss per event). The reference approach models vulnerability primarily via likelihood (controls); vulnerability impact is not modeled. | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.currency | anyOf |  | Optional currency code/symbol for severity inputs. | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.mu | anyOf |  | Distribution parameter (e.g. lognormal mu). Used to parameterize threat impact. Prefer 'median' for human-readable inputs. | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.sigma | anyOf |  | Distribution parameter (e.g. lognormal sigma). Controls variability of threat impact (loss per event). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.shape | anyOf |  | Distribution parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.scale | anyOf |  | Distribution parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.alpha | anyOf |  | Distribution parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.x_min | anyOf |  | Minimum loss / truncation parameter (model-specific). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.parameters.single_losses | anyOf |  | Optional list of explicit sample losses (used by some empirical severity models). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.severity.components | anyOf |  | Optional component breakdown (engine/tool-defined structure). | default=None |
| portfolio_bundle.scenarios[].scenario.scenario.controls | anyOf |  | Optional threat-centric declaration of relevant controls. Semantics: the threat can be mitigated by these controls if present in the portfolio. | default=None |
| portfolio_bundle.control_catalogs | array |  | Optional inlined control catalog packs referenced by the portfolio. |  |
| portfolio_bundle.control_catalogs[] | object |  |  |  |
| portfolio_bundle.control_catalogs[].crml_control_catalog | const | yes | Control catalog document version identifier. | const='1.0' |
| portfolio_bundle.control_catalogs[].catalog | object | yes |  |  |
| portfolio_bundle.control_catalogs[].catalog.id | anyOf |  | Optional identifier for this catalog (organization-owned). | default=None |
| portfolio_bundle.control_catalogs[].catalog.oscal_uuid | anyOf |  | Optional OSCAL UUID for the source catalog (interoperability metadata). CRML tooling should continue to reference the catalog via 'catalog.id' and controls via canonical 'id'. | default=None |
| portfolio_bundle.control_catalogs[].catalog.framework | string | yes | Free-form framework label for humans/tools. |  |
| portfolio_bundle.control_catalogs[].catalog.controls | array | yes | List of catalog entries. |  |
| portfolio_bundle.control_catalogs[].catalog.controls[] | object |  | Portable metadata about a control id.  Important: do not embed copyrighted standard text here. Keep this to identifiers and tool-friendly metadata. |  |
| portfolio_bundle.control_catalogs[].catalog.controls[].id | string | yes | Canonical unique control id present in this catalog. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.control_catalogs[].catalog.controls[].oscal_uuid | anyOf |  | Optional OSCAL UUID for this control. This is interoperability metadata only; CRML tools should continue to reference this control via the canonical 'id'. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].ref | anyOf |  | Optional structured locator to map the id to an external standard. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].title | anyOf |  | Optional short human-readable title for the control. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].description | anyOf |  | Optional free-form description text for this control entry. Only include standard/control prose if you have rights to distribute it. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].url | anyOf |  | Optional URL for additional reference material. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].tags | anyOf |  | Optional list of tags for grouping/filtering. | default=None |
| portfolio_bundle.control_catalogs[].catalog.controls[].defense_in_depth_layers | anyOf |  | Optional defense-in-depth layer tags. Allowed values: prevent, detect, respond, recover. | default=None |
| portfolio_bundle.control_catalogs[].catalog.groups | anyOf |  | Optional hierarchical group structure (e.g., OSCAL groups). Groups reference controls by id via 'control_ids'. | default=None |
| portfolio_bundle.assessments | array |  | Optional inlined assessment packs referenced by the portfolio. |  |
| portfolio_bundle.assessments[] | object |  |  | additionalProperties=false |
| portfolio_bundle.assessments[].crml_assessment | const | yes | Assessment document version identifier. | const='1.0' |
| portfolio_bundle.assessments[].assessment | object | yes |  | additionalProperties=false |
| portfolio_bundle.assessments[].assessment.id | anyOf |  | Optional identifier for this assessment catalog (organization-owned). | default=None |
| portfolio_bundle.assessments[].assessment.framework | string | yes | Free-form framework label for humans/tools (e.g. 'CISv8', 'ISO27001:2022'). |  |
| portfolio_bundle.assessments[].assessment.assessed_at | anyOf |  | When this assessment catalog was performed/recorded (ISO 8601 date-time). Example: '2025-12-17T10:15:30Z'. | default=None |
| portfolio_bundle.assessments[].assessment.assessments | array | yes | List of per-control assessment entries. |  |
| portfolio_bundle.assessments[].assessment.assessments[] | object |  |  | additionalProperties=false |
| portfolio_bundle.assessments[].assessment.assessments[].id | string | yes | Canonical unique control id in the form 'namespace:key' (no whitespace). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.assessments[].assessment.assessments[].oscal_uuid | anyOf |  | Optional OSCAL UUID for this control assessment target. This is interoperability metadata only; referencing/joining within CRML should use the canonical 'id'. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].ref | anyOf |  | Optional structured locator for mapping to an external standard (e.g. CIS/ISO). This is metadata only; referencing should use the canonical 'id'. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].implementation_effectiveness | anyOf |  | Organization-specific implementation strength for this control. Semantics: 0.0 = not implemented / no coverage, 1.0 = fully implemented. This represents vulnerability likelihood (susceptibility) posture used to mitigate a scenario's baseline threat frequency. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].coverage | anyOf |  | Breadth of deployment/application across the organization. This contributes to vulnerability likelihood reduction when applying this control to a scenario. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].reliability | anyOf |  | Reliability/uptime of the control as a probability of being effective in a given period. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].affects | anyOf |  | Which loss component this assessment affects. Default is 'frequency' (frequency-first). Note: the current reference engine primarily applies controls to frequency (lambda). | default='frequency' |
| portfolio_bundle.assessments[].assessment.assessments[].scf_cmm_level | anyOf |  | SCF Capability Maturity Model (CMM) level for this control (0..5). Levels: 0=Not Performed, 1=Performed Informally, 2=Planned & Tracked, 3=Well-Defined, 4=Quantitatively Controlled, 5=Continuously Improving. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].question | anyOf |  | Optional assessment prompt/question text for this control (tool/community-defined). Useful for questionnaires and evidence collection. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].description | anyOf |  | Optional additional description for this assessment entry (tool/community-defined). Avoid embedding copyrighted standard text unless you have rights. | default=None |
| portfolio_bundle.assessments[].assessment.assessments[].notes | anyOf |  | Free-form notes about this assessment entry. | default=None |
| portfolio_bundle.control_relationships | array |  | Optional inlined control relationships packs referenced by the portfolio. |  |
| portfolio_bundle.control_relationships[] | object |  |  |  |
| portfolio_bundle.control_relationships[].crml_control_relationships | const | yes | Control relationships document version identifier. | const='1.0' |
| portfolio_bundle.control_relationships[].relationships | object | yes | Relationship pack payload.  This is a standalone, shareable dataset that can be community- or org-authored. |  |
| portfolio_bundle.control_relationships[].relationships.id | anyOf |  | Optional identifier for this relationships pack (organization/community-owned). | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships | array | yes | List of grouped source-to-target relationship mappings. |  |
| portfolio_bundle.control_relationships[].relationships.relationships[] | object |  | Grouped relationship mapping for a single source control id.  Intended use: - A scenario references a (source) control A. - A portfolio implements one or more (target) controls B1..Bn. - This mapping expresses how each target relates to the source, including quantitative overlap metadata. |  |
| portfolio_bundle.control_relationships[].relationships.relationships[].source | string | yes | Source control id (often scenario/threat-centric). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets | array | yes | List of target relationship mappings for this source control id. | minItems=1 |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[] | object |  | Target-specific relationship metadata for a given relationship source.  This keeps per-target quantitative metadata (e.g., overlap weights) while allowing relationship packs to be authored in a grouped 1:N form. |  |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].target | string | yes | Target control id (often portfolio/implementation-centric). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].relationship_type | anyOf |  | Optional relationship type. Values: 'overlaps_with', 'mitigates', 'supports', 'equivalent_to', 'parent_of', 'child_of', 'backstops'. | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].overlap | object | yes | Quantitative overlap metadata used for downstream math.  Semantics (recommended): - weight: fraction of source coverage provided by the target in [0, 1] |  |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].overlap.weight | number | yes | Quantitative overlap/coverage weight in [0, 1]. Recommended semantics: the fraction of the source control's mitigation objective that is covered by the target control. | minimum=0.0; maximum=1.0 |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].overlap.dimensions | anyOf |  | Optional multidimensional overlap weights (dimension_name -> weight in [0, 1]). Dimension names are tool/community-defined (e.g. 'coverage', 'intent', 'implementation'). | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].overlap.rationale | anyOf |  | Optional free-form rationale explaining why the overlap weight(s) were chosen. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].confidence | anyOf |  | Optional confidence score in [0, 1] for this mapping/relationship (community/org-defined). | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].groupings | anyOf |  | Optional taxonomy/grouping tags for this relationship (framework-agnostic). Example: NIST CSF Function classification. | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].description | anyOf |  | Optional description of how/why the target relates to the source. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| portfolio_bundle.control_relationships[].relationships.relationships[].targets[].references | anyOf |  | Optional list of references/citations supporting this relationship. | default=None |
| portfolio_bundle.attack_catalogs | array |  | Optional inlined attack catalogs (e.g., MITRE ATT&CK) referenced by the portfolio. |  |
| portfolio_bundle.attack_catalogs[] | object |  |  |  |
| portfolio_bundle.attack_catalogs[].crml_attack_catalog | const | yes | Attack catalog document version identifier. | const='1.0' |
| portfolio_bundle.attack_catalogs[].catalog | object | yes |  |  |
| portfolio_bundle.attack_catalogs[].catalog.id | string | yes | Catalog identifier and namespace for all attack ids in this catalog. All catalog.attacks[*].id values must begin with '<catalog.id>:' (e.g. catalog.id='attck' -> 'attck:T1566'). | pattern='^[a-z][a-z0-9_-]{0,31}$'; minLength=1; maxLength=32 |
| portfolio_bundle.attack_catalogs[].catalog.framework | string | yes | Free-form framework label for humans/tools. Example: 'MITRE ATT&CK Enterprise'. |  |
| portfolio_bundle.attack_catalogs[].catalog.attacks | array | yes | List of attack pattern catalog entries. |  |
| portfolio_bundle.attack_catalogs[].catalog.attacks[] | object |  | Portable metadata about an attack id.  Important: do not embed copyrighted framework text here. Keep this to identifiers and tool-friendly metadata. |  |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].id | string | yes | Canonical unique attack id present in this catalog. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].kind | string | yes | Required normalized entry kind for engines and tools. | enum(10) |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].title | anyOf |  | Optional short human-readable title for the attack entry. | default=None |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].url | anyOf |  | Optional URL for additional reference material. | default=None |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].parent | anyOf |  | Optional parent attack id (same catalog namespace). Useful for hierarchical frameworks (e.g. ATT&CK technique -> sub-technique, NIST CSF function -> category -> subcategory). | default=None |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].phases | anyOf |  | Optional list of phase-like ids (same catalog namespace) that this entry is associated with. For ATT&CK, this can point to tactic ids. For kill chains, phases are typically represented as entries themselves. | default=None |
| portfolio_bundle.attack_catalogs[].catalog.attacks[].tags | anyOf |  | Optional extra tags for grouping/filtering. Tags are non-semantic and must not replace 'kind'. | default=None |
| portfolio_bundle.attack_control_relationships | array |  | Optional inlined attack-to-control relationships mappings referenced by the portfolio. |  |
| portfolio_bundle.attack_control_relationships[] | object |  |  |  |
| portfolio_bundle.attack_control_relationships[].crml_attack_control_relationships | const | yes | Attack-to-control relationships document version identifier. | const='1.0' |
| portfolio_bundle.attack_control_relationships[].relationships | object | yes | Relationship pack payload.  This is a standalone, shareable dataset that can be community- or org-authored. |  |
| portfolio_bundle.attack_control_relationships[].relationships.id | anyOf |  | Optional identifier for this relationships pack (organization/community-owned). | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.relationships | array | yes | List of grouped attack-to-control relationship mappings. |  |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[] | object |  | Grouped relationship mapping for a single attack pattern id. |  |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].attack | string | yes | Source attack-pattern id (recommended namespace: 'attck'). | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets | array | yes | List of mapped controls for this attack pattern. | minItems=1 |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[] | object |  | One target control mapped from an attack pattern. |  |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].control | string | yes | Target control id. | pattern='^[a-z][a-z0-9_-]{0,31}:[^\\s]{1,223}$'; minLength=1; maxLength=256 |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].relationship_type | string | yes | Relationship type between the attack pattern and the control. | enum='mitigated_by', 'detectable_by', 'respondable_by' |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].strength | anyOf |  | Optional quantitative strength in [0, 1] indicating how strongly this control mitigates/detects/responds to the attack pattern (tool/community-defined semantics). | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].confidence | anyOf |  | Optional confidence score in [0, 1] for this mapping (tool/community-defined). | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].description | anyOf |  | Optional description of how/why the control relates to the attack pattern. Avoid embedding copyrighted standard text unless you have rights. | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].references | anyOf |  | Optional list of references/citations supporting this mapping. | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.relationships[].targets[].tags | anyOf |  | Optional list of tags for grouping/filtering. | default=None |
| portfolio_bundle.attack_control_relationships[].relationships.metadata | anyOf |  | Optional free-form metadata for tools (e.g., source dataset name/version). Not interpreted by validators/engines. | default=None |
| portfolio_bundle.warnings | array |  | Non-fatal bundle warnings. |  |
| portfolio_bundle.warnings[] | object |  |  |  |
| portfolio_bundle.warnings[].level | string | yes | Message severity level. | enum='error', 'warning' |
| portfolio_bundle.warnings[].path | string | yes | Logical document path where the issue occurred. |  |
| portfolio_bundle.warnings[].message | string | yes | Human-readable message. |  |
| portfolio_bundle.metadata | object |  | Optional metadata for traceability (e.g., source refs). Not interpreted by engines. | additionalProperties=true |

### CRPortfolio

Source: `crml_lang/src/crml_lang/schemas/crml-portfolio-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_portfolio | const | yes | Portfolio document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags (at most one entry for portfolios). | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| portfolio | object | yes |  |  |
| portfolio.assets | array |  | List of assets/exposures in the portfolio. |  |
| portfolio.assets[] | object |  |  |  |
| portfolio.assets[].name | string | yes | Unique asset name within the portfolio. |  |
| portfolio.assets[].cardinality | integer | yes | Number of identical asset units represented by this asset entry (>= 1). | minimum=1 |
| portfolio.assets[].criticality_index | anyOf |  | Optional criticality index configuration for this asset. | default=None |
| portfolio.assets[].tags | anyOf |  | Optional list of tags for grouping/filtering assets. | default=None |
| portfolio.controls | anyOf |  | Optional list of controls present in the organization/portfolio. | default=None |
| portfolio.control_catalogs | anyOf |  | Optional list of file paths to referenced control catalogs. | default=None |
| portfolio.attack_catalogs | anyOf |  | Optional list of file paths to referenced attack catalogs (e.g., MITRE ATT&CK). These are metadata-only catalogs used by tools/engines to resolve attack-pattern ids. | default=None |
| portfolio.assessments | anyOf |  | Optional list of file paths to referenced assessment catalogs. | default=None |
| portfolio.control_relationships | anyOf |  | Optional list of file paths to referenced control relationships packs (control-to-control mappings). These can be used by tools/engines to resolve scenario control ids to implemented portfolio controls with quantitative overlap metadata. | default=None |
| portfolio.attack_control_relationships | anyOf |  | Optional list of file paths to referenced attack-to-control relationships mappings. These can be used by tools/engines to translate attack-pattern ids (e.g., ATT&CK) into relevant controls. | default=None |
| portfolio.scenarios | array | yes | List of scenario references included in the portfolio. |  |
| portfolio.scenarios[] | object |  |  |  |
| portfolio.scenarios[].id | string | yes | Unique scenario id within the portfolio. |  |
| portfolio.scenarios[].path | string | yes | Path to the referenced CRML scenario document. |  |
| portfolio.scenarios[].weight | anyOf |  | Optional weight used by some portfolio aggregation methods (model-specific). | default=None |
| portfolio.scenarios[].binding | object |  |  |  |
| portfolio.scenarios[].binding.applies_to_assets | anyOf |  | Optional explicit list of portfolio asset names this scenario applies to. Used for per-asset-unit scenarios to define the exposure set. | default=None |
| portfolio.scenarios[].tags | anyOf |  | Optional list of tags for grouping/filtering scenarios. | default=None |
| portfolio.semantics | object | yes |  |  |
| portfolio.semantics.method | string | yes | Aggregation semantics used to combine scenario losses. | enum='sum', 'mixture', 'choose_one', 'max' |
| portfolio.semantics.constraints | object |  |  |  |
| portfolio.semantics.constraints.require_paths_exist | boolean |  | If true, referenced file paths must exist during validation. | default=False |
| portfolio.semantics.constraints.validate_scenarios | boolean |  | If true, referenced scenario files are schema-validated during portfolio validation. | default=True |
| portfolio.semantics.constraints.validate_relevance | boolean |  | If true, perform additional relevance checks between the portfolio organization context (meta.locale/meta.industries/meta.company_sizes/meta.regulatory_frameworks) and the referenced scenarios. Also validates that portfolio control id namespaces align with declared regulatory frameworks. | default=False |
| portfolio.relationships | anyOf |  | Optional relationships between scenarios (correlation/conditional). | default=None |
| portfolio.dependency | anyOf |  | Optional dependency specification for runtime models (e.g. copulas). | default=None |
| portfolio.risk_tolerance | anyOf |  | Optional risk-tolerance threshold for this portfolio. Engines may use this for reporting (and optionally for gating/alerts), but it does not change the portfolio semantics by itself. | default=None |
| portfolio.context | object |  | Free-form context object for tools/runtimes (engine-defined). | additionalProperties=true |

### CRScenario

Source: `crml_lang/src/crml_lang/schemas/crml-scenario-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_scenario | const | yes | Scenario document version identifier. | const='1.0' |
| meta | object | yes |  |  |
| meta.name | string | yes | Human-friendly name for this document. |  |
| meta.version | anyOf |  | Optional version string for this document. | default=None |
| meta.description | anyOf |  | Optional free-form description. | default=None |
| meta.reference | anyOf |  | Optional reference URL for this document (provenance pointer). Tools should set this only when the source is a URL (not a local path). | default=None |
| meta.author | anyOf |  | Optional author/owner. | default=None |
| meta.organization | anyOf |  | Optional organization name. | default=None |
| meta.industries | anyOf |  | Optional list of industry tags. | default=None |
| meta.locale | object |  | Optional locale/region information and arbitrary locale metadata. | additionalProperties=true |
| meta.locale.regions | anyOf |  | Optional list of region tokens. | default=None |
| meta.locale.countries | anyOf |  | Optional list of ISO 3166-1 alpha-2 country codes. | default=None |
| meta.company_sizes | anyOf |  | Optional list of company size tags. | default=None |
| meta.regulatory_frameworks | anyOf |  | Optional list of regulatory frameworks relevant to this document. | default=None |
| meta.tags | anyOf |  | Optional list of user-defined tags. | default=None |
| meta.attck | anyOf |  | Optional list of ATT&CK tactic/technique/sub-technique identifiers relevant to this document, expressed as namespaced ids (e.g. 'attck:T1059.003'). | default=None |
| evidence | anyOf |  | Optional evidence/provenance section designed for scenarios authored from threat reports/news and for lightweight calibration metadata. | default=None |
| data | anyOf |  | Optional data source and feature mapping section. | default=None |
| scenario | object | yes |  |  |
| scenario.frequency | object | yes |  |  |
| scenario.frequency.basis | string |  | Frequency basis/denominator (e.g. per-organization-year, per-asset-unit-year). | enum='per_organization_per_year', 'per_asset_unit_per_year'; default='per_organization_per_year' |
| scenario.frequency.model | string |  | Frequency distribution/model identifier (engine-defined). If omitted, defaults to 'poisson'. | default='poisson' |
| scenario.frequency.parameters | object | yes |  |  |
| scenario.frequency.parameters.lambda | anyOf |  | Threat-event frequency parameter (e.g. Poisson rate). Interpreted as baseline threat likelihood (threat landscape) before organization-specific vulnerability/control posture is applied. Serialized as 'lambda' in YAML/JSON. | default=None |
| scenario.frequency.parameters.alpha_base | anyOf |  | Frequency model parameter (model-specific). | default=None |
| scenario.frequency.parameters.beta_base | anyOf |  | Frequency model parameter (model-specific). | default=None |
| scenario.frequency.parameters.r | anyOf |  | Frequency model parameter (model-specific). | default=None |
| scenario.frequency.parameters.p | anyOf |  | Probability parameter for frequency model (0..1). | default=None |
| scenario.severity | object | yes |  |  |
| scenario.severity.model | string | yes | Severity distribution/model identifier (engine-defined). |  |
| scenario.severity.parameters | object | yes |  |  |
| scenario.severity.parameters.median | anyOf |  | Median loss value (distribution-dependent). Interpreted as threat impact (monetary loss per event). The reference approach models vulnerability primarily via likelihood (controls); vulnerability impact is not modeled. | default=None |
| scenario.severity.parameters.currency | anyOf |  | Optional currency code/symbol for severity inputs. | default=None |
| scenario.severity.parameters.mu | anyOf |  | Distribution parameter (e.g. lognormal mu). Used to parameterize threat impact. Prefer 'median' for human-readable inputs. | default=None |
| scenario.severity.parameters.sigma | anyOf |  | Distribution parameter (e.g. lognormal sigma). Controls variability of threat impact (loss per event). | default=None |
| scenario.severity.parameters.shape | anyOf |  | Distribution parameter (model-specific). | default=None |
| scenario.severity.parameters.scale | anyOf |  | Distribution parameter (model-specific). | default=None |
| scenario.severity.parameters.alpha | anyOf |  | Distribution parameter (model-specific). | default=None |
| scenario.severity.parameters.x_min | anyOf |  | Minimum loss / truncation parameter (model-specific). | default=None |
| scenario.severity.parameters.single_losses | anyOf |  | Optional list of explicit sample losses (used by some empirical severity models). | default=None |
| scenario.severity.components | anyOf |  | Optional component breakdown (engine/tool-defined structure). | default=None |
| scenario.controls | anyOf |  | Optional threat-centric declaration of relevant controls. Semantics: the threat can be mitigated by these controls if present in the portfolio. | default=None |

### CRSimulationResult

Source: `crml_lang/src/crml_lang/schemas/crml-simulation-result-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_simulation_result | const |  | Simulation result document version identifier. | const='1.0'; default='1.0' |
| result | object | yes | Simulation result payload for `CRSimulationResult`. |  |
| result.success | boolean |  | True if the run completed successfully. | default=False |
| result.errors | array |  | List of error messages (if any). |  |
| result.errors[] | string |  |  |  |
| result.warnings | array |  | List of warning messages (if any). |  |
| result.warnings[] | string |  |  |  |
| result.engine | object | yes |  |  |
| result.engine.name | string | yes | Engine name/identifier. |  |
| result.engine.version | anyOf |  | Engine version string. | default=None |
| result.run | object |  |  |  |
| result.run.runs | anyOf |  | Number of Monte Carlo runs/samples executed. | default=None |
| result.run.seed | anyOf |  | Random seed used by the engine (if any). | default=None |
| result.run.runtime_ms | anyOf |  | Execution time in milliseconds (best-effort). | default=None |
| result.run.started_at | anyOf |  | UTC timestamp when execution started. | default=None |
| result.inputs | object |  |  |  |
| result.inputs.model_name | anyOf |  | Optional input model name (from scenario/portfolio meta). | default=None |
| result.inputs.model_version | anyOf |  | Optional input model version (from scenario/portfolio meta). | default=None |
| result.inputs.description | anyOf |  | Optional input model description (from meta). | default=None |
| result.inputs.risk_tolerance | anyOf |  | Optional risk-tolerance threshold captured from the input portfolio/bundle. Provided for reporting and downstream tooling. | default=None |
| result.units | anyOf |  | Optional unit metadata for values in this result. | default=None |
| result.summaries | array |  | Optional summary-statistics blocks for one or more target distributions. This provides a stable place for common analyst-facing statistics like P5/P50/P90/P95/P99, mean, std dev, and tail expectations. |  |
| result.summaries[] | object |  |  |  |
| result.summaries[].id | string | yes | Identifier for the summarized target distribution. Should align with a measure/artifact id where possible (e.g., 'loss.annual'). |  |
| result.summaries[].label | anyOf |  | Optional human-friendly label for the target distribution. | default=None |
| result.summaries[].unit | anyOf |  | Optional unit metadata for all values in this summary block. | default=None |
| result.summaries[].stats | object |  |  |  |
| result.summaries[].stats.mean | anyOf |  | Mean of the target distribution. | default=None |
| result.summaries[].stats.median | anyOf |  | Median (P50) of the target distribution. | default=None |
| result.summaries[].stats.mode | anyOf |  | Mode of the target distribution if well-defined/estimated (engine-defined). | default=None |
| result.summaries[].stats.std_dev | anyOf |  | Standard deviation of the target distribution. | default=None |
| result.summaries[].stats.quantiles | array |  | Requested/available quantiles (e.g., P5/P50/P90/P95/P99) as probability/value pairs. |  |
| result.summaries[].stats.quantiles[] | object |  |  |  |
| result.summaries[].stats.quantiles[].p | number | yes | Quantile probability level in [0,1]. Example: 0.95 for P95. | minimum=0.0; maximum=1.0 |
| result.summaries[].stats.quantiles[].value | anyOf |  | Quantile value at probability level `p`. | default=None |
| result.summaries[].stats.tail_expectations | array |  | Tail expectation measures such as CVaR/Expected Shortfall. |  |
| result.summaries[].stats.tail_expectations[] | object |  |  |  |
| result.summaries[].stats.tail_expectations[].kind | string |  | Tail expectation kind. 'cvar' is synonymous with Expected Shortfall in many contexts. | enum='cvar', 'expected_shortfall'; default='cvar' |
| result.summaries[].stats.tail_expectations[].level | number | yes | Confidence level for the tail expectation in [0,1]. Example: 0.95. | minimum=0.0; maximum=1.0 |
| result.summaries[].stats.tail_expectations[].tail | string |  | Which tail is considered extreme. For losses, this is typically the right tail. | enum='right', 'left'; default='right' |
| result.summaries[].stats.tail_expectations[].value | anyOf |  | Tail expectation value at the given level. | default=None |
| result.summaries[].estimation | object |  |  |  |
| result.summaries[].estimation.computed_from | anyOf |  | How the summary statistics were computed (engine-defined). | default='unknown' |
| result.summaries[].estimation.sample_count_used | anyOf |  | Number of samples used to compute summary statistics (if applicable). | default=None |
| result.summaries[].estimation.histogram_bins_used | anyOf |  | Number of histogram bins used to compute summary statistics (if applicable). | default=None |
| result.summaries[].estimation.truncated | anyOf |  | Whether the underlying samples/histogram used for summary statistics were truncated. | default=None |
| result.summaries[].estimation.method | anyOf |  | Optional method notes (e.g., quantile algorithm, KDE bandwidth), engine-defined. | default=None |
| result.trace | anyOf |  | Optional traceability/provenance block capturing resolved inputs, distributions/parameters, and dependency structures for auditability. | default=None |
| result.results | object |  |  |  |
| result.results.measures | array |  | List of computed summary measures. |  |
| result.results.measures[] | object |  |  |  |
| result.results.measures[].id | string | yes | Measure identifier (e.g. 'eal', 'var_95'). |  |
| result.results.measures[].value | anyOf |  | Numeric measure value. | default=None |
| result.results.measures[].unit | anyOf |  | Optional unit metadata for this measure. | default=None |
| result.results.measures[].parameters | object |  | Optional parameterization metadata for this measure (engine/UI defined). | additionalProperties=true |
| result.results.measures[].label | anyOf |  | Optional human-friendly label for display. | default=None |
| result.results.artifacts | array |  | List of computed artifacts (histograms/samples). |  |
| result.results.artifacts[] | anyOf |  |  |  |

### CRML FX Config

Source: `crml_engine/src/crml_engine/schemas/crml-fx-config-schema.json`

| Path | Type | Required | Description | Constraints |
|---|---:|:---:|---|---|
| crml_fx_config | const | yes | CRML FX config document version | const='1.0' |
| base_currency | string | yes |  | minLength=1 |
| output_currency | string | yes |  | minLength=1 |
| as_of | string \| null |  |  | default=None |
| rates | object | yes |  |  |

<!-- END: GENERATED FIELD REFERENCE -->
