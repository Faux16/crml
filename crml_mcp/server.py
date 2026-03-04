#!/usr/bin/env python3
"""
CRML Code MCP Server
---------------------
Exposes CRML Code as an MCP server so Claude Desktop, Claude Code,
and any MCP-compatible client can run cyber risk assessments as native tools.

Usage (stdio transport — default for Claude Desktop / Claude Code):
    python -m crml_mcp.server
    # or after pip install:
    crml-mcp
"""

import os
import sys
import json
import copy
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap — resolve scripts/crml_ai.py relative to this file
# Works both when running from repo root and when installed via pip
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT))

from mcp.server.fastmcp import FastMCP
import crml_ai

# ---------------------------------------------------------------------------
# Server definition
# ---------------------------------------------------------------------------
mcp = FastMCP(
    "crml-code",
    instructions=(
        "CRML Code is an AI-powered cyber risk modeling tool built on the "
        "Cyber Risk Modeling Language (CRML) standard.\n\n"
        "Available tools:\n"
        "  • assess_organization  — full end-to-end risk assessment (recommended)\n"
        "  • discover_org         — research a company's profile via web search\n"
        "  • simulate_risk        — run Monte Carlo simulation for named scenarios\n"
        "  • generate_report      — produce an executive underwriting report\n"
        "  • configure_key        — save your OpenAI API key for persistent use\n\n"
        "Start with configure_key if no key is saved, then use assess_organization."
    ),
)

# ---------------------------------------------------------------------------
# BYOK: key resolution (mirrors crml_cli.py logic)
# ---------------------------------------------------------------------------
CONFIG_PATH = Path.home() / ".crml" / "config.json"


def _resolve_key(provided: str = "") -> str:
    """Resolve OpenAI API key: tool arg → env var → ~/.crml/config.json."""
    if provided:
        return provided
    env_key = os.getenv("OPENAI_API_KEY", "")
    if env_key:
        return env_key
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
        if data.get("openai_api_key"):
            return data["openai_api_key"]
    return ""


def _init_client(provided_key: str = "") -> str | None:
    """Initialize crml_ai client. Returns an error string on failure, None on success."""
    key = _resolve_key(provided_key)
    if not key:
        return (
            "No OpenAI API key found. "
            "Use the configure_key tool to save one, or pass openai_api_key directly."
        )
    crml_ai.init_client(key)
    return None


# ---------------------------------------------------------------------------
# Tool: configure_key
# ---------------------------------------------------------------------------
@mcp.tool()
def configure_key(openai_api_key: str) -> str:
    """
    Save your OpenAI API key to ~/.crml/config.json for persistent use across
    all CRML tools. Run this once — subsequent tool calls will use the saved key
    automatically.

    Args:
        openai_api_key: Your OpenAI API key (starts with sk-).
    """
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    existing["openai_api_key"] = openai_api_key
    CONFIG_PATH.write_text(json.dumps(existing, indent=2))
    return "✓ API key saved to ~/.crml/config.json. You can now use the other CRML tools."


