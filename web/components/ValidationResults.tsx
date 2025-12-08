"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { CheckCircle, XCircle, AlertCircle, Info } from "lucide-react";

export interface ValidationResult {
    valid: boolean;
    errors?: string[];
    warnings?: string[];
    info?: {
        name?: string;
        version?: string;
        description?: string;
    };
}

interface ValidationResultsProps {
    result: ValidationResult | null;
    isValidating: boolean;
}

export default function ValidationResults({ result, isValidating }: ValidationResultsProps) {
    if (isValidating) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Validating...</CardTitle>
                    <CardDescription>Please wait while we validate your CRML model</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-12">
                        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!result) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle>Validation Results</CardTitle>
                    <CardDescription>Results will appear here after validation</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col items-center justify-center py-12 text-center">
                        <Info className="mb-4 h-12 w-12 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                            Paste your CRML model in the editor and click "Validate" to see results
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="h-full">
            <CardHeader>
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            {result.valid ? (
                                <>
                                    <CheckCircle className="h-5 w-5 text-green-600" />
                                    Validation Passed
                                </>
                            ) : (
                                <>
                                    <XCircle className="h-5 w-5 text-red-600" />
                                    Validation Failed
                                </>
                            )}
                        </CardTitle>
                        <CardDescription>
                            {result.valid
                                ? "Your CRML model is valid and ready to use"
                                : "Please fix the errors below"}
                        </CardDescription>
                    </div>
                    <Badge variant={result.valid ? "default" : "destructive"}>
                        {result.valid ? "Valid" : "Invalid"}
                    </Badge>
                </div>
            </CardHeader>
            <CardContent>
                <ScrollArea className="h-[400px]">
                    {/* Model Info */}
                    {result.info && (
                        <div className="mb-6 rounded-lg border bg-muted/50 p-4">
                            <h3 className="mb-2 font-semibold">Model Information</h3>
                            <div className="space-y-1 text-sm">
                                {result.info.name && (
                                    <p>
                                        <span className="font-medium">Name:</span> {result.info.name}
                                    </p>
                                )}
                                {result.info.version && (
                                    <p>
                                        <span className="font-medium">Version:</span> {result.info.version}
                                    </p>
                                )}
                                {result.info.description && (
                                    <p>
                                        <span className="font-medium">Description:</span> {result.info.description}
                                    </p>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Errors */}
                    {result.errors && result.errors.length > 0 && (
                        <div className="mb-6">
                            <h3 className="mb-3 flex items-center gap-2 font-semibold text-red-600">
                                <XCircle className="h-4 w-4" />
                                Errors ({result.errors.length})
                            </h3>
                            <div className="space-y-2">
                                {result.errors.map((error, index) => (
                                    <div
                                        key={index}
                                        className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950/20"
                                    >
                                        <p className="font-mono text-red-900 dark:text-red-300">{error}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Warnings */}
                    {result.warnings && result.warnings.length > 0 && (
                        <div className="mb-6">
                            <h3 className="mb-3 flex items-center gap-2 font-semibold text-yellow-600">
                                <AlertCircle className="h-4 w-4" />
                                Warnings ({result.warnings.length})
                            </h3>
                            <div className="space-y-2">
                                {result.warnings.map((warning, index) => (
                                    <div
                                        key={index}
                                        className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm dark:border-yellow-900 dark:bg-yellow-950/20"
                                    >
                                        <p className="font-mono text-yellow-900 dark:text-yellow-300">{warning}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Success Message */}
                    {result.valid && (!result.errors || result.errors.length === 0) && (
                        <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950/20">
                            <p className="text-sm text-green-900 dark:text-green-300">
                                ✓ Your CRML model passed all validation checks and is ready to use.
                            </p>
                        </div>
                    )}
                </ScrollArea>
            </CardContent>
        </Card>
    );
}
