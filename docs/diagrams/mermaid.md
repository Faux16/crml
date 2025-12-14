# CRML Diagrams

This page visualizes the structure and workflows within the Cyber Risk Modeling Language (CRML) ecosystem using Mermaid diagrams.

## 1. CRML Execution Workflow

This diagram illustrates how a CRML model file is processed from definition to final reporting.

```mermaid
graph LR
    User[User / Analyst] -->|Writes| CRML[CRML Model (.yaml)]
    CRML -->|Input| Validator[CRML Validator]
    Validator -->|Validates| Spec[CRML Spec 1.1]
    Validator -->|Pass| Engine[Simulation Engine]
    
    subgraph Engine Process
        Engine -->|Parses| ModelObj[Internal Model]
        ModelObj -->|Simulates| MC[Monte Carlo / MCMC]
        MC -->|Generates| Post[Posterior Distributions]
    end
    
    Post -->|Output| Report[Reports & Metrics]
    Post -->|Export| Data[CSV / JSON Data]
    
    style CRML fill:#f9f,stroke:#333,stroke-width:2px
    style Engine fill:#bbf,stroke:#333,stroke-width:2px
```

## 2. CRML Document Structure

The hierarchical structure of a valid CRML document.

```mermaid
classDiagram
    class CRML_Document {
        +String crml_version
    }
    class Meta {
        +String name
        +String version
        +String description
    }
    class Data {
        +Map sources
        +Map feature_mapping
    }
    class Model {
        +Assets assets
        +Frequency frequency
        +Severity severity
        +Dependency dependency
    }
    class Pipeline {
        +Simulation simulation
        +Validation validation
    }
    class Output {
        +List metrics
        +Map distributions
    }

    CRML_Document *-- Meta
    CRML_Document *-- Data
    CRML_Document *-- Model
    CRML_Document *-- Pipeline
    CRML_Document *-- Output
```

## 3. QBER Logic Flow

A visualization of the "QBER" (Quantified Bayesian Event Risk) model logic, showing how telemetry drives risk estimates.

```mermaid
graph TD
    subgraph Telemetry Sources
        PAM[PAM Logs]
        DLP[DLP Alerts]
        IAM[IAM Logs]
    end

    subgraph Feature Engineering
        Ent[Entropy Calculation]
    end

    subgraph Risk Model
        CI[Criticality Index]
        Freq[Frequency Model]
        Sev[Severity Model]
        Loss[Loss Distribution]
    end

    PAM --> Ent
    DLP --> Ent
    IAM --> Ent
    
    Ent -->|Input| CI
    CI -->|Weights| Freq
    
    Freq -->|Simulate| Loss
    Sev -->|Simulate| Loss
    
    style Ent fill:#dfd,stroke:#333,stroke-width:2px
    style CI fill:#fdd,stroke:#333,stroke-width:2px
```