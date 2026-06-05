"use client";

import Link from 'next/link';
import { DEMO_PROVIDERS, isDemoJobId } from './demoProviders';

// Shown only on the bundled demo reader pages. Lets a reader compare the
// same teaching digest rendered with each provider's image style.
export default function DemoProviderTabs({ jobId }: { jobId: string }) {
    if (!isDemoJobId(jobId)) return null;

    return (
        <section className="demo-provider-tabs" aria-label="Compare demo image versions">
            <div className="demo-provider-copy">
                <span className="demo-provider-label" id="demo-provider-label">Demo image versions</span>
                <span className="demo-provider-note">
                    Initial archives run locally with Gemma 4 through Ollama and need no AI subscription. Use the slicer on source archives to refine vision-selected frames.
                </span>
            </div>
            <div className="filter-pills" role="group" aria-labelledby="demo-provider-label">
                {DEMO_PROVIDERS.map((provider) => {
                    const active = provider.jobId === jobId;
                    return (
                        <Link
                            key={provider.jobId}
                            href={`/reader/${provider.jobId}`}
                            className={`pill-button ${active ? 'active' : ''}`}
                            aria-current={active ? 'page' : undefined}
                        >
                            {provider.label}
                        </Link>
                    );
                })}
            </div>
        </section>
    );
}
