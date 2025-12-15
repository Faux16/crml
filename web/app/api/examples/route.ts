import { NextResponse } from "next/server";
import { readFile, readdir } from "fs/promises";
import path from "path";
import yaml from "js-yaml";

export async function GET() {
    try {
        // Path to examples directory (relative to project root)
        const examplesDir = path.join(process.cwd(), "..", "spec", "examples");

        // Read all files and filter to only include YAML files, excluding FX config files
        const files = await readdir(examplesDir);
        const yamlFiles = files.filter(
            (file) => (file.endsWith(".yaml") || file.endsWith(".yml")) &&
                !file.startsWith("fx-config")
        );

        // Read and parse each example
        const examples = await Promise.all(
            yamlFiles.map(async (file) => {
                const filePath = path.join(examplesDir, file);
                const content = await readFile(filePath, "utf-8");

                try {
                    const parsed: any = yaml.load(content);
                    return {
                        id: file.replace(/\.(yaml|yml)$/, ""),
                        filename: file,
                        name: parsed?.meta?.name || file,
                        description: parsed?.meta?.description || "No description available",
                        tags: parsed?.meta?.tags || [],
                        content,
                    };
                } catch (error) {
                    return {
                        id: file.replace(/\.(yaml|yml)$/, ""),
                        filename: file,
                        name: file,
                        description: "Error parsing file",
                        tags: [],
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
