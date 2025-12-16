import { NextRequest, NextResponse } from 'next/server';
import { spawn } from 'child_process';
import path from 'path';

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { yaml, runs = 10000, seed, outputCurrency = 'USD' } = body;

        if (!yaml) {
            return NextResponse.json(
                { success: false, errors: ['YAML content is required'] },
                { status: 400 }
            );
        }

        // Validate runs parameter
        const numRuns = parseInt(runs as string);
        if (isNaN(numRuns) || numRuns < 100 || numRuns > 100000) {
            return NextResponse.json(
                { success: false, errors: ['Runs must be between 100 and 100,000'] },
                { status: 400 }
            );
        }

        // Validate currency
        const validCurrencies = ['USD', 'EUR', 'GBP', 'CHF', 'JPY', 'CAD', 'AUD', 'CNY', 'INR', 'BRL', 'MXN', 'KRW', 'SGD', 'HKD', 'PKR'];
        if (!validCurrencies.includes(outputCurrency)) {
            return NextResponse.json(
                { success: false, errors: [`Invalid currency: ${outputCurrency}`] },
                { status: 400 }
            );
        }

        // Run Python simulation
        const result = await runSimulation(yaml, numRuns, seed, outputCurrency);

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

async function runSimulation(yamlContent: string, runs: number, seed?: number, outputCurrency: string = 'USD'): Promise<any> {
    return new Promise(async (resolve, reject) => {
        // Read YAML from stdin instead of embedding in code
        const pythonCode = `
import sys
import json
sys.path.insert(0, r'${path.join(process.cwd(), '..', 'src')}')

from crml.runtime import run_simulation

# Read YAML from stdin
yaml_content = sys.stdin.read()

fx_config = {
    "base_currency": "USD",
    "output_currency": "${outputCurrency}",
    "rates": None  # Use default rates
}

result = run_simulation(yaml_content, n_runs=${runs}${seed ? `, seed=${seed}` : ''}, fx_config=fx_config)
print(json.dumps(result.model_dump()))
`;


        // Helper to check if a command exists
        async function commandExists(cmd: string): Promise<boolean> {
            return new Promise((resolve) => {
                const which = process.platform === 'win32' ? 'where' : 'which';
                const check = spawn(which, [cmd]);
                check.on('close', (code) => resolve(code === 0));
                check.on('error', () => resolve(false));
            });
        }

        let pythonCmd = 'python3';
        if (!(await commandExists('python3'))) {
            if (await commandExists('python')) {
                pythonCmd = 'python';
            } else {
                resolve({
                    success: false,
                    errors: ['Neither python3 nor python was found on the server.'],
                    metrics: {},
                    distribution: {},
                    metadata: {}
                });
                return;
            }
        }

        const python = spawn(pythonCmd, ['-c', pythonCode], {
            stdio: ['pipe', 'pipe', 'pipe']  // Enable stdin pipe
        });

        let stdout = '';
        let stderr = '';

        python.stdout.on('data', (data) => {
            stdout += data.toString();
        });

        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });

        // Write YAML content to stdin and close it
        python.stdin.write(yamlContent);
        python.stdin.end();

        // Set timeout for 30 seconds
        const timeout = setTimeout(() => {
            python.kill();
            reject(new Error('Simulation timeout (30s exceeded)'));
        }, 30000);

        python.on('close', (code) => {
            clearTimeout(timeout);

            if (code !== 0) {
                console.error('Python stderr:', stderr);
                resolve({
                    success: false,
                    errors: [`Simulation failed: ${stderr || 'Unknown error'}`],
                    metrics: {},
                    distribution: {},
                    metadata: {}
                });
                return;
            }

            try {
                // Parse the JSON output from Python
                const result = JSON.parse(stdout);
                resolve(result);
            } catch (error) {
                console.error('Failed to parse Python output:', stdout);
                resolve({
                    success: false,
                    errors: ['Failed to parse simulation results'],
                    metrics: {},
                    distribution: {},
                    metadata: {}
                });
            }
        });

        python.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
    });
}
