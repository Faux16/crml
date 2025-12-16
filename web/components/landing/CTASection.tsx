
import Link from "next/link";
import { Button } from "@/components/ui/button";

/**
 * CTASection Component
 * Final call to action at the bottom of the page.
 */
export function CTASection() {
    return (
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
    );
}
