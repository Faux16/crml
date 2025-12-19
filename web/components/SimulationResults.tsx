"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Download, TrendingUp, AlertCircle, BarChart3, HelpCircle, Info, DollarSign } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

export interface SimulationMetrics {
    eal: number;
    var_95: number;
    var_99: number;
    var_999: number;
    min: number;
    max: number;
    median: number;
    std_dev: number;
}

export interface CrmlCurrencyUnit {
    kind: "currency";
    code: string;
    symbol?: string;
}

export interface CrmlMeasure {
    id: string;
    value?: number;
    unit?: CrmlCurrencyUnit;
    parameters?: Record<string, unknown>;
    label?: string;
}

export interface CrmlHistogramArtifact {
    kind: "histogram";
    id: string;
    unit?: CrmlCurrencyUnit;
    bin_edges: number[];
    counts: number[];
    binning?: Record<string, unknown>;
}

export interface CrmlSamplesArtifact {
    kind: "samples";
    id: string;
    unit?: CrmlCurrencyUnit;
    values: number[];
    sample_count_total?: number;
    sample_count_returned?: number;
    sampling?: Record<string, unknown>;
}

export type CrmlArtifact = CrmlHistogramArtifact | CrmlSamplesArtifact;

export interface CrmlResultPayload {
    measures: CrmlMeasure[];
    artifacts: CrmlArtifact[];
}

export interface CRSimulationResultInner {
    success: boolean;
    errors?: string[];
    warnings?: string[];
    engine?: { name: string; version?: string };
    run?: { runs?: number; seed?: number; runtime_ms?: number; started_at?: string };
    inputs?: { model_name?: string; model_version?: string; description?: string };
    units?: { currency: CrmlCurrencyUnit; horizon?: string };
    results?: CrmlResultPayload;
}

// Canonical CRML-Lang envelope returned by the Python engine.
export interface CRSimulationResult {
    crml_simulation_result: "1.0";
    result: CRSimulationResultInner;
}

export interface SimulationDistribution {
    bins: number[];
    frequencies: number[];
    raw_data?: number[];
}

export interface SimulationMetadata {
    runs: number;
    runtime_ms: number;
    model_name: string;
    model_version?: string;
    description?: string;
    seed?: number;
    currency?: string;
    controls_applied?: boolean;
    lambda_baseline?: number;
    lambda_effective?: number;
    control_reduction_pct?: number;
    control_details?: Array<{
        id: string;
        type: string;
        effectiveness: number;
        coverage: number;
        reliability: number;
        reduction: number;
        cost?: number;
    }>;
    control_warnings?: string[];
    correlation_info?: Array<{
        assets: string[];
        value: number;
    }>;
}

export type SimulationResult = CRSimulationResult;

interface SimulationResultsProps {
    readonly result: SimulationResult | null;
    readonly isSimulating: boolean;
}

