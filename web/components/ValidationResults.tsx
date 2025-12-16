"use client";

import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ValidationSummary } from "./validator/ValidationSummary";
import { ModelMetadataCard } from "./validator/ModelMetadataCard";
import { ErrorDetailList } from "./validator/ErrorDetailList";

export interface ValidationResult {
    valid: boolean;
    errors?: string[];
    warnings?: string[];
    info?: {
        name?: string;
        version?: string;
        description?: string;
        author?: string;
        organization?: string;
        company_sizes?: string[];
        industries?: string[];
        regions?: string[];
        countries?: string | null;
        regulatory_frameworks?: string[];
        tags?: string[];
    };
}

interface ValidationResultsProps {
    result: ValidationResult | null;
    isValidating: boolean;
}

/**
 * ValidationResults Component
 * Main container for displaying validation outcomes.
 */
export default function ValidationResults({ result, isValidating }: ValidationResultsProps) {
    // If validating or no result, ValidationSummary handles the full card state
    if (isValidating || !result) {
        return <ValidationSummary result={result} isValidating={isValidating} />;
    }

    return (
        <Card className="h-full">
            <ValidationSummary result={result} isValidating={isValidating} />
            <CardContent>
                <ScrollArea className="h-[400px]">
                    {result.info && <ModelMetadataCard info={result.info} />}

                    <ErrorDetailList errors={result.errors} warnings={result.warnings} />

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
