#!/usr/bin/env python3
"""
Claude Code for Cyber Risk (CLI)
--------------------------------
A premium terminal interface for interactive cyber risk modeling.
"""

import os
import sys
import json
import yaml
import csv
import argparse
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from rich.status import Status
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import CRML AI Logic
sys.path.append(os.path.dirname(__file__))
import crml_ai

console = Console()

# --- BYOK: Config helpers ---
CONFIG_PATH = os.path.expanduser("~/.crml/config.json")

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}

def save_config(config: dict):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

def resolve_api_key(cli_arg) -> str:
    """Resolve OpenAI API key: CLI arg → env var → ~/.crml/config.json → prompt."""
    if cli_arg:
        return cli_arg
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_API_KEY")
    cfg = load_config()
    if cfg.get("openai_api_key"):
        return cfg["openai_api_key"]
    # Interactive prompt
    console.print("\n[bold yellow]No OpenAI API key found.[/bold yellow]")
    key = Prompt.ask("Enter your OpenAI API key", password=True)
    if key and Confirm.ask("Save key to ~/.crml/config.json for future runs?", default=True):
        cfg["openai_api_key"] = key
        save_config(cfg)
        console.print("[green]✓ Key saved to ~/.crml/config.json[/green]")
    return key

# Load MITRE ATT&CK Mappings
def load_mitre_mapping():
    mitre_path = os.path.join(os.path.dirname(__file__), "mitre_mapping.json")
    if os.path.exists(mitre_path):
        with open(mitre_path, 'r') as f:
            return json.load(f).get("mappings", [])
    return []

def tag_mitre(scenario_name, prompt_text=""):
    """Tag a scenario with MITRE ATT&CK techniques based on keywords."""
    mappings = load_mitre_mapping()
    text = (scenario_name + " " + prompt_text).lower()
    tags = []
    seen = set()
    for m in mappings:
        for kw in m["keywords"]:
            if kw in text and m["technique_id"] not in seen:
                tags.append({"id": m["technique_id"], "name": m["technique_name"], "tactic": m["tactic"]})
                seen.add(m["technique_id"])
                break
    return tags

def print_banner():
    banner = """
    [bold cyan] ▄████▄   ██▀███   ███▄ ▄███▓ ██▓ [/bold cyan]
    [bold cyan]▒██▀ ▀█  ▓██ ▒ ██▒▓██▒▀█▀ ██▒▓██▒ [/bold cyan]
    [bold cyan]▒▓█    ▄ ▓██ ░▄█ ▒▓██    ▓██░▒██░ [/bold cyan]
    [bold cyan]▒▓▓▄ ▄██▒▒██▀▀█▄  ▒██    ▒██ ▒██░ [/bold cyan]
    [bold cyan]▒ ▓███▀ ░░██▓ ▒██▒▒██▒   ░██▒░██████▒[/bold cyan]
    [bold cyan]░ ░▒ ▒  ░░ ▒▓ ░▒▓░░ ▒░   ░  ░░ ▒░▓  ░[/bold cyan]
    [bold cyan]  ░  ▒     ░▒ ░ ▒░░  ░      ░░ ░ ▒  ░[/bold cyan]
    [bold cyan]░          ░░   ░ ░      ░     ░ ░   [/bold cyan]
    [bold cyan]░ ░         ░            ░       ░  ░[/bold cyan]
    [bold cyan]░                                    [/bold cyan]
    [bold cyan]       C O D E   F O R   C Y B E R   R I S K[/bold cyan]
    """
    console.print(Panel(banner, border_style="cyan"))

