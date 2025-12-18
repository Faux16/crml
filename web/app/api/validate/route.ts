import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink, mkdir } from "node:fs/promises";
import { exec } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import os from "node:os";
import yaml from "js-yaml";

const execAsync = promisify(exec);

const FAILED_SUMMARY_RE = /failed CRML.*validation with \d+ error\(s\)/i;
const NUMBERED_ERROR_RE = /^\s*\d+\./;

type Result<T> = { ok: true; value: T } | { ok: false; response: NextResponse };

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asStringArray(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function getYamlContentFromBody(body: unknown): Result<string> {
    const yamlContent = isRecord(body) && typeof body["yaml"] === "string" ? body["yaml"] : undefined;
    if (!yamlContent) {
        return {
            ok: false,
            response: NextResponse.json(
                { valid: false, errors: ["No YAML content provided"] },
                { status: 400 }
            ),
        };
    }

    return { ok: true, value: yamlContent };
}

function parseYaml(yamlContent: string): Result<unknown> {
    try {
        return { ok: true, value: yaml.load(yamlContent) };
    } catch (error) {
        return {
            ok: false,
            response: NextResponse.json({
                valid: false,
                errors: [`YAML parsing error: ${(error as Error).message}`],
            }),
        };
    }
}

function extractMeta(parsedYaml: unknown): {
    meta: Record<string, unknown> | undefined;
    locale: Record<string, unknown> | undefined;
} {
    const parsedObj = isRecord(parsedYaml) ? parsedYaml : undefined;
    const meta = parsedObj && isRecord(parsedObj["meta"]) ? parsedObj["meta"] : undefined;
    const locale = meta && isRecord(meta["locale"]) ? meta["locale"] : undefined;
    return { meta, locale };
}

function buildInfo(meta: Record<string, unknown> | undefined, locale: Record<string, unknown> | undefined) {
    return {
        name: typeof meta?.["name"] === "string" ? meta["name"] : undefined,
        version: typeof meta?.["version"] === "string" ? meta["version"] : undefined,
        description: typeof meta?.["description"] === "string" ? meta["description"] : undefined,
        author: typeof meta?.["author"] === "string" ? meta["author"] : undefined,
        organization: typeof meta?.["organization"] === "string" ? meta["organization"] : undefined,
        company_sizes: asStringArray(meta?.["company_sizes"]),
        industries: asStringArray(meta?.["industries"]),
        regulatory_frameworks: asStringArray(meta?.["regulatory_frameworks"]),
        tags: asStringArray(meta?.["tags"]),
        regions: asStringArray(locale?.["regions"]),
        countries: asStringArray(locale?.["countries"]),
    };
}

async function withTempYamlFile<T>(yamlContent: string, fn: (tmpFile: string) => Promise<T>): Promise<T> {
    const tmpDir = path.join(os.tmpdir(), "crml-validator");
    await mkdir(tmpDir, { recursive: true });
    const tmpFile = path.join(tmpDir, `crml-${Date.now()}.yaml`);

    try {
        await writeFile(tmpFile, yamlContent, "utf-8");
        return await fn(tmpFile);
    } finally {
        try {
            await unlink(tmpFile);
        } catch {
            // Ignore cleanup errors
        }
    }
}

function parseWarningsFromOutput(output: string): string[] {
    return output
        .split("\n")
        .filter((line) => line.includes("[WARNING]"))
        .map((line) => line.replace("[WARNING]", "").trim());
}

function parseErrorsFromOutput(output: string): string[] {
    return output
        .split("\n")
        .filter((line) => line.trim())
        .filter((line) => line.includes("[ERROR]") || NUMBERED_ERROR_RE.exec(line) !== null || line.includes("failed CRML"))
        .filter((line) => FAILED_SUMMARY_RE.exec(line) === null)
        .map((line) => line.replace("[ERROR]", "").trim());
}

async function execCrmlValidate(tmpFile: string): Promise<{ stdout: string; stderr: string; ok: boolean; message?: string }> {
    try {
        const { stdout, stderr } = await execAsync(`crml validate "${tmpFile}"`);
        return { stdout, stderr, ok: true };
    } catch (execError: unknown) {
        const err = execError as { stdout?: string; stderr?: string; message?: string };
        return {
            stdout: err.stdout || "",
            stderr: err.stderr || "",
            ok: false,
            message: err.message,
        };
    }
}

export async function POST(request: NextRequest) {
    try {
        const body: unknown = await request.json();
        const yamlContentResult = getYamlContentFromBody(body);
        if (!yamlContentResult.ok) return yamlContentResult.response;

        const parsedYamlResult = parseYaml(yamlContentResult.value);
        if (!parsedYamlResult.ok) return parsedYamlResult.response;

        const { meta, locale } = extractMeta(parsedYamlResult.value);
        const info = buildInfo(meta, locale);

        return await withTempYamlFile(yamlContentResult.value, async (tmpFile) => {
            const { stdout, stderr, ok, message } = await execCrmlValidate(tmpFile);
            const output = `${stdout}\n${stderr}`;
            const warnings = parseWarningsFromOutput(output);

            if (ok && stdout.includes("[OK]")) {
                return NextResponse.json({
                    valid: true,
                    info,
                    warnings,
                });
            }

            const errorLines = parseErrorsFromOutput(output);
            if (errorLines.length > 0) {
                return NextResponse.json({
                    valid: false,
                    errors: errorLines,
                    warnings,
                    info,
                });
            }

            return NextResponse.json({
                valid: false,
                errors: [ok ? "Validation failed" : `Validation failed: ${message || "Unknown error"}`],
                warnings,
                info,
            });
        });
    } catch (error) {
        console.error("Validation error:", error);
        return NextResponse.json(
            {
                valid: false,
                errors: [
                    "Internal validation error. Please ensure CRML is installed on the server.",
                    (error as Error).message,
                ],
            },
            { status: 500 }
        );
    }
}
