import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import path from 'node:path';

const VALID_CURRENCIES = new Set([
    'USD', 'EUR', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'BRL', 'MXN', 'KRW', 'SGD', 'HKD', 'PKR',
]);

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function parseIntegerFromNumberOrString(value: unknown): number | undefined {
    if (typeof value === 'number') return value;
    if (typeof value !== 'string') return undefined;
    const parsed = Number.parseInt(value, 10);
    return Number.isNaN(parsed) ? undefined : parsed;
}

function isValidCurrency(currency: string): boolean {
    return VALID_CURRENCIES.has(currency);
}

function errorEnvelope(message: string, status = 400, run?: { runs?: number; seed?: number }) {
    return NextResponse.json(
        {
            crml_simulation_result: '1.0',
            result: {
                success: false,
                errors: [message],
                warnings: [],
                engine: { name: 'web', version: undefined },
                run,
                inputs: {},
                results: { measures: [], artifacts: [] },
            },
        },
        { status },
    );
}

async function commandExists(cmd: string): Promise<boolean> {
    return await new Promise((resolve) => {
        const which = process.platform === 'win32' ? 'where' : 'which';
        const check = spawn(which, [cmd]);
        check.on('close', (code) => resolve(code === 0));
        check.on('error', () => resolve(false));
    });
}

type PythonCandidate = { cmd: string; argsPrefix: string[] };

function isNonEmptyString(value: unknown): value is string {
    return typeof value === 'string' && value.trim().length > 0;
}

