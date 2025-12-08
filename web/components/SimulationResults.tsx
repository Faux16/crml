"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Download, TrendingUp, AlertCircle, BarChart3, HelpCircle, Info, DollarSign } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';

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
}

export interface SimulationResult {
    success: boolean;
    metrics?: SimulationMetrics;
    distribution?: SimulationDistribution;
    metadata?: SimulationMetadata;
    errors?: string[];
}

interface SimulationResultsProps {
    result: SimulationResult | null;
    isSimulating: boolean;
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
                        <p className="text-sm">Click "Simulate" to start</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (!result.success) {
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
                                {result.errors?.map((error, idx) => (
                                    <li key={idx}>{error}</li>
                                ))}
                            </ul>
                        </AlertDescription>
                    </Alert>
                </CardContent>
            </Card>
        );
    }

    const { metrics, distribution, metadata } = result;

    // Prepare chart data
    const chartData = distribution?.bins && distribution?.frequencies
        ? distribution.bins.slice(0, -1).map((bin, idx) => ({
            range: `$${(bin / 1000).toFixed(0)}K`,
            frequency: distribution.frequencies[idx],
            binStart: bin
        }))
        : [];

    const formatCurrency = (value: number) => {
        if (value >= 1000000) {
            return `$${(value / 1000000).toFixed(2)}M`;
        }
        return `$${(value / 1000).toFixed(0)}K`;
    };

    const handleDownloadJSON = () => {
        const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${metadata?.model_name || 'simulation'}_results.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
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
        document.body.removeChild(a);
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
                                <BarChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                                    <XAxis
                                        dataKey="range"
                                        angle={-45}
                                        textAnchor="end"
                                        height={70}
                                        interval={Math.floor(chartData.length / 8)}
                                        className="text-xs"
                                    />
                                    <YAxis className="text-xs" />
                                    <RechartsTooltip
                                        formatter={(value: number) => [value, 'Occurrences']}
                                        labelFormatter={(label) => `Loss: ${label}`}
                                    />
                                    <Bar dataKey="frequency" fill="hsl(var(--primary))" />
                                </BarChart>
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
