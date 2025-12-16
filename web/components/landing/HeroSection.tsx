
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight } from "lucide-react";

/**
 * HeroSection Component
 * Displays the main headline, description, and primary CTAs.
 */
export function HeroSection() {
    return (
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
                            <Link href="/simulation">
                                Try Simulation <ArrowRight className="h-4 w-4" />
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
    );
}
