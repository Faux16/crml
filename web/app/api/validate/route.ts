import { NextRequest, NextResponse } from "next/server";
import { writeFile, unlink } from "fs/promises";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
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

        // Create a temporary file
        const tmpDir = "/tmp";
        const tmpFile = path.join(tmpDir, `crml-${Date.now()}.yaml`);

        try {
            // Write YAML content to temporary file
            await writeFile(tmpFile, yamlContent, "utf-8");

            // Run CRML validation
            const { stdout, stderr } = await execAsync(`crml validate ${tmpFile}`);

            // Extract model info
            const info = {
                name: parsedYaml?.meta?.name,
                version: parsedYaml?.meta?.version,
                description: parsedYaml?.meta?.description,
            };

            // Check if validation passed
            if (stdout.includes("[OK]") || stdout.includes("valid")) {
                return NextResponse.json({
                    valid: true,
                    info,
                });
            } else {
                // Parse errors from stderr or stdout
                const errors = stderr
                    ? stderr.split("\n").filter((line) => line.trim())
                    : ["Validation failed"];

                return NextResponse.json({
                    valid: false,
                    errors,
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
