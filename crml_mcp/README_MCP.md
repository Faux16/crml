# CRML Code — Claude Plugin (MCP Server)

Turn any Claude conversation into a live cyber risk modeling session. CRML Code exposes the full CRML workflow — org discovery, Monte Carlo simulation, and executive report generation — as native Claude tools via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io).

---

## What you can do

Once installed, just talk to Claude:

> *"Run a full cyber risk assessment for Stripe"*
> *"What's the expected annual loss for a ransomware attack on Bank of America?"*
> *"Simulate risk scenarios for a fintech startup with SQL injection and unpatched SSL findings"*

Claude will call the CRML tools automatically and return a structured risk report.

---

## Installation

### 1. Clone the repo and install

```bash
git clone https://github.com/Faux16/crml.git
cd crml

# Install core CRML packages
pip install -e ./crml_lang -e ./crml_engine

# Install the MCP server
pip install -e ./crml_mcp
```

### 2. Save your OpenAI API key

```bash
crml-mcp
# or via Claude after setup — use the configure_key tool
```

Or set it in your environment:

```bash
export OPENAI_API_KEY=sk-...
```

---

## Add to Claude Desktop

Open your Claude Desktop config file:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add the CRML server:

```json
{
  "mcpServers": {
    "crml": {
      "command": "crml-mcp"
    }
  }
}
```

If you want to pass your API key directly instead of using the saved config:

```json
{
  "mcpServers": {
    "crml": {
      "command": "crml-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. You'll see CRML tools available in the tool list.

---

## Add to Claude Code

```bash
claude mcp add crml -- crml-mcp
```

Or add to your project's `.claude/settings.json`:

```json
{
  "mcpServers": {
    "crml": {
      "command": "crml-mcp"
    }
  }
}
```

---

## Available Tools

### `assess_organization` ⭐ recommended
Full end-to-end assessment in one call — org research, scenario discovery, Monte Carlo simulation, and executive report.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `company` | string | ✅ | Company name (e.g. `"Stripe"`, `"a large retail bank"`) |
| `findings` | string | ❌ | Comma-separated vulnerability findings |
| `openai_api_key` | string | ❌ | Override key for this call only |

**Example prompt:**
> *"Assess Stripe's cyber risk with these findings: SQL Injection (Critical), MFA not enforced (High)"*

---

### `discover_org`
Research a company's profile via live web search — revenue, headcount, industry, compliance frameworks, and AI-suggested risk parameters.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `company` | string | ✅ | Company name or description |
| `openai_api_key` | string | ❌ | Override key for this call only |

---

### `simulate_risk`
Run 10,000-trial Monte Carlo simulations for named risk scenarios. Returns EAL, VaR 95%, and a confidence band across three model variants.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `company` | string | ✅ | Company name |
| `industry` | string | ✅ | Industry sector |
| `revenue` | float | ✅ | Annual revenue in USD |
| `employees` | int | ✅ | Employee count |
| `scenarios` | string | ✅ | Comma-separated scenario names |
| `openai_api_key` | string | ❌ | Override key for this call only |

---

### `generate_report`
Generate an AI-written executive underwriting report saved as Markdown and HTML.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `company` | string | ✅ | Company name |
| `industry` | string | ✅ | Industry |
| `revenue` | float | ✅ | Revenue in USD |
| `employees` | int | ✅ | Employee count |
| `compliances` | string | ✅ | Comma-separated compliance frameworks |
| `scenario_results` | string | ✅ | JSON array of `{name, metrics: {eal, var_95}}` |
| `openai_api_key` | string | ❌ | Override key for this call only |

---

### `configure_key`
Save your OpenAI API key to `~/.crml/config.json` once. All subsequent tool calls will use it automatically.

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `openai_api_key` | string | ✅ | Your OpenAI API key |

---

## API key resolution order

Each tool resolves the key in this priority order:

```
1. openai_api_key argument (per-call override)
2. OPENAI_API_KEY environment variable
3. ~/.crml/config.json  (saved via configure_key or crml-cli --configure)
```

---

## Output files

All outputs are saved to `output/<org_slug>/` in the CRML repo directory:

| File | Contents |
|------|----------|
| `CRML_RISK_REPORT.md` | Executive underwriting report |
| `CRML_RISK_REPORT.html` | Styled HTML version |
| `portfolio.yaml` | Scenario models in CRML format |
| `benchmark.json` | Industry peer comparison |
| `control_roi.json` | Control ROI analysis |

---

## About CRML

CRML (Cyber Risk Modeling Language) is an open standard for describing cyber risk models in a portable, version-controlled format. CRML Code is the AI-powered CLI and Claude plugin that makes CRML accessible without writing YAML.

[Full CLI documentation →](../wiki/Guides/CLI.md)
[CRML specification →](../wiki/Language/)
