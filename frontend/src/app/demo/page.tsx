"use client";

import Link from 'next/link';
import { useState } from 'react';
import { getApiBase } from '@/lib/api';

type DemoKey = 'codex' | 'gemini';

const DEMOS: Record<DemoKey, {
    label: string;
    title: string;
    model: string;
    jobId: string;
    folder: string;
    summaryImage: string;
    description: string;
}> = {
    codex: {
        label: 'Codex',
        title: 'Codex Demo Digest',
        model: 'Codex + GPT 2.0 images',
        jobId: 'demo-smart-youtube-reader-digest',
        folder: 'smart-youtube-reader-demo-digest_demo',
        summaryImage: 'generated/chapter-03-default-ai-digest-premium.webp',
        description: 'The default bundled proof project, using Codex with GPT 2.0 image generation for the premium teaching-card set.'
    },
    gemini: {
        label: 'Gemini',
        title: 'Gemini Demo Digest',
        model: 'Gemini 3.5 Flash High images',
        jobId: 'demo-smart-youtube-reader-gemini',
        folder: 'smart-youtube-reader-gemini',
        summaryImage: 'generated/chapter-03-default-ai-digest-premium.webp',
        description: 'A parallel bundled proof project, using Gemini 3.5 Flash High image generation for the simple and premium teaching-card sets.'
    }
};

export default function DemoPage() {
    const [activeDemo, setActiveDemo] = useState<DemoKey>('codex');
    const demo = DEMOS[activeDemo];
    const imageUrl = `${getApiBase()}/data/jobs/${demo.folder}/${demo.summaryImage}`;

    return (
        <main className="container demo-page">
            <header className="page-header">
                <div>
                    <h1 className="page-title">Demo digest</h1>
                    <p className="muted">Choose the image-generation version you want to inspect.</p>
                </div>
                <Link href="/dashboard" className="btn btn-secondary btn-compact">
                    Dashboard
                </Link>
            </header>

            <div className="demo-tabs" role="tablist" aria-label="Demo digest image generator">
                {(Object.keys(DEMOS) as DemoKey[]).map((key) => {
                    const item = DEMOS[key];
                    const isActive = activeDemo === key;
                    return (
                        <button
                            key={key}
                            type="button"
                            role="tab"
                            aria-selected={isActive}
                            aria-controls="demo-panel"
                            id={`demo-tab-${key}`}
                            className={`demo-tab ${isActive ? 'active' : ''}`}
                            onClick={() => setActiveDemo(key)}
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
                aria-labelledby={`demo-tab-${activeDemo}`}
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
