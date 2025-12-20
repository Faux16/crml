import yaml from "js-yaml";

export type CrmlToggleableDocKind = "scenario" | "portfolio_bundle";

export type CrmlDocKind =
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

export interface CrmlInclusions {
    docKind: CrmlToggleableDocKind;
    controlIds: string[];
    attackIds: string[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asStringArray(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function uniqSorted(values: string[]): string[] {
    return Array.from(new Set(values)).sort((a, b) => a.localeCompare(b));
}

function cloneJsonLike<T>(value: T): T {
    if (typeof structuredClone === "function") {
        return structuredClone(value);
    }

    const cloneUnknown = (input: unknown): unknown => {
        if (Array.isArray(input)) {
            return input.map(cloneUnknown);
        }
        if (input instanceof Date) {
            return new Date(input);
        }
        if (isRecord(input)) {
            const output: Record<string, unknown> = {};
            for (const [key, val] of Object.entries(input)) {
                output[key] = cloneUnknown(val);
            }
            return output;
        }
        return input;
    };

    return cloneUnknown(value) as T;
}

function tryParseYamlRootRecord(yamlContent: string): Record<string, unknown> | null {
    let parsed: unknown;
    try {
        parsed = yaml.load(yamlContent);
    } catch {
        return null;
    }

    return isRecord(parsed) ? parsed : null;
}

export function tryDetectCrmlDocKindFromYaml(yamlContent: string): CrmlDocKind | null {
    const root = tryParseYamlRootRecord(yamlContent);
    if (!root) return null;

    if (typeof root["crml_portfolio_bundle"] === "string") return "portfolio_bundle";
    if (typeof root["crml_scenario"] === "string") return "scenario";
    if (typeof root["crml_portfolio"] === "string") return "portfolio";
    if (typeof root["crml_attack_catalog"] === "string") return "attack_catalog";
    if (typeof root["crml_control_catalog"] === "string") return "control_catalog";
    if (typeof root["crml_control_relationships"] === "string") return "control_relationships";
    if (typeof root["crml_attack_control_relationships"] === "string") return "attack_control_relationships";
    if (typeof root["crml_assessment"] === "string") return "assessment";
    if (typeof root["crml_fx_config"] === "string") return "fx_config";

    return "unknown";
}

function tryGetPortfolioBundleScenarios(doc: Record<string, unknown>): unknown[] | null {
    const bundle = isRecord(doc["portfolio_bundle"]) ? doc["portfolio_bundle"] : null;
    if (!bundle) return null;

    return Array.isArray(bundle["scenarios"]) ? bundle["scenarios"] : null;
}

function extractScenarioDocsFromBundleScenarios(scenarios: unknown[]): Record<string, unknown>[] {
    const scenarioDocs: Record<string, unknown>[] = [];

    for (const scenarioEntry of scenarios) {
        if (!isRecord(scenarioEntry)) continue;
        const scenarioDoc = isRecord(scenarioEntry["scenario"]) ? scenarioEntry["scenario"] : null;
        if (!scenarioDoc) continue;
        scenarioDocs.push(scenarioDoc);
    }

    return scenarioDocs;
}

function extractControlIdsFromControlsArray(controls: unknown): string[] {
    if (!Array.isArray(controls)) return [];

    const ids: string[] = [];
    for (const entry of controls) {
        if (typeof entry === "string") {
            ids.push(entry);
            continue;
        }
        if (isRecord(entry) && typeof entry["id"] === "string") {
            ids.push(entry["id"]);
        }
    }

    return ids;
}

function extractScenarioInclusionsFromScenarioDoc(doc: Record<string, unknown>): { controlIds: string[]; attackIds: string[] } {
    const meta = isRecord(doc["meta"]) ? doc["meta"] : undefined;
    const scenario = isRecord(doc["scenario"]) ? doc["scenario"] : undefined;

    const attackIds = uniqSorted(asStringArray(meta?.["attck"]));
    const controlIds = uniqSorted(extractControlIdsFromControlsArray(scenario?.["controls"]));

    return { controlIds, attackIds };
}

export function tryExtractInclusionsFromYaml(yamlContent: string): CrmlInclusions | null {
    const root = tryParseYamlRootRecord(yamlContent);
    if (!root) return null;

    if (typeof root["crml_scenario"] === "string") {
        const { controlIds, attackIds } = extractScenarioInclusionsFromScenarioDoc(root);
        if (controlIds.length === 0 && attackIds.length === 0) return null;
        return { docKind: "scenario", controlIds, attackIds };
    }

    if (typeof root["crml_portfolio_bundle"] === "string") {
        const scenarios = tryGetPortfolioBundleScenarios(root) ?? [];
        const scenarioDocs = extractScenarioDocsFromBundleScenarios(scenarios);

        const allControls: string[] = [];
        const allAttacks: string[] = [];

        for (const scenarioDoc of scenarioDocs) {
            const { controlIds, attackIds } = extractScenarioInclusionsFromScenarioDoc(scenarioDoc);
            allControls.push(...controlIds);
            allAttacks.push(...attackIds);
        }

        const controlIds = uniqSorted(allControls);
        const attackIds = uniqSorted(allAttacks);
        if (controlIds.length === 0 && attackIds.length === 0) return null;

        return { docKind: "portfolio_bundle", controlIds, attackIds };
    }

    return null;
}

function filterControlsArray(controls: unknown, disabledControls: Set<string>): unknown {
    if (!Array.isArray(controls)) return controls;

    const filtered = controls.filter((entry) => {
        if (typeof entry === "string") return !disabledControls.has(entry);
        if (isRecord(entry) && typeof entry["id"] === "string") return !disabledControls.has(entry["id"]);
        return true;
    });

    return filtered;
}

function applyScenarioTogglesToScenarioDoc(doc: Record<string, unknown>, disabledControls: Set<string>, disabledAttacks: Set<string>) {
    const meta = isRecord(doc["meta"]) ? doc["meta"] : undefined;
    const scenario = isRecord(doc["scenario"]) ? doc["scenario"] : undefined;

    if (meta && Array.isArray(meta["attck"])) {
        const filteredAttacks = asStringArray(meta["attck"]).filter((id) => !disabledAttacks.has(id));
        if (filteredAttacks.length === 0) {
            delete meta["attck"];
        } else {
            meta["attck"] = filteredAttacks;
        }
    }

    if (scenario && Array.isArray(scenario["controls"])) {
        const filteredControls = filterControlsArray(scenario["controls"], disabledControls);
        if (Array.isArray(filteredControls) && filteredControls.length === 0) {
            delete scenario["controls"];
        } else {
            scenario["controls"] = filteredControls;
        }
    }
}

export function applyInclusionTogglesToYaml(
    yamlContent: string,
    disabledControls: Set<string>,
    disabledAttacks: Set<string>,
): string {
    if (disabledControls.size === 0 && disabledAttacks.size === 0) return yamlContent;

    const root = tryParseYamlRootRecord(yamlContent);
    if (!root) return yamlContent;

    const doc = cloneJsonLike(root);

    if (typeof doc["crml_scenario"] === "string") {
        applyScenarioTogglesToScenarioDoc(doc, disabledControls, disabledAttacks);
        return yaml.dump(doc, { noRefs: true, lineWidth: 120 });
    }

    if (typeof doc["crml_portfolio_bundle"] === "string") {
        const scenarios = tryGetPortfolioBundleScenarios(doc);
        if (!scenarios) return yamlContent;

        const scenarioDocs = extractScenarioDocsFromBundleScenarios(scenarios);
        for (const scenarioDoc of scenarioDocs) {
            applyScenarioTogglesToScenarioDoc(scenarioDoc, disabledControls, disabledAttacks);
        }

        return yaml.dump(doc, { noRefs: true, lineWidth: 120 });
    }

    return yamlContent;
}
