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
                            <CardTitle>What CRML Is</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div>
                                <p className="text-sm text-muted-foreground">
                                    CRML (Cyber Risk Modeling Language) is a declarative YAML/JSON format for describing cyber
                                    risk models in a way that tools can validate, simulate, and visualize.
                                </p>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Think of it as…</h3>
                                <ul className="space-y-1 text-sm text-muted-foreground">
                                    <li>• A portable input contract (your models) that can be checked in CI</li>
                                    <li>• A shared vocabulary for scenarios, portfolios, controls, and relationships</li>
                                    <li>• A stable output envelope so dashboards and UIs can consume results consistently</li>
                                </ul>
                            </div>
                            <div>
                                <h3 className="mb-2 font-semibold">Where you’ll use it</h3>
                                <p className="text-sm text-muted-foreground">
                                    Write models as files, validate them with the CLI or the <Link href="/validator" className="text-primary hover:underline">Validator</Link>,
                                    and run simulations in the <Link href="/playground?tab=simulate" className="text-primary hover:underline">Simulation</Link> UI.
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Architecture (Language → Engine → UI)</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="mb-4 text-sm text-muted-foreground">
                                CRML is split on purpose so different tools can interoperate without being tightly coupled.
                            </p>
                            <div className="grid gap-4 md:grid-cols-3">
                                <div>
                                    <h3 className="mb-2 font-semibold">Language / Spec</h3>
                                    <p className="text-sm text-muted-foreground">
                                        <span className="font-mono">crml_lang</span> defines document shapes, schemas, and validation.
                                    </p>
                                </div>
                                <div>
                                    <h3 className="mb-2 font-semibold">Engine / Runtime</h3>
                                    <p className="text-sm text-muted-foreground">
                                        <span className="font-mono">crml_engine</span> executes simulations (CLI + runtime) using validated inputs.
                                    </p>
                                </div>
                                <div>
                                    <h3 className="mb-2 font-semibold">Web UI</h3>
                                    <p className="text-sm text-muted-foreground">
                                        <span className="font-mono">web/</span> (CRML Studio) calls the same validator/runtime and presents results.
                                    </p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Core Artifacts (Files You’ll See)</CardTitle>
                            <CardDescription>
                                Most CRML work is just authoring and moving a few well-defined document types around.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="grid gap-4 md:grid-cols-2">
                                <div>
                                    <h3 className="mb-2 font-semibold">Inputs</h3>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                        <li>• Scenario: frequency + severity assumptions for one risk</li>
                                        <li>• Portfolio: assets/exposure + scenario bindings</li>
                                        <li>• Catalogs: controls and attacks (stable identifiers + metadata)</li>
                                        <li>• Assessments & relationships: “what’s implemented” and how things map</li>
                                    </ul>
                                </div>
                                <div>
                                    <h3 className="mb-2 font-semibold">Contracts between tools</h3>
                                    <ul className="space-y-1 text-sm text-muted-foreground">
                                        <li>• Bundle: a self-contained, inlined input artifact for engines</li>
                                        <li>• Result envelope: a stable output format for UIs and reporting</li>
                                    </ul>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Typical End-to-End Workflow</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <ol className="space-y-2 text-sm text-muted-foreground">
                                <li>1) Start from an example scenario (or write a tiny one) and validate it.</li>
                                <li>2) Run Monte Carlo simulation to get metrics like expected loss and tail risk.</li>
                                <li>3) When you need exposure (many assets) or multiple scenarios, create a portfolio.</li>
                                <li>4) Optionally add catalogs, assessments, and mappings to connect controls ↔ threats.</li>
                                <li>5) Export results (JSON) for dashboards, or explore them here in CRML Studio.</li>
                            </ol>
                            <p className="text-sm text-muted-foreground">
                                Want something concrete? Open <Link href="/examples" className="text-primary hover:underline">Examples</Link> and load a scenario into the
                                simulation UI.
                            </p>
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
