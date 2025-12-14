import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, CheckCircle, Code, FileText, Zap, Shield, BarChart3, GitBranch } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col">
      {/* Hero Section */}
      <section className="relative overflow-hidden border-b bg-gradient-to-b from-background to-muted/20 py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl text-center">
            <Badge className="mb-4" variant="secondary">
              Version 1.1 • Open Source
            </Badge>
            <h1 className="mb-6 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl lg:text-7xl">
              Cyber Risk Modeling
              <span className="block bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Made Simple
              </span>
            </h1>
            <p className="mb-8 text-lg text-muted-foreground sm:text-xl md:text-2xl">
              An open, declarative language for expressing cyber risk models, telemetry mappings, and simulation pipelines.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Button asChild size="lg" className="gap-2">
                <Link href="/playground">
                  Try Playground <ArrowRight className="h-4 w-4" />
                </Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/validator">Validate Model</Link>
              </Button>
            </div>
          </div>
        </div>

        {/* Decorative gradient */}
        <div className="absolute inset-x-0 top-0 -z-10 transform-gpu overflow-hidden blur-3xl">
          <div className="relative left-[calc(50%-11rem)] aspect-[1155/678] w-[36.125rem] -translate-x-1/2 rotate-[30deg] bg-gradient-to-tr from-blue-600 to-purple-600 opacity-20 sm:left-[calc(50%-30rem)] sm:w-[72.1875rem]" />
        </div>
      </section>

      {/* Features Section */}
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

      {/* Use Cases Section */}
      <section className="border-t bg-muted/30 py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mb-12 text-center">
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Use Cases
            </h2>
            <p className="mx-auto max-w-2xl text-lg text-muted-foreground">
              CRML is designed for a wide range of cyber risk modeling scenarios
            </p>
          </div>

          <div className="mx-auto grid max-w-4xl gap-6">
            {[
              "Bayesian cyber risk models (QBER, MCMC-based)",
              "FAIR-style Monte Carlo engines",
              "Insurance actuarial risk systems",
              "Enterprise cyber risk quantification platforms",
              "Regulatory or audit-ready risk engines",
            ].map((useCase, index) => (
              <div key={index} className="flex items-start gap-3">
                <CheckCircle className="mt-1 h-5 w-5 flex-shrink-0 text-green-600" />
                <p className="text-lg">{useCase}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Start Section */}
      <section className="py-20 md:py-32">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-4xl">
            <div className="mb-12 text-center">
              <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
                Quick Start
              </h2>
              <p className="text-lg text-muted-foreground">
                Get started with CRML in minutes
              </p>
            </div>

            <Card className="border-2">
              <CardHeader>
                <CardTitle>Install from PyPI</CardTitle>
                <CardDescription>Install the CRML validator using pip</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-lg bg-muted p-4 font-mono text-sm">
                  <code>pip install crml-lang</code>
                </div>
              </CardContent>
            </Card>

            <div className="mt-6">
              <Card className="border-2">
                <CardHeader>
                  <CardTitle>Validate Your Model</CardTitle>
                  <CardDescription>Use the CLI to validate CRML files</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg bg-muted p-4 font-mono text-sm">
                    <code>crml validate path/to/your/model.yaml</code>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="mt-8 text-center">
              <Button asChild size="lg" variant="outline">
                <Link href="/docs">Read Full Documentation</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="border-t bg-gradient-to-b from-background to-muted/20 py-20">
        <div className="container mx-auto px-4">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="mb-4 text-3xl font-bold tracking-tight sm:text-4xl">
              Ready to Get Started?
            </h2>
            <p className="mb-8 text-lg text-muted-foreground">
              Try our online validator or explore example models to see CRML in action.
            </p>
            <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
              <Button asChild size="lg">
                <Link href="/validator">Open Validator</Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <Link href="/examples">Browse Examples</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
