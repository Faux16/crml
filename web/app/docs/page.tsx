import Link from "next/link";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BookOpen, FileText, Github, ExternalLink } from "lucide-react";

export default function DocsPage() {
    return (
        <div className="container mx-auto px-4 py-8">
            <div className="mb-8">
                <h1 className="mb-2 text-3xl font-bold tracking-tight sm:text-4xl">
                    Documentation
                </h1>
                <p className="text-lg text-muted-foreground">
                    Learn how to use CRML to define and validate cyber risk models
                </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {/* Getting Started */}
                <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                    <CardHeader>
                        <BookOpen className="mb-2 h-10 w-10 text-blue-600" />
                        <CardTitle>Getting Started</CardTitle>
                        <CardDescription>
                            Quick introduction to CRML and installation guide
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div>
                                <h3 className="mb-2 font-semibold">Installation</h3>
                                <div className="rounded-lg bg-muted p-3 font-mono text-sm">
                                    pip install crml-lang
                                </div>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Basic Usage</h3>
                                <div className="rounded-lg bg-muted p-3 font-mono text-sm">
                                    crml validate model.yaml
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Specification */}
                <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                    <CardHeader>
                        <FileText className="mb-2 h-10 w-10 text-purple-600" />
                        <CardTitle>CRML Specification</CardTitle>
                        <CardDescription>
                            Complete reference for CRML 1.1 syntax and features
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2 text-sm">
                            <li>• Model structure and components</li>
                            <li>• Data source definitions</li>
                            <li>• Frequency and severity models</li>
                            <li>• Simulation pipelines</li>
                            <li>• Output configuration</li>
                        </ul>
                        <Button asChild variant="outline" className="mt-4 w-full gap-2">
                            <a
                                href="https://github.com/Faux16/crml/blob/main/spec/crml-1.1.md"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                View Spec <ExternalLink className="h-4 w-4" />
                            </a>
                        </Button>
                    </CardContent>
                </Card>

                {/* Examples */}
                <Card className="border-2 transition-all hover:border-primary/50 hover:shadow-lg">
                    <CardHeader>
                        <Github className="mb-2 h-10 w-10 text-green-600" />
                        <CardTitle>Examples & Templates</CardTitle>
                        <CardDescription>
                            Real-world CRML models to get you started
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ul className="space-y-2 text-sm">
                            <li>• QBER enterprise model</li>
                            <li>• FAIR baseline model</li>
                            <li>• Custom risk scenarios</li>
                            <li>• Integration examples</li>
                        </ul>
                        <Button asChild className="mt-4 w-full">
                            <Link href="/examples">Browse Examples</Link>
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {/* Key Concepts */}
            <div className="mt-12">
                <h2 className="mb-6 text-2xl font-bold">Key Concepts</h2>
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Model Structure</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <h3 className="mb-2 font-semibold">Meta Section</h3>
                                <p className="text-sm text-muted-foreground">
                                    Contains model metadata including name, version, description, author, and tags.
                                </p>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Data Section</h3>
                                <p className="text-sm text-muted-foreground">
                                    Defines data sources, schemas, and feature mappings for telemetry integration.
                                </p>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Model Section</h3>
                                <p className="text-sm text-muted-foreground">
                                    Specifies assets, frequency models, severity models, dependencies, and temporal aspects.
                                </p>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Pipeline Section</h3>
                                <p className="text-sm text-muted-foreground">
                                    Configures simulation parameters including Monte Carlo and MCMC settings.
                                </p>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Output Section</h3>
                                <p className="text-sm text-muted-foreground">
                                    Defines metrics, distributions, diagnostics, and export formats.
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Supported Models</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <h3 className="mb-2 font-semibold">Frequency Models</h3>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                        <li>• Poisson</li>
                                        <li>• Negative Binomial</li>
                                        <li>• Hierarchical Gamma-Poisson</li>
                                    </ul>
                                </div>
                                <div>
                                    <h3 className="mb-2 font-semibold">Severity Models</h3>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                        <li>• Lognormal</li>
                                        <li>• Gamma</li>
                                        <li>• Mixture models</li>
                                    </ul>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            </div>

            {/* Resources */}
            <div className="mt-12">
                <h2 className="mb-6 text-2xl font-bold">Additional Resources</h2>
                <div className="grid gap-4 md:grid-cols-2">
                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">GitHub Repository</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="mb-4 text-sm text-muted-foreground">
                                Access the source code, report issues, and contribute to CRML development.
                            </p>
                            <Button asChild variant="outline" className="gap-2">
                                <a
                                    href="https://github.com/Faux16/crml"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    <Github className="h-4 w-4" />
                                    View on GitHub
                                </a>
                            </Button>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle className="text-lg">PyPI Package</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="mb-4 text-sm text-muted-foreground">
                                Install CRML from the Python Package Index for use in your projects.
                            </p>
                            <Button asChild variant="outline" className="gap-2">
                                <a
                                    href="https://pypi.org/project/crml-lang/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    <ExternalLink className="h-4 w-4" />
                                    View on PyPI
                                </a>
                            </Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}
