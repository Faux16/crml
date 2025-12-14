import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink, mkdir } from "fs/promises";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import os from "os";
import yaml from "js-yaml";

const execAsync = promisify(exec);

export async function POST(request: NextRequest) {
    try {
        const { yaml: yamlContent } = await request.json();

        if (!yamlContent) {
            return NextResponse.json(
                { valid: false, errors: ["No YAML content provided"] },
                { status: 400 }
            );
        }

        // Parse YAML to extract metadata
        let parsedYaml: any;
        try {
            parsedYaml = yaml.load(yamlContent);
        } catch (error) {
            return NextResponse.json({
                valid: false,
                errors: [`YAML parsing error: ${(error as Error).message}`],
            });
        }

        // Use OS-specific temp directory (cross-platform)
        const tmpDir = path.join(os.tmpdir(), "crml-validator");
        await mkdir(tmpDir, { recursive: true });
        const tmpFile = path.join(tmpDir, `crml-${Date.now()}.yaml`);

        try {
            // Write YAML content to temporary file
            await writeFile(tmpFile, yamlContent, "utf-8");

            // Extract model info
            const info = {
                name: parsedYaml?.meta?.name,
                version: parsedYaml?.meta?.version,
                description: parsedYaml?.meta?.description,
            };

            // Run CRML validation
            try {
                const { stdout, stderr } = await execAsync(`crml validate "${tmpFile}"`);

                // Check if validation passed
                if (stdout.includes("[OK]")) {
                    // Extract warnings from stdout
                    const warnings = stdout
                        .split("\n")
                        .filter((line) => line.includes("[WARNING]"))
                        .map((line) => line.replace("[WARNING]", "").trim());

                    return NextResponse.json({
                        valid: true,
                        info,
                        warnings,
                    });
                } else {
                    // Parse errors from stderr or stdout
                    const errors = (stderr || stdout)
                        .split("\n")
                        .filter((line) => line.trim() && !line.includes("[OK]"))
                        // Filter out summary lines like "file.yaml failed CRML 1.1 validation with X error(s):"
                        .filter((line) => !line.match(/failed CRML.*validation with \d+ error\(s\)/i))
                        .map((line) => line.trim());

                    return NextResponse.json({
                        valid: false,
                        errors: errors.length > 0 ? errors : ["Validation failed"],
                        info,
                    });
                }
            } catch (execError: any) {
                // exec throws when command exits with non-zero code
                // But stdout/stderr are still available on the error object
                const stdout = execError.stdout || "";
                const stderr = execError.stderr || "";
                const output = stdout + "\n" + stderr;

                // Parse the actual validation errors from output
                const errorLines = output
                    .split("\n")
                    .filter((line: string) => line.trim())
                    .filter((line: string) => 
                        line.includes("[ERROR]") || 
                        line.match(/^\s*\d+\./) ||  // numbered errors like "  1. [path] message"
                        line.includes("failed CRML")
                    )
                    // Filter out summary lines that just state the failure count
                    .filter((line: string) => !line.match(/failed CRML.*validation with \d+ error\(s\)/i))
                    .map((line: string) => line.replace("[ERROR]", "").trim());

                // Extract warnings too
                const warnings = output
                    .split("\n")
                    .filter((line: string) => line.includes("[WARNING]"))
                    .map((line: string) => line.replace("[WARNING]", "").trim());

                return NextResponse.json({
                    valid: false,
                    errors: errorLines.length > 0 ? errorLines : [`Validation failed: ${execError.message}`],
                    warnings,
                    info,
                });
            }
        } finally {
            // Clean up temporary file
            try {
                await unlink(tmpFile);
            } catch (error) {
                // Ignore cleanup errors
            }
        }
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