# ---------------------------------------------------------------------------
# Tool: discover_org
# ---------------------------------------------------------------------------
@mcp.tool()
def discover_org(company: str, openai_api_key: str = "") -> str:
    """
    Research an organization and return its cyber risk profile: revenue,
    employee count, industry, active compliance frameworks, and AI-suggested
    modeling parameters (lambda, severity weightage, reasoning).

    This is Step 1 of the CRML workflow. The returned profile is used as
    context for simulation and report generation.

    Args:
        company:        Company name or plain-language description.
                        Examples: "Stripe", "Bank of America", "a large Indian fintech".
        openai_api_key: Optional OpenAI API key. Uses saved config if omitted.
    """
    err = _init_client(openai_api_key)
    if err:
        return err

    ctx = crml_ai.discover_org_context(company)

    lines = [
        f"Organization Profile — {ctx.get('company', company)}",
        f"{'─' * 50}",
        f"Industry:    {ctx.get('industry', 'Unknown')}",
        f"Revenue:     ${ctx.get('revenue', 0):,.0f} USD",
        f"Employees:   {ctx.get('employees', 0):,}",
        f"Compliance:  {', '.join(ctx.get('compliances', [])) or 'None detected'}",
    ]

    if ctx.get("ticker"):
        lines.append(f"Ticker:      {ctx['ticker']}")
    if ctx.get("headquarters"):
        lines.append(f"HQ:          {ctx['headquarters']}")

    if "risk_guidance" in ctx:
        g = ctx["risk_guidance"]
        lines += [
            "",
            "AI Parameter Guidance:",
            f"  Suggested Lambda:      {g.get('suggested_lambda', 'N/A')}",
            f"  Severity Weightage:    {g.get('severity_weightage', 'N/A')}",
            f"  Key Parameters:        {', '.join(g.get('key_parameters', []))}",
            f"  Reasoning:             {g.get('reasoning', '')}",
        ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: simulate_risk
# ---------------------------------------------------------------------------
@mcp.tool()
def simulate_risk(
    company: str,
    industry: str,
    revenue: float,
    employees: int,
    scenarios: str,
    openai_api_key: str = "",
) -> str:
    """
    Generate CRML models and run 10,000-trial Monte Carlo simulations for a set
    of named risk scenarios. Returns EAL (Expected Annual Loss) and VaR 95%
    for each scenario, plus a portfolio-level confidence band across 3 model
    variants (conservative / baseline / heavy-tail).

    This is Step 3 of the CRML workflow. Use discover_org first to get the
    company profile, or supply the values manually.

    Args:
        company:        Legal company name.
        industry:       Industry sector (e.g. "Financial Services", "Healthcare").
        revenue:        Annual revenue in USD.
        employees:      Employee count.
        scenarios:      Comma-separated scenario names to model.
                        Example: "Ransomware, Phishing, Data Breach via SQL Injection"
        openai_api_key: Optional OpenAI API key. Uses saved config if omitted.
    """
    err = _init_client(openai_api_key)
    if err:
        return err

    try:
        from crml_engine.simulation.engine import run_monte_carlo
    except ImportError:
        return "crml-engine not found. Install with: pip install -e ./crml_engine"

    context = {
        "company": company,
        "industry": industry,
        "revenue": revenue,
        "employees": employees,
        "compliances": [],
    }

    kb = crml_ai.load_knowledge_base()
    scenario_list = [s.strip() for s in scenarios.split(",") if s.strip()]

    lines = [
        f"Monte Carlo Simulation — {company}",
        f"{'─' * 55}",
        f"{'Scenario':<35} {'EAL':>12} {'EAL Range':>22} {'VaR 95%':>12}",
        f"{'─' * 55}",
    ]

    total_eal = 0
    total_var = 0

    for name in scenario_list:
        model_dict = crml_ai.expert_ai_generator(name, kb, context=context)
        model_dict["meta"]["name"] = name
        allowed_keys = {"crml_scenario", "meta", "scenario"}
        clean_model = {k: v for k, v in model_dict.items() if k in allowed_keys}

        variants = [("conservative", 0.7), ("baseline", 1.0), ("heavy_tail", 1.5)]
        variant_results = []

        for v_name, sigma_mult in variants:
            v_model = copy.deepcopy(clean_model)
            try:
                sev = v_model["scenario"]["severity"]["parameters"]
                if "sigma" in sev:
                    sev["sigma"] *= sigma_mult
            except (KeyError, TypeError):
                pass
            sim = run_monte_carlo(v_model, n_runs=10000)
            if sim.success:
                variant_results.append({
                    "name": v_name,
                    "eal": sim.metrics.eal,
                    "var_95": sim.metrics.var_95,
                })

        if variant_results:
            baseline = next((v for v in variant_results if v["name"] == "baseline"), variant_results[0])
            eal = baseline["eal"]
            var95 = baseline["var_95"]
            eal_min = min(v["eal"] for v in variant_results)
            eal_max = max(v["eal"] for v in variant_results)
            eal_range = f"${eal_min:,.0f}–${eal_max:,.0f}"
            total_eal += eal
            total_var += var95
            lines.append(f"{name:<35} ${eal:>11,.0f} {eal_range:>22} ${var95:>11,.0f}")
        else:
            lines.append(f"{name:<35} {'Simulation failed':>48}")

    lines += [
        f"{'─' * 55}",
        f"{'PORTFOLIO TOTAL':<35} ${total_eal:>11,.0f} {'':>22} ${total_var:>11,.0f}",
        "",
        "Metrics:",
        f"  EAL  — Expected Annual Loss (average loss per year across 10,000 trials)",
        f"  VaR 95% — 95th percentile single-event loss (tail risk)",
        f"  EAL Range — min/max across conservative, baseline, and heavy-tail models",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: generate_report
# ---------------------------------------------------------------------------
@mcp.tool()
def generate_report(
    company: str,
    industry: str,
    revenue: float,
    employees: int,
    compliances: str,
    scenario_results: str,
    openai_api_key: str = "",
) -> str:
    """
    Generate an AI-written executive cyber risk underwriting report and save it
    to output/<org_slug>/CRML_RISK_REPORT.md and .html.

    This is Step 4 of the CRML workflow.

    Args:
        company:          Legal company name.
        industry:         Industry sector.
        revenue:          Annual revenue in USD.
        employees:        Employee count.
        compliances:      Comma-separated compliance frameworks (e.g. "SOC2, GDPR").
        scenario_results: JSON string of simulation results in the format:
                          '[{"name": "Ransomware", "metrics": {"eal": 500000, "var_95": 2000000}}]'
        openai_api_key:   Optional OpenAI API key. Uses saved config if omitted.
    """
    err = _init_client(openai_api_key)
    if err:
        return err

    context = {
        "company": company,
        "industry": industry,
        "revenue": revenue,
        "employees": employees,
        "compliances": [c.strip() for c in compliances.split(",")],
    }

    try:
        results = json.loads(scenario_results)
    except json.JSONDecodeError as e:
        return f"Invalid scenario_results JSON: {e}"

    report_json = crml_ai.generate_underwriter_report(context, results)
    try:
        report_data = json.loads(report_json)
    except Exception:
        return f"Report generation failed. Raw response:\n{report_json}"

    # Save to output dir
    org_slug = company.lower().replace(" ", "_").replace(".", "")
    output_dir = REPO_ROOT / "output" / org_slug
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / "CRML_RISK_REPORT.md"
    from datetime import datetime
    with open(md_path, "w") as f:
        f.write(f"# Cyber Risk Report — {company}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Executive Summary\n{report_data.get('executive_summary', 'N/A')}\n\n")
        f.write(f"## Company Profile\n{report_data.get('company_profile', 'N/A')}\n\n")
        f.write(f"## Financial Impact\n{report_data.get('financial_impact', 'N/A')}\n\n")
        f.write("## Recommendations\n")
        for rec in report_data.get("recommendations", []):
            f.write(f"- {rec}\n")

    lines = [
        f"Underwriting Report — {company}",
        f"{'─' * 50}",
        "",
        "Executive Summary:",
        report_data.get("executive_summary", "N/A"),
        "",
        "Financial Impact:",
        report_data.get("financial_impact", "N/A"),
        "",
        "Recommendations:",
    ]
    for rec in report_data.get("recommendations", []):
        lines.append(f"  • {rec}")

    lines += ["", f"Report saved to: {md_path}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool: assess_organization (full pipeline — recommended entry point)
# ---------------------------------------------------------------------------
@mcp.tool()
def assess_organization(
    company: str,
    findings: str = "",
    openai_api_key: str = "",
) -> str:
    """
    Run a complete end-to-end cyber risk assessment in one call:
      1. Research the organization via live web search
      2. Discover 3–5 risk scenarios from findings (or org context alone)
      3. Run 10,000-trial Monte Carlo simulation per scenario (3 model variants)
      4. Generate an executive underwriting report

    All output files are saved to output/<org_slug>/.

    Args:
        company:        Company name or plain-language description.
                        Examples: "Stripe", "a large Indian fintech", "Paytm".
        findings:       Optional comma-separated vulnerability findings.
                        Example: "SQL Injection (Critical), Unpatched SSL (High), MFA not enforced (Medium)"
                        Leave empty for AI-driven scenario discovery from org context alone.
        openai_api_key: Optional OpenAI API key. Uses saved config if omitted.
    """
    err = _init_client(openai_api_key)
    if err:
        return err

    try:
        from crml_engine.simulation.engine import run_monte_carlo
    except ImportError:
        return "crml-engine not found. Install with: pip install -e ./crml_engine"

    # ── Step 1: Org context ──────────────────────────────────────────────────
    ctx = crml_ai.discover_org_context(company)
    org_slug = ctx.get("company", company).lower().replace(" ", "_").replace(".", "")
    output_dir = REPO_ROOT / "output" / org_slug
    output_dir.mkdir(parents=True, exist_ok=True)
    ctx["output_dir"] = str(output_dir)

    # ── Step 2: Parse findings & discover scenarios ──────────────────────────
    raw_findings = []
    if findings:
        for f in findings.split(","):
            f = f.strip()
            if f:
                raw_findings.append({"vulnerability": f, "severity": "Unknown"})

    scenarios = crml_ai.discover_risk_scenarios(raw_findings, ctx)
    if not scenarios:
        return (
            "No risk scenarios could be discovered. "
            "Check your API key and try providing specific findings."
        )

    # ── Step 3: Simulate ────────────────────────────────────────────────────
    kb = crml_ai.load_knowledge_base()
    results = []

    for s in scenarios:
        model_dict = crml_ai.expert_ai_generator(s["prompt"], kb, context=ctx)
        model_dict["meta"]["name"] = s["name"]
        allowed_keys = {"crml_scenario", "meta", "scenario"}
        clean_model = {k: v for k, v in model_dict.items() if k in allowed_keys}

        variants = [("conservative", 0.7), ("baseline", 1.0), ("heavy_tail", 1.5)]
        variant_results = []

        for v_name, sigma_mult in variants:
            v_model = copy.deepcopy(clean_model)
            try:
                sev = v_model["scenario"]["severity"]["parameters"]
                if "sigma" in sev:
                    sev["sigma"] *= sigma_mult
            except (KeyError, TypeError):
                pass
            sim = run_monte_carlo(v_model, n_runs=10000)
            if sim.success:
                variant_results.append({
                    "name": v_name,
                    "eal": sim.metrics.eal,
                    "var_95": sim.metrics.var_95,
                })

        if variant_results:
            baseline = next(
                (v for v in variant_results if v["name"] == "baseline"),
                variant_results[0]
            )
            results.append({
                "name": s["name"],
                "metrics": {
                    "eal": baseline["eal"],
                    "var_95": baseline["var_95"],
                    "var_99": baseline.get("var_99", 0),
                },
                "confidence": {
                    "eal_min": min(v["eal"] for v in variant_results),
                    "eal_max": max(v["eal"] for v in variant_results),
                },
                "model": clean_model,
            })

    if not results:
        return "Simulation failed for all scenarios."

    # ── Step 4: Report ──────────────────────────────────────────────────────
    report_json = crml_ai.generate_underwriter_report(ctx, results)
    try:
        report_data = json.loads(report_json)
    except Exception:
        report_data = {}

    # Save Markdown report
    from datetime import datetime
    md_path = output_dir / "CRML_RISK_REPORT.md"
    with open(md_path, "w") as f:
        f.write(f"# Cyber Risk Report — {ctx.get('company', company)}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Executive Summary\n{report_data.get('executive_summary', 'N/A')}\n\n")
        f.write(f"## Company Profile\n{report_data.get('company_profile', 'N/A')}\n\n")
        f.write(f"## Financial Impact\n{report_data.get('financial_impact', 'N/A')}\n\n")
        f.write("## Recommendations\n")
        for rec in report_data.get("recommendations", []):
            f.write(f"- {rec}\n")

    # ── Build response ──────────────────────────────────────────────────────
    total_eal = sum(r["metrics"]["eal"] for r in results)
    total_var = sum(r["metrics"]["var_95"] for r in results)

    lines = [
        f"Cyber Risk Assessment — {ctx.get('company', company)}",
        f"{'─' * 55}",
        f"Industry:  {ctx.get('industry', 'N/A')}",
        f"Revenue:   ${ctx.get('revenue', 0):,.0f} USD",
        f"Employees: {ctx.get('employees', 0):,}",
        "",
        f"Portfolio EAL (Expected Annual Loss): ${total_eal:,.0f}",
        f"Portfolio VaR 95%:                    ${total_var:,.0f}",
        "",
        "Scenarios:",
    ]

    for r in results:
        conf = r.get("confidence", {})
        eal_range = (
            f"  [${conf['eal_min']:,.0f} – ${conf['eal_max']:,.0f}]"
            if conf else ""
        )
        lines.append(
            f"  • {r['name']}\n"
            f"    EAL: ${r['metrics']['eal']:,.0f}{eal_range}\n"
            f"    VaR 95%: ${r['metrics']['var_95']:,.0f}"
        )

    if report_data.get("executive_summary"):
        lines += ["", "Executive Summary:", report_data["executive_summary"]]

    if report_data.get("recommendations"):
        lines += ["", "Recommendations:"]
        for rec in report_data["recommendations"]:
            lines.append(f"  • {rec}")

    lines += [
        "",
        f"Files saved to: {output_dir}/",
        f"  • CRML_RISK_REPORT.md",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
