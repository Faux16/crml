"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import CodeEditor from "@/components/CodeEditor";
import ValidationResults, { ValidationResult } from "@/components/ValidationResults";
import SimulationResults, { CRSimulationResult } from "@/components/SimulationResults";
import { PORTFOLIO_BUNDLE_DOCUMENTED_YAML } from "@/lib/crmlExamples";
import { applyInclusionTogglesToYaml, tryDetectCrmlDocKindFromYaml, tryExtractInclusionsFromYaml } from "@/lib/crmlInclusions";
import { checkScenarioCompatibility, detectMissingCatalogs } from "@/lib/crmlValidationHelpers";
import yaml from "js-yaml";
import {
    ChevronDown,
    Download,
    FileText,
    HelpCircle,
    Info,
    Play,
    RotateCcw,
    Settings2,
    Upload,
} from "lucide-react";

type TabKey = "validate" | "compose" | "simulate";

interface Example {
    id: string;
    filename: string;
    name: string;
    description: string;
    docKind?:
    | "portfolio_bundle"
    | "scenario"
    | "portfolio"
    | "attack_catalog"
    | "control_catalog"
    | "control_relationships"
    | "attack_control_relationships"
    | "assessment"
    | "fx_config"
    | "unknown";
    content: string;
}

function slugifyId(input: string): string {
    const trimmed = input.trim().toLowerCase();
    const withoutExt = trimmed.replaceAll(/\.[a-z0-9]+$/gi, "");
    const hyphenated = withoutExt.replaceAll(/[^a-z0-9]+/g, "-");
    const cleaned = hyphenated.replaceAll(/(^-+)|(-+$)/g, "");
    return (cleaned.slice(0, 48) || "item").trim();
}

function parseYamlRootRecord(content: string, label: string, errors: string[]): Record<string, unknown> | null {
    try {
        const parsed = yaml.load(content);
        if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
            errors.push(`Invalid YAML root for ${label} (must be a mapping/object).`);
            return null;
        }
        return parsed as Record<string, unknown>;
    } catch (e) {
        errors.push(`Failed to parse YAML for ${label}: ${(e as Error).message}`);
        return null;
    }
}

function packKindLabel(kind: Example["docKind"]): string {
    switch (kind) {
        case "control_catalog":
            return "Control catalog";
        case "assessment":
            return "Assessment";
        case "control_relationships":
            return "Control <> Control mappings";
        case "attack_catalog":
            return "Attack catalog";
        case "attack_control_relationships":
            return "Attack <> Control mappings";
        default:
            return "Pack";
    }
}

