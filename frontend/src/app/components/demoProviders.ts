// Bundled demo digest variants. Each is a self-contained job under
// examples/demo-jobs/<folder> that the backend seeds into data/jobs/.
// The provider switcher in the reader and the Help nav active-state both
// read from this list so the three demos stay in sync.

export type DemoProvider = {
    jobId: string;
    label: string;
};

export const DEMO_PROVIDERS: DemoProvider[] = [
    { jobId: 'demo-smart-youtube-reader-digest', label: 'Codex' },
    { jobId: 'demo-smart-youtube-reader-gemini', label: 'Gemini' },
    { jobId: 'demo-smart-youtube-reader-claude', label: 'Claude' },
];

// The default demo the Help link opens.
export const DEFAULT_DEMO_JOB_ID = DEMO_PROVIDERS[0].jobId;

export const DEMO_JOB_IDS: string[] = DEMO_PROVIDERS.map((provider) => provider.jobId);

export function isDemoJobId(jobId: string | null | undefined): boolean {
    return Boolean(jobId) && DEMO_JOB_IDS.includes(jobId as string);
}
