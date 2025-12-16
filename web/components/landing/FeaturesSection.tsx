
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Shield, BarChart3, FileText, Code, GitBranch, Zap } from "lucide-react";

/**
 * FeaturesSection Component
 * Displays the grid of key features.
 */
export function FeaturesSection() {
    return (
        <section className="py-20 md:py-32">
            <div className="container mx-auto px-4">
                <div className="mb-12 text-center">
                    <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
                        Built for Risk Professionals
                    </h2>
                    <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
                        CRML provides a standardized way to define and validate cyber risk models across different platforms and tools.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <Shield className="mb-2 h-10 w-10 text-blue-600" />
                            <CardTitle>Bayesian Models</CardTitle>
                            <CardDescription>
                                Support for QBER, MCMC-based hierarchical Bayesian models with entropy-based confidence intervals
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <BarChart3 className="mb-2 h-10 w-10 text-purple-600" />
                            <CardTitle>Monte Carlo Engines</CardTitle>
                            <CardDescription>
                                FAIR-style Monte Carlo simulation pipelines for enterprise risk quantification
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <FileText className="mb-2 h-10 w-10 text-green-600" />
                            <CardTitle>Declarative Syntax</CardTitle>
                            <CardDescription>
                                Clean YAML-based syntax for defining models, data sources, and output requirements
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <Code className="mb-2 h-10 w-10 text-orange-600" />
                            <CardTitle>Schema Validation</CardTitle>
                            <CardDescription>
                                Built-in JSON Schema validation ensures your models are correct before execution
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <GitBranch className="mb-2 h-10 w-10 text-pink-600" />
                            <CardTitle>Implementation Agnostic</CardTitle>
                            <CardDescription>
                                Define once, run anywhere - CRML models work across different risk platforms
                            </CardDescription>
                        </CardHeader>
                    </Card>

                    <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                        <CardHeader>
                            <Zap className="mb-2 h-10 w-10 text-yellow-600" />
                            <CardTitle>Quick Validation</CardTitle>
                            <CardDescription>
                                Instant validation feedback with detailed error messages and suggestions
                            </CardDescription>
                        </CardHeader>
                    </Card>
                </div>
            </div>
        </section>
    );
}
