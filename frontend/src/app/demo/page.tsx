"use client";

import Link from 'next/link';
import { useState } from 'react';
import { getApiBase } from '@/lib/api';
import { DEFAULT_DEMO_JOB_ID, DEMO_PROVIDERS } from '../components/demoProviders';

export default function DemoPage() {
    const [activeJobId, setActiveJobId] = useState(DEFAULT_DEMO_JOB_ID);
    const demo = DEMO_PROVIDERS.find((provider) => provider.jobId === activeJobId) ?? DEMO_PROVIDERS[0];
    const imageUrl = `${getApiBase()}/data/jobs/${demo.folder}/${demo.summaryImage}`;

    return (
        <main className="container demo-page">
            <header className="page-header">
                <div>
                    <h1 className="page-title">Demo digest</h1>
                    <p className="muted">Choose the image-generation version you want to inspect.</p>
                    <p className="muted" style={{ marginTop: '0.5rem', maxWidth: '64ch' }}>
                        The initial video digest runs locally with Gemma 4 through MLX-VLM, so no AI subscription is needed to capture and read a structured archive. These demos compare optional external-agent image digest styles.
                    </p>
                    <p className="muted" style={{ marginTop: '0.5rem', maxWidth: '64ch' }}>
                        For source archives, the slicer lets you manually select the exact video frames that best match the chapter content before sharing or sending the archive to an agent.
                    </p>
                </div>
                <Link href="/dashboard" className="btn btn-secondary btn-compact">
                    Dashboard
                </Link>
            </header>

            <div className="demo-tabs" role="tablist" aria-label="Demo digest image generator">
                {DEMO_PROVIDERS.map((item) => {
                    const isActive = demo.jobId === item.jobId;
                    return (
                        <button
                            key={item.jobId}
                            type="button"
                            role="tab"
                            aria-selected={isActive}
                            aria-controls="demo-panel"
                            id={`demo-tab-${item.label.toLowerCase()}`}
                            className={`demo-tab ${isActive ? 'active' : ''}`}
                            onClick={() => setActiveJobId(item.jobId)}
                        >
                            <span>{item.label}</span>
                            <small>{item.model}</small>
                        </button>
                    );
                })}
            </div>

            <section
                id="demo-panel"
                role="tabpanel"
                aria-labelledby={`demo-tab-${demo.label.toLowerCase()}`}
                className="demo-panel"
            >
                <div className="demo-preview">
                    <img
                        src={imageUrl}
                        alt={`${demo.title} summary image`}
                        loading="eager"
                        decoding="async"
                    />
                </div>
                <div className="demo-copy">
                    <div className="badge-row">
                        <span className="status-badge badge-success">Bundled demo</span>
                        <span className="status-badge">{demo.model}</span>
                    </div>
                    <h2>{demo.title}</h2>
                    <p>{demo.description}</p>
                    <div className="action-row">
                        <Link href={`/reader/${demo.jobId}`} className="btn btn-primary btn-compact">
                            Open Demo
                        </Link>
                        <Link href="/dashboard" className="btn btn-secondary btn-compact">
                            View Library
                        </Link>
                    </div>
                </div>
            </section>
        </main>
    );
}
