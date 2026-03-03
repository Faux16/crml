#!/usr/bin/env python3
"""
CRML Agentic Bridge Prototype
------------------------------
A script to convert natural language into validated CRML models and run simulations.
"""

import sys
import os
import argparse
import json
import yaml
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# Load env variables
load_dotenv()

# Initialize OpenAI Client (lazy — call init_client() before use)
client = None

def init_client(api_key: str):
    """Initialize the global OpenAI client with the provided key."""
    global client
    client = OpenAI(api_key=api_key)
    os.environ["OPENAI_API_KEY"] = api_key

# Attempt to import CRML libraries
try:
    from crml_lang.models.scenario_model import CRScenario
    from crml_engine.simulation.engine import run_monte_carlo
except ImportError:
    print("Error: CRML libraries not found. Run 'pip install -e ./crml_lang -e ./crml_engine' first.")
    sys.exit(1)

def load_knowledge_base():
    kb_path = os.path.join(os.path.dirname(__file__), "industry_benchmarks.json")
    if os.path.exists(kb_path):
        with open(kb_path, 'r') as f:
            return json.load(f)
    return {"scenarios": []}

def expert_ai_generator(prompt, kb, context=None):
    """
    Knowledge-based generator that matches prompts to industry benchmarks.
    In production, this 'Grounding Logic' is sent as context to OpenAI.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    prompt_lower = prompt.lower()
    
    # Extract Context
    revenue = context.get("revenue") if context else None
    employees = context.get("employees") if context else None
    findings = context.get("findings", []) if context else []
    
    # Summarize findings for prompt
    findings_summary = ""
    if findings:
        findings_summary = "\n".join([f"- {f.get('vulnerability')} ({f.get('severity')}) on {f.get('asset')}" for f in findings[:20]])

    # --- GROUNDING LOGIC (Expert System) ---
    # ... (rest of function logic)
    selected_kb = None
    for scenario in kb.get("scenarios", []):
        if any(keyword in prompt_lower for keyword in scenario.get("keywords", [])):
            selected_kb = scenario
            break
    
    # --- LLM REASONING LAYER (if key exists) ---
    if openai_key and len(openai_key) > 10:
        try:
            # Construct the system context with Industry Knowledge and Org Profile
            system_prompt = f"""You are a Cyber Risk Modeling Expert. 
Your task is to convert a user's risk description into a CRML Scenario (JSON).

## GROUNDING DATA (Expert Knowledge Base)
Use these industry benchmarks as your primary source of truth for Lambda and Median values:
{json.dumps(kb, indent=2)}

## ORGANIZATIONAL CONTEXT
The target company has:
- Revenue: {f"${revenue:,.2f}" if revenue else "Unknown"}
- Employees: {employees if employees else "Unknown"}

## ATTACK SURFACE FINDINGS
The following vulnerabilities were detected:
{findings_summary if findings_summary else "No specific findings provided."}

## GUIDELINES
1. If the user's prompt matches one of the KB IDs, USE those parameters as a baseline.
2. SCALE parameters based on organizational context:
   - Frequency (Lambda): For a $1B+ pharmaceutical company, baseline Lambda should be 0.5-2.0 for Critical risks, 0.2-0.8 for High.
   - Severity (Median): For a $1B+ company, severity typically ranges from $500,000 to $50,000,000 depending on scenario.
3. If the user provides a SPECIFIC financial amount (e.g., "$1M"), OVERRIDE the KB's median value.
4. CRITICAL: NEVER return zero or near-zero values. Use these MINIMUM baselines:
   - Lambda (frequency): Minimum 0.1 for any risk
   - Median (severity): Minimum $100,000 for any enterprise scenario
