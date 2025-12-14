"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import CodeEditor from "@/components/CodeEditor";
import SimulationResults, { SimulationResult } from "@/components/SimulationResults";
import { Play, RotateCcw, FileText, Settings2, HelpCircle, Info, BookOpen } from "lucide-react";
import Link from "next/link";

const EXAMPLE_MODELS = {
    "data-breach": {
        name: "Data Breach (Simple)",
        description: "50 databases with PII, 5% annual breach probability, $100K median cost",
        explanation: "This model represents a small-medium organization with customer data. Lambda=0.05 means 5% chance per database per year (industry average). Median=100000 means $100K typical loss per breach.",
        content: `crml: "1.1"
meta:
  name: "data-breach-simple"
  description: "Simple data breach risk model"
model:
  assets:
    cardinality: 50  # Number of databases with PII
  frequency:
    model: poisson  # Rare, random events
    parameters:
      lambda: 0.05  # 5% annual probability per database
  severity:
    model: lognormal  # Typical small losses, rare large ones
    parameters:
      median: "100 000"  # $100K median loss
      currency: USD
      sigma: 1.2  # Moderate variability`
    },
    "ransomware": {
        name: "Ransomware Scenario",
        description: "500 critical servers, 8% annual ransomware probability, $700K median loss",
        explanation: "Enterprise ransomware model based on 2023 industry data. Lambda=0.08 reflects ~8% of organizations hit annually. Median=700000 means $700K median loss (ransom + downtime + recovery).",
        content: `crml: "1.1"
meta:
  name: "ransomware-scenario"
  description: "Ransomware risk based on industry statistics"
model:
  assets:
    cardinality: 500  # Critical servers/systems
  frequency:
    model: poisson
    parameters:
      lambda: 0.08  # 8% annual probability (Sophos 2023)
  severity:
    model: lognormal
    parameters:
      median: "700 000"  # $700K median (industry avg)
      currency: USD
      sigma: 1.8  # High variability (some pay $50K, others $5M)`
    },
    "fair-baseline": {
        name: "FAIR Baseline",
        description: "Simple FAIR-style portfolio model with 1.2 events/year, $8K median loss",
        explanation: "Basic FAIR model for portfolio-level analysis. Lambda=1.2 means ~1-2 events expected per year across all assets. Median=8100 means $8100 median loss.",
        content: `crml: "1.1"
meta:
  name: "fair-baseline"
  description: "Simple FAIR-like Poisson + Lognormal model"
model:
  frequency:
    model: poisson
    scope: portfolio  # Portfolio-level (not per-asset)
    parameters:
      lambda: 1.2  # ~1-2 events per year total
  severity:
    model: lognormal
    parameters:
      median: "8 100"  # $8,100 median loss
      currency: USD
      sigma: 1.0  # Low variability`
    },
    "qber-simplified": {
        name: "QBER Simplified",
        description: "1000 assets, hierarchical Bayesian model with mixture severity",
        explanation: "Simplified QBER-style model using hierarchical_gamma_poisson for frequency and mixture distributions for severity. Note: Full QBER uses MCMC; this is a Monte Carlo approximation.",
        content: `crml: "1.1"
meta:
  name: "qber-simplified"
  description: "Simplified QBER-style model"
model:
  assets:
    cardinality: 1000  # Enterprise scale
  frequency:
    model: hierarchical_gamma_poisson  # Bayesian hierarchical
    parameters:
      alpha_base: 1.5
      beta_base: 1.5
  severity:
    model: mixture  # 70% lognormal, 30% gamma
    components:
      - lognormal:
          weight: 0.7
          median: "162 755"  # ~$163K median loss
          currency: USD
          sigma: 1.2
      - gamma:
          weight: 0.3
          shape: 2.5
          scale: 10000`
    }
};

// Supported output currencies (rate = value of 1 unit in USD)
const OUTPUT_CURRENCIES = {
    "USD": { symbol: "$", name: "US Dollar" },
    "EUR": { symbol: "€", name: "Euro" },
    "GBP": { symbol: "£", name: "British Pound" },
    "CHF": { symbol: "Fr", name: "Swiss Franc" },
    "JPY": { symbol: "¥", name: "Japanese Yen" },
    "CNY": { symbol: "CN¥", name: "Chinese Yuan" },
    "CAD": { symbol: "C$", name: "Canadian Dollar" },
    "AUD": { symbol: "A$", name: "Australian Dollar" },
};

