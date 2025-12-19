"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import CodeEditor from "@/components/CodeEditor";
import ValidationResults, { ValidationResult } from "@/components/ValidationResults";
import SimulationResults, { CRSimulationResult } from "@/components/SimulationResults";
import { PORTFOLIO_BUNDLE_DOCUMENTED_YAML } from "@/lib/crmlExamples";
import {
    Download,
    FileText,
    HelpCircle,
    Info,
    Play,
    RotateCcw,
    Settings2,
    Upload,
} from "lucide-react";

type TabKey = "validate" | "simulate";

interface Example {
    id: string;
    filename: string;
    name: string;
    description: string;
    content: string;
}

const DEFAULT_YAML = PORTFOLIO_BUNDLE_DOCUMENTED_YAML;

const OUTPUT_CURRENCIES = {
    USD: { symbol: "$", name: "US Dollar" },
    EUR: { symbol: "€", name: "Euro" },
    GBP: { symbol: "£", name: "British Pound" },
    CHF: { symbol: "Fr", name: "Swiss Franc" },
    JPY: { symbol: "¥", name: "Japanese Yen" },
    CNY: { symbol: "CN¥", name: "Chinese Yuan" },
    CAD: { symbol: "C$", name: "Canadian Dollar" },
    AUD: { symbol: "A$", name: "Australian Dollar" },
} as const;

