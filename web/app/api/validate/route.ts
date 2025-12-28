import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink, mkdir } from "node:fs/promises";
import { existsSync } from "node:fs";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import os from "node:os";
import yaml from "js-yaml";

const execFileAsync = promisify(execFile);

const FAILED_SUMMARY_RE = /failed CRML.*validation with \d+ error\(s\)/i;
const NUMBERED_ERROR_RE = /^\s*\d+\./;

type Result<T> = { ok: true; value: T } | { ok: false; response: NextResponse };

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null && !Array.isArray(value);
}

function asString(value: unknown): string | undefined {
    if (typeof value === "string") return value;
    if (typeof value === "number" && Number.isFinite(value)) return String(value);
    return undefined;
}

function asStringArray(value: unknown): string[] {
    return Array.isArray(value) ? value.filter((v): v is string => typeof v === "string") : [];
}

function asNumber(value: unknown): number | undefined {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string") {
        const trimmed = value.trim();
        if (!trimmed) return undefined;
        const n = Number(trimmed.replaceAll(",", ""));
        return Number.isFinite(n) ? n : undefined;
    }
    return undefined;
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

function getLocaleFromMeta(meta: Record<string, unknown> | undefined): Record<string, unknown> | undefined {
    return meta && isRecord(meta["locale"]) ? meta["locale"] : undefined;
}

function getDocumentVersionFromRoot(parsedObj: Record<string, unknown>): string | undefined {
    const versionKeys = [
        "crml_scenario",
        "crml_portfolio",
        "crml_assessment",
        "crml_control_catalog",
        "crml_attack_catalog",
        "crml_control_relationships",
        "crml_attack_control_relationships",
    ] as const;

    for (const key of versionKeys) {
        const version = asString(parsedObj[key]);
        if (version) return version;
    }

    return undefined;
}

function extractPortfolioBundleMeta(
    parsedObj: Record<string, unknown>,
    portfolioBundleVersion: string
): {
    meta: Record<string, unknown> | undefined;
    locale: Record<string, unknown> | undefined;
    documentVersion: string | undefined;
} {
    const bundle = isRecord(parsedObj["portfolio_bundle"]) ? parsedObj["portfolio_bundle"] : undefined;

    const bundleMeta = bundle && isRecord(bundle["meta"]) ? bundle["meta"] : undefined;
    const portfolio = bundle && isRecord(bundle["portfolio"]) ? bundle["portfolio"] : undefined;
    const portfolioMeta = portfolio && isRecord(portfolio["meta"]) ? portfolio["meta"] : undefined;

    const meta = bundleMeta ?? portfolioMeta;
    const locale = getLocaleFromMeta(meta);

    return { meta, locale, documentVersion: portfolioBundleVersion };
}

function extractMeta(parsedYaml: unknown): {
    meta: Record<string, unknown> | undefined;
    locale: Record<string, unknown> | undefined;
    documentVersion: string | undefined;
} {
    const parsedObj = isRecord(parsedYaml) ? parsedYaml : undefined;
    if (!parsedObj) {
        return { meta: undefined, locale: undefined, documentVersion: undefined };
    }

    // Portfolio Bundle: metadata can live under:
    // - portfolio_bundle.meta (bundle-level), or
    // - portfolio_bundle.portfolio.meta (embedded portfolio)
    const portfolioBundleVersion = asString(parsedObj["crml_portfolio_bundle"]);
    if (portfolioBundleVersion) {
        return extractPortfolioBundleMeta(parsedObj, portfolioBundleVersion);
    }

    const meta = isRecord(parsedObj["meta"]) ? parsedObj["meta"] : undefined;
    const locale = getLocaleFromMeta(meta);
    const documentVersion = getDocumentVersionFromRoot(parsedObj);

    return { meta, locale, documentVersion };
}

