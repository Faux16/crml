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
import SimulationResults, { CRSimulationResult } from "@/components/SimulationResults";
import { Play, RotateCcw, FileText, Settings2, HelpCircle, Info, BookOpen } from "lucide-react";
import Link from "next/link";
import { PORTFOLIO_BUNDLE_DOCUMENTED_YAML } from "@/lib/crmlExamples";

const EXAMPLE_MODELS = {
        "portfolio-bundle": {
                name: "Portfolio Bundle (Documented)",
                description: "A full CRML PortfolioBundle with inlined scenarios and catalogs",
                explanation:
                        "This example is a self-contained portfolio bundle: it includes a portfolio, inlined scenarios, and optional catalogs/relationships for portable engine execution and audit-ready exchange.",
                content: PORTFOLIO_BUNDLE_DOCUMENTED_YAML
        },
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

export default function SimulationPage() {
    const [yamlContent, setYamlContent] = useState(EXAMPLE_MODELS["portfolio-bundle"].content);
    const [selectedExample, setSelectedExample] = useState("portfolio-bundle");
    const [simulationResult, setSimulationResult] = useState<CRSimulationResult | null>(null);
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

        const parsedRuns = Number.parseInt(runs, 10);
        const runsValue = Number.isNaN(parsedRuns) ? 10000 : parsedRuns;

        const parsedSeed = seed ? Number.parseInt(seed, 10) : undefined;
        const seedValue = parsedSeed === undefined || Number.isNaN(parsedSeed) ? undefined : parsedSeed;

        try {
            const response = await fetch("/api/simulate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    yaml: yamlContent,
                    runs: runsValue,
                    seed: seedValue,
                    outputCurrency: outputCurrency
                }),
            });

            const result = await response.json();
            setSimulationResult(result as CRSimulationResult);
        } catch (error) {
            setSimulationResult({
                crml_simulation_result: "1.0",
                result: {
                    success: false,
                    errors: ["Failed to run simulation: " + (error as Error).message],
                    warnings: [],
                    engine: { name: "web", version: undefined },
                    run: { runs: runsValue, seed: seedValue },
                    inputs: {},
                    results: { measures: [], artifacts: [] },
                },
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
                        CRML Simulation
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
                                    {(() => {
                                        const runsParsed = Number.parseInt(runs, 10);
                                        const runsForHint = Number.isNaN(runsParsed) ? 0 : runsParsed;
                                        if (runsForHint < 5000) return "⚡ Fast but less accurate";
                                        if (runsForHint <= 20000) return "✓ Good balance";
                                        return "🎯 High accuracy";
                                    })()}
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
                                    {" "}
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
                                    {" "}
                                    Severity (Lognormal)
                                </h3>
                                <p className="text-sm text-muted-foreground mb-2">
                                    <strong>Median:</strong> Typical loss amount (recommended)
                                </p>
                                <ul className="text-sm space-y-1 text-muted-foreground">
                                    <li>• &quot;8 000&quot; → ~$8K (minor incidents)</li>
                                    <li>• &quot;100 000&quot; → ~$100K (data breaches)</li>
                                    <li>• &quot;700 000&quot; → ~$700K (ransomware)</li>
                                    <li>• &quot;9 000 000&quot; → ~$9M (major breaches)</li>
                                </ul>
                                <p className="text-sm text-muted-foreground mt-3">
                                    <strong>Sigma (σ):</strong> Variability (0.5=low, 1.5=medium, 2.0+=high)
                                </p>
                                <p className="text-xs text-muted-foreground mt-2 italic">
                                    💡 Use median instead of mu - it&apos;s more intuitive!
                                </p>
                            </div>
                        </div>
                        <div className="mt-6 p-4 bg-muted rounded-lg">
                            <p className="text-sm">
                                <strong>💡 Tip:</strong>{" "}
                                Start with an example model, modify one parameter at a time, and observe how results change.
                                {" "}Check the{" "}
                                <Link href="/docs/understanding-parameters" className="text-primary hover:underline">full guide</Link>
                                {" "}for detailed explanations and data sources.
                            </p>
                        </div>
                        <div className="mt-4 p-4 border border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800 rounded-lg">
                            <p className="text-sm">
                                <strong>ℹ️ About Simulation Methods:</strong>{" "}
                                This simulation uses <strong>Monte Carlo</strong> simulation (random sampling).
                                Advanced CRML models (like QBER) can specify <strong>MCMC</strong> (Markov Chain Monte Carlo) for full Bayesian inference,
                                but this requires specialized tools like PyMC3 or Stan. This page approximates these models using Monte Carlo for speed and simplicity.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </TooltipProvider>
    );
}

