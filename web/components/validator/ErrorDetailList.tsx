
import { XCircle, AlertCircle } from "lucide-react";

interface ErrorDetailListProps {
    readonly errors?: string[];
    readonly warnings?: string[];
}

/**
 * ErrorDetailList Component
 * Displays a list of validation errors and warnings.
 */
export function ErrorDetailList({ errors, warnings }: ErrorDetailListProps) {
    const errorCounts = new Map<string, number>();
    const warningCounts = new Map<string, number>();

    return (
        <>
            {/* Errors */}
            {errors && errors.length > 0 && (
                <div className="mb-6">
                    <h3 className="mb-3 flex items-center gap-2 font-semibold text-red-600">
                        <XCircle className="h-4 w-4" />
                        Errors ({errors.length})
                    </h3>
                    <div className="space-y-2">
                        {errors.map((error) => {
                            const seen = errorCounts.get(error) ?? 0;
                            errorCounts.set(error, seen + 1);
                            const key = seen === 0 ? error : `${error}#${seen}`;

                            return (
                            <div
                                key={key}
                                className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950/20"
                            >
                                <p className="font-mono text-red-900 dark:text-red-300">{error}</p>
                            </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Warnings */}
            {warnings && warnings.length > 0 && (
                <div className="mb-6">
                    <h3 className="mb-3 flex items-center gap-2 font-semibold text-yellow-600">
                        <AlertCircle className="h-4 w-4" />
                        Warnings ({warnings.length})
                    </h3>
                    <div className="space-y-2">
                        {warnings.map((warning) => {
                            const seen = warningCounts.get(warning) ?? 0;
                            warningCounts.set(warning, seen + 1);
                            const key = seen === 0 ? warning : `${warning}#${seen}`;

                            return (
                            <div
                                key={key}
                                className="rounded-lg border border-yellow-200 bg-yellow-50 p-3 text-sm dark:border-yellow-900 dark:bg-yellow-950/20"
                            >
                                <p className="font-mono text-yellow-900 dark:text-yellow-300">{warning}</p>
                            </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </>
    );
}
