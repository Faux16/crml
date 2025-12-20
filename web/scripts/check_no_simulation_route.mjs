import fs from "node:fs/promises";
import path from "node:path";

const FORBIDDEN_PATTERNS = [
  {
    name: "hardcoded /simulation route",
    regex: /["']\/simulation(?:["'?#/]|\s|$)/g,
  },
  {
    name: "localhost /simulation URL",
    regex: /http:\/\/localhost:3000\/simulation\b/g,
  },
];

const DEFAULT_INCLUDE_DIRS = [
  // Web app sources
  "app",
  "components",
  "lib",
  // Docs in repo root
  path.join("..", "wiki"),
  path.join("..", "README.md"),
  "README.md",
];

const SKIP_DIR_NAMES = new Set([
  ".next",
  "node_modules",
  ".git",
  "dist",
  "build",
  "out",
  "coverage",
]);

const ALLOWED_EXTENSIONS = new Set([".ts", ".tsx", ".js", ".jsx", ".md", ".mdx"]);

async function isDirectory(p) {
  try {
    return (await fs.stat(p)).isDirectory();
  } catch {
    return false;
  }
}

async function isFile(p) {
  try {
    return (await fs.stat(p)).isFile();
  } catch {
    return false;
  }
}

async function walkFiles(startPath, collected) {
  const basename = path.basename(startPath);
  if (SKIP_DIR_NAMES.has(basename)) return;

  if (await isFile(startPath)) {
    const ext = path.extname(startPath);
    if (ALLOWED_EXTENSIONS.has(ext)) collected.push(startPath);
    return;
  }

  if (!(await isDirectory(startPath))) return;

  const entries = await fs.readdir(startPath, { withFileTypes: true });
  for (const entry of entries) {
    if (entry.isSymbolicLink()) continue;

    const fullPath = path.join(startPath, entry.name);
    if (entry.isDirectory()) {
      if (SKIP_DIR_NAMES.has(entry.name)) continue;
      await walkFiles(fullPath, collected);
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      if (ALLOWED_EXTENSIONS.has(ext)) collected.push(fullPath);
    }
  }
}

function findMatches(content) {
  const matches = [];
  for (const pattern of FORBIDDEN_PATTERNS) {
    pattern.regex.lastIndex = 0;
    let match;
    while ((match = pattern.regex.exec(content)) !== null) {
      matches.push({ name: pattern.name, index: match.index, snippet: match[0] });
    }
  }
  return matches;
}

function indexToLineCol(text, index) {
  const before = text.slice(0, index);
  const lines = before.split(/\r?\n/);
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  return { line, col };
}

async function main() {
  const webDir = process.cwd();

  const targets = DEFAULT_INCLUDE_DIRS.map((p) => path.resolve(webDir, p));

  const files = [];
  for (const target of targets) {
    await walkFiles(target, files);
  }

  const violations = [];
  for (const filePath of files) {
    const content = await fs.readFile(filePath, "utf8");
    const matches = findMatches(content);
    for (const m of matches) {
      const { line, col } = indexToLineCol(content, m.index);
      violations.push({ filePath, line, col, kind: m.name, snippet: m.snippet });
    }
  }

  if (violations.length > 0) {
    const rel = (p) => path.relative(path.resolve(webDir, ".."), p).replace(/\\/g, "/");

    console.error("Found forbidden references to the legacy /simulation route.\n");
    for (const v of violations) {
      console.error(`- ${rel(v.filePath)}:${v.line}:${v.col} (${v.kind}) -> ${v.snippet}`);
    }
    console.error("\nUse /playground?tab=simulate instead.");
    process.exit(1);
  }

  console.log("OK: no legacy /simulation route references found.");
}

await main();