function extractRiskTolerance(parsedYaml: unknown): { metric?: string; threshold?: number; currency?: string } | undefined {
    const parsedObj = isRecord(parsedYaml) ? parsedYaml : undefined;
    if (!parsedObj) return undefined;

    // Portfolio Bundle: portfolio_bundle.portfolio.portfolio.risk_tolerance
    const bundleVersion = asString(parsedObj["crml_portfolio_bundle"]);
    if (bundleVersion) {
        const bundle = isRecord(parsedObj["portfolio_bundle"]) ? parsedObj["portfolio_bundle"] : undefined;
        const portfolioDoc = bundle && isRecord(bundle["portfolio"]) ? bundle["portfolio"] : undefined;
        const portfolioBody = portfolioDoc && isRecord(portfolioDoc["portfolio"]) ? portfolioDoc["portfolio"] : undefined;
        const rt = portfolioBody && isRecord(portfolioBody["risk_tolerance"]) ? portfolioBody["risk_tolerance"] : undefined;
        if (!rt) return undefined;
        const metric = asString(rt["metric"]);
        const threshold = asNumber(rt["threshold"]);
        const currency = asString(rt["currency"]);
        if (!metric && threshold == null && !currency) return undefined;
        return { metric, threshold, currency };
    }

    // Portfolio: portfolio.risk_tolerance
    const portfolioVersion = asString(parsedObj["crml_portfolio"]);
    if (portfolioVersion) {
        const portfolioBody = isRecord(parsedObj["portfolio"]) ? parsedObj["portfolio"] : undefined;
        const rt = portfolioBody && isRecord(portfolioBody["risk_tolerance"]) ? portfolioBody["risk_tolerance"] : undefined;
        if (!rt) return undefined;
        const metric = asString(rt["metric"]);
        const threshold = asNumber(rt["threshold"]);
        const currency = asString(rt["currency"]);
        if (!metric && threshold == null && !currency) return undefined;
        return { metric, threshold, currency };
    }

    return undefined;
}

