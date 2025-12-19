import yaml from "js-yaml";

export type CrmlToggleableDocKind = "scenario" | "portfolio_bundle";

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
    return JSON.parse(JSON.stringify(value)) as T;
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
    let parsed: unknown;
    try {
        parsed = yaml.load(yamlContent);
    } catch {
        return null;
    }

    if (!isRecord(parsed)) return null;

    if (typeof parsed["crml_scenario"] === "string") {
        const { controlIds, attackIds } = extractScenarioInclusionsFromScenarioDoc(parsed);
        if (controlIds.length === 0 && attackIds.length === 0) return null;
        return { docKind: "scenario", controlIds, attackIds };
    }

    if (typeof parsed["crml_portfolio_bundle"] === "string") {
        const bundle = isRecord(parsed["portfolio_bundle"]) ? parsed["portfolio_bundle"] : undefined;
        const scenarios = Array.isArray(bundle?.["scenarios"]) ? bundle?.["scenarios"] : [];

        const allControls: string[] = [];
        const allAttacks: string[] = [];

        for (const scenarioEntry of scenarios) {
            if (!isRecord(scenarioEntry)) continue;
            const scenarioDoc = isRecord(scenarioEntry["scenario"]) ? scenarioEntry["scenario"] : undefined;
            if (!scenarioDoc) continue;

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
    const meta = isRecord(doc["meta"]) ? (doc["meta"] as Record<string, unknown>) : undefined;
    const scenario = isRecord(doc["scenario"]) ? (doc["scenario"] as Record<string, unknown>) : undefined;

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

    let parsed: unknown;
    try {
        parsed = yaml.load(yamlContent);
    } catch {
        return yamlContent;
    }

    if (!isRecord(parsed)) return yamlContent;

    const doc = cloneJsonLike(parsed);
    if (!isRecord(doc)) return yamlContent;

    if (typeof doc["crml_scenario"] === "string") {
        applyScenarioTogglesToScenarioDoc(doc, disabledControls, disabledAttacks);
        return yaml.dump(doc, { noRefs: true, lineWidth: 120 });
    }

    if (typeof doc["crml_portfolio_bundle"] === "string") {
        const bundle = isRecord(doc["portfolio_bundle"]) ? (doc["portfolio_bundle"] as Record<string, unknown>) : undefined;
        if (!bundle) return yamlContent;

        const scenarios = Array.isArray(bundle["scenarios"]) ? bundle["scenarios"] : undefined;
        if (!scenarios) return yamlContent;

        for (const scenarioEntry of scenarios) {
            if (!isRecord(scenarioEntry)) continue;
            const scenarioDoc = isRecord(scenarioEntry["scenario"]) ? (scenarioEntry["scenario"] as Record<string, unknown>) : undefined;
            if (!scenarioDoc) continue;
            applyScenarioTogglesToScenarioDoc(scenarioDoc, disabledControls, disabledAttacks);
        }

        return yaml.dump(doc, { noRefs: true, lineWidth: 120 });
    }

    return yamlContent;
}
