
import { ValidationResult } from "../ValidationResults";

interface ModelMetadataCardProps {
    info: NonNullable<ValidationResult['info']>;
}

/**
 * ModelMetadataCard Component
 * Displays metadata extracted from the CRML model.
 */
export function ModelMetadataCard({ info }: ModelMetadataCardProps) {
    if (!info) return null;

    return (
        <div className="mb-6 rounded-lg border bg-muted/50 p-4">
            <h3 className="mb-2 font-semibold">Model Information</h3>
            <div className="space-y-1 text-sm">
                {info.name && (
                    <p>
                        <span className="font-medium">Name:</span> {info.name}
                    </p>
                )}
                {info.version && (
                    <p>
                        <span className="font-medium">Version:</span> {info.version}
                    </p>
                )}
                {info.description && (
                    <p>
                        <span className="font-medium">Description:</span> {info.description}
                    </p>
                )}
                {info.author && (
                    <p>
                        <span className="font-medium">Author:</span> {info.author}
                    </p>
                )}
                {info.organization && (
                    <p>
                        <span className="font-medium">Organization:</span> {info.organization}
                    </p>
                )}
                {info.company_sizes && info.company_sizes.length > 0 && (
                    <p>
                        <span className="font-medium">Company Size:</span> {Array.isArray(info.company_sizes) ? info.company_sizes.join(", ") : info.company_sizes}
                    </p>
                )}
                {info.industries && info.industries.length > 0 && (
                    <p>
                        <span className="font-medium">Industries:</span> {Array.isArray(info.industries) ? info.industries.join(", ") : info.industries}
                    </p>
                )}
                {info.regulatory_frameworks && info.regulatory_frameworks.length > 0 && (
                    <p>
                        <span className="font-medium">Regulatory Frameworks:</span> {Array.isArray(info.regulatory_frameworks) ? info.regulatory_frameworks.join(", ") : info.regulatory_frameworks}
                    </p>
                )}
                {info.regions && info.regions.length > 0 && (
                    <p>
                        <span className="font-medium">Regions:</span> {Array.isArray(info.regions) ? info.regions.join(", ") : info.regions}
                    </p>
                )}
                {Array.isArray(info.countries) && info.countries.length > 0 && (
                    <p>
                        <span className="font-medium">Countries:</span> {info.countries.join(", ")}
                    </p>
                )}
                {info.tags && info.tags.length > 0 && (
                    <p>
                        <span className="font-medium">Tags:</span> {Array.isArray(info.tags) ? info.tags.join(", ") : info.tags}
                    </p>
                )}
            </div>
        </div>
    );
}