5. Output ONLY valid JSON matching the schema:
{{
  "crml_scenario": "1.0",
  "meta": {{ "name": "slug-name", "description": "brief desc" }},
  "scenario": {{
    "frequency": {{ "model": "poisson", "parameters": {{ "lambda": float }} }},
    "severity": {{ "model": "lognormal", "parameters": {{ "median": float, "currency": "USD", "sigma": float }} }}
  }},
  "rationale": "Why did you choose these numbers? Explain how you scaled them for this specific company."
}}"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            ai_data = json.loads(response.choices[0].message.content)
            
            # Extract structured scenario
            scenario_dict = ai_data["crml_scenario"] if "crml_scenario" in ai_data and isinstance(ai_data["crml_scenario"], dict) else ai_data
            
            # Extract rationale but don't delete yet
            rationale = ai_data.get("rationale", "No rationale provided.")
            
            # VALIDATION: Ensure minimum baseline values
            try:
                freq_params = scenario_dict.get("scenario", {}).get("frequency", {}).get("parameters", {})
                sev_params = scenario_dict.get("scenario", {}).get("severity", {}).get("parameters", {})
                
                # Enforce minimum lambda
                if freq_params.get("lambda", 0) < 0.1:
                    freq_params["lambda"] = 0.1
                
                # Enforce minimum median
                median_val = sev_params.get("median", 0)
                if isinstance(median_val, str):
                    median_val = float(median_val.replace(",", "").replace("$", ""))
                if median_val < 100000:
                    median_val = 500000
                sev_params["median"] = median_val
            except:
                pass
            
            # Attach rationale privately for CLI display
            scenario_dict["metadata_rationale"] = rationale
            return scenario_dict


            
        except Exception as e:
            if not os.getenv("JSON_MODE"): # We'll check an env var or just assume fallback is okay
                 print(f"[*] AI Layer Error: {e}. Falling back to Expert System...")

    # --- FALLBACK: Expert System Logic ---
    if not selected_kb:
        selected_kb = {
            "id": "generic",
            "baseline_lambda": 0.1,
            "typical_median": 500000,
            "sigma": 1.2,
            "rationale": "Generic baseline used as no specific industry match was found."
        }
    
    # Extract parameters
    name = selected_kb["id"].replace("_", "-")
    desc = f"Expert-grounded model: {prompt}"
    freq_lambda = selected_kb["baseline_lambda"]
    sev_median = selected_kb["typical_median"]
    sigma = selected_kb["sigma"]
    rationale = f"GROUNDED IN KB: {selected_kb['rationale']}"

    # Simple regex for overrides in fallback mode
    import re
    match = re.search(r'(\d+(?:\.\d+)?)\s*([km])?\b', prompt_lower)
    if match:
        val = float(match.group(1))
        suffix = match.group(2)
        if suffix == 'm' or "million" in prompt_lower:
            sev_median = int(val * 1000000)
        elif suffix == 'k' or "thousand" in prompt_lower:
            sev_median = int(val * 1000)
        else:
            sev_median = int(val)
        rationale += f" (Note: Base financial impact overridden by user value of ${sev_median:,})"

    scenario_dict = {
        "crml_scenario": "1.0",
        "meta": {
            "name": name,
            "description": desc,
            "author": "CRML-Expert-Agent"
        },
        "scenario": {
            "frequency": {
                "model": "poisson",
                "parameters": {
                    "lambda": freq_lambda
                }
            },
            "severity": {
                "model": "lognormal",
                "parameters": {
                    "median": str(sev_median),
                    "currency": "USD",
                    "sigma": sigma
                }
            }
        }
    }
    # Note: _rationale removed to avoid Pydantic validation errors
    return scenario_dict