function buildInfo(
    meta: Record<string, unknown> | undefined,
    locale: Record<string, unknown> | undefined,
    documentVersion: string | undefined,
    riskTolerance: { metric?: string; threshold?: number } | undefined
) {
    return {
        name: typeof meta?.["name"] === "string" ? meta["name"] : undefined,
        version:
            asString(meta?.["version"]) ??
            (typeof documentVersion === "string" ? documentVersion : undefined),
        description: typeof meta?.["description"] === "string" ? meta["description"] : undefined,
        author: typeof meta?.["author"] === "string" ? meta["author"] : undefined,
        organization: typeof meta?.["organization"] === "string" ? meta["organization"] : undefined,
        company_sizes: asStringArray(meta?.["company_sizes"]),
        industries: asStringArray(meta?.["industries"]),
        regulatory_frameworks: asStringArray(meta?.["regulatory_frameworks"]),
        tags: asStringArray(meta?.["tags"]),
        regions: asStringArray(locale?.["regions"]),
        countries: asStringArray(locale?.["countries"]),
        risk_tolerance: riskTolerance,
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
        .map((line) => line.replace("[ERROR]", "").trim())
        .map(sanitizeErrorMessage);
}

/**
 * Sanitize error messages to make them user-friendly
 * - Remove temporary file paths
 * - Simplify technical jargon
 * - Provide actionable context
 */
function sanitizeErrorMessage(error: string): string {
    // Remove temporary file paths (e.g., /var/folders/.../crml-validator/crml-123456.yaml)
    let sanitized = error.replaceAll(/\/(?:var|tmp)\/[^\s]+\/crml-validator\/[^\s]+\.yaml/g, "your bundle");
    sanitized = sanitized.replaceAll(/\/(?:var|tmp)\/[^\s]+\.yaml/g, "your bundle");

    // Remove Windows temp paths
    sanitized = sanitized.replaceAll(/[A-Z]:\\\\(?:Users|Windows|Temp)\\\\[^\s]+\\\\crml-validator\\\\[^\s]+\.yaml/g, "your bundle");

    // Improve common error messages
    if (sanitized.includes("failed CRML") && sanitized.includes("validation")) {
        // Extract version if present
        const versionMatch = /CRML\s+([\d.]+)/.exec(sanitized);
        const version = versionMatch?.[1] ?? "1.0";

        sanitized = `The bundle failed CRML ${version} validation. This usually means there are schema errors or incompatible configurations in your selected scenarios.`;
    }

    // Make "Additional property" errors more friendly
    if (sanitized.includes("Additional property") || sanitized.includes("additional property")) {
        sanitized = sanitized.replaceAll(/Additional property/gi, "Unexpected field");
    }

    // Clean up "is not allowed" messages
    if (sanitized.includes("is not allowed")) {
        sanitized += " Check the CRML schema documentation for valid fields.";
    }

    return sanitized;
}

type ExecResult = { stdout: string; stderr: string; ok: boolean; message?: string };

function findRepoRoot(startDir: string): string | undefined {
    let current = startDir;
    for (let i = 0; i < 6; i++) {
        const engineCli = path.join(current, "crml_engine", "src", "crml_engine", "cli.py");
        const langPkg = path.join(current, "crml_lang", "src", "crml_lang");
        if (existsSync(engineCli) && existsSync(langPkg)) return current;

        const parent = path.dirname(current);
        if (parent === current) break;
        current = parent;
    }
    return undefined;
}

function shouldFallbackToPython(message: string, combinedOutput: string): boolean {
    const text = `${message}\n${combinedOutput}`.toLowerCase();

    // Common "can't execute" / missing module symptoms on Windows.
    return (
        text.includes("enoent") ||
        text.includes("is not recognized as an internal or external command") ||
        text.includes("modulenotfounderror") ||
        text.includes("no module named") ||
        text.includes("importerror")
    );
}

async function runExecFile(cmd: string, args: string[], env?: NodeJS.ProcessEnv): Promise<ExecResult> {
    try {
        const { stdout, stderr } = await execFileAsync(cmd, args, {
            env,
            windowsHide: true,
            maxBuffer: 10 * 1024 * 1024,
        });
        return { stdout: stdout ?? "", stderr: stderr ?? "", ok: true };
    } catch (execError: unknown) {
        const err = execError as {
            stdout?: string;
            stderr?: string;
            message?: string;
        };
        return {
            stdout: err.stdout || "",
            stderr: err.stderr || "",
            ok: false,
            message: err.message,
        };
    }
}

async function execCrmlValidate(tmpFile: string): Promise<ExecResult> {
    // 1. If we are in the repo, prefer running from source (dev mode).
    // This ensures that changes to crml_lang/crml_engine source are picked up immediately,
    // bypassing any stale "crml" binary in the path.
    const repoRoot = findRepoRoot(process.cwd());
    if (repoRoot) {
        const pythonPathParts = [
            path.join(repoRoot, "crml_lang", "src"),
            path.join(repoRoot, "crml_engine", "src"),
        ];

        const delimiter = process.platform === "win32" ? ";" : ":";
        const pythonpath = [process.env.PYTHONPATH, ...pythonPathParts].filter(Boolean).join(delimiter);
        const env = { ...process.env, PYTHONPATH: pythonpath };

        // Try common Python launchers, prioritizing local .venv if it exists.
        const venvPython =
            process.platform === "win32"
                ? path.join(repoRoot, ".venv", "Scripts", "python.exe")
                : path.join(repoRoot, ".venv", "bin", "python3");

        const candidates: Array<{ cmd: string; argsPrefix: string[] }> = [
            { cmd: venvPython, argsPrefix: [] },
            ...(process.platform === "win32"
                ? [
                    { cmd: "py", argsPrefix: ["-3"] },
                    { cmd: "python", argsPrefix: [] },
                ]
                : [
                    { cmd: "python3", argsPrefix: [] },
                    { cmd: "python", argsPrefix: [] },
                ]),
        ];

        for (const candidate of candidates) {
            // Check if candidate exists or is executable (simple check by trying to run it)
            // But runExecFile handles failures gracefully.
            const attempt = await runExecFile(
                candidate.cmd,
                [...candidate.argsPrefix, "-m", "crml_engine.cli", "validate", tmpFile],
                env
            );

            // If it ran successfully (ok=true), return it. 
            // If it failed because of "module not found" or "command not found", we continue.
            // But if it ran and returned exit code 1 (validation error), we should probably return it
            // unless we suspect environment issues. 
            // For now, if it executed (ok=true) OR if it failed with a validation error (code 1),
            // runExecFile catches non-zero exit codes.
            // Wait, runExecFile implementation in this file catches error and returns { ok: false, ... }.
            // We need to differentiate "execution failed (no python)" from "validation failed".
            // If message includes/implies 'module not found', continue.

            if (attempt.ok) return attempt;

            const output = `${attempt.stdout}\n${attempt.stderr}`;
            if (!shouldFallbackToPython(attempt.message || "", output)) {
                // It ran but failed validation (or other runtime error), so trust this result.
                return attempt;
            }
            // Otherwise (missing python, missing module), try next candidate.
        }
    }

    // 2. Try the local .venv CLI (legacy check).
    const venvBin = process.platform === 'win32' ? 'Scripts' : 'bin';
    const venvCrml = path.join(process.cwd(), "..", ".venv", venvBin, "crml");
    const venvAttempt = await runExecFile(venvCrml, ["validate", tmpFile], process.env);
    if (venvAttempt.ok) return venvAttempt;

    // 3. Fallback to globally installed 'crml'
    const direct = await runExecFile("crml", ["validate", tmpFile], process.env);
    return direct;
}

export async function POST(request: NextRequest) {
    try {
        const body: unknown = await request.json();
        const yamlContentResult = getYamlContentFromBody(body);
        if (!yamlContentResult.ok) return yamlContentResult.response;

        const parsedYamlResult = parseYaml(yamlContentResult.value);
        if (!parsedYamlResult.ok) return parsedYamlResult.response;

        const { meta, locale, documentVersion } = extractMeta(parsedYamlResult.value);
        const riskTolerance = extractRiskTolerance(parsedYamlResult.value);
        const info = buildInfo(meta, locale, documentVersion, riskTolerance);

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
