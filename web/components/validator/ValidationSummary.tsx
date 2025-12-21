
import { Card, CardDescription, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle, XCircle, Info } from "lucide-react";
import { ValidationResult } from "../ValidationResults";

interface ValidationSummaryProps {
    readonly result: ValidationResult | null;
    readonly isValidating: boolean;
}

/**
 * ValidationSummary Component
 * Displays the high-level status of the validation (Valid/Invalid/Loading/Empty).
 */
export function ValidationSummary({ result, isValidating }: ValidationSummaryProps) {
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
                            Paste your CRML model in the editor and click &quot;Validate&quot; to see results
                        </p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
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
    );
}
