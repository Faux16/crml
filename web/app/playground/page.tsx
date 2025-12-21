import { Suspense } from "react";
import PlaygroundClient from "./PlaygroundClient";

export default function PlaygroundPage() {
    return (
        <Suspense fallback={<div className="container mx-auto px-4 py-8" />}> 
            <PlaygroundClient />
        </Suspense>
    );
}