def get_org_context():
    console.print("\n[bold yellow]Step 1: Organizational Context[/bold yellow]")
    initial_input = Prompt.ask("Who are you modeling for? (e.g. 'Paytm', 'A large retail bank')")
    
    with console.status(f"[bold green]Researching '{initial_input}' (with web search)...") as status:
        context = crml_ai.discover_org_context(initial_input)

    # Show data source and entity resolution
    source = context.get("_source", "unknown")
    if source == "web_search":
        console.print("[bold green]✓ Data sourced from live web search[/bold green]")
        if "data_sources" in context:
            console.print(f"[dim]Sources: {context['data_sources']}[/dim]")
    else:
        console.print("[yellow]⚠ Data from AI training data (may be outdated). Please verify.[/yellow]")
    
    # Show entity resolution if brand ≠ legal name
    brand = context.get("brand_name", "")
    legal = context.get("company", initial_input)
    if brand and brand.lower() != legal.lower():
        console.print(f"[bold cyan]🔍 Entity Resolved:[/bold cyan] {brand} → [bold]{legal}[/bold]")
    
    # Show extra metadata
    extras = []
    if context.get("ticker"):
        extras.append(f"Ticker: {context['ticker']}")
    if context.get("headquarters"):
        extras.append(f"HQ: {context['headquarters']}")
    if context.get("revenue_year"):
        extras.append(f"Revenue Year: {context['revenue_year']}")
    if extras:
        console.print(f"[dim]{' | '.join(extras)}[/dim]")
    if context.get("revenue_note"):
        console.print(f"[dim italic]ℹ {context['revenue_note']}[/dim italic]")

    # 1.1 Show AI Guidance & Reasoning
    if "risk_guidance" in context:
        g = context["risk_guidance"]
        guidance_panel = Panel(
            f"[bold blue]AI Parameter Guidance for {context['company']}[/bold blue]\n\n"
            f"• [bold]Suggested Lambda:[/bold] {g.get('suggested_lambda')}\n"
            f"• [bold]Severity Weightage:[/bold] {g.get('severity_weightage')}\n"
            f"• [bold]Key Parameters:[/bold] {', '.join(g.get('key_parameters', []))}\n\n"
            f"[italic white]Reasoning:[/italic white]\n{g.get('reasoning')}",
            title="AI Reasoning Logic",
            border_style="blue"
        )
        console.print(guidance_panel)

    # Allow user to refine
    console.print(f"\n[bold blue]Discovered Details for {context['company']}:[/bold blue]")
    company = Prompt.ask("Company Name", default=context.get('company', initial_input))
    
    # Robust revenue parsing — handle None, strings, millions shorthand
    raw_rev = context.get('revenue', 0)
    try:
        parsed_rev = float(raw_rev) if raw_rev else 0.0
    except (ValueError, TypeError):
        # Handle string like "$670K" or "1.2M"
        rev_str = str(raw_rev).replace("$", "").replace(",", "").strip()
        if rev_str.upper().endswith("M"):
            parsed_rev = float(rev_str[:-1]) * 1_000_000
        elif rev_str.upper().endswith("B"):
            parsed_rev = float(rev_str[:-1]) * 1_000_000_000
        elif rev_str.upper().endswith("K"):
            parsed_rev = float(rev_str[:-1]) * 1_000
        else:
            parsed_rev = 0.0
    
    # Show original currency for transparency
    orig_rev = context.get("revenue_original", "")
    orig_curr = context.get("revenue_original_currency", "USD")
    if orig_rev:
        console.print(f"  [dim]Source Revenue: {orig_rev} ({orig_curr})[/dim]")
    
    # INR sanity check — if original is INR but revenue looks unconverted
    if orig_curr == "INR" and parsed_rev > 100_000_000:
        corrected = parsed_rev / 83.0
        console.print(f"[yellow]⚠ Revenue ${parsed_rev:,.0f} appears to be INR passed as USD. Auto-correcting to ${corrected:,.0f} (÷83)[/yellow]")
        parsed_rev = corrected
    
    # If revenue looks like it's in millions (< 1000), auto-scale
    if 0 < parsed_rev < 1000:
        console.print(f"[yellow]⚠ Revenue ${parsed_rev:,.2f} looks like it's in millions. Auto-scaling to ${parsed_rev * 1_000_000:,.0f}[/yellow]")
        parsed_rev = parsed_rev * 1_000_000
    
    if parsed_rev > 0:
        console.print(f"  [dim]Discovered Revenue: ${parsed_rev:,.0f}[/dim]")
    revenue = FloatPrompt.ask("Annual Revenue (USD)", default=parsed_rev)
    
    raw_emp = context.get('employees', 0)
    try:
        parsed_emp = int(raw_emp) if raw_emp else 0
    except (ValueError, TypeError):
        parsed_emp = 0
    employees = IntPrompt.ask("Employee Count", default=parsed_emp)
    
    industry = Prompt.ask("Primary Industry", default=context.get('industry', "Technology") or "Technology")
    raw_compliances = context.get('compliances', [])
    if isinstance(raw_compliances, list) and raw_compliances:
        compliance_str = ", ".join(raw_compliances)
    else:
        compliance_str = "GDPR, SOC2"
    compliances = Prompt.ask("Compliances", default=compliance_str)
    
    # Create Organization Folder
    org_slug = company.lower().replace(" ", "_").replace(".", "")
    output_dir = os.path.join("output", org_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    return {
        "company": company,
        "revenue": revenue,
        "employees": employees,
        "industry": industry,
        "compliances": [c.strip() for c in compliances.split(",")],
        "output_dir": output_dir
    }

def parse_scan_file(filepath):
    """Parse a Zeron/generic scan report (JSON or CSV) into normalized findings."""
    findings = []
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.json':
            with open(filepath, 'r') as f:
                data = json.load(f)
            # Support various JSON structures
            if isinstance(data, list):
                raw = data
            elif "findings" in data:
                raw = data["findings"]
            elif "vulnerabilities" in data:
                raw = data["vulnerabilities"]
            elif "results" in data:
                raw = data["results"]
            else:
                raw = [data]
            
            for item in raw:
                findings.append({
                    "vulnerability": item.get("vulnerability", item.get("title", item.get("name", str(item)))),
                    "severity": item.get("severity", item.get("risk", "Unknown")),
                    "asset": item.get("asset", item.get("host", item.get("target", "Unknown"))),
                    "description": item.get("description", item.get("detail", ""))
                })
                
        elif ext == '.csv':
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Flexible column name matching
                    vuln = row.get("vulnerability") or row.get("Vulnerability") or row.get("title") or row.get("Title") or row.get("name") or "Unknown"
                    sev = row.get("severity") or row.get("Severity") or row.get("risk") or row.get("Risk") or "Unknown"
                    asset = row.get("asset") or row.get("Asset") or row.get("host") or row.get("Host") or "Unknown"
                    desc = row.get("description") or row.get("Description") or ""
                    findings.append({
                        "vulnerability": vuln,
                        "severity": sev,
                        "asset": asset,
                        "description": desc
                    })
        else:
            console.print(f"[red]Unsupported file format: {ext}. Use .json or .csv[/red]")
            return []
            
    except Exception as e:
        console.print(f"[red]Error parsing scan file: {e}[/red]")
        return []
    
    return findings

def run_discovery(context, scan_findings=None):
    console.print("\n[bold yellow]Step 2: Risk Discovery[/bold yellow]")
    
    findings = []
    
    if scan_findings:
        # Show scan summary
        console.print(f"[bold green]✓ Loaded {len(scan_findings)} findings from scan file[/bold green]")
        sev_counts = {}
        for f in scan_findings:
            sev = f.get("severity", "Unknown")
            sev_counts[sev] = sev_counts.get(sev, 0) + 1
        
        scan_table = Table(title="Scan Summary")
        scan_table.add_column("Severity", style="cyan")
        scan_table.add_column("Count", justify="right", style="white")
        for sev, count in sorted(sev_counts.items()):
            color = "red" if sev.lower() in ["critical", "high"] else "yellow" if sev.lower() == "medium" else "green"
            scan_table.add_row(f"[{color}]{sev}[/{color}]", str(count))
        console.print(scan_table)
        
        findings = scan_findings
    else:
        findings_raw = Prompt.ask("Describe any security findings or vulnerability types (or press Enter for AI discovery)")
        if findings_raw:
            findings = [{"vulnerability": line.strip(), "severity": "Unknown"} for line in findings_raw.split(",")]
    
    with console.status("[bold green]Discovering risk scenarios with AI...") as status:
        scenarios = crml_ai.discover_risk_scenarios(findings, context)
        
    if not scenarios:
        console.print("[red]No scenarios discovered. Please try a different description.[/red]")
        return []

    table = Table(title="Discovered Scenarios")
    table.add_column("ID", style="cyan")
    table.add_column("Scenario Name", style="white")
    
    for i, s in enumerate(scenarios):
        table.add_row(str(i+1), s["name"])
    
    console.print(table)
    return scenarios

def simulate_scenarios(scenarios, context):
    console.print("\n[bold yellow]Step 3: Quantitative Modeling & Simulation[/bold yellow]")
    
    kb = crml_ai.load_knowledge_base()
    results = []
    
    for s in scenarios:
        with console.status(f"[bold green]Generating model for {s['name']}...") as status:
            # Generate Model
            model_dict = crml_ai.expert_ai_generator(s["prompt"], kb, context=context)
            model_dict['meta']['name'] = s["name"]
            
            # Show Reasoning + MITRE Tags for this scenario
            rationale = model_dict.get("metadata_rationale", "No rationale provided.")
            mitre_tags = tag_mitre(s['name'], s.get('prompt', ''))
            mitre_str = ", ".join([f"[bold red]{t['id']}[/bold red] ({t['name']})" for t in mitre_tags]) if mitre_tags else "[dim]None matched[/dim]"
            
            console.print(f"\n[bold cyan]➡ Scenario: {s['name']}[/bold cyan]")
            console.print(f"[bold]MITRE ATT&CK:[/bold] {mitre_str}")
            console.print(f"[italic white]AI Logic:[/italic white] {rationale}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task_id = progress.add_task(f"Simulating 10,000 runs (3 models)...", total=100)
            
            # Strict Filter for CRML Schema
            allowed_keys = {"crml_scenario", "meta", "scenario"}
            clean_model = {k: v for k, v in model_dict.items() if k in allowed_keys}
            
            from crml_engine.simulation.engine import run_monte_carlo
            import copy
            
            # Run 3 distribution variants for confidence band
            variants = [
                ("conservative", 0.7),   # Tighter distribution (lower sigma)
                ("baseline", 1.0),       # Original model
                ("heavy_tail", 1.5),     # Fatter tails (higher sigma)
            ]
            
            variant_results = []
            for v_name, sigma_mult in variants:
                v_model = copy.deepcopy(clean_model)
                try:
                    sev = v_model.get("scenario", {}).get("severity", {}).get("parameters", {})
                    if "sigma" in sev:
                        sev["sigma"] = sev["sigma"] * sigma_mult
                except:
                    pass
                
                v_sim = run_monte_carlo(v_model, n_runs=10000)
                if v_sim.success:
                    variant_results.append({
                        "model": v_name,
                        "eal": v_sim.metrics.eal,
                        "var_95": v_sim.metrics.var_95,
                        "var_99": v_sim.metrics.var_99
                    })
            
            progress.update(task_id, completed=100)
            
            if variant_results:
                # Use baseline as primary metrics
                baseline = next((v for v in variant_results if v["model"] == "baseline"), variant_results[0])
                metrics = {
                    "eal": baseline["eal"],
                    "var_95": baseline["var_95"],
                    "var_99": baseline["var_99"]
                }
                confidence = {
                    "eal_min": min(v["eal"] for v in variant_results),
                    "eal_max": max(v["eal"] for v in variant_results),
                    "var95_min": min(v["var_95"] for v in variant_results),
                    "var95_max": max(v["var_95"] for v in variant_results),
                }
                results.append({
                    "name": s["name"],
                    "metrics": metrics,
                    "model": clean_model,
                    "mitre": mitre_tags,
                    "confidence": confidence
                })
                # Save Individual Scenario YAML
                scenario_file = os.path.join(context['output_dir'], f"{s['name'].lower().replace(' ', '_')}.yaml")
                with open(scenario_file, "w") as f:
                    yaml.dump(clean_model, f, sort_keys=False)
            else:
                console.print(f"[red]Simulation failed for {s['name']}[/red]")

    # Display Results
    res_table = Table(title="Quantitative Risk Assessment")
    res_table.add_column("Scenario", style="cyan")
    res_table.add_column("MITRE", style="red")
    res_table.add_column("EAL (Avg Loss/Year)", justify="right", style="green")
    res_table.add_column("EAL Range (3-Model)", justify="right", style="dim green")
    res_table.add_column("VaR 95% (Tail Risk)", justify="right", style="magenta")
    
    for r in results:
        mitre_ids = ", ".join([t['id'] for t in r.get('mitre', [])])
        conf = r.get("confidence", {})
        eal_range = f"${conf.get('eal_min', 0):,.0f} – ${conf.get('eal_max', 0):,.0f}" if conf else "-"
        res_table.add_row(
            r["name"],
            mitre_ids or "-",
            f"${r['metrics']['eal']:,.0f}",
            eal_range,
            f"${r['metrics']['var_95']:,.0f}"
        )
    
    console.print(res_table)
    
    # Save Portfolio YAML
    portfolio = {"crml_portfolio": "1.0", "meta": {"org": context['company']}, "scenarios": [r['model'] for r in results]}
    portfolio_file = os.path.join(context['output_dir'], "portfolio.yaml")
    with open(portfolio_file, "w") as f:
        yaml.dump(portfolio, f, sort_keys=False)
    
    # Comparative Benchmarking
    if results:
        with console.status("[bold blue]Benchmarking against industry peers...") as status:
            benchmark = crml_ai.generate_benchmark_comparison(context, results)
        
        if "error" not in benchmark:
            tier_color = {"Low": "green", "Medium": "yellow", "High": "red", "Critical": "bold red"}.get(benchmark.get("risk_tier", ""), "white")
            bench_panel = Panel(
                f"[bold]Industry Avg EAL:[/bold] ${benchmark.get('industry_avg_eal', 0):,.0f}\n"
                f"[bold]Your EAL Ratio:[/bold] [{tier_color}]{benchmark.get('eal_ratio', 'N/A')}[/{tier_color}]\n"
                f"[bold]Risk Tier:[/bold] [{tier_color}]{benchmark.get('risk_tier', 'N/A')}[/{tier_color}]\n\n"
                f"[italic]{benchmark.get('peer_comparison', '')}[/italic]\n\n"
                f"[bold yellow]Top Outlier:[/bold yellow] {benchmark.get('top_outlier_scenario', 'N/A')}",
                title="📊 Peer Benchmark Comparison",
                border_style="blue"
            )
            console.print(bench_panel)
            
            # Save benchmark to org folder
            bench_file = os.path.join(context['output_dir'], "benchmark.json")
            with open(bench_file, "w") as f:
                json.dump(benchmark, f, indent=2)
    
    # Control ROI Analysis
    if results:
        kb = crml_ai.load_knowledge_base()
        controls = kb.get("controls", [])
        if controls:
            console.print("\n[bold yellow]Step 3b: Control ROI Analysis[/bold yellow]")
            
            # Keyword mapping: scenario keywords → relevant control IDs
            scenario_control_map = {
                "phishing": ["mfa", "awareness_training"],
                "email": ["mfa", "awareness_training"],
                "credential": ["mfa", "zta"],
                "ransomware": ["edr", "immutable_backups", "patch_management"],
                "encryption": ["edr", "immutable_backups"],
                "insider": ["dlp", "zta"],
                "data breach": ["dlp", "zta", "edr"],
                "sql injection": ["patch_management", "zta"],
                "cloud": ["zta", "dlp"],
                "supply chain": ["zta", "patch_management"],
                "denial of service": ["zta"],
                "privilege": ["mfa", "zta"],
                "access control": ["mfa", "zta"],
            }
            
            roi_table = Table(title="🛡️ Control ROI Recommendations")
            roi_table.add_column("Control", style="cyan")
            roi_table.add_column("Affects", style="white")
            roi_table.add_column("Annual Cost", justify="right", style="yellow")
            roi_table.add_column("EAL Reduction", justify="right", style="green")
            roi_table.add_column("Net Savings", justify="right", style="bold green")
            roi_table.add_column("ROI", justify="right", style="magenta")
            
            seen_controls = set()
            roi_data = []
            
            for r in results:
                scenario_lower = r["name"].lower()
                matched_ids = set()
                for kw, ctrl_ids in scenario_control_map.items():
                    if kw in scenario_lower:
                        matched_ids.update(ctrl_ids)
                
                for ctrl in controls:
                    if ctrl["id"] in matched_ids and ctrl["id"] not in seen_controls:
                        seen_controls.add(ctrl["id"])
                        eff = ctrl["effectiveness"]
                        cost = ctrl["annual_cost"]
                        
                        # Calculate EAL reduction across all matching scenarios
                        total_reduction = 0
                        for r2 in results:
                            r2_lower = r2["name"].lower()
                            for kw, ids in scenario_control_map.items():
                                if kw in r2_lower and ctrl["id"] in ids:
                                    if ctrl["affects"] == "frequency":
                                        total_reduction += r2["metrics"]["eal"] * eff
                                    elif ctrl["affects"] == "severity":
                                        total_reduction += r2["metrics"]["eal"] * eff * 0.6
                                    else:  # both
                                        total_reduction += r2["metrics"]["eal"] * eff * 0.8
                                    break
                        
                        net = total_reduction - cost
                        roi_pct = (net / cost * 100) if cost > 0 else 0
                        color = "green" if net > 0 else "red"
                        
                        roi_table.add_row(
                            ctrl["name"],
                            ctrl["affects"].title(),
                            f"${cost:,.0f}",
                            f"${total_reduction:,.0f}",
                            f"[{color}]${net:,.0f}[/{color}]",
                            f"[{color}]{roi_pct:,.0f}%[/{color}]"
                        )
                        roi_data.append({"control": ctrl["name"], "cost": cost, "reduction": total_reduction, "net": net, "roi_pct": roi_pct})
            
            if roi_data:
                console.print(roi_table)
                # Save ROI data
                roi_file = os.path.join(context['output_dir'], "control_roi.json")
                with open(roi_file, "w") as f:
                    json.dump(roi_data, f, indent=2)
    
    return results

def generate_report(results, context):
    console.print("\n[bold yellow]Step 4: Finalizing Underwriter Report[/bold yellow]")
    
    # --- Historical Tracking ---
    history_file = os.path.join(context['output_dir'], "session_history.json")
    history = []
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            history = json.load(f)
    
    # Current session snapshot
    current_session = {
        "timestamp": datetime.now().isoformat(),
        "total_eal": sum(r['metrics']['eal'] for r in results),
        "total_var95": sum(r['metrics']['var_95'] for r in results),
        "scenario_count": len(results),
        "scenarios": {r['name']: r['metrics'] for r in results}
    }
    
    # Show delta if previous session exists
    if history:
        prev = history[-1]
        eal_delta = current_session["total_eal"] - prev["total_eal"]
        var_delta = current_session["total_var95"] - prev["total_var95"]
        eal_pct = (eal_delta / prev["total_eal"] * 100) if prev["total_eal"] > 0 else 0
        
        arrow_eal = "↑" if eal_delta > 0 else "↓"
        color_eal = "red" if eal_delta > 0 else "green"
        arrow_var = "↑" if var_delta > 0 else "↓"
        color_var = "red" if var_delta > 0 else "green"
        
        delta_panel = Panel(
            f"[bold]Previous Run:[/bold] {prev['timestamp'][:10]}\n"
            f"[bold]EAL Change:[/bold] [{color_eal}]{arrow_eal} ${abs(eal_delta):,.0f} ({eal_pct:+.1f}%)[/{color_eal}]\n"
            f"[bold]VaR 95% Change:[/bold] [{color_var}]{arrow_var} ${abs(var_delta):,.0f}[/{color_var}]\n"
            f"[bold]Sessions Tracked:[/bold] {len(history) + 1}",
            title="📈 Risk Trend (vs Previous Run)",
            border_style="yellow"
        )
        console.print(delta_panel)
    
    # Append current session
    history.append(current_session)
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    # --- Report Generation ---
    report_results = []
    for r in results:
        report_results.append({
            "name": r["name"],
            "metrics": r["metrics"]
        })

    with console.status("[bold blue]Drafting Executive Report...") as status:
        report_json = crml_ai.generate_underwriter_report(context, report_results)
        try:
            report_data = json.loads(report_json)
        except:
            report_data = {"executive_summary": "Error generating report. Check API keys."}

    report_file = os.path.join(context['output_dir'], "CRML_RISK_REPORT.md")
    with open(report_file, "w") as f:
        f.write(f"# Cyber Risk Report for {context['company']}\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write(f"## Executive Summary\n{report_data.get('executive_summary', 'N/A')}\n\n")
        f.write(f"## Company Profile\n{report_data.get('company_profile', 'N/A')}\n\n")
        f.write(f"## Financial Impact Analysis\n{report_data.get('financial_impact', 'N/A')}\n\n")
        f.write("## Recommendations\n")
        for rec in report_data.get("recommendations", []):
            f.write(f"- {rec}\n")
    
    # --- HTML Report Export (Feature 8) ---
    generate_html_report(context, results, report_data)
            
    console.print(Panel(f"Analysis Complete!\nAll files saved to: [bold green]{context['output_dir']}[/bold green]", border_style="green"))

def generate_html_report(context, results, report_data):
    """Generate a branded HTML report alongside the Markdown."""
    total_eal = sum(r['metrics']['eal'] for r in results)
    total_var = sum(r['metrics']['var_95'] for r in results)
    
    scenario_rows = ""
    for r in results:
        mitre = ", ".join([t['id'] for t in r.get('mitre', [])])
        conf = r.get("confidence", {})
        eal_range = f"${conf.get('eal_min', 0):,.0f} – ${conf.get('eal_max', 0):,.0f}" if conf else "-"
        scenario_rows += f"""
        <tr>
            <td>{r['name']}</td>
            <td><span class="mitre">{mitre or '-'}</span></td>
            <td class="money">${r['metrics']['eal']:,.0f}</td>
            <td class="range">{eal_range}</td>
            <td class="money">${r['metrics']['var_95']:,.0f}</td>
        </tr>"""
    
    recs_html = "".join([f"<li>{r}</li>" for r in report_data.get("recommendations", [])])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CRML Risk Report — {context['company']}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0a0e1a; color: #e0e0e0; padding: 40px; }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  .header {{ background: linear-gradient(135deg, #1a1f36 0%, #0d1117 100%); border: 1px solid #30363d; border-radius: 16px; padding: 40px; margin-bottom: 30px; }}
  .header h1 {{ color: #58a6ff; font-size: 28px; margin-bottom: 8px; }}
  .header .subtitle {{ color: #8b949e; font-size: 14px; }}
  .metrics {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }}
  .metric-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 24px; text-align: center; }}
  .metric-card .value {{ font-size: 32px; font-weight: 700; color: #f0883e; }}
  .metric-card .label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; margin-top: 8px; }}
  .section {{ background: #161b22; border: 1px solid #30363d; border-radius: 12px; padding: 30px; margin-bottom: 20px; }}
  .section h2 {{ color: #58a6ff; font-size: 18px; margin-bottom: 16px; border-bottom: 1px solid #30363d; padding-bottom: 10px; }}
  .section p, .section li {{ color: #c9d1d9; line-height: 1.7; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{ background: #0d1117; color: #58a6ff; text-align: left; padding: 12px; font-size: 12px; text-transform: uppercase; letter-spacing: 1px; }}
  td {{ padding: 12px; border-bottom: 1px solid #21262d; font-size: 14px; }}
  .money {{ color: #3fb950; font-weight: 600; font-variant-numeric: tabular-nums; }}
  .range {{ color: #8b949e; font-size: 12px; }}
  .mitre {{ background: #da3633; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  ul {{ padding-left: 20px; }}
  li {{ margin-bottom: 8px; }}
  .footer {{ text-align: center; color: #484f58; font-size: 12px; margin-top: 40px; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>🛡️ Cyber Risk Assessment Report</h1>
    <div class="subtitle">{context['company']} &mdash; {context.get('industry', 'N/A')} &mdash; Generated {datetime.now().strftime('%B %d, %Y')}</div>
  </div>
  
  <div class="metrics">
    <div class="metric-card"><div class="value">${total_eal:,.0f}</div><div class="label">Total Expected Annual Loss</div></div>
    <div class="metric-card"><div class="value">${total_var:,.0f}</div><div class="label">Portfolio VaR 95%</div></div>
    <div class="metric-card"><div class="value">{len(results)}</div><div class="label">Risk Scenarios</div></div>
  </div>
  
  <div class="section">
    <h2>Executive Summary</h2>
    <p>{report_data.get('executive_summary', 'N/A')}</p>
  </div>
  
  <div class="section">
    <h2>Scenario Analysis</h2>
    <table>
      <thead><tr><th>Scenario</th><th>MITRE</th><th>EAL</th><th>Confidence Range</th><th>VaR 95%</th></tr></thead>
      <tbody>{scenario_rows}</tbody>
    </table>
  </div>
  
  <div class="section">
    <h2>Financial Impact</h2>
    <p>{report_data.get('financial_impact', 'N/A')}</p>
  </div>
  
  <div class="section">
    <h2>Recommendations</h2>
    <ul>{recs_html}</ul>
  </div>
  
  <div class="footer">Generated by CRML Code — Cyber Risk Modeling Language</div>
</div>
</body>
</html>"""
    
    html_file = os.path.join(context['output_dir'], "CRML_RISK_REPORT.html")
    with open(html_file, "w") as f:
        f.write(html)
    console.print(f"[bold green]✓ HTML Report saved:[/bold green] {html_file}")


def what_if_mode(results, context):
    """Interactive What-If mode: tweak parameters and re-simulate instantly."""
    console.print("\n[bold yellow]🔬 What-If Mode[/bold yellow]")
    console.print("[dim]Tweak scenario parameters and see how risk changes instantly.[/dim]\n")
    
    from crml_engine.simulation.engine import run_monte_carlo
    import copy
    
    while True:
        # List scenarios
        for i, r in enumerate(results):
            console.print(f"  [{i+1}] {r['name']} (EAL: ${r['metrics']['eal']:,.0f})")
        
        choice = Prompt.ask("\nSelect scenario to tweak (number, or 'q' to quit)")
        if choice.lower() == 'q':
            break
        
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(results):
                console.print("[red]Invalid selection.[/red]")
                continue
        except ValueError:
            console.print("[red]Enter a number or 'q'.[/red]")
            continue
        
        r = results[idx]
        model = copy.deepcopy(r["model"])
        
        # Show current params
        freq = model.get("scenario", {}).get("frequency", {}).get("parameters", {})
        sev = model.get("scenario", {}).get("severity", {}).get("parameters", {})
        
        console.print(f"\n[bold]Current Parameters for {r['name']}:[/bold]")
        console.print(f"  Lambda (frequency): {freq.get('lambda', 'N/A')}")
        console.print(f"  Median (severity):  ${sev.get('median', 0):,.0f}")
        console.print(f"  Sigma (tail risk):  {sev.get('sigma', 'N/A')}")
        
        # Let user tweak
        new_lambda = FloatPrompt.ask("New Lambda", default=freq.get('lambda', 0.1))
        new_median = FloatPrompt.ask("New Median ($)", default=float(sev.get('median', 500000)))
        new_sigma = FloatPrompt.ask("New Sigma", default=float(sev.get('sigma', 1.5)))
        
        freq['lambda'] = new_lambda
        sev['median'] = new_median
        sev['sigma'] = new_sigma
        
        # Re-simulate
        with console.status("[bold green]Re-simulating...") as status:
            sim = run_monte_carlo(model, n_runs=10000)
        
        if sim.success:
            old_eal = r['metrics']['eal']
            new_eal = sim.metrics.eal
            delta = new_eal - old_eal
            color = "red" if delta > 0 else "green"
            arrow = "↑" if delta > 0 else "↓"
            
            console.print(Panel(
                f"[bold]Original EAL:[/bold] ${old_eal:,.0f}\n"
                f"[bold]New EAL:[/bold] ${new_eal:,.0f}\n"
                f"[bold]Change:[/bold] [{color}]{arrow} ${abs(delta):,.0f}[/{color}]\n"
                f"[bold]New VaR 95%:[/bold] ${sim.metrics.var_95:,.0f}",
                title=f"What-If Result: {r['name']}",
                border_style="cyan"
            ))
        else:
            console.print("[red]Simulation failed with new parameters.[/red]")
        
        console.print("")


class SessionLogger:
    """Mirrors console output to a session log file."""
    def __init__(self, output_dir):
        self.log_path = os.path.join(output_dir, "session_log.txt")
        self.entries = []
        self.start_time = datetime.now()
    
    def log(self, event, detail=""):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "elapsed_s": (datetime.now() - self.start_time).total_seconds(),
            "event": event,
            "detail": str(detail)[:500]
        }
        self.entries.append(entry)
    
    def save(self):
        with open(self.log_path, "w") as f:
            f.write(f"CRML Session Log\n")
            f.write(f"Started: {self.start_time.isoformat()}\n")
            f.write(f"{'='*60}\n\n")
            for e in self.entries:
                f.write(f"[{e['elapsed_s']:>7.1f}s] {e['event']}: {e['detail']}\n")
            f.write(f"\n{'='*60}\n")
            f.write(f"Total events: {len(self.entries)}\n")
            f.write(f"Duration: {(datetime.now() - self.start_time).total_seconds():.1f}s\n")


def interactive_loop():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="CRML Code — Cyber Risk Modeling CLI")
    parser.add_argument("--scan", "-s", help="Path to Zeron scan report (JSON or CSV)")
    parser.add_argument("--api-key", "-k", help="OpenAI API key (overrides env and ~/.crml/config.json)")
    parser.add_argument("--configure", action="store_true", help="Update saved OpenAI API key and exit")
    args = parser.parse_args()

    # --configure: update saved key and exit
    if args.configure:
        key = Prompt.ask("Enter your OpenAI API key", password=True)
        if key:
            cfg = load_config()
            cfg["openai_api_key"] = key
            save_config(cfg)
            console.print("[green]✓ Key saved to ~/.crml/config.json[/green]")
        return

    # Resolve API key before anything else
    api_key = resolve_api_key(args.api_key)
    if not api_key:
        console.print("[red]Error: No OpenAI API key provided. Exiting.[/red]")
        return
    crml_ai.init_client(api_key)

    print_banner()
    
    # Pre-load scan findings if provided
    scan_findings = None
    if args.scan:
        if not os.path.exists(args.scan):
            console.print(f"[red]Scan file not found: {args.scan}[/red]")
            return
        console.print(f"[bold green]📄 Scan file loaded: {args.scan}[/bold green]")
        scan_findings = parse_scan_file(args.scan)
        if not scan_findings:
            console.print("[red]No findings parsed from scan file. Falling back to manual input.[/red]")
            scan_findings = None
    
    try:
        context = get_org_context()
        
        # Initialize Session Logger (Feature 9)
        session = SessionLogger(context['output_dir'])
        session.log("SESSION_START", f"Organization: {context['company']}")
        if args.scan:
            session.log("SCAN_LOADED", f"File: {args.scan}, Findings: {len(scan_findings) if scan_findings else 0}")
        
        scenarios = run_discovery(context, scan_findings=scan_findings)
        session.log("DISCOVERY", f"Scenarios found: {len(scenarios)}")
        
        if not scenarios:
            session.log("ABORT", "No scenarios discovered")
            session.save()
            return

        results = simulate_scenarios(scenarios, context)
        session.log("SIMULATION", f"Results: {len(results)} scenarios, Total EAL: ${sum(r['metrics']['eal'] for r in results):,.0f}")
        
        generate_report(results, context)
        session.log("REPORT", f"Files saved to {context['output_dir']}")
        
        # Feature 7: Interactive What-If Mode
        if results and Confirm.ask("\n[bold cyan]Enter What-If mode?[/bold cyan]", default=False):
            session.log("WHAT_IF_START", "User entered what-if mode")
            what_if_mode(results, context)
            session.log("WHAT_IF_END", "User exited what-if mode")
        
        session.log("SESSION_END", "Complete")
        session.save()
        console.print(f"[dim]Session log saved to {context['output_dir']}/session_log.txt[/dim]")
        
    except KeyboardInterrupt:
        console.print("\n[bold red]Interrupted by user. Exiting...[/bold red]")
    except Exception as e:
        console.print(f"\n[bold red]Fatal Error:[/bold red] {e}")

if __name__ == "__main__":
    interactive_loop()