export default function SimulationResults({ result, isSimulating }: SimulationResultsProps) {
    if (isSimulating) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5 animate-pulse" />
                        Running Simulation...
                    </CardTitle>
                    <CardDescription>
                        This may take a few seconds
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex items-center justify-center py-12">
                        <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!result) {
        return (
            <Card className="h-full">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <BarChart3 className="h-5 w-5" />
                        Simulation Results
                    </CardTitle>
                    <CardDescription>
                        Run a simulation to see results
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="flex flex-col items-center justify-center py-12 text-center text-muted-foreground">
                        <TrendingUp className="mb-4 h-12 w-12 opacity-50" />
                        <p>No results yet</p>
                        <p className="text-sm">Click &quot;Simulate&quot; to start</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const inner = result.result;

    if (!inner.success) {
        const errorKeyCounts = new Map<string, number>();
        return (
            <Card className="h-full border-destructive">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="h-5 w-5" />
                        Simulation Failed
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <Alert variant="destructive">
                        <AlertDescription>
                            <ul className="list-disc space-y-1 pl-4">
                                {inner.errors?.map((error) => {
                                    const count = errorKeyCounts.get(error) ?? 0;
                                    errorKeyCounts.set(error, count + 1);
                                    return <li key={`${error}::${count}`}>{error}</li>;
                                })}
                            </ul>
                        </AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    const measures = inner.results?.measures ?? [];
    const artifacts = inner.results?.artifacts ?? [];

    const currency = inner.units?.currency?.symbol || inner.units?.currency?.code || '$';

    const getMeasure = (id: string) => measures.find(m => m.id === id);
    const getVar = (level: number) => measures.find((m) => {
        if (m.id !== "loss.var") return false;
        const candidate = m.parameters?.["level"];
        return typeof candidate === "number" && candidate === level;
    });
    const histogram = artifacts.find((a): a is CrmlHistogramArtifact => a.kind === "histogram" && a.id === "loss.annual");
    const samples = artifacts.find((a): a is CrmlSamplesArtifact => a.kind === "samples" && a.id === "loss.annual");

    const metrics: SimulationMetrics = {
        eal: (getMeasure("loss.eal")?.value as number) || 0,
        var_95: (getVar(0.95)?.value as number) || 0,
        var_99: (getVar(0.99)?.value as number) || 0,
        var_999: (getVar(0.999)?.value as number) || 0,
        min: (getMeasure("loss.min")?.value as number) || 0,
        max: (getMeasure("loss.max")?.value as number) || 0,
        median: (getMeasure("loss.median")?.value as number) || 0,
        std_dev: (getMeasure("loss.std_dev")?.value as number) || 0,
    };

    const metadata: SimulationMetadata = {
        runs: inner.run?.runs || 0,
        runtime_ms: inner.run?.runtime_ms || 0,
        model_name: inner.inputs?.model_name || "",
        model_version: inner.inputs?.model_version,
        description: inner.inputs?.description,
        seed: inner.run?.seed,
        currency,
    };

    const distribution: SimulationDistribution | undefined = histogram
        ? {
            bins: histogram.bin_edges,
            frequencies: histogram.counts,
            raw_data: samples?.values,
        }
        : undefined;

    const formatCurrency = (value: number) => {
        if (!Number.isFinite(value)) return `${currency}0`;
        const abs = Math.abs(value);
        if (abs >= 1000000) {
            return `${currency}${(value / 1000000).toFixed(2)}M`;
        }
        if (abs >= 1000) {
            return `${currency}${(value / 1000).toFixed(0)}K`;
        }
        return `${currency}${value.toFixed(0)}`;
    };

    // Prepare chart data (numeric axis to avoid duplicate categorical labels)
    const chartData = distribution?.bins && distribution?.frequencies
        ? distribution.bins.slice(0, -1).map((binStart, idx) => {
            const binEnd = distribution.bins[idx + 1];
            const x = (binStart + binEnd) / 2;
            return {
                x,
                frequency: distribution.frequencies[idx],
                binStart,
                binEnd,
            };
        })
        : [];

    // Staged x-axis scaling for heavy-tailed distributions.
    // If the max is much larger than a percentile metric (VaR), use that VaR
    // as the display cap (with slight headroom) so the left cluster is readable.
    const toPositiveFinite = (v: unknown): number | null => {
        if (typeof v !== "number") return null;
        if (!Number.isFinite(v) || v <= 0) return null;
        return v;
    };

    const maxEdge = distribution?.bins?.length ? (distribution.bins.at(-1) ?? null) : null;
    const maxX = toPositiveFinite(maxEdge ?? metrics.max) ?? 0;

    const STAGE_RATIO_TRIGGER = 1.8;
    const STAGE_HEADROOM = 1.05;

    const var95 = toPositiveFinite(metrics.var_95);
    const var99 = toPositiveFinite(metrics.var_99);
    const var999 = toPositiveFinite(metrics.var_999);

    const pickDomainMax = (): number => {
        if (maxX <= 0) return 0;

        if (var999 && maxX / var999 >= STAGE_RATIO_TRIGGER) {
            return Math.min(maxX, var999 * STAGE_HEADROOM);
        }
        if (var99 && maxX / var99 >= STAGE_RATIO_TRIGGER) {
            return Math.min(maxX, var99 * STAGE_HEADROOM);
        }
        if (var95 && maxX / var95 >= STAGE_RATIO_TRIGGER) {
            return Math.min(maxX, var95 * STAGE_HEADROOM);
        }

        return maxX;
    };

    const domainMax = pickDomainMax();
    const displayChartData = domainMax > 0
        ? chartData.filter((d) => typeof d.x === "number" && d.x >= 0 && d.x <= domainMax)
        : chartData;

    const handleDownloadJSON = () => {
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${metadata?.model_name || 'simulation'}_results.json`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    const handleDownloadCSV = () => {
        if (!distribution?.raw_data) return;

        const csv = ['Loss Amount\n', ...distribution.raw_data.map(v => `${v}\n`)].join('');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${metadata?.model_name || 'simulation'}_data.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    return (
        <TooltipProvider>
            <div className="space-y-4">
                {/* Success Banner */}
                <Card className="bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
                    <CardHeader className="pb-3">
                        <div className="flex items-center gap-2">
                            <BarChart3 className="h-4 w-4 text-green-600 dark:text-green-400" />
                            <CardTitle className="text-base">Simulation Complete</CardTitle>
                        </div>
                        <CardDescription className="text-xs">
                            {metadata?.runs.toLocaleString()} iterations • {metadata?.runtime_ms.toFixed(0)}ms
                        </CardDescription>
                    </CardHeader>
                </Card>

                {/* Correlation Info */}
                {metadata?.correlation_info && metadata.correlation_info.length > 0 && (
                    <Card className="bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800">
                        <CardHeader className="pb-3">
                            <div className="flex items-center gap-2">
                                <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                                <CardTitle className="text-base">Correlated Risks Active</CardTitle>
                            </div>
                            <CardDescription className="text-xs">
                                Asset failures are modeled as dependent events (Copula method).
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <div className="text-xs font-medium text-muted-foreground mb-2">Active Correlations:</div>
                            <div className="grid grid-cols-1 gap-1">
                                {metadata.correlation_info.map((c) => (
                                    <div key={`${c.assets.join("|")}::${c.value}`} className="flex items-center justify-between p-2 bg-white dark:bg-gray-900 rounded border border-blue-100 dark:border-blue-900 text-xs">
                                        <div className="flex items-center gap-2">
                                            <span className="font-semibold">{c.assets[0]}</span>
                                            <span className="text-muted-foreground">↔</span>
                                            <span className="font-semibold">{c.assets[1]}</span>
                                        </div>
                                        <div className="font-bold text-blue-600 dark:text-blue-400">
                                            {c.value.toFixed(2)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Control Effectiveness */}
                {metadata?.controls_applied && (
                    <Card className="bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800">
                        <CardHeader className="pb-3">
                            <div className="flex items-center gap-2">
                                <DollarSign className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                                <CardTitle className="text-base">Control Effectiveness</CardTitle>
                            </div>
                            <CardDescription className="text-xs">
                                Security controls reduced risk by {metadata.control_reduction_pct?.toFixed(1)}%
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {/* Baseline vs Effective */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Baseline (no controls)</p>
                                    <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                                        {(metadata.lambda_baseline! * 100).toFixed(1)}%
                                    </p>
                                    <p className="text-xs text-muted-foreground">Annual probability</p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Effective (with controls)</p>
                                    <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                                        {(metadata.lambda_effective! * 100).toFixed(2)}%
                                    </p>
                                    <p className="text-xs text-muted-foreground">Annual probability</p>
                                </div>
                            </div>

                            {/* Risk Reduction Bar */}
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">Risk Reduction</span>
                                    <span className="font-semibold text-green-600 dark:text-green-400">
                                        {metadata.control_reduction_pct?.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all"
                                        style={{ width: `${Math.min(metadata.control_reduction_pct || 0, 100)}%` }}
                                    />
                                </div>
                            </div>

                            {/* Individual Controls */}
                            {metadata.control_details && metadata.control_details.length > 0 && (
                                <div className="space-y-2">
                                    <p className="text-xs font-medium text-muted-foreground">
                                        Individual Controls ({metadata.control_details.length})
                                    </p>
                                    <div className="space-y-1.5 max-h-32 overflow-y-auto">
                                        {metadata.control_details.slice(0, 5).map((ctrl) => (
                                            <div key={`${ctrl.id}::${ctrl.type}`} className="flex items-center justify-between text-xs p-1.5 bg-white dark:bg-gray-900 rounded">
                                                <div className="flex-1">
                                                    <span className="font-medium">{ctrl.id}</span>
                                                    <span className="text-muted-foreground ml-1">({ctrl.type})</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <span className="text-green-600 dark:text-green-400 font-semibold">
                                                                {(ctrl.reduction * 100).toFixed(0)}%
                                                            </span>
                                                        </TooltipTrigger>
                                                        <TooltipContent className="text-xs">
                                                            <p>Effectiveness: {(ctrl.effectiveness * 100).toFixed(0)}%</p>
                                                            <p>Coverage: {(ctrl.coverage * 100).toFixed(0)}%</p>
                                                            <p>Reliability: {(ctrl.reliability * 100).toFixed(0)}%</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </div>
                                            </div>
                                        ))}
                                        {metadata.control_details.length > 5 && (
                                            <p className="text-xs text-muted-foreground text-center py-1">
                                                ... and {metadata.control_details.length - 5} more controls
                                            </p>
                                        )}
                                    </div>
                                </div>
                            )}

                            {/* Warnings */}
                            {metadata.control_warnings && metadata.control_warnings.length > 0 && (
                                <Alert variant="default" className="py-2">
                                    <AlertCircle className="h-3 w-3" />
                                    <AlertDescription className="text-xs">
                                        {metadata.control_warnings[0]}
                                    </AlertDescription>
                                </Alert>
                            )}
                        </CardContent>
                    </Card>
                )}

                {/* Key Metrics */}
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Card className="border-2 border-primary">
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-1">
                                <CardDescription className="text-xs font-medium">EAL</CardDescription>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-xs">
                                        <p className="text-xs"><strong>Expected Annual Loss:</strong> Average loss per year. Use for budgeting.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <CardTitle className="text-2xl">{formatCurrency(metrics?.eal || 0)}</CardTitle>
                            <p className="text-xs text-muted-foreground">Avg yearly loss</p>
                        </CardHeader>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-1">
                                <CardDescription className="text-xs font-medium">VaR 95%</CardDescription>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-xs">
                                        <p className="text-xs">95% of years will be below this. Only 1 in 20 years exceeds.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <CardTitle className="text-2xl">{formatCurrency(metrics?.var_95 || 0)}</CardTitle>
                            <p className="text-xs text-muted-foreground">95% confidence</p>
                        </CardHeader>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-1">
                                <CardDescription className="text-xs font-medium">VaR 99%</CardDescription>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-xs">
                                        <p className="text-xs">99% of years below this. 1 in 100 years exceeds. For stress testing.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <CardTitle className="text-2xl">{formatCurrency(metrics?.var_99 || 0)}</CardTitle>
                            <p className="text-xs text-muted-foreground">99% confidence</p>
                        </CardHeader>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <div className="flex items-center justify-between mb-1">
                                <CardDescription className="text-xs font-medium">VaR 99.9%</CardDescription>
                                <Tooltip>
                                    <TooltipTrigger>
                                        <HelpCircle className="h-3 w-3 text-muted-foreground" />
                                    </TooltipTrigger>
                                    <TooltipContent className="max-w-xs">
                                        <p className="text-xs">Extreme worst-case. 1 in 1000 years. Catastrophic planning.</p>
                                    </TooltipContent>
                                </Tooltip>
                            </div>
                            <CardTitle className="text-2xl">{formatCurrency(metrics?.var_999 || 0)}</CardTitle>
                            <p className="text-xs text-muted-foreground">99.9% confidence</p>
                        </CardHeader>
                    </Card>
                </div>

                {/* Distribution Chart */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-base">Loss Distribution</CardTitle>
                        <CardDescription className="text-xs">
                            Taller bars = more common. Most losses cluster left (smaller amounts).
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[250px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={displayChartData}>
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                    <XAxis
                                        dataKey="x"
                                        type="number"
                                        scale="linear"
                                        domain={[0, domainMax > 0 ? domainMax : 'auto']}
                                        tickFormatter={(v: number) => formatCurrency(v)}
                                        angle={-45}
                                        textAnchor="end"
                                        height={70}
                                        tickCount={7}
                                        interval={0}
                                        className="text-xs"
                                    />
                                    <YAxis className="text-xs" />
                                    <RechartsTooltip
                                        formatter={(value: number) => [value, 'Occurrences']}
                                        labelFormatter={(label) => `Loss: ${formatCurrency(Number(label))}`}
                                    />
                                    <Area
                                        type="stepAfter"
                                        dataKey="frequency"
                                        stroke="hsl(var(--primary))"
                                        fill="hsl(var(--primary))"
                                        fillOpacity={0.25}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Interpretation */}
                <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950 dark:border-blue-800">
                    <CardHeader className="pb-3">
                        <CardTitle className="text-base flex items-center gap-2">
                            <Info className="h-4 w-4" />
                            What This Means
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                        <div>
                            <p className="font-semibold">Budget: {formatCurrency(metrics?.eal || 0)}/year</p>
                            <p className="text-xs text-muted-foreground">Plan for this average annual loss</p>
                        </div>
                        <div>
                            <p className="font-semibold">Normal worst-case: {formatCurrency(metrics?.var_95 || 0)}</p>
                            <p className="text-xs text-muted-foreground">Prepare for losses up to this (95% confidence)</p>
                        </div>
                        <div>
                            <p className="font-semibold">Extreme scenario: {formatCurrency(metrics?.var_99 || 0)}</p>
                            <p className="text-xs text-muted-foreground">Rare but possible. Ensure insurance coverage</p>
                        </div>
                    </CardContent>
                </Card>

                {/* Stats & Downloads */}
                <Card>
                    <CardHeader className="pb-3">
                        <CardTitle className="text-base">Details & Export</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-3 md:grid-cols-2">
                            <div className="space-y-1.5 text-sm">
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Min:</span>
                                    <span className="font-medium">{formatCurrency(metrics?.min || 0)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Max:</span>
                                    <span className="font-medium">{formatCurrency(metrics?.max || 0)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Median:</span>
                                    <span className="font-medium">{formatCurrency(metrics?.median || 0)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Std Dev:</span>
                                    <span className="font-medium">{formatCurrency(metrics?.std_dev || 0)}</span>
                                </div>
                            </div>
                            <div className="space-y-2">
                                <Button onClick={handleDownloadJSON} variant="outline" size="sm" className="w-full gap-2">
                                    <Download className="h-3 w-3" />
                                    Download JSON
                                </Button>
                                <Button onClick={handleDownloadCSV} variant="outline" size="sm" className="w-full gap-2">
                                    <Download className="h-3 w-3" />
                                    Download CSV
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </TooltipProvider>
    );
}
