#!/usr/bin/env python3
"""
CRML ROI Optimizer
------------------
A script to compare security investments and recommend the most cost-effective controls.
"""

import sys
import os
import argparse
import json
import copy
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import the bridge logic
from crml_ai import load_knowledge_base, expert_ai_generator
from crml_engine.simulation.engine import run_monte_carlo

def calculate_roi(risk_reduction, cost):
    if cost == 0:
        return 0
    return (risk_reduction - cost) / cost

def main():
    parser = argparse.ArgumentParser(description="CRML ROI Optimizer: Compare Security Investments")
    parser.add_argument("prompt", help="Natural language description of the risk baseline")
    parser.add_argument("--runs", type=int, default=10000, help="Number of simulation runs")
    
    # Contextual Arguments
    parser.add_argument("--company", help="Company name for autonomous discovery")
    parser.add_argument("--revenue", type=float, help="Company annual revenue in USD")
    parser.add_argument("--employees", type=int, help="Number of employees")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    kb = load_knowledge_base()
    
    if not args.json:
        print(f"[*] Analyzing Baseline Risk: '{args.prompt}'...")
    
    # Context Dictionary
    context = {
        "revenue": args.revenue,
        "employees": args.employees,
        "company": args.company
    }
    
    # 1. GENERATE BASELINE
    baseline_model = expert_ai_generator(args.prompt, kb, context=context)
    baseline_rationale = baseline_model.pop("_rationale", "No rationale provided.")
    
    # We need to know which KB ID it matched to find relevant controls
    kb_match_id = baseline_model['meta']['name'].replace("-", "_")
    
    # Run Baseline Simulation
    if not args.json:
        print(f"[*] Running Baseline Simulation...")
    baseline_res = run_monte_carlo(baseline_model, n_runs=args.runs)
    if not baseline_res.success:
        print(f"[-] Baseline failed: {baseline_res.errors}")
        sys.exit(1)
        
    baseline_eal = baseline_res.metrics.eal
    if not args.json:
        print(f"[+] Baseline EAL: ${baseline_eal:,.2f}")
    
    # 2. IDENTIFY AND RUN CONTROLS
    if not args.json:
        print("\n[*] Evaluating Potential Investments...")
    results = []
    
    for control in kb.get("controls", []):
        # Create a modified scenario for this control
        modified_model = copy.deepcopy(baseline_model)
        
        affects = control.get("affects", "frequency")
        eff = control['effectiveness']
        
        # Apply reductions based on control type
        if affects in ["frequency", "both"]:
            orig_lambda = float(modified_model['scenario']['frequency']['parameters']['lambda'])
            modified_model['scenario']['frequency']['parameters']['lambda'] = orig_lambda * (1 - eff)
            
        if affects in ["severity", "both"]:
            orig_median = float(modified_model['scenario']['severity']['parameters']['median'])
            modified_model['scenario']['severity']['parameters']['median'] = str(int(orig_median * (1 - eff)))
            
        modified_model['meta']['name'] += f"-with-{control['id']}"
        
        # Run Modified Simulation
        res = run_monte_carlo(modified_model, n_runs=args.runs)
        if res.success:
            reduction = baseline_eal - res.metrics.eal
            roi = calculate_roi(reduction, control['annual_cost'])
            
            results.append({
                "name": control['name'],
                "cost": control['annual_cost'],
                "new_eal": res.metrics.eal,
                "reduction": reduction,
                "roi": roi,
                "rationale": control['rationale']
            })

    # 3. DISPLAY RANKINGS OR OUTPUT JSON
    if args.json:
        output_data = {
            "baseline": {
                "eal": baseline_eal,
                "rationale": baseline_rationale,
                "model": baseline_model
            },
            "investments": results
        }
        print(json.dumps(output_data))
        return

    # Sort by ROI (descending)
    results.sort(key=lambda x: x['roi'], reverse=True)
    
    print("\n" + "="*85)
    print(f"{'SECURE INVESTMENT RANKING':^85}")
    print("="*85)
    print(f"{'Investment':<30} | {'Cost':<12} | {'Reduction':<15} | {'ROI':<10}")
    print("-" * 85)
    
    for r in results:
        print(f"{r['name']:<30} | ${r['cost']:<11,} | ${r['reduction']:<14,.0f} | {r['roi']:>9.1f}x")
        
    print("="*85)
    
    if results:
        best = results[0]
        print(f"\n[!] RECOMMENDATION: Implement **{best['name']}**.")
        print(f"    Why: {best['rationale']}")
        print(f"    Outcome: Reduces expected annual loss by ${best['reduction']:,.0f} with an ROI of {best['roi']:.1f}x.")

if __name__ == "__main__":
    main()
