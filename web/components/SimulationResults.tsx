"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Download, TrendingUp, AlertCircle, BarChart3, HelpCircle, Info, DollarSign } from "lucide-react";
import type { EChartsOption } from "echarts";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

const VAR_LEVEL_95 = 0.95;
const VAR_LEVEL_99 = 0.99;
const VAR_LEVEL_999 = 0.999;

const PERCENT_MULTIPLIER = 100;

const THOUSAND = 1_000;
const MILLION = 1_000_000;

const CONTROL_DETAILS_PREVIEW_COUNT = 5;

const HISTOGRAM_BIN_COUNT = 50;
const HISTOGRAM_CAP_QUANTILE = 0.99;

const numberOrZero = (v: unknown): number => (typeof v === "number" && Number.isFinite(v) ? v : 0);

const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
};

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
    inputs?: {
        model_name?: string;
        model_version?: string;
        description?: string;
        risk_tolerance?: { metric?: string; threshold?: number; currency?: string };
    };
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

// Wrapper component: no hooks here.
// This avoids React hook order mismatches when switching between
// "no result" / "loading" / "error" / "success" UI states.
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

    return <SimulationResultsSuccess result={result} isSimulating={false} />;
}

function SimulationResultsSuccess({ result }: SimulationResultsProps) {
    // By construction this component only renders for successful results.
    // That keeps hook execution consistent across renders.
    const inner = result!.result;

    const measures = inner.results?.measures ?? [];
    const artifacts = inner.results?.artifacts ?? [];

    // ECharts renders to canvas; it cannot resolve CSS variables like `hsl(var(--primary))`.
    // Resolve the theme tokens into concrete color strings for chart styling.
    const [chartPrimary, setChartPrimary] = useState<string | undefined>(undefined);
    const [chartMuted, setChartMuted] = useState<string | undefined>(undefined);

    const cssVarToCanvasHsl = (varName: string): string | undefined => {
        const raw = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
        if (!raw) return undefined;

        // shadcn/ui Tailwind tokens typically look like: "222.2 47.4% 11.2%".
        // Convert to a widely supported (canvas-friendly) comma-separated syntax.
        const [hslPart, alphaPartRaw] = raw.split("/").map((s) => s.trim());
        const parts = hslPart.split(/\s+/).filter(Boolean);
        if (parts.length < 3) return undefined;

        const h = parts[0];
        const s = parts[1];
        const l = parts[2];

        if (alphaPartRaw) {
            return `hsla(${h}, ${s}, ${l}, ${alphaPartRaw})`;
        }
        return `hsl(${h}, ${s}, ${l})`;
    };

    useEffect(() => {
        if (typeof window === "undefined") return;

        const update = () => {
            setChartPrimary(cssVarToCanvasHsl("--primary"));
            setChartMuted(cssVarToCanvasHsl("--muted-foreground"));
        };

        update();

        // Update on theme/class changes (e.g., dark mode toggle).
        const observer = new MutationObserver(update);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class", "style"] });
        return () => observer.disconnect();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const currency = inner.units?.currency?.symbol ?? inner.units?.currency?.code ?? "$";

    const getMeasure = (id: string) => measures.find((m) => m.id === id);
    const getVar = (level: number) => measures.find((m) => {
        if (m.id !== "loss.var") return false;
        const candidate = m.parameters?.["level"];
        return typeof candidate === "number" && candidate === level;
    });
    const histogram = artifacts.find((a): a is CrmlHistogramArtifact => a.kind === "histogram" && a.id === "loss.annual");
    const samples = artifacts.find((a): a is CrmlSamplesArtifact => a.kind === "samples" && a.id === "loss.annual");

    const metrics: SimulationMetrics = {
        eal: numberOrZero(getMeasure("loss.eal")?.value),
        var_95: numberOrZero(getVar(VAR_LEVEL_95)?.value),
        var_99: numberOrZero(getVar(VAR_LEVEL_99)?.value),
        var_999: numberOrZero(getVar(VAR_LEVEL_999)?.value),
        min: numberOrZero(getMeasure("loss.min")?.value),
        max: numberOrZero(getMeasure("loss.max")?.value),
        median: numberOrZero(getMeasure("loss.median")?.value),
        std_dev: numberOrZero(getMeasure("loss.std_dev")?.value),
    };

    const metadata: SimulationMetadata = {
        runs: inner.run?.runs ?? 0,
        runtime_ms: inner.run?.runtime_ms ?? 0,
        model_name: inner.inputs?.model_name ?? "",
        model_version: inner.inputs?.model_version,
        description: inner.inputs?.description,
        seed: inner.run?.seed,
        currency,
    };

    const downloadBaseName = metadata.model_name || "simulation";
    const controlReductionPct = metadata.control_reduction_pct ?? 0;

    const distributionInfo = useMemo(() => {
        const values = samples?.values;
        if (Array.isArray(values) && values.length > 0) {
            let zeroCount = 0;
            const positive: number[] = [];

            for (const v of values) {
                if (typeof v !== "number" || !Number.isFinite(v)) continue;
                if (v === 0) {
                    zeroCount += 1;
                    continue;
                }
                if (v > 0) positive.push(v);
            }

            const total = values.length;
            const zeroShare = total > 0 ? zeroCount / total : null;

            if (positive.length < 2) {
                return {
                    zeroCount,
                    zeroShare,
                    distribution: undefined as SimulationDistribution | undefined,
                    domainMax: 0,
                };
            }

            const sorted = positive.slice().sort((a, b) => a - b);
            const idx = Math.max(0, Math.min(sorted.length - 1, Math.floor(HISTOGRAM_CAP_QUANTILE * (sorted.length - 1))));
            const cap = sorted[idx];
            const domainMax = Number.isFinite(cap) && cap > 0 ? cap : (sorted.at(-1) ?? 0);
            if (!(domainMax > 0)) {
                return {
                    zeroCount,
                    zeroShare,
                    distribution: undefined as SimulationDistribution | undefined,
                    domainMax: 0,
                };
            }

            const binCount = HISTOGRAM_BIN_COUNT;
            const step = domainMax / binCount;
            const bins = Array.from({ length: binCount + 1 }, (_, i) => i * step);
            const frequencies = Array.from({ length: binCount }, () => 0);

            for (const v of positive) {
                if (!(v > 0) || !Number.isFinite(v)) continue;
                if (v > domainMax) continue;
                const ratio = v / domainMax;
                const binIdx = Math.min(binCount - 1, Math.max(0, Math.floor(ratio * binCount)));
                frequencies[binIdx] += 1;
            }

            return {
                zeroCount,
                zeroShare,
                distribution: {
                    bins,
                    frequencies,
                    raw_data: values,
                } as SimulationDistribution,
                domainMax,
            };
        }

        // Fallback: use engine-provided histogram as-is.
        if (histogram?.bin_edges?.length && histogram?.counts?.length) {
            const bins = histogram.bin_edges;
            const frequencies = histogram.counts;
            const maxEdge = bins.at(-1) ?? 0;
            const domainMax = typeof maxEdge === "number" && Number.isFinite(maxEdge) ? maxEdge : 0;
            return {
                zeroCount: 0,
                zeroShare: null as number | null,
                distribution: {
                    bins,
                    frequencies,
                    raw_data: undefined,
                } as SimulationDistribution,
                domainMax,
            };
        }

        return {
            zeroCount: 0,
            zeroShare: null as number | null,
            distribution: undefined as SimulationDistribution | undefined,
            domainMax: 0,
        };
    }, [samples?.values, histogram?.bin_edges, histogram?.counts]);

    const distribution = distributionInfo.distribution;

    const formatCurrency = (value: number) => {
        if (!Number.isFinite(value)) return `${currency}0`;
        const abs = Math.abs(value);
        if (abs >= MILLION) {
            return `${currency}${(value / MILLION).toFixed(2)}M`;
        }
        if (abs >= THOUSAND) {
            return `${currency}${(value / THOUSAND).toFixed(0)}K`;
        }
        return `${currency}${value.toFixed(0)}`;
    };

    const domainMax = distributionInfo.domainMax;

    const riskTolerance = inner.inputs?.risk_tolerance;
    const rtThreshold = riskTolerance?.threshold;
    const rtMetric = riskTolerance?.metric;
    const rtCurrency = (riskTolerance?.currency ?? inner.units?.currency?.code ?? "").trim();

    const rtObserved = (() => {
        if (!rtMetric) return null;
        switch (rtMetric) {
            case "max_eal":
                return metrics.eal;
            case "max_var_95":
                return metrics.var_95;
            case "max_var_99":
                return metrics.var_99;
            case "max_var_999":
                return metrics.var_999;
            // CVaR/ES measures are not currently computed as measures in the envelope.
            case "max_cvar_95":
            case "max_cvar_99":
            default:
                return null;
        }
    })();

    const rtPass = (typeof rtThreshold === "number" && Number.isFinite(rtThreshold) && rtObserved != null)
        ? rtObserved <= rtThreshold
        : null;

    const glProductivity = numberOrZero(getMeasure("investment.gordon_loeb.productivity")?.value);
    const glOptimal = numberOrZero(getMeasure("investment.gordon_loeb.optimal")?.value);
    const glResidualEal = numberOrZero(getMeasure("investment.gordon_loeb.residual_eal")?.value);
    const glTotalCostMin = numberOrZero(getMeasure("investment.gordon_loeb.total_cost_min")?.value);

    const investmentChartOption: EChartsOption | null = useMemo(() => {
        const eal = metrics.eal;
        const g = glProductivity;
        if (!(eal > 0) || !(g > 0)) return null;

        const maxX = Math.max(glOptimal * 3, eal);
        const steps = 60;
        const data: Array<[number, number]> = [];
        for (let i = 0; i <= steps; i++) {
            const z = (maxX * i) / steps;
            const residual = eal * Math.exp(-(g * z) / eal);
            const total = z + residual;
            data.push([z, total]);
        }

        const markLines = (glOptimal > 0 && Number.isFinite(glOptimal)) ? [{ xAxis: glOptimal, name: "Optimal" }] : [];

        return {
            animation: false,
            grid: { left: 40, right: 20, top: 28, bottom: 45, containLabel: true },
            xAxis: {
                type: "value",
                min: 0,
                max: maxX,
                axisLabel: { formatter: (v: unknown) => formatCurrency(Number(v)) },
                splitLine: { lineStyle: { type: "dashed" } },
            },
            yAxis: {
                type: "value",
                axisLabel: { formatter: (v: unknown) => formatCurrency(Number(v)) },
                splitLine: { lineStyle: { type: "dashed" } },
            },
            tooltip: {
                trigger: "axis",
                formatter: (params: any) => {
                    const p = Array.isArray(params) ? params[0] : params;
                    const v = p?.value;
                    if (Array.isArray(v) && v.length >= 2) {
                        return `Investment: ${formatCurrency(Number(v[0]))}<br/>Total expected cost: ${formatCurrency(Number(v[1]))}`;
                    }
                    return "";
                },
            },
            series: [
                {
                    name: "Total expected cost",
                    type: "line",
                    data,
                    showSymbol: false,
                    lineStyle: { color: chartPrimary, width: 2 },
                    z: 10,
                    emphasis: { disabled: true },
                    blur: { lineStyle: { opacity: 1 } },
                    markLine: {
                        symbol: ["none", "none"],
                        label: {
                            formatter: (p: any) => p?.name ?? "",
                            position: "end",
                            offset: [0, 10],
                        },
                        lineStyle: { type: "dashed", color: chartMuted ?? chartPrimary, width: 2, opacity: 0.9 },
                        z: 100,
                        data: markLines,
                    },
                },
            ],
        } as EChartsOption;
    }, [metrics.eal, glProductivity, glOptimal, chartPrimary, chartMuted]);

    const lossChartOption: EChartsOption | null = useMemo(() => {
        if (!distribution?.bins?.length || !distribution?.frequencies?.length) return null;
        const bins = distribution.bins;
        const freqs = distribution.frequencies;

        const maxFreq = freqs.reduce((acc, v) => {
            const n = typeof v === "number" && Number.isFinite(v) ? v : 0;
            return n > acc ? n : acc;
        }, 0);

        const barData = bins.slice(0, -1).map((start, idx) => [start, bins[idx + 1], freqs[idx] ?? 0]);
        const lineData = bins.slice(0, -1).map((start, idx) => [start, freqs[idx] ?? 0]);

        const rtLine = typeof rtThreshold === "number" && Number.isFinite(rtThreshold) && rtThreshold >= 0
            ? [{ xAxis: rtThreshold, name: "Risk tolerance" }]
            : [];

        return {
            animation: false,
            grid: { left: 40, right: 20, top: 28, bottom: 55, containLabel: true },
            xAxis: {
                type: "value",
                min: 0,
                max: domainMax > 0 ? domainMax : undefined,
                axisLabel: {
                    rotate: 45,
                    formatter: (v: unknown) => formatCurrency(Number(v)),
                },
                splitLine: { lineStyle: { type: "dashed" } },
            },
            yAxis: {
                type: "value",
                min: 0,
                max: maxFreq > 0 ? Math.ceil(maxFreq * 1.1) : undefined,
                minInterval: 1,
                axisLabel: { formatter: (v: unknown) => Number(v).toLocaleString() },
                splitLine: { lineStyle: { type: "dashed" } },
            },
            tooltip: {
                trigger: "item",
                formatter: (params: any) => {
                    const value = params?.value;
                    if (Array.isArray(value) && value.length >= 3) {
                        const [start, end, count] = value;
                        return `Loss: ${formatCurrency(Number(start))} – ${formatCurrency(Number(end))}<br/>Occurrences: ${Number(count).toLocaleString()}`;
                    }
                    if (Array.isArray(value) && value.length >= 2) {
                        return `Loss: ${formatCurrency(Number(value[0]))}<br/>Occurrences: ${Number(value[1]).toLocaleString()}`;
                    }
                    return "";
                },
            },
            series: [
                {
                    // Invisible full-height hover zones so you can hover anywhere in a bin's x-range
                    // (even if the visible bar height is near zero) and still get that bin's tooltip.
                    name: "Bin hover",
                    type: "custom",
                    data: barData,
                    encode: {
                        x: [0, 1],
                        y: 2,
                        tooltip: [0, 1, 2],
                    },
                    renderItem: (params: any, api: any) => {
                        const x0 = api.value(0);
                        const x1 = api.value(1);
                        const top = api.coord([x0, maxFreq > 0 ? maxFreq : 1]);
                        const bottom = api.coord([x1, 0]);
                        const width = bottom[0] - top[0];
                        const height = bottom[1] - top[1];
                        return {
                            type: "rect",
                            shape: {
                                x: top[0],
                                y: top[1],
                                width,
                                height,
                            },
                            style: {
                                fill: "rgba(0,0,0,0)",
                                stroke: "rgba(0,0,0,0)",
                            },
                        };
                    },
                    // Keep hover zones behind overlays like markLines.
                    z: 0,
                    silent: false,
                },
                {
                    name: "Histogram",
                    type: "custom",
                    data: barData,
                    encode: {
                        x: [0, 1],
                        y: 2,
                        tooltip: [0, 1, 2],
                    },
                    renderItem: (params: any, api: any) => {
                        const x0 = api.value(0);
                        const x1 = api.value(1);
                        const y = api.value(2);
                        const start = api.coord([x0, y]);
                        const end = api.coord([x1, 0]);
                        const width = end[0] - start[0];
                        const height = end[1] - start[1];
                        return {
                            type: "rect",
                            shape: {
                                x: start[0],
                                y: start[1],
                                width: width,
                                height: height,
                            },
                            style: api.style({ fill: chartPrimary, opacity: 0.25 }),
                        };
                    },
                    silent: false,
                },
                {
                    name: "Frequency",
                    type: "line",
                    data: lineData,
                    encode: { x: 0, y: 1 },
                    showSymbol: false,
                    step: "end",
                    lineStyle: { color: chartPrimary, width: 2 },
                    z: 10,
                    markLine: {
                        symbol: ["none", "none"],
                        label: {
                            formatter: (p: any) => p?.name ?? "",
                            position: "end",
                            offset: [0, 10],
                        },
                        lineStyle: { type: "dashed", color: chartMuted ?? chartPrimary, width: 2, opacity: 0.95 },
                        z: 100,
                        data: rtLine,
                    },
                },
            ],
        } as EChartsOption;
    }, [distribution?.bins, distribution?.frequencies, domainMax, rtThreshold, chartPrimary, chartMuted]);

    const handleDownloadJSON = () => {
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `${downloadBaseName}_results.json`);
    };

    const handleDownloadCSV = () => {
        if (!distribution?.raw_data) return;

        const csv = ['Loss Amount\n', ...distribution.raw_data.map(v => `${v}\n`)].join('');
        const blob = new Blob([csv], { type: 'text/csv' });
        downloadBlob(blob, `${downloadBaseName}_data.csv`);
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
                            {metadata.runs.toLocaleString()} iterations • {metadata.runtime_ms.toFixed(0)}ms
                        </CardDescription>
                    </CardHeader>
                </Card>

                {/* Correlation Info */}
                {metadata.correlation_info && metadata.correlation_info.length > 0 && (
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
                {metadata?.controls_applied && metadata.lambda_baseline != null && metadata.lambda_effective != null && (
                    <Card className="bg-purple-50 dark:bg-purple-950 border-purple-200 dark:border-purple-800">
                        <CardHeader className="pb-3">
                            <div className="flex items-center gap-2">
                                <DollarSign className="h-4 w-4 text-purple-600 dark:text-purple-400" />
                                <CardTitle className="text-base">Control Effectiveness</CardTitle>
                            </div>
                            <CardDescription className="text-xs">
                                Security controls reduced risk by {controlReductionPct.toFixed(1)}%
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-3">
                            {/* Baseline vs Effective */}
                            <div className="grid grid-cols-2 gap-3">
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Baseline (no controls)</p>
                                    <p className="text-lg font-semibold text-red-600 dark:text-red-400">
                                        {(metadata.lambda_baseline * PERCENT_MULTIPLIER).toFixed(1)}%
                                    </p>
                                    <p className="text-xs text-muted-foreground">Annual probability</p>
                                </div>
                                <div className="space-y-1">
                                    <p className="text-xs text-muted-foreground">Effective (with controls)</p>
                                    <p className="text-lg font-semibold text-green-600 dark:text-green-400">
                                        {(metadata.lambda_effective * PERCENT_MULTIPLIER).toFixed(2)}%
                                    </p>
                                    <p className="text-xs text-muted-foreground">Annual probability</p>
                                </div>
                            </div>

                            {/* Risk Reduction Bar */}
                            <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                    <span className="text-muted-foreground">Risk Reduction</span>
                                    <span className="font-semibold text-green-600 dark:text-green-400">
                                        {controlReductionPct.toFixed(1)}%
                                    </span>
                                </div>
                                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all"
                                        style={{ width: `${Math.min(Math.max(controlReductionPct, 0), PERCENT_MULTIPLIER)}%` }}
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
                                        {metadata.control_details.slice(0, CONTROL_DETAILS_PREVIEW_COUNT).map((ctrl) => (
                                            <div key={`${ctrl.id}::${ctrl.type}`} className="flex items-center justify-between text-xs p-1.5 bg-white dark:bg-gray-900 rounded">
                                                <div className="flex-1">
                                                    <span className="font-medium">{ctrl.id}</span>
                                                    <span className="text-muted-foreground ml-1">({ctrl.type})</span>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    <Tooltip>
                                                        <TooltipTrigger>
                                                            <span className="text-green-600 dark:text-green-400 font-semibold">
                                                                {(ctrl.reduction * PERCENT_MULTIPLIER).toFixed(0)}%
                                                            </span>
                                                        </TooltipTrigger>
                                                        <TooltipContent className="text-xs">
                                                            <p>Effectiveness: {(ctrl.effectiveness * PERCENT_MULTIPLIER).toFixed(0)}%</p>
                                                            <p>Coverage: {(ctrl.coverage * PERCENT_MULTIPLIER).toFixed(0)}%</p>
                                                            <p>Reliability: {(ctrl.reliability * PERCENT_MULTIPLIER).toFixed(0)}%</p>
                                                        </TooltipContent>
                                                    </Tooltip>
                                                </div>
                                            </div>
                                        ))}
                                        {metadata.control_details.length > CONTROL_DETAILS_PREVIEW_COUNT && (
                                            <p className="text-xs text-muted-foreground text-center py-1">
                                                ... and {metadata.control_details.length - CONTROL_DETAILS_PREVIEW_COUNT} more controls
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
                            <CardTitle className="text-2xl">{formatCurrency(metrics.eal)}</CardTitle>
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
                            <CardTitle className="text-2xl">{formatCurrency(metrics.var_95)}</CardTitle>
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
                            <CardTitle className="text-2xl">{formatCurrency(metrics.var_99)}</CardTitle>
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
                            <CardTitle className="text-2xl">{formatCurrency(metrics.var_999)}</CardTitle>
                            <p className="text-xs text-muted-foreground">99.9% confidence</p>
                        </CardHeader>
                    </Card>
                </div>

                {/* Risk Tolerance + Optimal Investment */}
                <div className="space-y-3">
                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">Risk Tolerance</CardTitle>
                            <CardDescription className="text-xs">
                                Threshold from the input bundle/portfolio; the observed value is computed from the simulation results.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="text-sm">
                            {riskTolerance?.metric || riskTolerance?.threshold != null ? (
                                <div className="space-y-1">
                                    <div className="flex items-start justify-between gap-3">
                                        <span className="shrink-0 text-muted-foreground">Rule</span>
                                        <span className="min-w-0 text-right font-medium break-words whitespace-normal">
                                            {rtMetric ?? "(unspecified)"}
                                            {typeof rtThreshold === "number" && Number.isFinite(rtThreshold)
                                                ? ` <= ${(rtCurrency ? rtCurrency + " " : "")}${rtThreshold.toLocaleString()}`
                                                : ""}
                                        </span>
                                    </div>
                                    <div className="flex items-start justify-between gap-3">
                                        <span className="shrink-0 text-muted-foreground">Observed</span>
                                        <span className="min-w-0 text-right font-medium break-words whitespace-normal">
                                            {rtObserved != null ? `${rtCurrency ? rtCurrency + " " : ""}${rtObserved.toLocaleString()}` : "(not available)"}
                                        </span>
                                    </div>
                                    <div className="flex items-start justify-between gap-3">
                                        <span className="shrink-0 text-muted-foreground">Status</span>
                                        <span className={`min-w-0 text-right font-semibold break-words whitespace-normal ${rtPass === null ? "text-muted-foreground" : rtPass ? "text-green-600 dark:text-green-400" : "text-destructive"}`}>
                                            {rtPass === null ? "—" : rtPass ? "Within tolerance" : "Exceeds tolerance"}
                                        </span>
                                    </div>
                                </div>
                            ) : (
                                <p className="text-muted-foreground">No risk tolerance specified.</p>
                            )}
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader className="pb-2">
                            <CardTitle className="text-base">Optimal Investment (Gordon–Loeb)</CardTitle>
                            <CardDescription className="text-xs">
                                Computed in the engine and returned as measures; this is a simple, illustrative cost-benefit model.
                            </CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-2">
                            <div className="grid grid-cols-2 gap-3 text-sm">
                                <div className="min-w-0">
                                    <div className="text-xs text-muted-foreground">Optimal</div>
                                    <div className="font-semibold break-words">{formatCurrency(glOptimal)}</div>
                                    <div className="text-[11px] text-muted-foreground">Recommended spend that minimizes total expected cost.</div>
                                </div>
                                <div className="min-w-0">
                                    <div className="text-xs text-muted-foreground">Residual EAL</div>
                                    <div className="font-semibold break-words">{formatCurrency(glResidualEal)}</div>
                                    <div className="text-[11px] text-muted-foreground">Expected yearly loss after investing the “Optimal” amount.</div>
                                </div>
                                <div className="min-w-0">
                                    <div className="text-xs text-muted-foreground">Min total cost</div>
                                    <div className="font-semibold break-words">{formatCurrency(glTotalCostMin)}</div>
                                    <div className="text-[11px] text-muted-foreground">Investment + residual expected loss (minimum of the curve).</div>
                                </div>
                                <div className="min-w-0">
                                    <div className="text-xs text-muted-foreground">Productivity (g)</div>
                                    <div className="font-semibold break-words">{glProductivity ? glProductivity.toFixed(2) : "—"}</div>
                                    <div className="text-[11px] text-muted-foreground">How effectively spend reduces loss in this model (higher = more effective).</div>
                                </div>
                            </div>
                            <p className="text-xs text-muted-foreground">
                                Interpretation: the curve shows “total expected cost” = investment + remaining expected loss. The dashed line marks the minimum.
                            </p>
                            <div className="h-[220px]">
                                {investmentChartOption ? (
                                    <ReactECharts option={investmentChartOption} style={{ height: "100%", width: "100%" }} />
                                ) : (
                                    <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                                        Not available.
                                    </div>
                                )}
                            </div>
                        </CardContent>
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
                        {samples?.values?.length ? (
                            (() => {
                                const returned = samples.values.length;
                                const total = (typeof samples.sample_count_total === "number" && Number.isFinite(samples.sample_count_total) && samples.sample_count_total > 0)
                                    ? samples.sample_count_total
                                    : ((typeof inner.run?.runs === "number" && Number.isFinite(inner.run.runs) && inner.run.runs > 0) ? inner.run.runs : returned);

                                const pctReturned = returned > 0 ? (distributionInfo.zeroCount / returned) * 100 : 0;
                                const suffix = total !== returned
                                    ? ` (based on returned samples: ${returned.toLocaleString()} of ${total.toLocaleString()})`
                                    : "";

                                return (
                                    <p className="mb-2 text-sm">
                                        <span className="font-medium">Zero-loss years:</span>{" "}
                                        <span className="font-semibold">{distributionInfo.zeroCount.toLocaleString()}</span>
                                        {" / "}
                                        <span className="font-semibold">{returned.toLocaleString()}</span>
                                        {" "}
                                        <span className="text-muted-foreground">({pctReturned.toFixed(1)}%){suffix}</span>
                                    </p>
                                );
                            })()
                        ) : (
                            <p className="mb-2 text-xs text-muted-foreground">
                                Zero-loss years: not available (engine did not return sample values).
                            </p>
                        )}
                        <div className="h-[250px]">
                            {lossChartOption ? (
                                <ReactECharts option={lossChartOption} style={{ height: "100%", width: "100%" }} />
                            ) : (
                                <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                                    No distribution data available.
                                </div>
                            )}
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
                            <p className="font-semibold">Budget: {formatCurrency(metrics.eal)}/year</p>
                            <p className="text-xs text-muted-foreground">Plan for this average annual loss</p>
                        </div>
                        <div>
                            <p className="font-semibold">Normal worst-case: {formatCurrency(metrics.var_95)}</p>
                            <p className="text-xs text-muted-foreground">Prepare for losses up to this (95% confidence)</p>
                        </div>
                        <div>
                            <p className="font-semibold">Extreme scenario: {formatCurrency(metrics.var_99)}</p>
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
                                    <span className="font-medium">{formatCurrency(metrics.min)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Max:</span>
                                    <span className="font-medium">{formatCurrency(metrics.max)}</span>
                                </div>
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Median:</span>
                                    <span className="font-medium">{formatCurrency(metrics.median)}</span>
                                </div>
                                {metrics.median === 0 && metrics.max > 0 && (distributionInfo.zeroShare ?? 0) >= 0.5 ? (
                                    <p className="text-xs text-muted-foreground">
                                        Median is {formatCurrency(0)} because more than half of simulated years had no loss.
                                    </p>
                                ) : null}
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Std Dev:</span>
                                    <span className="font-medium">{formatCurrency(metrics.std_dev)}</span>
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
