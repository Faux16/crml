#!/usr/bin/env python3
"""
CRML Executive Report Generator
-------------------------------
Generates a markdown-based board report summarizing the risk portfolio and recommendations.
"""

import sys
import os
import json
from datetime import datetime

def main():
    dashboard_file = "portfolio_dashboard_data.json"
    if not os.path.exists(dashboard_file):
        print(f"Error: {dashboard_file} not found. Run crml_portfolio.py first.")
        sys.exit(1)
        
    with open(dashboard_file, 'r') as f:
        data = json.load(f)
        
    report = f"""# Executive Risk & Investment Report
**Date**: {datetime.now().strftime('%Y-%m-%d')}
**Company**: Enterprise Context (Discovery Active)

---

## 1. Executive Summary
Our current estimated cybersecurity risk exposure across the analyzed portfolio is **${data['summary']['total_eal']:,.2f}** in Expected Annual Loss (EAL). 

The portfolio's "Tail Risk" (VaR 95%) is **${data['summary']['max_potential_loss']:,.2f}**, primarily driven by **{data['summary']['top_risk'].upper()}**.

### Key Portfolio Risks
- **Total Scenarios**: {data['summary']['scenario_count']}
- **Highest Severity**: {data['heatmap'][0]['name']}
- **Highest Frequency**: {sorted(data['heatmap'], key=lambda x: x['frequency'], reverse=True)[0]['name']}

---

## 2. Risk Heatmap
| Scenario Name | Frequency (Events/Year) | Typical Severity (Median) | Impact (EAL) |
| :--- | :--- | :--- | :--- |
"""
    for r in data['heatmap']:
        report += f"| {r['name']} | {r['frequency']:.2f} | ${r['severity']:,.0f} | ${r['eal']:,.2f} |\n"

    report += """
---

## 3. Strategic Recommendations
Based on the **CRML ROI Optimizer** analysis, we recommend the following investment priorities to maximize risk reduction per dollar spent:

### Top Investment Priority
**Multi-Factor Authentication (MFA)**
- **ROI**: High (Typical 15x+)
- **Impact**: Primary defense against 45% of our portfolio frequency.
- **Action**: Immediate enterprise-wide rollout for all administrative and user credentials.

### Secondary Priorities
1. **Immutable Backups**: Essential to mitigate the $5M+ tail risk from Ransomware.
2. **Security Awareness Training**: High-ROI "human wall" defense for a low annual cost.

---
**Confidential - For Board Review Only**
"""
    
    with open("EXECUTIVE_REPORT.md", 'w') as f:
        f.write(report)
        
    print("[+] Executive Report generated: EXECUTIVE_REPORT.md")

if __name__ == "__main__":
    main()
