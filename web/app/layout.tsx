import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "CRML - Cyber Risk Modeling Language",
  description: "An open, declarative, implementation-agnostic language for expressing cyber risk models, telemetry mappings, simulation pipelines, dependencies, and output requirements.",
  keywords: ["CRML", "cyber risk", "risk modeling", "Bayesian", "FAIR", "QBER", "risk quantification"],
  authors: [{ name: "Zeron Research Labs" }],
  openGraph: {
    title: "CRML - Cyber Risk Modeling Language",
    description: "An open, declarative language for cyber risk models",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