export default function PlaygroundClient() {
    const searchParams = useSearchParams();

    const initialTab = (searchParams.get("tab") as TabKey | null) ?? "validate";
    const exampleId = searchParams.get("example");

    const [activeTab, setActiveTab] = useState<TabKey>(initialTab);
    const [yamlContent, setYamlContent] = useState(DEFAULT_YAML);
    const [initialYamlContent, setInitialYamlContent] = useState(DEFAULT_YAML);

    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [isValidating, setIsValidating] = useState(false);

    const [simulationResult, setSimulationResult] = useState<CRSimulationResult | null>(null);
    const [isSimulating, setIsSimulating] = useState(false);
    const [runs, setRuns] = useState("10000");
    const [seed, setSeed] = useState("");
    const [outputCurrency, setOutputCurrency] = useState<keyof typeof OUTPUT_CURRENCIES>("USD");

    const [loadedExample, setLoadedExample] = useState<Pick<Example, "id" | "name" | "description"> | null>(null);

    useEffect(() => {
        setActiveTab(initialTab);
    }, [initialTab]);

    useEffect(() => {
        const loadExample = async () => {
            if (!exampleId) return;

            try {
                const response = await fetch("/api/examples");
                const data = await response.json();
                const examples: Example[] = data.examples || [];
                const example = examples.find((e) => e.id === exampleId);

                if (!example) return;

                setYamlContent(example.content);
                setInitialYamlContent(example.content);
                setLoadedExample({ id: example.id, name: example.name, description: example.description });

                setValidationResult(null);
                setSimulationResult(null);
            } catch {
                // Ignore example-loading failures; user can still paste YAML manually.
            }
        };

        void loadExample();
    }, [exampleId]);

    const handleValidate = async () => {
        setIsValidating(true);
        try {
            const response = await fetch("/api/validate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ yaml: yamlContent }),
            });

            const result = await response.json();
            setValidationResult(result);
        } catch (error) {
            setValidationResult({
                valid: false,
                errors: ["Failed to validate: " + (error as Error).message],
            });
        } finally {
            setIsValidating(false);
        }
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
                    runs: Number.parseInt(runs, 10) || 10000,
                    seed: seed ? Number.parseInt(seed, 10) : undefined,
                    outputCurrency,
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
                    run: { runs: Number.parseInt(runs, 10) || 10000, seed: seed ? Number.parseInt(seed, 10) : undefined },
                    inputs: {},
                    results: { measures: [], artifacts: [] },
                },
            });
        } finally {
            setIsSimulating(false);
        }
    };

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const content = await file.text();
        setYamlContent(content);
        setInitialYamlContent(content);
        setLoadedExample(null);
        setValidationResult(null);
        setSimulationResult(null);
    };

    const handleDownload = () => {
        const blob = new Blob([yamlContent], { type: "text/yaml" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "model.yaml";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    const handleReset = () => {
        setYamlContent(initialYamlContent);
        setValidationResult(null);
        setSimulationResult(null);
    };

    const exampleBanner = useMemo(() => {
        if (!loadedExample) return null;
        return (
            <Alert className="mb-6">
                <Info className="h-4 w-4" />
                <AlertDescription>
                    <strong>{loadedExample.name}:</strong> {loadedExample.description}
                </AlertDescription>
            </Alert>
        );
    }, [loadedExample]);

    return (
        <TooltipProvider>
            <div className="container mx-auto px-4 py-8">
                <div className="mb-8">
                    <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">CRML Playground</h1>
                    <p className="text-lg text-muted-foreground">Validate and simulate CRML models in one place</p>
                </div>

                {exampleBanner}

                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabKey)}>
                    <TabsList className="mb-6">
                        <TabsTrigger value="validate">Validate</TabsTrigger>
                        <TabsTrigger value="simulate">Simulate</TabsTrigger>
                    </TabsList>

                    <TabsContent value="validate" className="m-0">
                        <div className="mb-6 flex flex-wrap gap-3">
                            <Button onClick={handleValidate} disabled={isValidating} className="gap-2">
                                <Play className="h-4 w-4" />
                                {isValidating ? "Validating..." : "Validate"}
                            </Button>
                            <Button variant="outline" className="gap-2" asChild>
                                <label htmlFor="file-upload" className="cursor-pointer">
                                    <Upload className="h-4 w-4" />
                                    Upload File
                                    <input
                                        id="file-upload"
                                        type="file"
                                        accept=".yaml,.yml"
                                        className="hidden"
                                        onChange={handleFileUpload}
                                    />
                                </label>
                            </Button>
                            <Button variant="outline" onClick={handleDownload} className="gap-2">
                                <Download className="h-4 w-4" />
                                Download
                            </Button>
                        </div>
                    </TabsContent>

                    <TabsContent value="simulate" className="m-0">
                        <Card className="mb-6">
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2">
                                    <Settings2 className="h-5 w-5" />
                                    Simulation Settings
                                </CardTitle>
                                <CardDescription>Configure your Monte Carlo simulation parameters</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="grid gap-4 md:grid-cols-4">
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
                                                        <li>• 1,000: Quick testing</li>
                                                        <li>• 10,000: Standard analysis</li>
                                                        <li>• 50,000+: Higher accuracy</li>
                                                    </ul>
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
                                                    <p className="text-xs">Use the same seed to get identical results</p>
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
                                    </div>
                                    <div className="space-y-2">
                                        <div className="flex items-center gap-2">
                                            <Label htmlFor="currency">Output Currency</Label>
                                        </div>
                                        <Select
                                            value={outputCurrency}
                                            onValueChange={(v) => setOutputCurrency(v as keyof typeof OUTPUT_CURRENCIES)}
                                        >
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
                                    </div>
                                    <div className="flex items-end gap-2">
                                        <Button onClick={handleSimulate} disabled={isSimulating} className="flex-1 gap-2">
                                            <Play className="h-4 w-4" />
                                            {isSimulating ? "Running..." : "Simulate"}
                                        </Button>
                                        <Button onClick={handleReset} variant="outline" size="icon" aria-label="Reset YAML">
                                            <RotateCcw className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                </Tabs>

                <div className="grid gap-6 lg:grid-cols-2">
                    <Card className="flex flex-col">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <FileText className="h-5 w-5" />
                                YAML Editor
                            </CardTitle>
                            <CardDescription>Edit your CRML model or upload a YAML file</CardDescription>
                        </CardHeader>
                        <CardContent className="flex-1">
                            <div className="h-[600px]">
                                <CodeEditor value={yamlContent} onChange={setYamlContent} />
                            </div>
                        </CardContent>
                    </Card>

                    <div className="h-full">
                        {activeTab === "validate" ? (
                            <ValidationResults result={validationResult} isValidating={isValidating} />
                        ) : (
                            <SimulationResults result={simulationResult} isSimulating={isSimulating} />
                        )}
                    </div>
                </div>
            </div>
        </TooltipProvider>
    );
}
