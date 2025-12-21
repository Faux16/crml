import { NextResponse } from "next/server";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import yaml from "js-yaml";

type CrmlExampleDocKind =
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

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asStringArray(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function asStringArrayOrSingleton(value: unknown): string[] {
    if (Array.isArray(value)) return value.filter((v): v is string => typeof v === "string");
    if (typeof value === "string") return [value];
    return [];
}

function detectDocKind(parsedObj: Record<string, unknown> | undefined): CrmlExampleDocKind {
    if (!parsedObj) return "unknown";
    if (typeof parsedObj["crml_portfolio_bundle"] === "string") return "portfolio_bundle";
    if (typeof parsedObj["crml_scenario"] === "string") return "scenario";
    if (typeof parsedObj["crml_portfolio"] === "string") return "portfolio";
    if (typeof parsedObj["crml_attack_catalog"] === "string") return "attack_catalog";
    if (typeof parsedObj["crml_control_catalog"] === "string") return "control_catalog";
    if (typeof parsedObj["crml_control_relationships"] === "string") return "control_relationships";
    if (typeof parsedObj["crml_attack_control_relationships"] === "string") return "attack_control_relationships";
    if (typeof parsedObj["crml_assessment"] === "string") return "assessment";
    if (typeof parsedObj["crml_fx_config"] === "string") return "fx_config";
    return "unknown";
}

async function listYamlFiles(dir: string, baseDir: string): Promise<string[]> {
    const entries = await readdir(dir, { withFileTypes: true });
    const results: string[] = [];

    for (const entry of entries) {
        // Ignore common noise
        if (entry.name.startsWith(".")) continue;
        if (entry.name === "node_modules") continue;

        const abs = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            results.push(...await listYamlFiles(abs, baseDir));
            continue;
        }

        const isYaml = entry.name.endsWith(".yaml") || entry.name.endsWith(".yml");
        if (!isYaml) continue;

        // Exclude FX config documents from the examples gallery
        if (entry.name.startsWith("fx-config")) continue;

        results.push(path.relative(baseDir, abs));
    }

    return results;
}

export async function GET() {
    try {
        // Path to examples directory (relative to project root)
        const examplesDir = path.join(process.cwd(), "..", "examples");

        const yamlFiles = await listYamlFiles(examplesDir, examplesDir);

        // Read and parse each example
        const examples = await Promise.all(
            yamlFiles.map(async (file) => {
                const filePath = path.join(examplesDir, file);
                const content = await readFile(filePath, "utf-8");

                try {
                    const parsed = yaml.load(content);
                    const parsedObj = isRecord(parsed) ? parsed : undefined;
                    const meta = parsedObj && isRecord(parsedObj["meta"]) ? parsedObj["meta"] : undefined;
                    const docKind = detectDocKind(parsedObj);

                    // According to schema, regions and countries are in meta.locale
                    const locale = meta && isRecord(meta["locale"]) ? meta["locale"] : undefined;
                    const regions = asStringArray(locale?.["regions"]);

                    const countries = asStringArrayOrSingleton(locale?.["countries"]);

                    const id = file
                        .replace(/\.(yaml|yml)$/, "")
                        .replaceAll("\\", "__")
                        .replaceAll("/", "__");

                    return {
                        id,
                        filename: file,
                        name: (typeof meta?.["name"] === "string" ? meta["name"] : undefined) || file,
                        description: (typeof meta?.["description"] === "string" ? meta["description"] : undefined) || "No description available",
                        tags: asStringArray(meta?.["tags"]),
                        regions,
                        countries,
                        company_size: asStringArray(meta?.["company_size"]),
                        docKind,
                        content,
                    };
                } catch {
                    const id = file
                        .replace(/\.(yaml|yml)$/, "")
                        .replaceAll("\\", "__")
                        .replaceAll("/", "__");
                    return {
                        id,
                        filename: file,
                        name: file,
                        description: "Error parsing file",
                        tags: [],
                        regions: [],
                        countries: [],
                        company_size: [],
                        docKind: "unknown" as const,
                        content,
                    };
                }
            })
        );

        return NextResponse.json({ examples });
    } catch (error) {
        console.error("Error reading examples:", error);
        return NextResponse.json(
            { error: "Failed to load examples", examples: [] },
            { status: 500 }
        );
    }
}
