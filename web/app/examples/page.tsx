"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, ExternalLink, Copy, Check } from "lucide-react";

type CrmlExampleDocKind =
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

interface Example {
    id: string;
    filename: string;
    name: string;
    description: string;
    tags: string[];
    regions?: string[];
    countries?: string[];
    company_size?: string[];
    docKind?: CrmlExampleDocKind;
    content: string;
}

const SECTION_ORDER: Array<{ kind: CrmlExampleDocKind; title: string; subtitle?: string }> = [
    {
        kind: "portfolio_bundle",
        title: "Portfolio Bundles",
        subtitle:
            "Runnable end-to-end inputs. A bundle is a single, self-contained artifact that embeds a Portfolio and inlines the Scenarios it references. To create one you typically need: (1) a Portfolio (assets + aggregation semantics + scenario references), (2) the referenced Scenario documents inlined under the bundle, and optionally (3) Control/Attack catalogs, Assessments, and relationship packs for mapping and posture.",
    },
    {
        kind: "scenario",
        title: "Scenarios",
        subtitle:
            "Scenario documents model one risk scenario (frequency + severity, plus any control factors). They’re usually referenced by a Portfolio and become directly runnable when included in a Portfolio Bundle.",
    },
    {
        kind: "portfolio",
        title: "Portfolios",
        subtitle:
            "Portfolio documents define the exposure surface (assets), how scenario losses aggregate across the portfolio, and which scenarios are in-scope. Tools often use a Portfolio as the ‘index’ that ties scenarios and optional catalogs/assessments together.",
    },
    {
        kind: "attack_catalog",
        title: "Attack Catalogs",
        subtitle:
            "Attack catalogs are dictionaries of attack technique/tactic ids used for classification, reporting, and mapping. Scenarios may reference these ids as metadata; relationship packs can connect them to controls.",
    },
    {
        kind: "control_catalog",
        title: "Control Catalogs",
        subtitle:
            "Control catalogs define the dictionary of control ids (titles/tags) referenced by Scenarios and Assessments. They provide the canonical list of controls without embedding copyrighted standard text.",
    },
    {
        kind: "assessment",
        title: "Assessments",
        subtitle:
            "Assessments capture organization-specific control posture (e.g., coverage/implementation/reliability or maturity). Engines combine this posture with scenario control factors to estimate how controls change frequency or severity.",
    },
    {
        kind: "control_relationships",
        title: "Control <> Control mappings",
        subtitle:
            "Control relationship packs describe mappings and interactions between controls (e.g., equivalence, overlap, dependencies). They help tooling/engines roll up frameworks and avoid double-counting control effects.",
    },
    {
        kind: "attack_control_relationships",
        title: "Attack <> Control mappings",
        subtitle:
            "Attack-control relationship packs link attack ids to the controls that mitigate them. They enable mapping from attack-centric scenario metadata to an organization’s control posture.",
    },
    {
        kind: "unknown",
        title: "Other",
        subtitle: "Examples that don’t match a known CRML document type (or are missing the top-level CRML version marker).",
    },
];

function ExampleCard({
    example,
    copiedId,
    onOpenInPlayground,
    onCopy,
}: {
    readonly example: Example;
    readonly copiedId: string | null;
    readonly onOpenInPlayground: (example: Example) => void;
    readonly onCopy: (example: Example) => void;
}) {
    return (
        <Card className="flex flex-col border-2 transition-all hover:border-primary/50 hover:shadow-lg">
            <CardHeader>
                <div className="flex items-start justify-between">
                    <div className="flex-1">
                        <CardTitle className="mb-2">{example.name}</CardTitle>
                        <CardDescription>{example.description}</CardDescription>
                    </div>
                    <FileText className="h-5 w-5 text-muted-foreground" />
                </div>
                {(example.tags && example.tags.length > 0) ||
                    (example.regions && example.regions.length > 0) ||
                    (example.company_size && example.company_size.length > 0) ||
                    !!example.countries ? (
                    <div className="flex flex-wrap gap-2 pt-2">
                        {example.tags?.map((tag) => (
                            <Badge key={`tag:${example.id}:${tag}`} variant="secondary">{tag}</Badge>
                        ))}

                        {example.regions && example.regions.length > 0 && (
                            <Badge key={`region:${example.id}`} variant="secondary">
                                Regions: {example.regions.join(", ")}
                            </Badge>
                        )}

                        {example.countries && example.countries.length > 0 && (
                            <Badge key={`country:${example.id}`} variant="secondary">
                                Countries: {example.countries.join(", ")}
                            </Badge>
                        )}

                        {example.company_size && example.company_size.length > 0 && (
                            <Badge key={`size:${example.id}`} variant="secondary">
                                Sizes: {example.company_size.join(", ")}
                            </Badge>
                        )}
                    </div>
                ) : null}
            </CardHeader>
            <CardContent className="flex-1">
                <div className="mb-4 rounded-lg bg-muted p-4">
                    <pre className="overflow-x-auto text-xs">
                        <code>{example.content.split("\n").slice(0, 10).join("\n")}...</code>
                    </pre>
                </div>
                <div className="flex flex-wrap gap-2">
                    <Button onClick={() => onOpenInPlayground(example)} className="gap-2">
                        <ExternalLink className="h-4 w-4" />
                        Open in Playground
                    </Button>
                    <Button variant="outline" onClick={() => onCopy(example)} className="gap-2">
                        {copiedId === example.id ? (
                            <>
                                <Check className="h-4 w-4" />
                                Copied!
                            </>
                        ) : (
                            <>
                                <Copy className="h-4 w-4" />
                                Copy
                            </>
                        )}
                    </Button>
                </div>
            </CardContent>
        </Card>
    );
}

