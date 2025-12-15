"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FileText, ExternalLink, Copy, Check } from "lucide-react";

interface Example {
    id: string;
    filename: string;
    name: string;
    description: string;
    tags: string[];
    regions?: string[];
    country?: string | null;
    company_size?: string[];
    content: string;
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

    const handleLoadInValidator = (example: Example) => {
        // Store the example content in sessionStorage
        sessionStorage.setItem("crml-validator-content", example.content);
        router.push("/validator");
    };

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
                <div className="grid gap-6 md:grid-cols-2">
                    {examples.map((example) => (
                        <Card key={example.id} className="flex flex-col border-2 transition-all hover:border-primary/50 hover:shadow-lg">
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
                                    !!example.country ? (
                                    <div className="flex flex-wrap gap-2 pt-2">
                                        {example.tags?.map((tag) => (
                                            <Badge key={`tag:${tag}`} variant="secondary">{tag}</Badge>
                                        ))}

                                        {example.regions?.map((region) => (
                                            <Badge key={`region:${region}`} variant="secondary">region: {region}</Badge>
                                        ))}

                                        {example.country ? (
                                            <Badge key={`country:${example.country}`} variant="secondary">country: {example.country}</Badge>
                                        ) : null}

                                        {example.company_size?.map((size) => (
                                            <Badge key={`size:${size}`} variant="secondary">size: {size}</Badge>
                                        ))}
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
                                    <Button
                                        onClick={() => handleLoadInValidator(example)}
                                        className="gap-2"
                                    >
                                        <ExternalLink className="h-4 w-4" />
                                        Load in Validator
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => handleCopyContent(example)}
                                        className="gap-2"
                                    >
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
                    ))}
                </div>
            )}
        </div>
    );
}
