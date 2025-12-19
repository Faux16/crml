"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { Menu, X, Link2 } from "lucide-react";

export default function Navbar() {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
            <div className="container mx-auto px-4">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center space-x-2">
                        <Image src="/crml-logo.png" alt="CRML Logo" width={32} height={32} className="h-8 w-8" />
                        <span className="font-bold text-xl">CRML</span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center space-x-6">
                        <Link href="/" className="text-sm font-medium hover:text-primary transition-colors">
                            Home
                        </Link>
                        <Link href="/playground" className="text-sm font-medium hover:text-primary transition-colors">
                            Playground
                        </Link>
                        <Link href="/examples" className="text-sm font-medium hover:text-primary transition-colors">
                            Examples
                        </Link>
                        <Link href="/docs" className="text-sm font-medium hover:text-primary transition-colors">
                            Docs
                        </Link>
                        <a
                            href="https://github.com/Faux16/crml"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm font-medium hover:text-primary transition-colors"
                        >
                            <Link2 className="h-5 w-5" />
                        </a>
                    </div>

                    {/* Mobile menu button */}
                    <button
                        className="md:hidden"
                        onClick={() => setIsOpen(!isOpen)}
                        aria-label="Toggle menu"
                    >
                        {isOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                    </button>
                </div>

                {/* Mobile Navigation */}
                {isOpen && (
                    <div className="md:hidden py-4 space-y-2">
                        <Link
                            href="/"
                            className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Home
                        </Link>
                        <Link
                            href="/playground"
                            className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Playground
                        </Link>
                        <Link
                            href="/examples"
                            className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Examples
                        </Link>
                        <Link
                            href="/docs"
                            className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                            onClick={() => setIsOpen(false)}
                        >
                            Docs
                        </Link>
                        <a
                            href="https://github.com/Faux16/crml"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block py-2 text-sm font-medium hover:text-primary transition-colors"
                        >
                            GitHub
                        </a>
                    </div>
                )}
            </div>
        </nav>
    );
}
