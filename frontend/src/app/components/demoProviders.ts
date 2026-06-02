// Bundled demo digest variants. Each is a self-contained job under
// examples/demo-jobs/<folder> that the backend seeds into data/jobs/.
// The provider switcher in the reader and the Help nav active-state both
// read from this list so the three demos stay in sync.

export type DemoProvider = {
    jobId: string;
    label: string;
    title: string;
    model: string;
    folder: string;
    summaryImage: string;
    description: string;
};

export const DEMO_PROVIDERS: DemoProvider[] = [
    {
        jobId: 'demo-smart-youtube-reader-claude',
        label: 'Claude',
        title: 'Smart YouTube Reader Demo Digest (Claude)',
        model: 'Claude Opus 4.8 images',
        folder: 'smart-youtube-reader-claude',
        summaryImage: 'generated/chapter-03-default-ai-digest-premium.webp',
        description: 'A bundled proof project, using Claude Opus 4.8-authored HTML/CSS rendered to WebP for the simple and premium teaching-card sets.'
    },
    {
        jobId: 'demo-smart-youtube-reader-digest',
        label: 'Codex',
        title: 'Smart YouTube Reader Demo Digest (Codex)',
        model: 'Codex GPT 5.5 images',
        folder: 'smart-youtube-reader-demo-digest_demo',
        summaryImage: 'generated/chapter-03-default-ai-digest-premium.webp',
        description: 'The default bundled proof project, using Codex GPT 5.5 image generation for the premium teaching-card set.'
    },
    {
        jobId: 'demo-smart-youtube-reader-gemini',
        label: 'Gemini',
        title: 'Smart YouTube Reader Demo Digest (Gemini 3.5 Flash High)',
        model: 'Gemini 3.5 Flash High images',
        folder: 'smart-youtube-reader-gemini',
        summaryImage: 'generated/chapter-04-group-digest-premium.webp',
        description: 'A bundled proof project, using Gemini 3.5 Flash High image generation for the simple and premium teaching-card sets.'
    },
];

// The demo selector opens on the first alphabetical provider.
export const DEFAULT_DEMO_JOB_ID = DEMO_PROVIDERS[0].jobId;

export const DEMO_JOB_IDS: string[] = DEMO_PROVIDERS.map((provider) => provider.jobId);

export function isDemoJobId(jobId: string | null | undefined): boolean {
    return Boolean(jobId) && DEMO_JOB_IDS.includes(jobId as string);
}
