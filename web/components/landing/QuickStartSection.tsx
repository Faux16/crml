
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * QuickStartSection Component
 * Provides instructions for getting started.
 */
export function QuickStartSection() {
    return (
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
    );
}