function buildPortfolioBundleYaml(params: {
    selectedPortfolio: Example | undefined;
    selectedScenarios: Example[];
    selectedPacks: Example[];
}): { yaml: string; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];
    const { selectedPortfolio, selectedScenarios, selectedPacks } = params;

    const packFilenames = (packDocs: Array<{ example: Example; doc: Record<string, unknown> }>, kind: Example["docKind"]) =>
        packDocs.filter((p) => p.example.docKind === kind).map((p) => p.example.filename);

    const packDocsForKind = (packDocs: Array<{ example: Example; doc: Record<string, unknown> }>, kind: Example["docKind"]) =>
        packDocs.filter((p) => p.example.docKind === kind).map((p) => p.doc);

    const rewritePortfolioForBundle = (
        portfolioDoc: Record<string, unknown>,
        scenarioDocs: Array<{ example: Example; doc: Record<string, unknown> }>,
        packDocs: Array<{ example: Example; doc: Record<string, unknown> }>,
    ) => {
        const portfolioBody = portfolioDoc["portfolio"];
        if (typeof portfolioBody !== "object" || portfolioBody === null || Array.isArray(portfolioBody)) return;

        const portfolioBodyRec = portfolioBody as Record<string, unknown>;

        const semantics = portfolioBodyRec["semantics"];
        if (typeof semantics === "object" && semantics !== null && !Array.isArray(semantics)) {
            const constraints = (semantics as Record<string, unknown>)["constraints"];
            if (typeof constraints === "object" && constraints !== null && !Array.isArray(constraints)) {
                (constraints as Record<string, unknown>)["require_paths_exist"] = false;
                (constraints as Record<string, unknown>)["validate_scenarios"] = false;
            }
        }

        // Rewrite portfolio.scenarios to match selection (path is traceability in bundle).
        portfolioBodyRec["scenarios"] = scenarioDocs.map((s) => ({
            id: slugifyId(s.example.filename),
            path: s.example.filename,
        }));

        // If packs are selected, set portfolio references to traceability paths.
        const controlCatalogPaths = packFilenames(packDocs, "control_catalog");
        const assessmentPaths = packFilenames(packDocs, "assessment");
        const controlRelPaths = packFilenames(packDocs, "control_relationships");
        const attackCatalogPaths = packFilenames(packDocs, "attack_catalog");
        const attackControlRelPaths = packFilenames(packDocs, "attack_control_relationships");

        if (controlCatalogPaths.length > 0) portfolioBodyRec["control_catalogs"] = controlCatalogPaths;
        if (assessmentPaths.length > 0) portfolioBodyRec["assessments"] = assessmentPaths;
        if (controlRelPaths.length > 0) portfolioBodyRec["control_relationships"] = controlRelPaths;
        if (attackCatalogPaths.length > 0) portfolioBodyRec["attack_catalogs"] = attackCatalogPaths;
        if (attackControlRelPaths.length > 0) portfolioBodyRec["attack_control_relationships"] = attackControlRelPaths;
    };

    const buildBundleObject = (
        portfolioDoc: Record<string, unknown>,
        scenarioDocs: Array<{ example: Example; doc: Record<string, unknown> }>,
        packDocs: Array<{ example: Example; doc: Record<string, unknown> }>,
    ): Record<string, unknown> => {
        const bundle: Record<string, unknown> = {
            crml_portfolio_bundle: "1.0",
            portfolio_bundle: {
                portfolio: portfolioDoc,
                scenarios: scenarioDocs.map((s) => ({
                    id: slugifyId(s.example.filename),
                    weight: 1,
                    source_path: `examples/${s.example.filename}`,
                    scenario: s.doc,
                })),
            },
        };

        const bundleBody = bundle["portfolio_bundle"] as Record<string, unknown>;

        const includePacks = (kind: Example["docKind"], field: string) => {
            const docs = packDocsForKind(packDocs, kind);
            if (docs.length > 0) bundleBody[field] = docs;
        };

        includePacks("control_catalog", "control_catalogs");
        includePacks("assessment", "assessments");
        includePacks("control_relationships", "control_relationships");
        includePacks("attack_catalog", "attack_catalogs");
        includePacks("attack_control_relationships", "attack_control_relationships");

        return bundle;
    };

    if (!selectedPortfolio) {
        errors.push("Please select a portfolio to compose a bundle.");
    }
    if (selectedScenarios.length === 0) {
        errors.push("Please select at least one scenario to include in the bundle.");
    }

    // Check scenario compatibility and add warnings
    if (selectedScenarios.length > 0) {
        const compatibilityWarnings = checkScenarioCompatibility(selectedScenarios);
        warnings.push(...compatibilityWarnings);

        const catalogWarnings = detectMissingCatalogs(selectedScenarios, selectedPacks);
        warnings.push(...catalogWarnings);
    }

    const portfolioDoc = selectedPortfolio ? parseYamlRootRecord(selectedPortfolio.content, "portfolio", errors) : null;

    const scenarioDocs = selectedScenarios
        .map((s) => ({ example: s, doc: parseYamlRootRecord(s.content, `scenario ${s.filename}`, errors) }))
        .filter((x): x is { example: Example; doc: Record<string, unknown> } => !!x.doc);

    const packDocs = selectedPacks
        .map((p) => ({ example: p, doc: parseYamlRootRecord(p.content, `pack ${p.filename}`, errors) }))
        .filter((x): x is { example: Example; doc: Record<string, unknown> } => !!x.doc);

    if (!portfolioDoc || scenarioDocs.length === 0) {
        return { yaml: "", errors, warnings };
    }

    rewritePortfolioForBundle(portfolioDoc, scenarioDocs, packDocs);

    const bundle = buildBundleObject(portfolioDoc, scenarioDocs, packDocs);
    const yamlOut = yaml.dump(bundle, { noRefs: true, lineWidth: 120 });
    return { yaml: yamlOut, errors, warnings };
}

