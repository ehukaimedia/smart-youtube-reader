"use client";

import Link from 'next/link';
import { DEMO_PROVIDERS, isDemoJobId } from './demoProviders';

// Shown only on the bundled demo reader pages. Lets a reader compare the
// same teaching digest rendered with each provider's image style.
export default function DemoProviderTabs({ jobId }: { jobId: string }) {
    if (!isDemoJobId(jobId)) return null;

    return (
        <section className="demo-provider-tabs" aria-label="Compare demo image versions">
            <span className="demo-provider-label" id="demo-provider-label">Demo image versions</span>
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
