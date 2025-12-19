export const PORTFOLIO_BUNDLE_DOCUMENTED_YAML = `# CRML Portfolio Bundle (crml_portfolio_bundle: "1.0")
#
# Goal
# ----
# A portfolio bundle is a single, self-contained artifact intended to be the
# contract between crml_lang and engines:
#
# - It contains a full CRML Portfolio document.
# - It inlines the referenced Scenario documents.
# - It can optionally inline catalogs and relationship packs that an engine or
#   tooling may use to resolve ids and apply control posture.
#
# Important design principle:
# - Engines SHOULD NOT require filesystem access when executing a bundle.
#   source_path fields are traceability only.
#
# Notes
# -----
# - This file is intentionally heavily documented inline.
#
# (This example is based on examples/portfolio_bundles/portfolio-bundle-documented.yaml)

crml_portfolio_bundle: "1.0"

portfolio_bundle:
  # ---------------------------------------------------------------------------
  # 1) Portfolio (required)
  # ---------------------------------------------------------------------------
  portfolio:
    crml_portfolio: "1.0"
    meta:
      name: "Documented portfolio bundle example"
      description: |
        Demonstration bundle showing how to inline a portfolio + scenarios +
        catalogs + assessments + relationships.

        This is designed for:
        - tooling workflows (validation, mapping, XLSX round-trips)
        - engine input without filesystem dependency
      tags: ["example", "bundle", "portfolio"]

    portfolio:
      # Portfolio semantics
      semantics:
        method: sum
        constraints:
          require_paths_exist: false
          validate_scenarios: false

      # Assets / exposure surface
      assets:
        - name: "employees"
          cardinality: 250
          tags: ["workforce"]
        - name: "endpoints"
          cardinality: 450
          tags: ["it", "endpoint"]

      # Optional referenced packs (paths)
      control_catalogs:
        - ../control_catalogs/control-catalog.yaml
      assessments:
        - ../control_assessments/control-assessment.yaml
      control_relationships:
        - ../control_relationships/cisv8-mappings.yaml
      attack_catalogs:
        - ../attack_catalogs/attck-catalog.yaml
      attack_control_relationships:
        - ../attack_control_relationships/attck-to-cisv8-mappings.yaml

      # Dependency modeling (copula example)
      dependency:
        copula:
          type: gaussian
          targets:
            - "control:org:iam.mfa:state"
            - "control:org:edr:state"
          structure: toeplitz
          rho: 0.35

      # Scenarios referenced by this portfolio
      scenarios:
        - id: phishing
          path: ../scenarios/scenario-phishing.yaml

  # ---------------------------------------------------------------------------
  # 2) Inlined scenarios (required for full portability)
  # ---------------------------------------------------------------------------
  scenarios:
    - id: phishing
      weight: 1.0
      source_path: "examples/scenarios/scenario-phishing.yaml"
      scenario:
        crml_scenario: "1.0"
        meta:
          name: "Phishing scenario (bundle example)"
          description: |
            Minimal phishing scenario to demonstrate how a bundle carries
            executable scenario inputs alongside a portfolio.
          tags: ["example", "phishing"]
          attck:
            - "attck:TA0001"
            - "attck:T1566"
            - "attck:T1566.001"

        scenario:
          frequency:
            basis: per_organization_per_year
            model: poisson
            parameters:
              lambda: 0.8

          severity:
            model: lognormal
            parameters:
              currency: USD
              median: "250 000"
              sigma: 1.1

          controls:
            - id: "org:iam.mfa"
              affects: frequency
              factor: 0.55
              notes: "MFA reduces successful credential abuse / account takeover."
            - id: "org:edr"
              affects: severity
              factor: 0.8
              notes: "EDR can reduce impact via faster detection/response."

  # ---------------------------------------------------------------------------
  # 3) Optional inlined control catalog(s)
  # ---------------------------------------------------------------------------
  control_catalogs:
    - crml_control_catalog: "1.0"
      meta:
        name: "Org control catalog (bundle example)"
        tags: ["example", "org"]
      catalog:
        id: "org"
        framework: "Org"
        controls:
          - id: "org:iam.mfa"
            title: "Multi-factor authentication"
            tags: ["identity", "prevent"]
          - id: "org:edr"
            title: "Endpoint detection and response"
            tags: ["endpoint", "detect", "respond"]

  # ---------------------------------------------------------------------------
  # 4) Optional inlined assessment(s)
  # ---------------------------------------------------------------------------
  assessments:
    - crml_assessment: "1.0"
      meta:
        name: "Org assessment (bundle example)"
        description: "Mixed posture styles across controls; never mixed within a single control entry."
        tags: ["example", "assessment"]
      assessment:
        id: "org-assessment-2025"
        framework: "Org"
        assessed_at: "2025-12-18T10:00:00Z"
        assessments:
          - id: "org:iam.mfa"
            implementation_effectiveness: 0.75
            coverage:
              value: 0.6
              basis: employees
              notes: "Percent of workforce accounts enforced (approx)."
            reliability: 0.98
            affects: frequency
            notes: "Rollout in progress; some service accounts excluded."

          - id: "org:edr"
            scf_cmm_level: 3
            affects: severity
            notes: "Standardized deployment; tuning still maturing."

  # ---------------------------------------------------------------------------
  # 5) Optional inlined control-to-control relationships
  # ---------------------------------------------------------------------------
  control_relationships:
    - crml_control_relationships: "1.0"
      meta:
        name: "Control relationships (bundle example)"
        tags: ["example", "control-relationships"]
      relationships:
        id: "org-rel-pack"
        relationships:
          - source: "cisv8:4.2"
            targets:
              - target: "org:iam.mfa"
                relationship_type: "supports"
                overlap:
                  weight: 0.55
                confidence: 0.6
                description: "Example crosswalk entry (not authoritative)."

  # ---------------------------------------------------------------------------
  # 6) Optional inlined attack catalog(s)
  # ---------------------------------------------------------------------------
  attack_catalogs:
    - crml_attack_catalog: "1.0"
      meta:
        name: "ATT&CK catalog (bundle example subset)"
        description: "Subset of ATT&CK entries used in this bundle. Metadata only."
        tags: ["example", "attck"]
      catalog:
        id: "attck"
        framework: "MITRE ATT&CK (Enterprise)"
        attacks:
          - id: "attck:TA0001"
            title: "Initial Access"
            url: "https://attack.mitre.org/tactics/TA0001/"
            tags: ["tactic"]
          - id: "attck:T1566"
            title: "Phishing"
            url: "https://attack.mitre.org/techniques/T1566/"
            tags: ["technique"]
            kill_chain_phases: ["mitre-attack:initial-access"]
          - id: "attck:T1566.001"
            title: "Spearphishing Attachment"
            url: "https://attack.mitre.org/techniques/T1566/001/"
            tags: ["sub-technique"]
            kill_chain_phases: ["mitre-attack:initial-access"]

  # ---------------------------------------------------------------------------
  # 7) Optional inlined attack-to-control relationships
  # ---------------------------------------------------------------------------
  attack_control_relationships:
    - crml_attack_control_relationships: "1.0"
      meta:
        name: "ATT&CK → controls mapping (bundle example)"
        tags: ["example", "attck", "mapping"]
      relationships:
        id: "attck-org-demo"
        metadata:
          source: "example"
          notes: "Demonstration-only; not authoritative."
        relationships:
          - attack: "attck:T1566"
            targets:
              - control: "org:iam.mfa"
                relationship_type: mitigated_by
                strength: 0.6
                confidence: 0.6
              - control: "org:edr"
                relationship_type: detectable_by
                strength: 0.5
                confidence: 0.7

  # ---------------------------------------------------------------------------
  # 8) Optional bundle messages + metadata
  # ---------------------------------------------------------------------------
  warnings: []

  metadata:
    source_kind: "example"
    created_at: "2025-12-18"
    notes: |
      This bundle is intentionally small. Real bundles would inline all referenced
      scenarios and packs and may be used as the engine input contract.
`; 