export default function PlaygroundPage() {
    const [yamlContent, setYamlContent] = useState(EXAMPLE_MODELS["data-breach"].content);
    const [selectedExample, setSelectedExample] = useState("data-breach");
    const [simulationResult, setSimulationResult] = useState<SimulationResult | null>(null);
    const [isSimulating, setIsSimulating] = useState(false);
    const [runs, setRuns] = useState("10000");
    const [seed, setSeed] = useState("");
    const [outputCurrency, setOutputCurrency] = useState("USD");

    const handleExampleChange = (value: string) => {
        setSelectedExample(value);
        setYamlContent(EXAMPLE_MODELS[value as keyof typeof EXAMPLE_MODELS].content);
        setSimulationResult(null);
    };

    const handleReset = () => {
        setYamlContent(EXAMPLE_MODELS[selectedExample as keyof typeof EXAMPLE_MODELS].content);
        setSimulationResult(null);
    };

    const handleSimulate = async () => {
        setIsSimulating(true);
        try {
            const response = await fetch("/api/simulate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    yaml: yamlContent,
                    runs: parseInt(runs) || 10000,
                    seed: seed ? parseInt(seed) : undefined,
                    outputCurrency: outputCurrency
                }),
            });

            const result = await response.json();
            setSimulationResult(result);
        } catch (error) {
            setSimulationResult({
                success: false,
                errors: ["Failed to run simulation: " + (error as Error).message],
            });
        } finally {
            setIsSimulating(false);
        }
    };

    const currentModel = EXAMPLE_MODELS[selectedExample as keyof typeof EXAMPLE_MODELS];

    return (
        <TooltipProvider>
            <div className="container mx-auto px-4 py-8">
                <div className="mb-8">
                    <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">
                        CRML Playground
                    </h1>
                    <p className="text-lg text-muted-foreground">
                        Write CRML models and run Monte Carlo simulations in real-time
                    </p>
                </div>

                {/* Model Explanation Alert */}
                {currentModel.explanation && (
                    <Alert className="mb-6">
                        <Info className="h-4 w-4" />
                        <AlertDescription>
                            <strong>{currentModel.name}:</strong> {currentModel.explanation}
                        </AlertDescription>
                    </Alert>
                )}

                {/* Controls */}
                <Card className="mb-6">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Settings2 className="h-5 w-5" />
                            Simulation Settings
                        </CardTitle>
                        <CardDescription>
                            Configure your Monte Carlo simulation parameters
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-5">
                            <div className="space-y-2">
                                <Label htmlFor="example-select">Example Model</Label>
                                <Select value={selectedExample} onValueChange={handleExampleChange}>
                                    <SelectTrigger id="example-select">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(EXAMPLE_MODELS).map(([key, model]) => (
                                            <SelectItem key={key} value={key}>
                                                {model.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-muted-foreground">
                                    {currentModel.description}
                                </p>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <Label htmlFor="runs">Iterations</Label>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                        </TooltipTrigger>
                                        <TooltipContent className="max-w-xs">
                                            <p className="font-semibold mb-1">How many times to run the simulation</p>
                                            <ul className="text-xs space-y-1">
                                                <li>• 1,000: Quick testing (~1s)</li>
                                                <li>• 10,000: Standard analysis (~3s)</li>
                                                <li>• 50,000+: High-stakes decisions (~15s)</li>
                                            </ul>
                                            <p className="text-xs mt-2">More iterations = more accurate results</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </div>
                                <Input
                                    id="runs"
                                    type="number"
                                    value={runs}
                                    onChange={(e) => setRuns(e.target.value)}
                                    min="100"
                                    max="100000"
                                />
                                <p className="text-xs text-muted-foreground">
                                    {parseInt(runs) < 5000 && "⚡ Fast but less accurate"}
                                    {parseInt(runs) >= 5000 && parseInt(runs) <= 20000 && "✓ Good balance"}
                                    {parseInt(runs) > 20000 && "🎯 High accuracy"}
                                </p>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <Label htmlFor="seed">Random Seed</Label>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                        </TooltipTrigger>
                                        <TooltipContent className="max-w-xs">
                                            <p className="font-semibold mb-1">Makes results reproducible</p>
                                            <p className="text-xs mb-2">Use the same seed to get identical results every time</p>
                                            <ul className="text-xs space-y-1">
                                                <li>• Testing: Use seed (e.g., 42)</li>
                                                <li>• Documentation: Include in reports</li>
                                                <li>• Production: Leave empty</li>
                                            </ul>
                                        </TooltipContent>
                                    </Tooltip>
                                </div>
                                <Input
                                    id="seed"
                                    type="number"
                                    value={seed}
                                    onChange={(e) => setSeed(e.target.value)}
                                    placeholder="Optional"
                                />
                                <p className="text-xs text-muted-foreground">
                                    {seed ? "🔒 Reproducible results" : "🎲 Random each time"}
                                </p>
                            </div>
                            <div className="space-y-2">
                                <div className="flex items-center gap-2">
                                    <Label htmlFor="currency">Output Currency</Label>
                                    <Tooltip>
                                        <TooltipTrigger asChild>
                                            <HelpCircle className="h-4 w-4 text-muted-foreground" />
                                        </TooltipTrigger>
                                        <TooltipContent className="max-w-xs">
                                            <p className="font-semibold mb-1">Display results in your currency</p>
                                            <p className="text-xs mb-2">All values will be converted using static FX rates</p>
                                            <p className="text-xs">Model values (e.g., USD in YAML) are auto-converted</p>
                                        </TooltipContent>
                                    </Tooltip>
                                </div>
                                <Select value={outputCurrency} onValueChange={setOutputCurrency}>
                                    <SelectTrigger id="currency">
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {Object.entries(OUTPUT_CURRENCIES).map(([code, info]) => (
                                            <SelectItem key={code} value={code}>
                                                {info.symbol} {code} - {info.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                                <p className="text-xs text-muted-foreground">
                                    Results shown in {OUTPUT_CURRENCIES[outputCurrency as keyof typeof OUTPUT_CURRENCIES].symbol}
                                </p>
                            </div>
                            <div className="flex items-end gap-2">
                                <Button onClick={handleSimulate} disabled={isSimulating} className="flex-1 gap-2">
                                    <Play className="h-4 w-4" />
                                    {isSimulating ? "Running..." : "Simulate"}
                                </Button>
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Button onClick={handleReset} variant="outline" size="icon">
                                            <RotateCcw className="h-4 w-4" />
                                        </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        Reset to original model
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Main Content */}
                <div className="grid gap-6 lg:grid-cols-2">
                    {/* Editor */}
                    <Card className="flex flex-col">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5" />
                                CRML Model
                            </CardTitle>
                            <CardDescription>
                                Edit the YAML to customize your risk model
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="h-[600px]">
                                <CodeEditor value={yamlContent} onChange={setYamlContent} />
                            </div>
                        </CardContent>
                    </Card>

                    {/* Results */}
                    <div className="h-full">
                        <SimulationResults result={simulationResult} isSimulating={isSimulating} />
                    </div>
                </div>

                {/* Help Section */}
                <Card className="mt-8">
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <CardTitle>Understanding the Parameters</CardTitle>
                            <Button asChild variant="outline" size="sm" className="gap-2">
                                <Link href="/docs/understanding-parameters" target="_blank">
                                    <BookOpen className="h-4 w-4" />
                                    Full Guide
                                </Link>
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-6 md:grid-cols-2">
                            <div>
                                <h3 className="mb-3 font-semibold flex items-center gap-2">
                                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">1</span>
                                    Frequency (Poisson)
                                </h3>
                                <p className="text-sm text-muted-foreground mb-2">
                                    <strong>Lambda (λ):</strong> Probability of event per asset per year
                                </p>
                                <ul className="text-sm space-y-1 text-muted-foreground">
                                    <li>• 0.01 = 1% chance (rare, like zero-days)</li>
                                    <li>• 0.05 = 5% chance (data breaches)</li>
                                    <li>• 0.1 = 10% chance (phishing incidents)</li>
                                    <li>• 0.5 = 50% chance (common attacks)</li>
                                </ul>
                            </div>
                            <div>
                                <h3 className="mb-3 font-semibold flex items-center gap-2">
                                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm">2</span>
                                    Severity (Lognormal)
                                </h3>
                                <p className="text-sm text-muted-foreground mb-2">
                                    <strong>Mu (μ):</strong> Controls median loss amount
                                </p>
                                <ul className="text-sm space-y-1 text-muted-foreground">
                                    <li>• 9.0 → ~$8K (minor incidents)</li>
                                    <li>• 11.5 → ~$100K (data breaches)</li>
                                    <li>• 13.5 → ~$700K (ransomware)</li>
                                    <li>• 16.0 → ~$9M (major breaches)</li>
                                </ul>
                                <p className="text-sm text-muted-foreground mt-3">
                                    <strong>Sigma (σ):</strong> Variability (0.5=low, 1.5=medium, 2.0+=high)
                                </p>
                            </div>
                        </div>
                        <div className="mt-6 p-4 bg-muted rounded-lg">
                            <p className="text-sm">
                                <strong>💡 Tip:</strong> Start with an example model, modify one parameter at a time, and observe how results change.
                                Check the <Link href="/docs/understanding-parameters" className="text-primary hover:underline">full guide</Link> for detailed explanations and data sources.
                            </p>
                        </div>
                        <div className="mt-4 p-4 border border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800 rounded-lg">
                            <p className="text-sm">
                                <strong>ℹ️ About Simulation Methods:</strong> This playground uses <strong>Monte Carlo</strong> simulation (random sampling).
                                Advanced CRML models (like QBER) can specify <strong>MCMC</strong> (Markov Chain Monte Carlo) for full Bayesian inference,
                                but this requires specialized tools like PyMC3 or Stan. The playground approximates these models using Monte Carlo for speed and simplicity.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </TooltipProvider>
    );
}