def generate_underwriter_report(context, results, attack_surface=None):
    """
    Generates a professional Cyber Insurance Underwriter Report in JSON format.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return '{"error": "OpenAI API Key not found. Cannot generate report."}'

    # Summarize results for the LLM
    scenarios_summary = []
    for r in results:
        scenarios_summary.append(f"- **{r['name']}**: EAL=${r['metrics']['eal']:,.2f}, VaR95=${r['metrics']['var_95']:,.2f}")
    
    attack_surface_str = json.dumps(attack_surface, indent=2) if attack_surface else "Not available"

    prompt = f"""You are a Senior Cyber Risk Underwriter. Write a detailed "Cyber Insurance Underwriting Report" for:
    
    **Organization**: {context.get('company', 'Unknown')}
    **Industry**: {context.get('industry', 'Unknown')}
    **Revenue**: ${context.get('revenue', 0):,.2f}
    **Employees**: {context.get('employees', 0)}
    **Compliances**: {", ".join(context.get('compliances', []))}
    
    ## RISK ANALYSIS RESULTS
    {chr(10).join(scenarios_summary)}
    
    ## ATTACK SURFACE INTELLIGENCE
    {attack_surface_str}
    
    ## OBJECTIVE
    Output a structured JSON report (do NOT output markdown).
    
    ## INSTRUCTIONS
    1. **Company Profile**: Synthesize a professional description. Mention inferred/stated compliances.
    2. **Methodology**: Explain the Risk Score calculation: Industry Baseline (40%), Company Size/Revenue (30%), and Attack Surface Findings (30%).
    
    Schema:
    {{
        "company_profile": "Professional summary of the organization, industry position, and compliance posture.",
        "executive_summary": "High-level risk assessment (Low/Medium/High) and key findings.",
        "digital_footprint": "Summarize the tech stack and potential exposures found.",
        "financial_impact": "Interpret the VaR and EAL numbers. Explain what they mean for insurance limits.",
        "recommendations": ["Control 1", "Control 2", "Exclusion 1"],
        "methodology": "Explanation of the CRML probabilistic approach and the 40/30/30 weighted scoring model."
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({"error": f"Could not generate report: {e}"})


def discover_risk_scenarios(findings, context):
    """
    Analyzes raw findings and groups them into distinct risk scenarios.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("[-] Error: OPENAI_API_KEY not found in environment.")
        return []

    # Summarize findings to avoid token limits
    summary_findings = []
    if isinstance(findings, list):
        for f in findings[:50]: # Limit to top 50 to avoid context overflow
            summary_findings.append(f"{f.get('vulnerability', 'Issue')} ({f.get('severity', 'Low')})")
    
    findings_str = "\n".join(summary_findings)

    prompt = f"""You are a Cyber Risk Architect. Analyze these vulnerability findings for {context.get('company')}:
    
    FINDINGS:
    {findings_str}
    
    Identify 3-5 distinct, major risk scenarios that could materialize from these findings. 
    Do not just list vulnerabilities; group them into scenarios (e.g. "Data Breach via SQL Injection", "Ransomware via Unpatched Server").
    
    Return JSON Object:
    {{
        "scenarios": [
            {{ "name": "Scenario Title", "prompt": "Description of how the attack happens based on findings" }}
        ]
    }}
    """

    try:
        if not client.api_key:
            client.api_key = openai_key
            
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        data = json.loads(content)
        
        discovered = []
        if "scenarios" in data:
            discovered = data["scenarios"]
        elif isinstance(data, list):
            discovered = data
            
        return discovered
    except Exception as e:
        print(f"Discovery Error: {e}")
        return []


def discover_org_context(company_name):
    """
    Researches organization details using OpenAI's web search for live data.
    Falls back to Chat Completions if Responses API is unavailable.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {
            "company": company_name, 
            "revenue": 0, 
            "employees": 0, 
            "industry": "Unknown", 
            "compliances": [],
            "guidance": {"lambda": 0.5, "severity_weight": "Medium", "logic": "No API key found."}
        }

    current_date = datetime.now().strftime("%B %Y")
    
    prompt = f"""Search the web for the latest information about this company and provide accurate, current data.

    TODAY'S DATE: {current_date}
    COMPANY INPUT: {company_name}

    CRITICAL: You MUST find the most recent financial data available as of {current_date}. 
    For revenue, look for FY2025 or the latest reported fiscal year first. Do NOT return outdated figures from 2023 or earlier if newer data exists. Check annual reports, quarterly earnings, SEC/SEBI filings, or reliable financial news.

    STEP 1 — ENTITY RESOLUTION (CRITICAL):
    The user may have entered a brand name, product name, subsidiary, or abbreviation.
    You MUST search the web to find the EXACT REGISTERED legal entity name. 
    
    DO NOT just append "Private Limited", "Inc.", or "Ltd" to the brand name — that is WRONG.
    Instead, search for the company on official registries or reliable sources:
    - India: MCA (Ministry of Corporate Affairs), Tofler, Zauba Corp
    - US: SEC EDGAR, state corporation databases
    - UK: Companies House
    - Or: LinkedIn company page, Crunchbase, official website legal/about pages
    
    Examples of correct resolution:
    - "Paytm" → "One97 Communications Limited" (NOT "Paytm Private Limited")
    - "Google" → "Alphabet Inc." (NOT "Google Inc.")
    - "Instagram" → "Meta Platforms, Inc." (NOT "Instagram Inc.")
    - "PhonePe" → "PhonePe Private Limited" (this one IS correct because the registered name matches)
    - "Zomato" → "Zomato Limited" (NOT "Zomato Private Limited" — they went public)
    
    Search the web for "{company_name} registered company name" or "{company_name} CIN number" to find the actual legal name.

    STEP 2 — DATA COLLECTION (SEARCH HARD — DO NOT GIVE UP):
    After identifying the correct legal entity, you MUST search MULTIPLE sources to find financial data.
    DO NOT say "revenue not publicly disclosed" without trying ALL of the following:

    For Indian companies, search EACH of these:
    1. Tofler.in — search "{company_name} Tofler" (has MCA-filed revenue for most Indian companies)
    2. Zauba Corp — search "{company_name} Zauba Corp" (has ROC filings with revenue)
    3. TheKredible — search "{company_name} TheKredible revenue"
    4. Tracxn — search "{company_name} Tracxn" (has revenue estimates for startups)
    5. Crunchbase — search "{company_name} Crunchbase" (has funding + estimated revenue)
    6. Inc42 / Entrackr — search "{company_name} revenue Entrackr" (Indian startup revenue reporting)
    7. Economic Times / Moneycontrol — search "{company_name} revenue"
    8. LinkedIn company page — employee count is always available here
    9. GetLatka — search "{company_name} GetLatka"
    10. Google News — search "{company_name} revenue FY2024 OR FY2025"

    For US/Global companies: SEC EDGAR, Yahoo Finance, Macrotrends, Statista

    IMPORTANT: Indian private company financials ARE available through MCA/ROC filings on Tofler and Zauba Corp. 
    Even if the company website doesn't show revenue, Tofler almost always has it from annual MCA filings.
    
    If after searching all sources you truly cannot find revenue, provide your BEST ESTIMATE based on:
    - Funding raised (e.g., raised $10M → likely $2-5M annual revenue)
    - Employee count (e.g., 50 employees × $50K avg cost ≈ $2.5M minimum revenue)
    - Industry benchmarks
    And mark it clearly as an estimate in revenue_note.

    Return the following in JSON format:
    {{
        "company": "Full Legal/Registered Name of the entity",
        "brand_name": "Common brand name if different from legal name (e.g., 'Paytm')",
        "ticker": "Stock ticker symbol if publicly listed (e.g., 'PAYTM.NS', 'GOOGL'), or null",
        "headquarters": "City, Country",
        "revenue_original": "The EXACT revenue figure as found in the source, including currency. e.g., '₹132 crore' or '$15.8M' or '€500M'",
        "revenue_original_currency": "The currency code of the original figure. e.g., 'INR', 'USD', 'EUR'",
        "revenue": <revenue converted to USD as a full number. CONVERSION RULES below>,
        "revenue_year": "Fiscal year of the revenue figure (e.g., 'FY2025')",
        "revenue_note": "Explain why this year was chosen and if newer data exists.",
        "employees": <latest employee count as an integer>,
        "industry": "Primary Industry Name",
        "compliances": ["List of known regulatory compliances like GDPR, SOC2, PCI-DSS, HIPAA, ISO27001, etc."],
        "data_sources": "Brief note on where the data was sourced from (e.g., annual report, Wikipedia, SEC filings)",
        "risk_guidance": {{
            "suggested_lambda": "Expected breach frequency (e.g., 0.5 for 1 event every 2 years). Base this on industry breach statistics.",
            "severity_weightage": "How revenue/industry scales impact severity (e.g., 'High' for Finance, 'Critical' for Healthcare)",
            "key_parameters": ["List of specific risk metrics to watch for THIS company like Transaction Volume, PII count, Cloud Infrastructure, API exposure"],
            "reasoning": "Detailed logic on why these parameters were chosen for THIS specific organization based on its industry, size, and publicly known incidents."
        }}
    }}

    REVENUE CONVERSION RULES (CRITICAL — get this right):
    - The "revenue" field must be the FULL amount in USD (not millions, not shorthand).
    - "Revenue" means ONLY: Revenue from Operations / Total Income / Turnover / Net Sales.
    - DO NOT USE: AUM (Assets Under Management), GMV, GTV, TPV, Loan Book, Disbursements — these are NOT revenue.
    - For fintech companies: AUM can be 10x-100x of actual revenue. Only use "Revenue from Operations".
    - If the source says "₹132 crore", that is 1,320,000,000 INR. Convert: 1,320,000,000 / 83 = ~15,900,000 USD. So revenue = 15900000.
    - If the source says "$15.8M", that is already USD. revenue = 15800000.
    - If the source says "₹50 lakh", that is 5,000,000 INR. Convert: 5,000,000 / 83 = ~60,000 USD. So revenue = 60000.
    - Common mistake: DO NOT put INR values directly in the revenue field. ₹132 crore is NOT $1,320,000,000 — it is ~$16M.
    - Use approximate exchange rate: 1 USD = 83 INR, 1 USD = 0.92 EUR, 1 USD = 0.79 GBP.
    - Always return the LEGAL entity name in "company", not the brand name.
    - Return ONLY valid JSON.
    """

    # Try Responses API with web search first
    try:
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=prompt,
        )
        
        # Extract text content from the response
        result_text = ""
        for item in response.output:
            if hasattr(item, 'content'):
                for content_block in item.content:
                    if hasattr(content_block, 'text'):
                        result_text = content_block.text
        
        if result_text:
            # Extract JSON from possible markdown code block
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            data = json.loads(result_text)
            data["_source"] = "web_search"
            
            # Revenue retry — if revenue is 0/null/missing, do a focused search
            rev = data.get("revenue", 0)
            try:
                rev = float(rev) if rev else 0
            except (ValueError, TypeError):
                rev = 0
            
            if rev == 0:
                legal_name = data.get("company", company_name)
                hq = data.get('headquarters', 'India')
                is_indian = "india" in hq.lower()
                employees = data.get('employees', 0)
                
                if is_indian:
                    search_instructions = f"""You MUST find the annual revenue for this Indian company. Do NOT return 0.

CRITICAL — REVENUE ≠ AUM/GMV/GTV/TPV:
- "Revenue" means ACTUAL income earned by the company (Revenue from Operations / Total Income / Turnover)
- DO NOT confuse with: AUM (Assets Under Management), GMV (Gross Merchandise Value), GTV (Gross Transaction Value), TPV (Total Payment Volume), Loan Book Size, Disbursements
- For fintech companies: AUM or transaction volume can be 10x-100x of actual revenue. ONLY report REVENUE.
- Look specifically for "Revenue from Operations" or "Total Income" in financial statements

SEARCH STRATEGY — do ALL of these Google searches:
1. "{company_name} annual revenue site:tracxn.com" — Google indexes Tracxn company pages with revenue data
2. "{company_name} revenue from operations site:tofler.in" — Tofler has MCA-filed revenue for Indian companies  
3. "{legal_name} total income OR revenue from operations"
4. "{company_name} operating revenue FY2024 OR FY2025"
5. "{company_name} turnover crore"
6. "{company_name} revenue site:entrackr.com" OR "{company_name} revenue site:inc42.com"
7. "{company_name} funding raised" — if revenue not found, use funding to estimate

Look for these SPECIFIC line items in financial data:
- "Revenue from Operations" (this is the correct field)
- "Total Income" 
- "Turnover"
- NOT: AUM, GMV, Loan disbursements, Transaction volume

The company: {legal_name} (brand: {company_name}), HQ: {hq}, Employees: {employees or 'unknown'}"""
                else:
                    search_instructions = f"""You MUST find the annual revenue for this company. Do NOT return 0.

1. "{legal_name} annual revenue site:macrotrends.net"
2. "{company_name} revenue site:finance.yahoo.com"
3. "{legal_name} revenue 10-K SEC filing"
4. "{company_name} revenue site:crunchbase.com"
5. "{company_name} annual report revenue FY2024 OR FY2025"

The company: {legal_name} (brand: {company_name}), HQ: {hq}, Employees: {employees or 'unknown'}"""

                retry_prompt = f"""{search_instructions}

Return JSON ONLY:
{{
    "revenue_original": "exact figure as found, e.g. '₹12.5 crore' or '$15.8M' or '₹98 lakh'",
    "revenue_original_currency": "INR or USD or EUR",
    "revenue": <FULL amount in USD as integer>,
    "revenue_year": "FY20XX",
    "revenue_note": "exact source URL or name where you found this",
    "data_sources": "website name that provided this data"
}}

CONVERSION RULES (if currency is INR):
- ₹1 crore = 10,000,000 INR. To convert to USD: divide by 83.
- Example: ₹12 crore = 120,000,000 INR / 83 = 1,445,783 USD → revenue = 1445783
- Example: ₹98 lakh = 9,800,000 INR / 83 = 118,072 USD → revenue = 118072

IF you truly cannot find exact revenue from any source, you MUST estimate:
- If total funding raised is known: revenue ≈ 30% of total funding
- If employee count is known: revenue ≈ employees × $40,000 (for Indian companies)
- Mark as "ESTIMATED based on [funding/employees]" in revenue_note
NEVER return revenue as 0."""
                
                try:
                    retry_response = client.responses.create(
                        model="gpt-4o",
                        tools=[{"type": "web_search_preview"}],
                        input=retry_prompt,
                    )
                    retry_text = ""
                    for r_item in retry_response.output:
                        if hasattr(r_item, 'content'):
                            for r_block in r_item.content:
                                if hasattr(r_block, 'text'):
                                    retry_text = r_block.text
                    
                    if retry_text:
                        if "```json" in retry_text:
                            retry_text = retry_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in retry_text:
                            retry_text = retry_text.split("```")[1].split("```")[0].strip()
                        
                        rev_data = json.loads(retry_text)
                        # Merge revenue data back
                        for key in ["revenue", "revenue_original", "revenue_original_currency", "revenue_year", "revenue_note"]:
                            if rev_data.get(key):
                                data[key] = rev_data[key]
                        if rev_data.get("data_sources"):
                            data["data_sources"] = data.get("data_sources", "") + "; " + rev_data["data_sources"]
                except Exception as retry_err:
                    print(f"[Revenue Retry] Could not find revenue: {retry_err}")
            
            return data

    except Exception as e:
        print(f"[Web Search] Falling back to standard API: {e}")
    
    # Fallback: standard Chat Completions (no web search)
    try:
        fallback_prompt = f"""You are a Cyber Risk Intelligence AI. Provide the best available data about this company.

        COMPANY: {company_name}

        RETURN JSON ONLY:
        {{
            "company": "Full Legal Name",
            "revenue": 123456789,
            "employees": 1234,
            "industry": "Primary Industry Name",
            "compliances": ["GDPR", "SOC2", "etc"],
            "risk_guidance": {{
                "suggested_lambda": "Expected frequency",
                "severity_weightage": "Impact scale",
                "key_parameters": ["Metrics to monitor"],
                "reasoning": "Detailed logic for parameter choices."
            }}
        }}
        """
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": fallback_prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        data["_source"] = "training_data"
        return data
    except Exception as e:
        print(f"Discovery Error: {e}")
        return {"company": company_name, "revenue": 0, "employees": 0, "industry": "Unknown", "compliances": []}


def generate_benchmark_comparison(context, results):
    """
    Compares the organization's risk metrics against industry benchmarks.
    """
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        return {"error": "No API key"}

    total_eal = sum(r['metrics']['eal'] for r in results)
    total_var95 = sum(r['metrics']['var_95'] for r in results)
    scenarios_summary = ", ".join([f"{r['name']} (EAL=${r['metrics']['eal']:,.0f})" for r in results])

    prompt = f"""You are a Cyber Risk Benchmarking Analyst. Compare this organization's risk profile against industry peers.

    ORGANIZATION: {context.get('company')}
    INDUSTRY: {context.get('industry')}
    REVENUE: ${context.get('revenue', 0):,.0f}
    EMPLOYEES: {context.get('employees', 0)}

    RISK METRICS:
    - Total EAL (Expected Annual Loss): ${total_eal:,.0f}
    - Total VaR 95%: ${total_var95:,.0f}
    - Scenarios: {scenarios_summary}

    Provide a comparative analysis. Return JSON:
    {{
        "industry_avg_eal": float (estimated industry average EAL for similar-sized companies),
        "eal_ratio": "X.Xx" (org EAL / industry avg, e.g., "1.5x means 50% higher than peers"),
        "risk_tier": "Low/Medium/High/Critical (relative to peers)",
        "peer_comparison": "2-3 sentence narrative comparing to industry peers",
        "top_outlier_scenario": "Which scenario is most above-average vs peers and why"
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"error": f"Benchmark comparison failed: {e}"}


def main():
    parser = argparse.ArgumentParser(description="Agentic CRML Bridge: NL to Risk Model")
    parser.add_argument("prompt", nargs="?", help="Natural language description of the risk")
    parser.add_argument("--out", "-o", help="Output YAML file path", default="generated_scenario.yaml")
    parser.add_argument("--simulate", "-s", action="store_true", help="Run simulation immediately")
    parser.add_argument("--runs", type=int, default=10000, help="Number of simulation runs")
    
    # Contextual Arguments
    parser.add_argument("--company", help="Company name for autonomous discovery")
    parser.add_argument("--revenue", type=float, help="Company annual revenue in USD")
    parser.add_argument("--employees", type=int, help="Number of employees")
    parser.add_argument("--attack-surface", help="JSON string of attack surface data")
    parser.add_argument("--compliances", help="Comma-separated list of compliances") 
    parser.add_argument("--discover-scenarios", action="store_true", help="Automatically discover scenarios from findings")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    
    # Load Knowledge Base
    kb = load_knowledge_base()
    
    context = {
        "revenue": args.revenue,
        "employees": args.employees,
        "company": args.company,
        "compliances": args.compliances.split(",") if args.compliances else [],
        "findings": [] # Placeholder, will be updated if attack_surface is provided
    }

    # Determine Scenarios to Run
    scenarios_to_run = []
    
    if args.discover_scenarios and args.attack_surface:
        # Dynamic Mode
        if not args.json: print("[*] Discovering risk scenarios from findings...")
        try:
            as_data = json.loads(args.attack_surface)
            findings = as_data.get("findings", [])
            context["findings"] = findings # Update context with actual findings
            discovered = discover_risk_scenarios(findings, context)
            for s in discovered:
                scenarios_to_run.append(s)
        except Exception as e:
            if not args.json: print(f"[-] Error parsing attack surface: {e}")
            
    elif args.prompt:
        # specific prompt mode
        scenarios_to_run.append({"name": "Custom Scenario", "prompt": args.prompt})
    else:
        # Fallback
        scenarios_to_run.append({"name": "General Risk", "prompt": "General cyber risk assessment"})

    
    # Run Analysis Loop
    simulation_results = []
    
    if not args.json:
        print(f"[*] Analyzing {len(scenarios_to_run)} scenarios...")

    generated_yamls = []

    for scenario_req in scenarios_to_run:
        prompt = scenario_req.get("prompt", scenario_req.get("name"))
        name_override = scenario_req.get("name")
        
        # 1. GENERATE MODEL
        model_dict = expert_ai_generator(prompt, kb, context=context)
        if name_override:
            model_dict['meta']['name'] = name_override
        
        # DEBUG: Print model parameters
        freq_params = model_dict.get('scenario', {}).get('frequency', {}).get('parameters', {})
        sev_params = model_dict.get('scenario', {}).get('severity', {}).get('parameters', {})
        if not args.json:
            print(f"  Model params for '{name_override}': lambda={freq_params.get('lambda')}, median={sev_params.get('median')}")
            
        # 2. SIMULATE
        metrics = {"eal": 0, "var_95": 0, "var_99": 0}
        if args.simulate:
            result = run_monte_carlo(model_dict, n_runs=args.runs)
            if result.success:
                metrics = {
                    "eal": result.metrics.eal,
                    "var_95": result.metrics.var_95,
                    "var_99": result.metrics.var_99
                }
            else:
                if not args.json:
                    print(f"  WARNING: Simulation failed: {result.errors}")

        
        simulation_results.append({
            "name": model_dict['meta']['name'],
            "prompt": prompt,
            "metrics": metrics,
            "crml_yaml": yaml.dump(model_dict, sort_keys=False)
        })
        generated_yamls.append(yaml.dump(model_dict, sort_keys=False))

    # Output Generation
    if args.json:
        # Parse attack surface if passed
        attack_surface_data = None
        if args.attack_surface:
            try:
                attack_surface_data = json.loads(args.attack_surface)
            except:
                pass
        
        report = generate_underwriter_report(context, simulation_results, attack_surface=attack_surface_data)

        output = {
            "scenarios": simulation_results,
            "report": report
        }
        print(json.dumps(output))
    else:
        # CLI Output
        print("\n" + "="*40)
        print(" AGGREGATED ANALYSIS RESULTS")
        print("="*40)
        for res in simulation_results:
            print(f" [ {res['name']} ]")
            print(f"   EAL: ${res['metrics']['eal']:,.2f}")
            print(f"   VaR 95%: ${res['metrics']['var_95']:,.2f}")
            print("-" * 20)
        
        print("\n" + "="*40)
        print(" REPORT SUMMARY")
        print("="*40)
        print(generate_underwriter_report(context, simulation_results)[:500] + "...")

if __name__ == "__main__":
    main()
