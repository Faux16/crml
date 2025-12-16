
import { CheckCircle } from "lucide-react";

/**
 * UseCasesSection Component
 * Lists the primary use cases for CRML.
 */
export function UseCasesSection() {
    return (
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
    );
}
