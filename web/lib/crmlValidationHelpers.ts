/**
 * Helper utilities for enhancing CRML validation errors with context and suggestions.
 */

export interface EnhancedError {
    message: string;
    suggestion?: string;
    affectedItems?: string[];
    category: 'composition' | 'schema' | 'reference' | 'compatibility';
}

export interface Example {
    id: string;
    name: string;
    filename: string;
    docKind?: string;
    content: string;
}

/**
 * Enhance validation errors with context-aware suggestions
 */
export function enhanceValidationErrors(
    errors: string[],
    context: {
        selectedPortfolio?: Example;
        selectedScenarios: Example[];
        selectedPacks: Example[];
    }
): EnhancedError[] {
    return errors.map(error => {
        const enhanced: EnhancedError = {
            message: error,
            category: categorizeError(error),
        };

        // Add suggestions based on error patterns
        if (error.includes('File not found') || error.includes('path')) {
            enhanced.category = 'reference';
            enhanced.suggestion = 'This usually means a scenario references a catalog or mapping that is not selected. Check the optional catalogs section.';
        } else if (error.includes('schema') || error.includes('validation')) {
            enhanced.category = 'schema';
            enhanced.suggestion = 'Review the YAML structure and ensure all required fields are present.';
        } else if (error.includes('currency') || error.includes('model')) {
            enhanced.category = 'compatibility';
            enhanced.suggestion = 'Selected scenarios may have incompatible configurations. Try selecting scenarios from the same use case.';
        }

        return enhanced;
    });
}

/**
 * Categorize error based on content
 */
function categorizeError(error: string): EnhancedError['category'] {
    const lowerError = error.toLowerCase();

    if (lowerError.includes('select') || lowerError.includes('required')) {
        return 'composition';
    }
    if (lowerError.includes('schema') || lowerError.includes('invalid') || lowerError.includes('missing field')) {
        return 'schema';
    }
    if (lowerError.includes('file') || lowerError.includes('path') || lowerError.includes('not found')) {
        return 'reference';
    }
    if (lowerError.includes('currency') || lowerError.includes('model') || lowerError.includes('conflict')) {
        return 'compatibility';
    }

    return 'schema';
}

/**
 * Check scenario compatibility and return warnings
 */
export function checkScenarioCompatibility(scenarios: Example[]): string[] {
    const warnings: string[] = [];

    if (scenarios.length === 0) {
        return warnings;
    }

    // Check for currency consistency
    const currencies = new Set<string>();
    scenarios.forEach(scenario => {
        const currencyMatch = scenario.content.match(/currency:\s*['"]?(\w+)['"]?/i);
        if (currencyMatch) {
            currencies.add(currencyMatch[1]);
        }
    });

    if (currencies.size > 1) {
        warnings.push(`Selected scenarios use different currencies (${Array.from(currencies).join(', ')}). Consider using scenarios with the same currency or adding FX configuration.`);
    }

    // Check for frequency model consistency
    const freqModels = new Set<string>();
    scenarios.forEach(scenario => {
        const modelMatch = scenario.content.match(/frequency:\s*\n\s*model:\s*['"]?(\w+)['"]?/i);
        if (modelMatch) {
            freqModels.add(modelMatch[1]);
        }
    });

    if (freqModels.size > 1) {
        warnings.push(`Selected scenarios use different frequency models (${Array.from(freqModels).join(', ')}). This may cause unexpected behavior.`);
    }

    return warnings;
}

/**
 * Detect missing catalog references in scenarios
 */
export function detectMissingCatalogs(
    scenarios: Example[],
    selectedPacks: Example[]
): string[] {
    const warnings: string[] = [];
    const selectedCatalogTypes = new Set(selectedPacks.map(p => p.docKind));

    scenarios.forEach(scenario => {
        // Check for control catalog references
        if (scenario.content.includes('control_catalog') && !selectedCatalogTypes.has('control_catalog')) {
            warnings.push(`Scenario "${scenario.name}" may reference a control catalog. Consider adding one from the catalogs section.`);
        }

        // Check for attack catalog references
        if (scenario.content.includes('attack_catalog') && !selectedCatalogTypes.has('attack_catalog')) {
            warnings.push(`Scenario "${scenario.name}" may reference an attack catalog. Consider adding one from the catalogs section.`);
        }

        // Check for control relationships
        if (scenario.content.includes('control_relationships') && !selectedCatalogTypes.has('control_relationships')) {
            warnings.push(`Scenario "${scenario.name}" may reference control relationships. Consider adding a mapping from the catalogs section.`);
        }
    });

    return warnings;
}