async function pickPythonCandidates(): Promise<PythonCandidate[]> {
    const envPython = process.env.CRML_PYTHON;
    const candidates: PythonCandidate[] = [];

    if (isNonEmptyString(envPython)) {
        candidates.push({ cmd: envPython, argsPrefix: [] });
    }

    const venvPython = process.platform === 'win32'
        ? path.join(process.cwd(), '..', '.venv', 'Scripts', 'python.exe')
        : path.join(process.cwd(), '..', '.venv', 'bin', 'python3');

    // Note: on Windows, the venv python.exe can exist but still fail to launch if
    // its base interpreter was moved/removed. We'll detect that at runtime and
    // fall back to the next candidates.
    if (existsSync(venvPython)) {
        candidates.push({ cmd: venvPython, argsPrefix: [] });
    }

    if (process.platform === 'win32') {
        if (await commandExists('py')) candidates.push({ cmd: 'py', argsPrefix: ['-3'] });
        if (await commandExists('python')) candidates.push({ cmd: 'python', argsPrefix: [] });
    } else {
        if (await commandExists('python3')) candidates.push({ cmd: 'python3', argsPrefix: [] });
        if (await commandExists('python')) candidates.push({ cmd: 'python', argsPrefix: [] });
    }

    // Remove duplicates while preserving order.
    const seen = new Set<string>();
    return candidates.filter((c) => {
        const key = `${c.cmd}::${c.argsPrefix.join(' ')}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

export async function POST(request: NextRequest) {
    try {
        const body: unknown = await request.json();
        const yaml = isRecord(body) && typeof body['yaml'] === 'string' ? body['yaml'] : undefined;
        const runs = isRecord(body) ? body['runs'] : undefined;
        const seed = isRecord(body) ? body['seed'] : undefined;
        const outputCurrency = isRecord(body) && typeof body['outputCurrency'] === 'string' ? body['outputCurrency'] : 'USD';

        if (!yaml) {
            return errorEnvelope('YAML content is required', 400);
        }

        // Validate runs parameter
        const numRuns = parseIntegerFromNumberOrString(runs);
        if (numRuns == null || numRuns < 100 || numRuns > 100000) {
            return errorEnvelope('Runs must be between 100 and 100,000', 400);
        }

        // Validate currency
        if (!isValidCurrency(outputCurrency)) {
            return errorEnvelope(`Invalid currency: ${outputCurrency}`, 400, { runs: numRuns });
        }

        // Run Python simulation
        const seedNumber = parseIntegerFromNumberOrString(seed);
        const result = await runSimulation(yaml, numRuns, seedNumber, outputCurrency);

        return NextResponse.json(result);
    } catch (error) {
        console.error('Simulation error:', error);
        return errorEnvelope(`Server error: ${error instanceof Error ? error.message : 'Unknown error'}`, 500);
    }
}

async function runSimulation(yamlContent: string, runs: number, seed: number | undefined, outputCurrency: string): Promise<unknown> {
    const candidates = await pickPythonCandidates();
    if (candidates.length === 0) {
        return {
            crml_simulation_result: '1.0',
            result: {
                success: false,
                errors: ['Neither python3 nor python was found on the server.'],
                warnings: [],
                engine: { name: 'web', version: undefined },
                run: { runs, seed },
                inputs: {},
                results: { measures: [], artifacts: [] },
            },
        };
    }

    const seedArg = seed === undefined ? '' : `, seed=${seed}`;

    // Read YAML from stdin instead of embedding in code
    const pythonCode = `
import sys
import json

sys.path.insert(0, r'${path.join(process.cwd(), '..', 'crml_engine', 'src')}')
sys.path.insert(0, r'${path.join(process.cwd(), '..', 'crml_lang', 'src')}')

from crml_engine.runtime import run_simulation_envelope

yaml_content = sys.stdin.read()

fx_config = {
    "base_currency": "USD",
    "output_currency": "${outputCurrency}",
    "rates": None,
}

result = run_simulation_envelope(yaml_content, n_runs=${runs}${seedArg}, fx_config=fx_config)
payload = result.model_dump(mode='json')
print(json.dumps(payload, ensure_ascii=True))
`;

    const timeoutMs = 30000;

    let lastStderr = '';
    for (const candidate of candidates) {
        const { stdout, stderr, exitCode, timedOut } = await runPythonWithStdin(
            candidate,
            pythonCode,
            yamlContent,
            timeoutMs,
        );

        if (timedOut) {
            return {
                crml_simulation_result: '1.0',
                result: {
                    success: false,
                    errors: ['Simulation timeout (30s exceeded)'],
                    warnings: [],
                    engine: { name: 'web', version: undefined },
                    run: { runs, seed },
                    inputs: {},
                    results: { measures: [], artifacts: [] },
                },
            };
        }

        if (exitCode !== 0) {
            lastStderr = stderr;
            const lower = (stderr || '').toLowerCase();
            // Common symptom of a broken venv launcher on Windows (base interpreter moved).
            if (lower.includes('did not find executable at') || lower.includes('the system cannot find the path specified')) {
                continue;
            }
            console.error('Python stderr:', stderr);
            return {
                crml_simulation_result: '1.0',
                result: {
                    success: false,
                    errors: [`Simulation failed: ${stderr || 'Unknown error'}`],
                    warnings: [],
                    engine: { name: 'web', version: undefined },
                    run: { runs, seed },
                    inputs: {},
                    results: { measures: [], artifacts: [] },
                },
            };
        }

        try {
            return JSON.parse(stdout.trim());
        } catch {
            console.error('Failed to parse Python output:', stdout);
            return {
                crml_simulation_result: '1.0',
                result: {
                    success: false,
                    errors: ['Failed to parse simulation results'],
                    warnings: [],
                    engine: { name: 'web', version: undefined },
                    run: { runs, seed },
                    inputs: {},
                    results: { measures: [], artifacts: [] },
                },
            };
        }
    }

    return {
        crml_simulation_result: '1.0',
        result: {
            success: false,
            errors: [
                "Python could not be started for simulation. If you're on Windows and your .venv was created with a different Python install, recreate it or set CRML_PYTHON.",
                lastStderr || 'No Python candidates succeeded.',
            ],
            warnings: [],
            engine: { name: 'web', version: undefined },
            run: { runs, seed },
            inputs: {},
            results: { measures: [], artifacts: [] },
        },
    };
}

function runPythonWithStdin(
    python: PythonCandidate,
    pythonCode: string,
    stdinContent: string,
    timeoutMs: number,
): Promise<{ stdout: string; stderr: string; exitCode: number | null; timedOut: boolean }> {
    return new Promise((resolve, reject) => {
        const child = spawn(python.cmd, [...python.argsPrefix, '-c', pythonCode], {
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        let stdout = '';
        let stderr = '';

        child.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        child.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        child.stdin.write(stdinContent);
        child.stdin.end();

        let timedOut = false;
        const timeout = setTimeout(() => {
            timedOut = true;
            child.kill();
        }, timeoutMs);

        child.on('close', (code) => {
            clearTimeout(timeout);
            resolve({ stdout, stderr, exitCode: code, timedOut });
        });

        child.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}
