import Image from "next/image";
import Link from "next/link";
import { Link2, Mail, Globe } from "lucide-react";

export default function Footer() {
    return (
        <footer className="border-t bg-muted/50">
            <div className="container mx-auto px-4 py-8">
                <div className="grid gap-8 md:grid-cols-3">
                    {/* Logo & Description */}
                    <div>
                        <Link href="/" className="flex items-center space-x-2 mb-3">
                            <Image src="/crml-logo.png" alt="CRML Logo" width={32} height={32} className="h-8 w-8" />
                            <span className="font-bold text-lg">CRML</span>
                        </Link>
                        <p className="text-sm text-muted-foreground">
                            Cyber Risk Modeling Language - An open, declarative language for cyber risk models.
                        </p>
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-semibold mb-3">Quick Links</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <Link href="/validator" className="text-muted-foreground hover:text-primary transition-colors">
                                    Validator
                                </Link>
                            </li>
                            <li>
                                <Link href="/examples" className="text-muted-foreground hover:text-primary transition-colors">
                                    Examples
                                </Link>
                            </li>
                            <li>
                                <Link href="/docs" className="text-muted-foreground hover:text-primary transition-colors">
                                    Documentation
                                </Link>
                            </li>
                        </ul>
                    </div>

                    {/* Resources */}
                    <div>
                        <h3 className="font-semibold mb-3">Resources</h3>
                        <ul className="space-y-2 text-sm">
                            <li>
                                <a
                                    href="https://github.com/Faux16/crml"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-muted-foreground hover:text-primary transition-colors"
                                >
                                    GitHub Repository
                                </a>
                            </li>
                            <li>
                                <a
                                    href="https://pypi.org/project/crml-lang/"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-muted-foreground hover:text-primary transition-colors"
                                >
                                    PyPI Package
                                </a>
                            </li>
                            <li>
                                <a
                                    href="https://github.com/Faux16/crml/blob/main/CONTRIBUTING.md"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-muted-foreground hover:text-primary transition-colors"
                                >
                                    Contributing
                                </a>
                            </li>
                        </ul>
                    </div>

                    {/* Contact */}
                    <div>
                        <h3 className="font-semibold mb-3">Contact</h3>
                        <ul className="space-y-2 text-sm">
                            <li className="flex items-center space-x-2 text-muted-foreground">
                                <Globe className="h-4 w-4" />
                                <a
                                    href="https://zeron.one"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-primary transition-colors"
                                >
                                    zeron.one
                                </a>
                            </li>
                            <li className="flex items-center space-x-2 text-muted-foreground">
                                <Mail className="h-4 w-4" />
                                <a
                                    href="mailto:research@zeron.one"
                                    className="hover:text-primary transition-colors"
                                >
                                    research@zeron.one
                                </a>
                            </li>
                            <li className="flex items-center space-x-2 text-muted-foreground">
                                <Link2 className="h-4 w-4" />
                                <a
                                    href="https://github.com/Faux16"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:text-primary transition-colors"
                                >
                                    @Faux16
                                </a>
                            </li>
                        </ul>
                    </div>
                </div>

                <div className="mt-8 pt-8 border-t text-center text-sm text-muted-foreground">
                    <p>
                        © {new Date().getFullYear()} Zeron Research Labs. Licensed under{" "}
                        <a
                            href="https://opensource.org/licenses/MIT"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-primary transition-colors"
                        >
                            MIT License
                        </a>.
                    </p>
                </div>
            </div>
        </footer>
    );
}
