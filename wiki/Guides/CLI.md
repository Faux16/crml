# CRML Code — CLI Guide

**CRML Code** (`crml-cli`) is an AI-powered terminal interface for interactive cyber risk modeling. It takes you from a company name or a scan report to a full quantitative risk assessment and executive report — with no YAML required.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Bring Your Own Key (BYOK)](#bring-your-own-key-byok)
- [Usage](#usage)
- [Workflow](#workflow)
- [Output Files](#output-files)
- [Flags Reference](#flags-reference)
- [Architecture](#architecture)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.10+ |
| pip packages | `openai`, `rich`, `pyyaml`, `python-dotenv` |
| crml-lang | installed (from this repo) |
| crml-engine | installed (from this repo) |
| OpenAI API key | Your own key with GPT-4o access |

---

## Installation

```bash
# 1. Clone and enter the repo
git clone https://github.com/your-org/crml.git
cd crml

# 2. Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. Install the CRML packages
pip install -e ./crml_lang -e ./crml_engine

# 4. Install CLI dependencies
pip install openai rich pyyaml python-dotenv

# 5. Make the CLI executable
chmod +x crml-cli
```

---

## Bring Your Own Key (BYOK)

CRML Code uses your own OpenAI API key. It never ships with or requires a shared key.

### Key resolution order

The CLI looks for your key in this order and uses the first one it finds:

```
1. --api-key flag     (highest priority — one-time override)
2. OPENAI_API_KEY     (environment variable)
3. ~/.crml/config.json (persisted via --configure)
4. Interactive prompt  (fallback — asks you at startup)
```

### Saving your key (recommended)

Run `--configure` once. Your key is saved to `~/.crml/config.json` — a file outside the project directory that is never committed to git.

```bash
./crml-cli --configure
# Enter your OpenAI API key: ••••••••••••••••••••
# ✓ Key saved to ~/.crml/config.json
```

After this, you can run `./crml-cli` without any flags indefinitely.

### Config file format

`~/.crml/config.json`:
```json
{
  "openai_api_key": "sk-..."
}
```

### One-time override

```bash
./crml-cli --api-key sk-your-temp-key
```

The key is used for this session only and does **not** overwrite your saved config.

### Environment variable

```bash
export OPENAI_API_KEY=sk-your-key
./crml-cli
```

The env var takes priority over the saved config file.

---

## Usage

```bash
# Interactive mode (recommended)
./crml-cli

# Load a vulnerability scan report instead of manual input
./crml-cli --scan /path/to/report.json
./crml-cli --scan /path/to/report.csv

# Save/update your API key
./crml-cli --configure

# One-time key override
./crml-cli --api-key sk-...

# Combine: scan + key override
./crml-cli --scan report.json --api-key sk-...
```

---

## Workflow

### Step 1 — Organizational Context

You enter a company name (e.g. `"Stripe"`, `"a large retail bank"`). The CLI uses GPT-4o with web search to auto-discover:

- Legal company name and brand resolution (e.g. `Paytm → One97 Communications`)
- Annual revenue (with INR→USD conversion when needed)
- Employee count
- Industry classification
- Compliance frameworks in scope (GDPR, SOC 2, PCI-DSS, etc.)
- AI parameter guidance (suggested lambda, severity weighting, reasoning)

You can accept the discovered values or override any field.

### Step 2 — Risk Discovery

If you provided a scan file (`--scan`), findings are parsed and summarized automatically (supports JSON and CSV formats from Zeron and generic scanners).

If not, you can describe your findings in plain text (comma-separated), or press Enter to let the AI discover scenarios from the org context alone.

GPT-4o groups findings into **3–5 named risk scenarios** (e.g. `"Ransomware via Unpatched Server"`, `"Data Breach via SQL Injection"`).

### Step 3 — Quantitative Simulation

For each scenario, the CLI:

1. Generates a calibrated CRML model (frequency + severity parameters) grounded in the industry knowledge base
2. Shows MITRE ATT&CK technique tags (e.g. `T1566 Phishing`, `T1486 Data Encrypted for Impact`)
3. Shows the AI's reasoning for the chosen parameters
4. Runs **10,000 Monte Carlo trials** across **3 distribution variants**:

| Variant | Description |
|---------|-------------|
| Conservative | Tighter distribution (sigma × 0.7) |
| Baseline | Original model |
| Heavy-tail | Fatter tails (sigma × 1.5) |

Results show:
- **EAL** — Expected Annual Loss (average loss per year)
- **EAL Range** — Min–max across the 3 variants (confidence band)
- **VaR 95%** — 95th percentile loss (tail risk)

### Step 3b — Control ROI

Relevant security controls are automatically matched to your scenarios. The table shows:

| Column | Description |
|--------|-------------|
| Control | Control name (e.g. MFA, EDR, DLP) |
| Affects | Whether the control reduces frequency, severity, or both |
| Annual Cost | Estimated implementation + licensing cost |
| EAL Reduction | Expected loss reduction across matched scenarios |
| Net Savings | EAL Reduction minus Annual Cost |
| ROI | Net Savings as a percentage of cost |

### Step 4 — Report Generation

A peer benchmark comparison is shown (your EAL vs industry average, risk tier).

Then the CLI generates two report files:

- **`CRML_RISK_REPORT.md`** — Underwriter-style Markdown report
- **`CRML_RISK_REPORT.html`** — Styled dark-theme HTML report (ready to share)

Risk trend tracking: if you've run the CLI for this org before, a delta panel shows how EAL and VaR have changed since the last session.

### What-If Mode (optional)

After the report is generated, you can enter **What-If mode** to interactively tweak scenario parameters:

```
Select scenario to tweak: 2
Current Parameters for Ransomware via Unpatched Server:
  Lambda (frequency): 0.4
  Median (severity):  $2,500,000
  Sigma (tail risk):  1.5

New Lambda: 0.2          ← halve the frequency
New Median ($): 2500000
New Sigma: 1.8

What-If Result: Ransomware via Unpatched Server
  Original EAL: $1,234,000
  New EAL:        $678,000
  Change:      ↓ $556,000
  New VaR 95%: $8,900,000
```

---

## Output Files

All files are saved to `output/<org_slug>/`:

| File | Description |
|------|-------------|
| `portfolio.yaml` | All scenario models in CRML format (importable into CRML Studio) |
| `<scenario_name>.yaml` | Individual scenario CRML file |
| `CRML_RISK_REPORT.md` | Markdown executive report |
| `CRML_RISK_REPORT.html` | Styled HTML executive report |
| `benchmark.json` | Industry peer comparison data |
| `control_roi.json` | Control ROI table data |
| `session_history.json` | Historical EAL/VaR trend across runs |
| `session_log.txt` | Timestamped event log for the session |

---

## Flags Reference

| Flag | Short | Description |
|------|-------|-------------|
| `--api-key KEY` | `-k` | OpenAI API key (overrides env and config) |
| `--scan FILE` | `-s` | Path to vulnerability scan report (`.json` or `.csv`) |
| `--configure` | — | Update saved API key in `~/.crml/config.json` and exit |
| `--help` | `-h` | Show help |

---

## Architecture

```
crml-cli (bash wrapper)
  └── scripts/crml_cli.py       ← interactive CLI, arg parsing, BYOK key resolution
        └── scripts/crml_ai.py  ← OpenAI GPT-4o integration
              ├── init_client()             ← initializes OpenAI client with resolved key
              ├── discover_org_context()    ← web search for company data
              ├── discover_risk_scenarios() ← groups findings into scenarios
              ├── expert_ai_generator()     ← generates CRML model parameters
              ├── generate_benchmark_comparison() ← peer industry comparison
              └── generate_underwriter_report()   ← executive report content
        └── crml_engine.simulation.engine  ← Monte Carlo runner
        └── scripts/mitre_mapping.json     ← ATT&CK technique keyword map
        └── scripts/industry_benchmarks.json ← scenario parameter knowledge base
```

### BYOK key resolution (in `crml_cli.py`)

```python
resolve_api_key(cli_arg)
  → checks: cli_arg → os.getenv("OPENAI_API_KEY") → ~/.crml/config.json → Prompt.ask()
  → calls:  crml_ai.init_client(api_key)
              → sets global OpenAI client
              → sets os.environ["OPENAI_API_KEY"] (for per-function env checks)
```

---

## Troubleshooting

### `Fatal Error: 'NoneType' object has no attribute 'chat'`

The OpenAI client was not initialized. This means `init_client()` was not called before the AI functions ran. Make sure you are using the `crml-cli` wrapper (not calling `crml_cli.py` directly with an unresolved key).

### `No scenarios discovered`

- Check your OpenAI API key has GPT-4o access
- If using `--scan`, verify the file is valid JSON or CSV with recognizable column names (`vulnerability`, `severity`, `asset`)
- Try entering a manual description when prompted

### `Revenue appears to be INR passed as USD`

The CLI auto-detects when Indian company revenues (in crores/INR) are passed without conversion and applies a ÷83 correction. Review the corrected value at the prompt and adjust if needed.

### Scan file format

**JSON:**
```json
[
  { "vulnerability": "SQL Injection", "severity": "Critical", "asset": "web-app-01", "description": "..." },
  { "vulnerability": "Unpatched OpenSSL", "severity": "High", "asset": "api-server-02" }
]
```

**CSV:**
```csv
vulnerability,severity,asset,description
SQL Injection,Critical,web-app-01,User input not sanitized
Unpatched OpenSSL,High,api-server-02,
```

Flexible column aliases are supported: `title`/`name` for vulnerability, `risk` for severity, `host`/`target` for asset.
