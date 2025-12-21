"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import CodeEditor from "@/components/CodeEditor";
import ValidationResults, { ValidationResult } from "@/components/ValidationResults";
import { Upload, Play, FileText, Download } from "lucide-react";
import { PORTFOLIO_BUNDLE_DOCUMENTED_YAML } from "@/lib/crmlExamples";

const DEFAULT_YAML = PORTFOLIO_BUNDLE_DOCUMENTED_YAML;

export default function ValidatorPage() {
    const [yamlContent, setYamlContent] = useState(DEFAULT_YAML);
    const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
    const [isValidating, setIsValidating] = useState(false);

    // Load content from sessionStorage if coming from examples page
    useEffect(() => {
        const storedContent = sessionStorage.getItem("crml-validator-content");
        if (storedContent) {
            setYamlContent(storedContent);
            sessionStorage.removeItem("crml-validator-content");
        }
    }, []);

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

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const content = await file.text();
        setYamlContent(content);
        setValidationResult(null);
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

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">
                    CRML Validator
                </h1>
                <p className="text-lg text-muted-foreground">
                    Validate your CRML models in real-time with detailed error reporting
                </p>
            </div>

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

            <div className="grid gap-6 lg:grid-cols-2">
                {/* Editor */}
                <Card className="flex flex-col">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <FileText className="h-5 w-5" />
                            YAML Editor
                        </CardTitle>
                        <CardDescription>
                            Edit your CRML model or upload a YAML file
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
                    <ValidationResults result={validationResult} isValidating={isValidating} />
                </div>
            </div>

            {/* Help Section */}
            <Card className="mt-8">
                <CardHeader>
                    <CardTitle>Quick Tips</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                        <div>
                            <h3 className="mb-2 font-semibold">Getting Started</h3>
                            <ul className="space-y-1 text-sm text-muted-foreground">
                                <li>• Start with the example model provided</li>
                                <li>• Upload your own YAML file to validate</li>
                                <li>• Check the examples page for more templates</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="mb-2 font-semibold">Common Issues</h3>
                            <ul className="space-y-1 text-sm text-muted-foreground">
                                <li>• Ensure YAML syntax is correct</li>
                                <li>• Check that all required fields are present</li>
                                <li>• Verify parameter types match the schema</li>
                            </ul>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
