import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'node:child_process';
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

async function commandExists(cmd: string): Promise<boolean> {
    return await new Promise((resolve) => {
        const which = process.platform === 'win32' ? 'where' : 'which';
        const check = spawn(which, [cmd]);
        check.on('close', (code) => resolve(code === 0));
        check.on('error', () => resolve(false));
    });
}

async function pickPythonCommand(): Promise<string | undefined> {
    if (await commandExists('python3')) return 'python3';
    if (await commandExists('python')) return 'python';
    return undefined;
}

export async function POST(request: NextRequest) {
    try {
        const body: unknown = await request.json();
        const yaml = isRecord(body) && typeof body['yaml'] === 'string' ? body['yaml'] : undefined;
        const runs = isRecord(body) ? body['runs'] : undefined;
        const seed = isRecord(body) ? body['seed'] : undefined;
        const outputCurrency = isRecord(body) && typeof body['outputCurrency'] === 'string' ? body['outputCurrency'] : 'USD';

        if (!yaml) {
            return NextResponse.json(
                { success: false, errors: ['YAML content is required'] },
                { status: 400 }
            );
        }

        // Validate runs parameter
        const numRuns = parseIntegerFromNumberOrString(runs);
        if (numRuns == null || numRuns < 100 || numRuns > 100000) {
            return NextResponse.json(
                { success: false, errors: ['Runs must be between 100 and 100,000'] },
                { status: 400 }
            );
        }

        // Validate currency
        if (!isValidCurrency(outputCurrency)) {
            return NextResponse.json(
                { success: false, errors: [`Invalid currency: ${outputCurrency}`] },
                { status: 400 }
            );
        }

        // Run Python simulation
    const seedNumber = parseIntegerFromNumberOrString(seed);
        const result = await runSimulation(yaml, numRuns, seedNumber, outputCurrency);

        return NextResponse.json(result);
    } catch (error) {
        console.error('Simulation error:', error);
        return NextResponse.json(
            {
                success: false,
                errors: [`Server error: ${error instanceof Error ? error.message : 'Unknown error'}`]
            },
            { status: 500 }
        );
    }
}

async function runSimulation(yamlContent: string, runs: number, seed: number | undefined, outputCurrency: string): Promise<unknown> {
    const pythonCmd = await pickPythonCommand();
    if (!pythonCmd) {
        return {
            success: false,
            errors: ['Neither python3 nor python was found on the server.'],
            metrics: {},
            distribution: {},
            metadata: {},
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

# Read YAML from stdin
yaml_content = sys.stdin.read()

fx_config = {
    "base_currency": "USD",
    "output_currency": "${outputCurrency}",
    "rates": None  # Use default rates
}

result = run_simulation_envelope(yaml_content, n_runs=${runs}${seedArg}, fx_config=fx_config)
print(json.dumps(result.model_dump()))
`;

    const { stdout, stderr, exitCode, timedOut } = await runPythonWithStdin(pythonCmd, pythonCode, yamlContent, 30000);
    if (timedOut) {
        return {
            success: false,
            errors: ['Simulation timeout (30s exceeded)'],
            metrics: {},
            distribution: {},
            metadata: {},
        };
    }

    if (exitCode !== 0) {
        console.error('Python stderr:', stderr);
        return {
            success: false,
            errors: [`Simulation failed: ${stderr || 'Unknown error'}`],
            metrics: {},
            distribution: {},
            metadata: {},
        };
    }

    try {
        return JSON.parse(stdout);
    } catch {
        console.error('Failed to parse Python output:', stdout);
        return {
            success: false,
            errors: ['Failed to parse simulation results'],
            metrics: {},
            distribution: {},
            metadata: {},
        };
    }
}

function runPythonWithStdin(
    pythonCmd: string,
    pythonCode: string,
    stdinContent: string,
    timeoutMs: number,
): Promise<{ stdout: string; stderr: string; exitCode: number | null; timedOut: boolean }> {
    return new Promise((resolve, reject) => {
        const python = spawn(pythonCmd, ['-c', pythonCode], {
            stdio: ['pipe', 'pipe', 'pipe'],
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        python.stdin.write(stdinContent);
        python.stdin.end();

        let timedOut = false;
        const timeout = setTimeout(() => {
            timedOut = true;
            python.kill();
        }, timeoutMs);

        python.on('close', (code) => {
            clearTimeout(timeout);
            resolve({ stdout, stderr, exitCode: code, timedOut });
        });

        python.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}
