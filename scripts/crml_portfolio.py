#!/usr/bin/env python3
"""
CRML Portfolio Aggregator & Dashboard Data Generator
----------------------------------------------------
Aggregates multiple risk scenarios and generates summary metrics for the Executive Dashboard.
"""

import sys
import os
import argparse
import json
import yaml
from pathlib import Path
from crml_engine.simulation.engine import run_monte_carlo
from crml_ai import load_knowledge_base

def main():
    parser = argparse.ArgumentParser(description="CRML Portfolio Aggregator")
    parser.add_argument("scenarios", nargs="+", help="Paths to scenario YAML files")
    parser.add_argument("--runs", type=int, default=10000, help="Number of simulation runs")
    parser.add_argument("--out", "-o", default="portfolio_dashboard_data.json", help="Output JSON file for dashboard")
    
    args = parser.parse_args()
    
    dashboard_data = {
        "summary": {
            "total_eal": 0,
            "max_potential_loss": 0,
            "scenario_count": len(args.scenarios),
            "top_risk": ""
        },
        "heatmap": [],
        "roi_data": []
    }
    
    scenarios_results = []
    
    print(f"[*] Aggregating {len(args.scenarios)} scenarios...")
    
    for s_path in args.scenarios:
        if not os.path.exists(s_path):
            print(f"[!] Warning: Scenario file not found: {s_path}")
            continue
            
        with open(s_path, 'r') as f:
            model_dict = yaml.safe_load(f)
            
        print(f"[*] Simulating: {model_dict['meta']['name']}...")
        result = run_monte_carlo(model_dict, n_runs=args.runs)
        
        if result.success:
            eal = result.metrics.eal
            var95 = result.metrics.var_95
            
            dashboard_data["summary"]["total_eal"] += eal
            if var95 > dashboard_data["summary"]["max_potential_loss"]:
                dashboard_data["summary"]["max_potential_loss"] = var95
                dashboard_data["summary"]["top_risk"] = model_dict['meta']['name']
            
            # Map to Heatmap (Freq vs Sev)
            # Use Lambda as Frequency and Median as Severity
            freq = float(model_dict['scenario']['frequency']['parameters']['lambda'])
            sev = float(model_dict['scenario']['severity']['parameters']['median'])
            
            dashboard_data["heatmap"].append({
                "name": model_dict['meta']['name'],
                "frequency": freq,
                "severity": sev,
                "eal": eal
            })
        else:
            print(f"[!] Simulation failed for {s_path}: {result.errors}")

    # Display Executive Summary
    print("\n" + "="*60)
    print(f"{'EXECUTIVE RISK PORTFOLIO SUMMARY':^60}")
    print("="*60)
    print(f" Total Expected Annual Loss (EAL): ${dashboard_data['summary']['total_eal']:,.2f}")
    print(f" Portfolio VaR (95th Percentile): ${dashboard_data['summary']['max_potential_loss']:,.2f}")
    print(f" Top Identified Risk:             {dashboard_data['summary']['top_risk'].upper()}")
    print(f" Number of Scenarios Analyzed:    {dashboard_data['summary']['scenario_count']}")
    print("="*60)
    
    # Heatmap Table
    print(f"\n{'RISK HEATMAP DATA':<30} | {'Freq (λ)':<10} | {'Median ($)':<12}")
    print("-" * 60)
    for h in dashboard_data["heatmap"]:
        print(f"{h['name']:<30} | {h['frequency']:<10.2f} | ${h['severity']:<11,.0f}")
    
    # Save to JSON
    with open(args.out, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    print(f"\n[+] Dashboard data saved to {args.out}")

if __name__ == "__main__":
    main()