function ComposeTab(props: {
    readonly examplesLoading: boolean;
    readonly examplesError: string | null;
    readonly portfolioExamples: Example[];
    readonly scenarioExamples: Example[];
    readonly packExamples: Example[];
    readonly composePortfolioId: string;
    readonly setComposePortfolioId: (id: string) => void;
    readonly composeScenarioIds: Set<string>;
    readonly setComposeScenarioIds: (updater: (prev: Set<string>) => Set<string>) => void;
    readonly composePackIds: Set<string>;
    readonly setComposePackIds: (updater: (prev: Set<string>) => Set<string>) => void;
    readonly composeBundle: { yaml: string; errors: string[]; warnings: string[] };
    readonly composeValidationResult: ValidationResult | null;
    readonly isComposeValidating: boolean;
    readonly toggleIdInSet: (prev: Set<string>, id: string) => Set<string>;
    readonly onSendToSimulation: () => void;
    readonly onCopy: () => void;
    readonly onDownload: () => void;
}) {
    const {
        examplesLoading,
        examplesError,
        portfolioExamples,
        scenarioExamples,
        packExamples,
        composePortfolioId,
        setComposePortfolioId,
        composeScenarioIds,
        setComposeScenarioIds,
        composePackIds,
        setComposePackIds,
        composeBundle,
        composeValidationResult,
        isComposeValidating,
        toggleIdInSet,
        onSendToSimulation,
        onCopy,
        onDownload,
    } = props;

    const canSendToSimulation =
        composeBundle.yaml.length > 0 &&
        composeBundle.errors.length === 0 &&
        !isComposeValidating &&
        composeValidationResult?.valid === true;

    const sortByName = useCallback(
        (a: Example, b: Example) => a.name.localeCompare(b.name, undefined, { sensitivity: "base" }),
        [],
    );

    const sortedPortfolioExamples = useMemo(() => [...portfolioExamples].sort(sortByName), [portfolioExamples, sortByName]);
    const sortedScenarioExamples = useMemo(() => [...scenarioExamples].sort(sortByName), [scenarioExamples, sortByName]);
    const sortedPackExamples = useMemo(() => [...packExamples].sort(sortByName), [packExamples, sortByName]);

    const catalogPacks = useMemo(
        () => sortedPackExamples.filter((p) => p.docKind === "control_catalog" || p.docKind === "attack_catalog"),
        [sortedPackExamples],
    );
    const assessmentPacks = useMemo(() => sortedPackExamples.filter((p) => p.docKind === "assessment"), [sortedPackExamples]);
    const mappingPacks = useMemo(
        () => sortedPackExamples.filter((p) => p.docKind === "control_relationships" || p.docKind === "attack_control_relationships"),
        [sortedPackExamples],
    );

    const hasAnyPacks = catalogPacks.length > 0 || assessmentPacks.length > 0 || mappingPacks.length > 0;

    const renderPackButton = (p: Example) => {
        const selected = composePackIds.has(p.id);
        const kindLabel = packKindLabel(p.docKind);
        return (
            <button
                key={p.id}
                type="button"
                onClick={() => setComposePackIds((prev) => toggleIdInSet(prev, p.id))}
                className={cn(
                    "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                    selected ? "bg-background" : "bg-muted text-muted-foreground",
                )}
            >
                <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-medium">{p.name}</span>
                    <span className="shrink-0 text-xs">{kindLabel}</span>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{p.description}</p>
            </button>
        );
    };

    return (
        <div className="grid gap-6 lg:grid-cols-2 lg:min-h-[calc(100vh-220px)]">
            <Card className="flex flex-col min-h-0">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Settings2 className="h-5 w-5" />
                        Compose Portfolio Bundle
                    </CardTitle>
                    <CardDescription>
                        Choose what your organization looks like and what could happen to it — we’ll assemble everything into one model you can run.
                    </CardDescription>
                </CardHeader>
                <CardContent className="flex flex-1 min-h-0 flex-col gap-6">
                    {examplesError ? (
                        <Alert>
                            <Info className="h-4 w-4" />
                            <AlertDescription>Failed to load examples: {examplesError}</AlertDescription>
                        </Alert>
                    ) : null}

                    <div className="flex min-h-0 flex-1 flex-col gap-6">
                        <div className="space-y-2">
                            <Label>Portfolio</Label>
                            <Select
                                value={composePortfolioId}
                                onValueChange={(v) => setComposePortfolioId(v)}
                                disabled={examplesLoading || portfolioExamples.length === 0}
                            >
                                <SelectTrigger>
                                    <SelectValue placeholder={examplesLoading ? "Loading..." : "Select a portfolio"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {sortedPortfolioExamples.map((p) => (
                                        <SelectItem key={p.id} value={p.id}>
                                            {p.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                            {sortedPortfolioExamples.length === 0 && !examplesLoading ? (
                                <p className="text-sm text-muted-foreground">No portfolio examples found.</p>
                            ) : null}
                        </div>

                        <div className="flex min-h-0 flex-1 flex-col gap-2">
                            <div className="flex items-center justify-between">
                                <Label>Scenarios</Label>
                                <p className="text-xs text-muted-foreground">{composeScenarioIds.size} selected</p>
                            </div>
                            <ScrollArea className="min-h-0 flex-1 rounded-md border p-2">
                                <div className="space-y-2">
                                    {sortedScenarioExamples.length === 0 && !examplesLoading ? (
                                        <p className="text-sm text-muted-foreground">No scenario examples found.</p>
                                    ) : (
                                        sortedScenarioExamples.map((s) => {
                                            const selected = composeScenarioIds.has(s.id);
                                            return (
                                                <button
                                                    key={s.id}
                                                    type="button"
                                                    onClick={() => setComposeScenarioIds((prev) => toggleIdInSet(prev, s.id))}
                                                    className={cn(
                                                        "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors",
                                                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                                                        selected ? "bg-background" : "bg-muted text-muted-foreground",
                                                    )}
                                                >
                                                    <div className="flex items-center justify-between gap-2">
                                                        <span className="truncate font-medium">{s.name}</span>
                                                        <span className="shrink-0 text-xs">{selected ? "Selected" : ""}</span>
                                                    </div>
                                                    <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">{s.description}</p>
                                                </button>
                                            );
                                        })
                                    )}
                                </div>
                            </ScrollArea>
                        </div>

                        <div className="flex min-h-0 flex-1 flex-col gap-2">
                            <div className="flex items-center justify-between">
                                <Label>Optional catalogs and mappings</Label>
                                <p className="text-xs text-muted-foreground">{composePackIds.size} selected</p>
                            </div>
                            <ScrollArea className="min-h-0 flex-1 rounded-md border p-2">
                                <div className="space-y-2">
                                    {!hasAnyPacks && !examplesLoading ? (
                                        <p className="text-sm text-muted-foreground">No catalogs or mappings found.</p>
                                    ) : (
                                        <>
                                            {catalogPacks.length > 0 ? (
                                                <div className="space-y-2">
                                                    <p className="text-xs font-medium text-muted-foreground">Catalogs</p>
                                                    {catalogPacks.map(renderPackButton)}
                                                </div>
                                            ) : null}
                                            {assessmentPacks.length > 0 ? (
                                                <div className="space-y-2 pt-2">
                                                    <p className="text-xs font-medium text-muted-foreground">Assessments</p>
                                                    {assessmentPacks.map(renderPackButton)}
                                                </div>
                                            ) : null}
                                            {mappingPacks.length > 0 ? (
                                                <div className="space-y-2 pt-2">
                                                    <p className="text-xs font-medium text-muted-foreground">Mappings</p>
                                                    {mappingPacks.map(renderPackButton)}
                                                </div>
                                            ) : null}
                                        </>
                                    )}
                                </div>
                            </ScrollArea>
                        </div>
                    </div>
                </CardContent>
            </Card>

            <Card className="flex flex-col min-h-0">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="h-5 w-5" />
                        Generated Bundle
                    </CardTitle>
                    <CardDescription>Review the generated YAML, then load it into the editor to validate/simulate.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {composeBundle.errors.length > 0 ? (
                        <Alert variant="destructive">
                            <Info className="h-4 w-4" />
                            <AlertDescription>
                                <div className="space-y-1">
                                    {composeBundle.errors.map((error, i) => (
                                        <div key={i}>• {error}</div>
                                    ))}
                                </div>
                            </AlertDescription>
                        </Alert>
                    ) : null}

                    {composeBundle.warnings.length > 0 ? (
                        <Alert>
                            <Info className="h-4 w-4" />
                            <AlertDescription>
                                <div className="font-medium mb-1">Warnings:</div>
                                <div className="space-y-1 text-sm">
                                    {composeBundle.warnings.map((warning, i) => (
                                        <div key={i}>• {warning}</div>
                                    ))}
                                </div>
                            </AlertDescription>
                        </Alert>
                    ) : null}

                    <div className="h-[420px]">
                        <CodeEditor
                            value={composeBundle.yaml || "# Select a portfolio + scenario(s) to generate a bundle."}
                            onChange={() => { }}
                            readOnly
                        />
                    </div>

                    <div className="flex flex-wrap gap-2">
                        <Button onClick={onSendToSimulation} disabled={!canSendToSimulation} className="gap-2">
                            <Play className="h-4 w-4" />
                            Send to Simulation
                        </Button>
                        <Button variant="outline" onClick={onCopy} disabled={!composeBundle.yaml} className="gap-2">
                            Copy
                        </Button>
                        <Button variant="outline" onClick={onDownload} disabled={!composeBundle.yaml} className="gap-2">
                            <Download className="h-4 w-4" />
                            Download
                        </Button>
                    </div>

                    <div className="pt-2">
                        <ValidationResults result={composeValidationResult} isValidating={isComposeValidating} />
                    </div>
                </CardContent>
            </Card>
        </div>
    );
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

    const rawTab = searchParams.get("tab");
    const initialTab: TabKey = rawTab === "simulate" || rawTab === "compose" || rawTab === "validate" ? rawTab : "validate";
    const exampleId = searchParams.get("example");

    const [activeTab, setActiveTab] = useState<TabKey>(initialTab);
    const [yamlContent, setYamlContent] = useState(DEFAULT_YAML);
    const [initialYamlContent, setInitialYamlContent] = useState(DEFAULT_YAML);

    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [isValidating, setIsValidating] = useState(false);

    const [composeValidationResult, setComposeValidationResult] = useState<ValidationResult | null>(null);
    const [isComposeValidating, setIsComposeValidating] = useState(false);

    const composeValidationSeq = useRef(0);

    const [simulationResult, setSimulationResult] = useState<CRSimulationResult | null>(null);
    const [isSimulating, setIsSimulating] = useState(false);
    const [runs, setRuns] = useState("50000");
    const [seed, setSeed] = useState("");
    const [outputCurrency, setOutputCurrency] = useState<keyof typeof OUTPUT_CURRENCIES>("USD");

    const [disabledControlIds, setDisabledControlIds] = useState<Set<string>>(() => new Set());
    const [disabledAttackIds, setDisabledAttackIds] = useState<Set<string>>(() => new Set());

    const [loadedExample, setLoadedExample] = useState<Pick<Example, "id" | "name" | "description"> | null>(null);

    const [examples, setExamples] = useState<Example[]>([]);
    const [examplesLoading, setExamplesLoading] = useState(false);
    const [examplesError, setExamplesError] = useState<string | null>(null);

    const [composePortfolioId, setComposePortfolioId] = useState<string>("");
    const [composeScenarioIds, setComposeScenarioIds] = useState<Set<string>>(() => new Set());
    const [composePackIds, setComposePackIds] = useState<Set<string>>(() => new Set());

    const [pendingNavigateToSimulate, setPendingNavigateToSimulate] = useState(false);

    useEffect(() => {
        setActiveTab(initialTab);
    }, [initialTab]);

    useEffect(() => {
        const loadExamples = async () => {
            setExamplesLoading(true);
            setExamplesError(null);
            try {
                const response = await fetch("/api/examples");
                const data = await response.json();
                const fetched: Example[] = data.examples || [];
                setExamples(fetched);
            } catch (error) {
                setExamplesError((error as Error).message);
                setExamples([]);
            } finally {
                setExamplesLoading(false);
            }
        };

        void loadExamples();
    }, []);

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

    const docKind = useMemo(() => tryDetectCrmlDocKindFromYaml(yamlContent), [yamlContent]);
    const canSimulate = docKind === "portfolio_bundle";

    useEffect(() => {
        // Guard against deep links like ?tab=simulate when the loaded YAML can't be simulated.
        if (!canSimulate && activeTab === "simulate") {
            setActiveTab("validate");
        }
    }, [activeTab, canSimulate]);

    const inclusions = useMemo(() => tryExtractInclusionsFromYaml(yamlContent), [yamlContent]);

    useEffect(() => {
        // Reset toggles when the loaded document type changes.
        setDisabledControlIds(new Set());
        setDisabledAttackIds(new Set());
    }, [inclusions?.docKind]);

    useEffect(() => {
        // Keep disabled-id sets consistent with the currently loaded YAML.
        // (Prevents negative counts if the user switches to a bundle with fewer/no ids.)
        if (!inclusions) {
            setDisabledControlIds(new Set());
            setDisabledAttackIds(new Set());
            return;
        }

        setDisabledControlIds((prev) => {
            if (prev.size === 0) return prev;
            const allowed = new Set(inclusions.controlIds);
            const next = new Set(Array.from(prev).filter((id) => allowed.has(id)));
            return next.size === prev.size ? prev : next;
        });

        setDisabledAttackIds((prev) => {
            if (prev.size === 0) return prev;
            const allowed = new Set(inclusions.attackIds);
            const next = new Set(Array.from(prev).filter((id) => allowed.has(id)));
            return next.size === prev.size ? prev : next;
        });
    }, [inclusions]);

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
            const yamlForSimulation = applyInclusionTogglesToYaml(yamlContent, disabledControlIds, disabledAttackIds);
            const response = await fetch("/api/simulate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    yaml: yamlForSimulation,
                    runs: Number.parseInt(runs, 10) || 50000,
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
                    run: { runs: Number.parseInt(runs, 10) || 50000, seed: seed ? Number.parseInt(seed, 10) : undefined },
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

    const handleCopyText = async (text: string) => {
        try {
            await navigator.clipboard.writeText(text);
        } catch {
            // Ignore clipboard failures.
        }
    };

    const handleDownloadText = (text: string, filename: string) => {
        const blob = new Blob([text], { type: "text/yaml" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    const toggleIdInSetGeneric = useCallback((prev: Set<string>, id: string) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
    }, []);

    const portfolioExamples = useMemo(() => examples.filter((e) => e.docKind === "portfolio"), [examples]);
    const scenarioExamples = useMemo(() => examples.filter((e) => e.docKind === "scenario"), [examples]);
    const packExamples = useMemo(() => {
        const allowed = new Set([
            "control_catalog",
            "assessment",
            "control_relationships",
            "attack_catalog",
            "attack_control_relationships",
        ]);
        return examples.filter((e) => e.docKind && allowed.has(e.docKind));
    }, [examples]);

    useEffect(() => {
        if (portfolioExamples.length > 0 && !composePortfolioId) {
            setComposePortfolioId(portfolioExamples[0].id);
        }
        // Intentionally do not auto-select packs.
    }, [composePortfolioId, composeScenarioIds.size, portfolioExamples, scenarioExamples]);

    const composeBundle = useMemo(() => {
        const selectedPortfolio = examples.find((e) => e.id === composePortfolioId);
        const selectedScenarios = examples.filter((e) => composeScenarioIds.has(e.id));
        const selectedPacks = examples.filter((e) => composePackIds.has(e.id));
        return buildPortfolioBundleYaml({ selectedPortfolio, selectedScenarios, selectedPacks });
    }, [composePackIds, composePortfolioId, composeScenarioIds, examples]);

    useEffect(() => {
        // Validate the generated bundle directly in the Compose tab.
        const seq = ++composeValidationSeq.current;

        const validateComposed = async () => {
            if (!composeBundle.yaml) {
                if (seq === composeValidationSeq.current) {
                    setComposeValidationResult(null);
                    setIsComposeValidating(false);
                }
                return;
            }

            if (seq === composeValidationSeq.current) {
                setComposeValidationResult(null);
                setIsComposeValidating(true);
            }
            try {
                const response = await fetch("/api/validate", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ yaml: composeBundle.yaml }),
                });

                const result = await response.json();
                if (seq === composeValidationSeq.current) {
                    setComposeValidationResult(result);
                }
            } catch (error) {
                if (seq === composeValidationSeq.current) {
                    setComposeValidationResult({
                        valid: false,
                        errors: ["Failed to validate: " + (error as Error).message],
                    });
                }
            } finally {
                if (seq === composeValidationSeq.current) {
                    setIsComposeValidating(false);
                }
            }
        };

        // Reset while selection errors exist (but warnings are ok).
        if (composeBundle.errors.length > 0) {
            setComposeValidationResult(null);
            setIsComposeValidating(false);
            return;
        }

        void validateComposed();
    }, [composeBundle.errors.length, composeBundle.yaml]);

    useEffect(() => {
        if (!pendingNavigateToSimulate) return;
        if (!canSimulate) return;
        setActiveTab("simulate");
        setPendingNavigateToSimulate(false);
    }, [canSimulate, pendingNavigateToSimulate]);

    type InclusionKind = "control" | "attack";

    const toggleIdInSet = useCallback((prev: Set<string>, id: string) => {
        const next = new Set(prev);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
    }, []);

    const handleInclusionToggle = useCallback((event: React.MouseEvent<HTMLButtonElement>) => {
        const id = event.currentTarget.dataset.id;
        const kind = event.currentTarget.dataset.kind as InclusionKind | undefined;
        if (!id || !kind) return;

        if (kind === "control") {
            setDisabledControlIds((prev) => toggleIdInSet(prev, id));
        } else {
            setDisabledAttackIds((prev) => toggleIdInSet(prev, id));
        }
    }, [toggleIdInSet]);

    const toggleCard = useMemo(() => {
        if (!canSimulate) return null;
        if (activeTab !== "simulate") return null;
        if (!inclusions) return null;

        const makeToggle = (kind: InclusionKind, id: string, enabled: boolean) => (
            <button
                key={id}
                type="button"
                aria-pressed={enabled}
                data-kind={kind}
                data-id={id}
                onClick={handleInclusionToggle}
                className={cn(
                    "flex w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-left text-sm transition-colors",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                    enabled ? "bg-background" : "bg-muted text-muted-foreground",
                )}
            >
                <span className="truncate">{id}</span>
                <span className="shrink-0 text-xs">{enabled ? "On" : "Off"}</span>
            </button>
        );

        return (
            <Card className="mb-6">
                <details className="group">
                    <summary
                        className={cn(
                            "cursor-pointer list-none rounded-lg",
                            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
                            "[&::-webkit-details-marker]:hidden",
                        )}
                    >
                        <CardHeader>
                            <div className="flex items-start justify-between gap-4">
                                <div className="space-y-1">
                                    <CardTitle className="text-base">Included attacks & controls</CardTitle>
                                    <CardDescription>
                                        Use these toggles to turn items on/off for the simulation — your editor content stays the same.
                                    </CardDescription>
                                </div>
                                <ChevronDown className="mt-1 h-4 w-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
                            </div>
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
                                <span>
                                    Controls: {inclusions.controlIds.length - disabledControlIds.size}/{inclusions.controlIds.length} on
                                </span>
                                <span>
                                    Attacks: {inclusions.attackIds.length - disabledAttackIds.size}/{inclusions.attackIds.length} on
                                </span>
                            </div>
                        </CardHeader>
                    </summary>

                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm font-medium">Controls</p>
                                    <p className="text-xs text-muted-foreground">
                                        {inclusions.controlIds.length - disabledControlIds.size}/{inclusions.controlIds.length} on
                                    </p>
                                </div>
                                <ScrollArea className="h-48 rounded-md border p-2">
                                    <div className="space-y-2">
                                        {inclusions.controlIds.length === 0 ? (
                                            <p className="text-sm text-muted-foreground">No controls found.</p>
                                        ) : (
                                            inclusions.controlIds.map((id) => {
                                                const enabled = !disabledControlIds.has(id);
                                                return makeToggle("control", id, enabled);
                                            })
                                        )}
                                    </div>
                                </ScrollArea>
                            </div>

                            <div className="space-y-2">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm font-medium">Attacks</p>
                                    <p className="text-xs text-muted-foreground">
                                        {inclusions.attackIds.length - disabledAttackIds.size}/{inclusions.attackIds.length} on
                                    </p>
                                </div>
                                <ScrollArea className="h-48 rounded-md border p-2">
                                    <div className="space-y-2">
                                        {inclusions.attackIds.length === 0 ? (
                                            <p className="text-sm text-muted-foreground">No attacks found.</p>
                                        ) : (
                                            inclusions.attackIds.map((id) => {
                                                const enabled = !disabledAttackIds.has(id);
                                                return makeToggle("attack", id, enabled);
                                            })
                                        )}
                                    </div>
                                </ScrollArea>
                            </div>
                        </div>
                    </CardContent>
                </details>
            </Card>
        );
    }, [activeTab, canSimulate, disabledAttackIds, disabledControlIds, handleInclusionToggle, inclusions]);

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
                    <p className="text-lg text-muted-foreground">Validate, compose and simulate CRML models in one place</p>
                </div>

                {exampleBanner}

                <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabKey)}>
                    <TabsList className="mb-6">
                        <TabsTrigger value="validate">Validate</TabsTrigger>
                        <TabsTrigger value="compose">Compose</TabsTrigger>
                        {canSimulate ? <TabsTrigger value="simulate">Simulate</TabsTrigger> : null}
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

                    <TabsContent value="compose" className="m-0">
                        <ComposeTab
                            examplesLoading={examplesLoading}
                            examplesError={examplesError}
                            portfolioExamples={portfolioExamples}
                            scenarioExamples={scenarioExamples}
                            packExamples={packExamples}
                            composePortfolioId={composePortfolioId}
                            setComposePortfolioId={setComposePortfolioId}
                            composeScenarioIds={composeScenarioIds}
                            setComposeScenarioIds={setComposeScenarioIds}
                            composePackIds={composePackIds}
                            setComposePackIds={setComposePackIds}
                            composeBundle={composeBundle}
                            composeValidationResult={composeValidationResult}
                            isComposeValidating={isComposeValidating}
                            toggleIdInSet={toggleIdInSetGeneric}
                            onSendToSimulation={() => {
                                if (!composeBundle.yaml) return;
                                if (composeBundle.errors.length > 0) return;
                                if (composeValidationResult?.valid !== true) return;

                                setYamlContent(composeBundle.yaml);
                                setInitialYamlContent(composeBundle.yaml);
                                setLoadedExample(null);
                                setValidationResult(null);
                                setSimulationResult(null);
                                setPendingNavigateToSimulate(true);
                            }}
                            onCopy={() => {
                                if (!composeBundle.yaml) return;
                                void handleCopyText(composeBundle.yaml);
                            }}
                            onDownload={() => {
                                if (!composeBundle.yaml) return;
                                handleDownloadText(composeBundle.yaml, "portfolio-bundle.yaml");
                            }}
                        />
                    </TabsContent>

                    {canSimulate ? (
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
                    ) : null}
                </Tabs>

                {activeTab === "simulate" ? toggleCard : null}

                {activeTab === "compose" ? null : (
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
                                <div className="h-[800px]">
                                    <CodeEditor value={yamlContent} onChange={setYamlContent} />
                                </div>
                            </CardContent>
                        </Card>

                        <div className="h-full">
                            {activeTab === "simulate" && canSimulate ? (
                                <SimulationResults result={simulationResult} isSimulating={isSimulating} />
                            ) : (
                                <ValidationResults result={validationResult} isValidating={isValidating} />
                            )}
                        </div>
                    </div>
                )}
            </div>
        </TooltipProvider>
    );
}