export default function ExamplesPage() {
    const [examples, setExamples] = useState<Example[]>([]);
    const [loading, setLoading] = useState(true);
    const [copiedId, setCopiedId] = useState<string | null>(null);
    const router = useRouter();

    useEffect(() => {
        fetchExamples();
    }, []);

    const fetchExamples = async () => {
        try {
            const response = await fetch("/api/examples");
            const data = await response.json();
            setExamples(data.examples || []);
        } catch (error) {
            console.error("Failed to fetch examples:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleCopyContent = async (example: Example) => {
        try {
            await navigator.clipboard.writeText(example.content);
            setCopiedId(example.id);
            setTimeout(() => setCopiedId(null), 2000);
        } catch (error) {
            console.error("Failed to copy:", error);
        }
    };

    const handleOpenInPlayground = (example: Example) => {
        const qs = new URLSearchParams({ example: example.id, tab: "validate" });
        router.push(`/playground?${qs.toString()}`);
    };

    const examplesByKind = useMemo(() => {
        const map = new Map<CrmlExampleDocKind, Example[]>();
        for (const ex of examples) {
            const kind = ex.docKind ?? "unknown";
            const arr = map.get(kind) ?? [];
            arr.push(ex);
            map.set(kind, arr);
        }

        // Stable, human-friendly ordering inside sections
        for (const arr of map.values()) {
            arr.sort((a, b) => (a.name || a.filename).localeCompare(b.name || b.filename));
        }

        return map;
    }, [examples]);

    const availableSections = useMemo(() => {
        return SECTION_ORDER.filter((section) => (examplesByKind.get(section.kind)?.length ?? 0) > 0);
    }, [examplesByKind]);

    const [activeKind, setActiveKind] = useState<CrmlExampleDocKind | null>(null);

    useEffect(() => {
        if (availableSections.length === 0) return;
        if (activeKind && availableSections.some((s) => s.kind === activeKind)) return;
        setActiveKind(availableSections[0].kind);
    }, [activeKind, availableSections]);

    if (loading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="flex items-center justify-center py-12">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                </div>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">
                    CRML Examples
                </h1>
                <p className="text-lg text-muted-foreground">
                    Explore example CRML models and use them as templates for your own risk models
                </p>
            </div>

            {examples.length === 0 ? (
                <Card>
                    <CardContent className="py-12 text-center">
                        <FileText className="mx-auto mb-4 h-12 w-12 text-muted-foreground" />
                        <p className="text-muted-foreground">No examples available</p>
                    </CardContent>
                </Card>
            ) : (
                <Tabs value={activeKind ?? undefined} onValueChange={(v) => setActiveKind(v as CrmlExampleDocKind)}>
                    <TabsList className="mb-6 flex w-full flex-wrap justify-start">
                        {availableSections.map((section) => (
                            <TabsTrigger key={section.kind} value={section.kind}>
                                {section.title}
                            </TabsTrigger>
                        ))}
                    </TabsList>

                    {availableSections.map((section) => {
                        const sectionExamples = examplesByKind.get(section.kind) ?? [];
                        return (
                            <TabsContent key={section.kind} value={section.kind} className="m-0">
                                {section.subtitle ? (
                                    <p className="mb-4 text-sm text-muted-foreground">{section.subtitle}</p>
                                ) : null}
                                <div className="grid gap-6 md:grid-cols-2">
                                    {sectionExamples.map((example) => (
                                        <ExampleCard
                                            key={example.id}
                                            example={example}
                                            copiedId={copiedId}
                                            onOpenInPlayground={handleOpenInPlayground}
                                            onCopy={handleCopyContent}
                                        />
                                    ))}
                                </div>
                            </TabsContent>
                        );
                    })}
                </Tabs>
            )}
        </div>
    );
}
