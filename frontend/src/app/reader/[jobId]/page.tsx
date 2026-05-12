'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getApiBase, getShareOrigin } from '@/lib/api';
import { copyText } from '@/lib/clipboard';
import { useToast } from '../../components/ToastProvider';

type Job = {
    id: string;
    status: string;
    video_url?: string | null;
    title?: string | null;
    created_at: number;
    error?: string | null;
    data_folder_name?: string | null;
    current_step?: string | null;
    kind?: string | null;
    source_job_id?: string | null;
    digest_model?: string | null;
    media_policy?: string | null;
};

type TranscriptLine = {
    text: string;
    start: number;
    duration?: number;
};

type ArchiveChapter = {
    concept: string;
    summary: string;
    content: string;
    timestamp_start: number;
    timestamp_end?: number;
    images?: string[];
    _image_context?: Record<string, FrameMetadata>;
    _slice_id?: string;
    type: 'chapter';
    sortTime: number;
};

type ArchiveMetadata = {
    summary_image?: string;
    media_policy?: string;
};

type FrameMetadata = {
    timestamp?: number;
    visual_score?: number;
    edge_density?: number;
    dark_ratio?: number;
    skin_ratio?: number;
};

type SliceManifest = {
    frames?: Array<{
        filename?: string;
        timestamp?: number;
    }>;
};

export default function ReaderPage() {
    const { jobId } = useParams();
    const [job, setJob] = useState<Job | null>(null);
    const [transcript, setTranscript] = useState<TranscriptLine[] | null>(null);
    const [error, setError] = useState('');
    const [promptCopied, setPromptCopied] = useState(false);
    const [linkCopied, setLinkCopied] = useState(false);
    const [digestTaskCopied, setDigestTaskCopied] = useState(false);
    const [digestWithImagesTaskCopied, setDigestWithImagesTaskCopied] = useState(false);

    const copyLearningPrompt = (job: Job) => {
        const archiveUrl = `${getApiBase()}/jobs/${job.id}/archive`;
        const baseUrl = `${getApiBase()}/data/jobs/${job.data_folder_name}`;
        const prompt = `You have access to a structured archive of a YouTube video.

Video: "${job.title || job.id}"
YouTube: ${job.video_url || '(not available)'}
Archive JSON: ${archiveUrl}

Each chapter in the archive has:
- concept: topic title
- summary: one-sentence overview
- content: compact transcript-grounded teaching evidence for the section
- timestamp_start / timestamp_end: seconds into the video
- images: array of frame filenames — fetch and read these, they often contain slides, diagrams, and visual explanations that are NOT in the transcript text

To read a frame image: ${baseUrl}/<filename>  (e.g. ${baseUrl}/frames/0007.png)
To jump to a section on YouTube: append &t=<timestamp_start> to the YouTube URL

Start by fetching the archive JSON, then for each chapter read both the content text AND the frame images — this video likely uses visual slides to explain its concepts.

What would you like to know about this video?`;
        const onCopied = () => {
            setPromptCopied(true);
            setTimeout(() => setPromptCopied(false), 2000);
        };
        copyText(prompt, onCopied);
    };

    const copyProjectLink = async () => {
        const shareOrigin = await getShareOrigin();
        const url = `${shareOrigin}/reader/${jobId}`;
        const onCopied = () => {
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        };

        copyText(url, onCopied);
    };

    const copyAiDigestWithImagesTask = (job: Job) => {
        const projectFolder = `data/jobs/${job.data_folder_name}`;
        const draftPath = `${projectFolder}/generated/ai-digest-draft.json`;
        const prompt = `Create a Smart YouTube Reader AI digest version with generated teaching images for this project using the local CLI.

Do not use an in-app model option. You are the digest-and-image agent.
Run commands from the smart-youtube-reader repo root.

Important:
- Read archive.json and inspect the attached frame images before deciding what to keep.
- Create a new digestible chapter structure, not a light paraphrase.
- Create one novel generated teaching image per digest chapter.
- Keep the digest to at most 6 chapters/images. If the material truly needs more than 6 images, explain the needed count in operator_image_note and still produce the best 6-image digest.
- Do not copy, crop, trace, or reuse source frames, screenshots, or YouTube thumbnails.

Workflow:
1. Run this command to print the exact digest-with-images task:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --with-images
2. Read archive.json and inspect the attached frame images as evidence.
3. Cut fluff, repetition, sponsor chatter, intros/outros, and low-value transitions.
4. Preserve durable facts, theory, procedures, examples, caveats, failure modes, and useful visual explanations.
5. Save the generated images under:
   ${projectFolder}/generated/
6. Write the required JSON draft to:
   ${draftPath}
7. Materialize the new AI digest project:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --draft "${draftPath}"
8. Verify the dashboard shows the new project with an AI Digest badge and the reader opens it with one generated image per chapter.

Source project:
${projectFolder}`;
        const onCopied = () => {
            setDigestWithImagesTaskCopied(true);
            setTimeout(() => setDigestWithImagesTaskCopied(false), 2000);
        };

        copyText(prompt, onCopied);
    };

    const copyAiDigestTask = (job: Job) => {
        const projectFolder = `data/jobs/${job.data_folder_name}`;
        const draftPath = `${projectFolder}/generated/ai-digest-draft.json`;
        const prompt = `Create a Smart YouTube Reader AI digest version for this project using the local CLI.

Do not use an in-app model option. You are the digest agent.
Run commands from the smart-youtube-reader repo root.

Workflow:
1. Run this command to print the exact digest task:
   python3 tools/create_ai_digest_version.py "${projectFolder}"
2. Read archive.json and inspect the attached frame images before deciding what to keep.
3. Cut fluff, repetition, sponsor chatter, intros/outros, and low-value transitions.
4. Preserve durable concepts, procedures, definitions, examples, caveats, and useful visual explanations.
5. Write the required JSON draft to:
   ${draftPath}
6. Materialize the new AI digest project:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --draft "${draftPath}"
7. Verify the dashboard shows the new project with an AI Digest badge and the reader opens it.

Source project:
${projectFolder}`;
        const onCopied = () => {
            setDigestTaskCopied(true);
            setTimeout(() => setDigestTaskCopied(false), 2000);
        };

        copyText(prompt, onCopied);
    };

    useEffect(() => {
        if (!jobId) return;

        let cancelled = false;
        const fetchStatus = async () => {
            try {
                const res = await fetch(`${getApiBase()}/jobs/${jobId}`);
                if (!res.ok) throw new Error('Failed to fetch job');
                const data = await res.json();
                if (cancelled) return;
                setJob(data);

                if (data.status === 'complete' && !transcript) {
                    // Fetch transcript
                    const tres = await fetch(`${getApiBase()}/jobs/${jobId}/transcript`);
                    if (cancelled) return;
                    if (tres.ok) {
                        const tdata = await tres.json();
                        if (cancelled) return;
                        setTranscript(tdata);
                    }
                }
            } catch (err) {
                console.error(err);
                setError('Failed to load job');
            }
        };

        fetchStatus();
        if (job?.status === 'complete' || job?.status === 'failed') {
            return () => { cancelled = true; };
        }
        const interval = setInterval(fetchStatus, 2000);
        return () => {
            cancelled = true;
            clearInterval(interval);
        };
    }, [jobId, transcript, job?.status]);

    if (error) return <div className="container text-red-500">{error}</div>;
    if (!job) return <div className="container">Loading...</div>;
    const canOpenSlicer = job.kind !== 'group_ai_digest' && job.media_policy !== 'lightweight_generated_images_only';
    const kindLabel = job.kind === 'group_ai_digest'
        ? 'Group AI Digest'
        : job.kind === 'ai_digest'
            ? 'AI Digest'
            : 'Source Archive';

    return (
        <div className="container reader-page">
            <header className="reader-header">
                <div>
                    <div className="badge-row reader-badges">
                        <span className="status-badge badge-success">{kindLabel}</span>
                        <span className={`status-badge status-${job.status}`}>{job.status}</span>
                    </div>
                    {job.title && <h1 className="reader-title">{job.title}</h1>}
                    {job.source_job_id && (
                        <p className="muted">Source {job.source_job_id.slice(0, 8)}</p>
                    )}
                </div>
            </header>

            {job.status === 'complete' && job.data_folder_name && (
                <section className="action-bar">
                    <button
                        onClick={() => copyLearningPrompt(job)}
                        className="btn btn-primary btn-compact"
                    >
                        {promptCopied ? 'Copied Learning Prompt' : 'Copy Learning Prompt'}
                    </button>
                    <button
                        onClick={copyProjectLink}
                        className="btn btn-secondary btn-compact"
                    >
                        {linkCopied ? 'Copied Link' : 'Copy Project Link'}
                    </button>
                    {job.video_url && (
                        <a href={job.video_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-compact">
                            Open YouTube
                        </a>
                    )}
                    {canOpenSlicer && (
                        <a href={`/slicer/${job.id}`} className="btn btn-secondary btn-compact">
                            Open Slicer
                        </a>
                    )}
                    <details className="overflow-menu">
                        <summary aria-label="Reader actions">⋯</summary>
                        <div className="overflow-content">
                            {!job.kind && (
                                <>
                                    <button onClick={() => copyAiDigestTask(job)}>
                                        {digestTaskCopied ? 'Copied Digest Task' : 'Copy AI Digest CLI Task'}
                                    </button>
                                    <button onClick={() => copyAiDigestWithImagesTask(job)}>
                                        {digestWithImagesTaskCopied ? 'Copied Images Task' : 'Copy AI Digest with Images CLI Task'}
                                    </button>
                                </>
                            )}
                            <a
                                href={`${getApiBase()}/jobs/${job.id}/download`}
                                download={`${job.data_folder_name || job.id}.zip`}
                            >
                                Download Project ZIP
                            </a>
                        </div>
                    </details>
                </section>
            )}

            {job.status === 'processing' && (
                <div className="surface-panel" style={{ textAlign: 'center', padding: '4rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                    <div className="spinner"></div>
                    <div>
                        <h3 className="blink" style={{ marginBottom: '0.5rem' }}>
                            {job.current_step || 'Processing Video...'}
                        </h3>
                        <p style={{ color: 'var(--muted)' }}>Please wait while the AI analyzes the content.</p>
                    </div>
                </div>
            )}

            {job.status === 'failed' && (
                <div className="surface-panel" style={{ textAlign: 'center', padding: '4rem', borderColor: 'var(--error)' }}>
                    <h3 style={{ color: 'var(--error)' }}>Job Failed</h3>
                    <p>{job.error}</p>
                </div>
            )}

            {job.status === 'complete' && transcript && (
                <div className="reader-content-stack">
                    {/* AI Archive — primary content */}
                    <section className="surface-panel">
                        <h2 className="section-title">AI Archive</h2>
                        <ArchivePreview jobId={job.id} folderName={job.data_folder_name || undefined} videoUrl={job.video_url || undefined} kind={job.kind || undefined} />
                    </section>

                    {/* Raw Transcript — collapsible secondary */}
                    <details className="surface-panel">
                        <summary className="details-summary">Raw Transcript</summary>
                        <div className="raw-transcript">
                            {transcript.map((line: TranscriptLine, idx: number) => {
                                const videoId = job.video_url?.match(/[?&]v=([^&]+)/)?.[1];
                                const tsUrl = videoId
                                    ? `https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(line.start)}`
                                    : null;
                                return (
                                    <div key={idx} style={{ marginBottom: '0.75rem' }}>
                                        {tsUrl ? (
                                            <a href={tsUrl} target="_blank" rel="noopener noreferrer"
                                                style={{ color: 'var(--muted)', fontSize: '0.8rem', marginRight: '1rem', userSelect: 'none', textDecoration: 'none' }}>
                                                {Math.floor(line.start / 60)}:{String(Math.floor(line.start % 60)).padStart(2, '0')}
                                            </a>
                                        ) : (
                                            <span style={{ color: 'var(--muted)', fontSize: '0.8rem', marginRight: '1rem', userSelect: 'none' }}>
                                                {Math.floor(line.start / 60)}:{String(Math.floor(line.start % 60)).padStart(2, '0')}
                                            </span>
                                        )}
                                        <span>{line.text}</span>
                                    </div>
                                );
                            })}
                        </div>
                    </details>
                </div>
            )}
        </div>
    );
}

function ArchivePreview({ jobId, folderName, videoUrl, kind }: { jobId: string, folderName?: string, videoUrl?: string, kind?: string }) {
    const router = useRouter();
    const toast = useToast();
    const videoId = videoUrl?.match(/[?&]v=([^&]+)/)?.[1];
    const [timeline, setTimeline] = useState<ArchiveChapter[]>([]);
    const [archiveMeta, setArchiveMeta] = useState<ArchiveMetadata>({});
    const [frameMetadata, setFrameMetadata] = useState<Record<string, FrameMetadata>>({});
    const [loading, setLoading] = useState(true);
    const [imageAction, setImageAction] = useState('');
    const usesGeneratedOnlyImages = kind === 'group_ai_digest';

    const loadArchive = useCallback(async () => {
        if (!folderName) return;

        try {
            const archiveRes = await fetch(`${getApiBase()}/jobs/${jobId}/archive`, { cache: 'no-store' });
            if (archiveRes.ok) {
                const data = await archiveRes.json();
                const chapters: ArchiveChapter[] = ((data.archive || []) as Omit<ArchiveChapter, 'type' | 'sortTime'>[]).map((a) => ({
                    ...a,
                    type: 'chapter' as const,
                    sortTime: a.timestamp_start
                }));
                setTimeline(chapters);
                setArchiveMeta({
                    summary_image: data.summary_image,
                    media_policy: data.media_policy
                });
                const nextFrameMetadata: Record<string, FrameMetadata> = {};
                const archiveUsesGeneratedOnlyImages = usesGeneratedOnlyImages || data.media_policy === 'lightweight_generated_images_only';
                if (!archiveUsesGeneratedOnlyImages) {
                    Object.assign(nextFrameMetadata, await fetch(`${getApiBase()}/data/jobs/${folderName}/frames.json`, { cache: 'no-store' })
                        .then(res => res.ok ? res.json() : {})
                        .catch(() => ({})));

                    const sliceIds = Array.from(new Set(
                        chapters.flatMap(chapter => (chapter.images || [])
                            .map(imagePath => imagePath.match(/^slices\/([^/]+)\/frames\/.+$/)?.[1])
                            .filter((sliceId): sliceId is string => Boolean(sliceId))
                        )
                    ));

                    const sliceManifests = await Promise.all(sliceIds.map(async sliceId => {
                        const manifest = await fetch(`${getApiBase()}/data/jobs/${folderName}/slices/${sliceId}/slice.json`, { cache: 'no-store' })
                            .then(res => res.ok ? res.json() : null)
                            .catch(() => null) as SliceManifest | null;
                        return { sliceId, manifest };
                    }));

                    for (const { sliceId, manifest } of sliceManifests) {
                        if (!manifest?.frames) continue;
                        for (const frame of manifest.frames) {
                            if (!frame.filename || typeof frame.timestamp !== 'number') continue;
                            nextFrameMetadata[`slices/${sliceId}/frames/${frame.filename}`] = {
                                timestamp: frame.timestamp
                            };
                        }
                    }
                }

                setFrameMetadata(nextFrameMetadata);
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [folderName, jobId, usesGeneratedOnlyImages]);

    const deleteSlice = async (sliceId: string | undefined) => {
        if (!sliceId) return;
        const confirmed = await toast.confirm('Remove curated visuals from this chapter? The AI-selected images will be cleared.', { confirmLabel: 'Remove Visuals' });
        if (!confirmed) return;

        try {
            const res = await fetch(`${getApiBase()}/jobs/${jobId}/slices/${sliceId}`, { method: 'DELETE' });
            if (!res.ok) {
                const error = await res.json().catch(() => null);
                throw new Error(error?.detail || 'Failed to remove curated visuals');
            }
            await loadArchive();
        } catch (err) {
            console.error(err);
            toast.error(err instanceof Error ? err.message : 'Failed to remove curated visuals');
        }
    };

    const setChapterImages = (chapterIndex: number, images: string[]) => {
        setTimeline(prev => prev.map((chapter, index) =>
            index === chapterIndex ? { ...chapter, images } : chapter
        ));
    };

    const removeArchiveImage = async (chapterIndex: number, imagePath: string, timestampStart: number): Promise<boolean> => {
        setImageAction(`${chapterIndex}:${imagePath}`);
        try {
            const res = await fetch(`${getApiBase()}/jobs/${jobId}/archive/image`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    chapter_index: chapterIndex,
                    image_path: imagePath,
                    timestamp_start: timestampStart
                })
            });

            if (!res.ok) {
                const error = await res.json().catch(() => null);
                throw new Error(error?.detail || 'Image update failed');
            }

            const data = await res.json();
            setChapterImages(data.chapter_index ?? chapterIndex, data.images || []);
            if (!data.removed) {
                toast.info('That image was already removed. The archive has been refreshed.');
                await loadArchive();
            }
            return true;
        } catch (err) {
            console.error(err);
            toast.error(err instanceof Error ? err.message : 'Image update failed');
            return false;
        } finally {
            setImageAction('');
        }
    };

    const removeImage = async (chapterIndex: number, imagePath: string) => {
        const confirmed = await toast.confirm('Remove this image from the chapter context? The source file will stay in the project.', { confirmLabel: 'Remove Image' });
        if (!confirmed) return;
        const chapter = timeline[chapterIndex];
        await removeArchiveImage(chapterIndex, imagePath, chapter?.timestamp_start ?? 0);
    };

    const findFrameInfo = (imagePath: string, chapter?: ArchiveChapter): FrameMetadata | undefined => {
        if (chapter?._image_context?.[imagePath]) return chapter._image_context[imagePath];
        const filename = imagePath.split('/').pop() || imagePath;
        const stem = filename.replace(/\.[^.]+$/, '');
        const candidates = [
            imagePath,
            filename,
            `${stem}.png`,
            `${stem}.jpg`,
            `${stem}.jpeg`,
            `frames/${stem}.png`,
            `frames/${stem}.jpg`,
            `frames/${stem}.jpeg`,
        ];
        for (const candidate of candidates) {
            const info = frameMetadata[candidate];
            if (info) return info;
        }
        return undefined;
    };

    const formatTimestamp = (seconds?: number) => {
        if (typeof seconds !== 'number' || !Number.isFinite(seconds)) return 'time unknown';
        const clamped = Math.max(0, seconds);
        return `${Math.floor(clamped / 60)}:${String(Math.floor(clamped % 60)).padStart(2, '0')}`;
    };

    const qualityLabel = (info?: FrameMetadata) => {
        if (typeof info?.visual_score !== 'number') return 'score n/a';
        return `score ${Math.round(info.visual_score * 100)}`;
    };

    const replaceInSlicer = async (chapterIndex: number, imagePath: string, timestampStart: number) => {
        const confirmed = await toast.confirm('Open the slicer to choose a replacement? The current image will stay attached until the replacement is saved.', { confirmLabel: 'Open Slicer' });
        if (!confirmed) return;
        const imageTimestamp = findFrameInfo(imagePath, timeline[chapterIndex])?.timestamp;
        const replacementStart = typeof imageTimestamp === 'number' ? imageTimestamp - 2 : timestampStart;
        const start = Math.max(0, Math.floor(replacementStart));
        const returnTo = encodeURIComponent(`/reader/${jobId}#chapter-${chapterIndex}`);
        router.push(`/slicer/${jobId}?start=${start}&return=${returnTo}&replaceChapter=${chapterIndex}&replaceImage=${encodeURIComponent(imagePath)}`);
    };

    const openChapterSlicer = (chapterIndex: number, timestampStart: number) => {
        const start = Math.max(0, Math.floor(timestampStart));
        const returnTo = encodeURIComponent(`/reader/${jobId}#chapter-${chapterIndex}`);
        router.push(`/slicer/${jobId}?start=${start}&return=${returnTo}&replaceChapter=${chapterIndex}`);
    };

    useEffect(() => {
        loadArchive();
    }, [loadArchive]);

    useEffect(() => {
        if (loading || timeline.length === 0 || !window.location.hash) return;
        window.setTimeout(() => {
            const target = document.querySelector(window.location.hash);
            target?.scrollIntoView({ block: 'start' });
        }, 100);
    }, [loading, timeline.length]);

    const usesLightweightGeneratedImages = archiveMeta.media_policy === 'lightweight_generated_images_only';
    const hideSourceImageControls = usesGeneratedOnlyImages || usesLightweightGeneratedImages;

    if (loading) return <div className="blink">Loading Archive Preview... (Waiting for file)</div>;
    if (timeline.length === 0) return <div style={{ color: 'var(--error)' }}>Archive could not be loaded.</div>;

    return (
        <div className="archive-layout">
            <aside className="chapter-index" aria-label="Chapters">
                <strong>Chapters</strong>
                {timeline.map((item, idx) => (
                    <a key={`chapter-link-${idx}`} href={`#chapter-${idx}`} className="chapter-index-row">
                        <span>{formatTimestamp(item.timestamp_start)}</span>
                        <span>{item.concept}</span>
                    </a>
                ))}
            </aside>

            <article className="archive-article">
                {archiveMeta.summary_image && (
                    <section className="summary-image-block">
                        <h3 className="chapter-title">
                            {usesGeneratedOnlyImages
                                ? 'Group Summary Image'
                                : usesLightweightGeneratedImages
                                    ? 'AI Digest Summary Image'
                                    : 'Video Summary Image'}
                        </h3>
                        <img
                            src={`${getApiBase()}/data/jobs/${folderName}/${archiveMeta.summary_image}`}
                            alt={usesGeneratedOnlyImages
                                ? 'AI-generated group summary'
                                : usesLightweightGeneratedImages
                                    ? 'AI-generated digest teaching summary'
                                    : 'AI-generated video summary'}
                            className="archive-image"
                            loading="lazy"
                            decoding="async"
                        />
                    </section>
                )}
                {timeline.map((item: ArchiveChapter, idx: number) => (
                    <section id={`chapter-${idx}`} key={`chapter-${idx}`} className="archive-chapter">
                        <div className="chapter-heading-row">
                            <h3 className="chapter-title">{item.concept}</h3>
                            {videoId ? (
                                <a
                                    href={`https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(item.timestamp_start)}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="timestamp-link"
                                >
                                    {formatTimestamp(item.timestamp_start)} ↗
                                </a>
                            ) : (
                                <span className="timestamp-link">
                                    {formatTimestamp(item.timestamp_start)}
                                </span>
                            )}
                        </div>
                        <p className="chapter-summary">{item.summary}</p>
                        <p className="chapter-content">{item.content}</p>

                    {item.images && item.images.length > 0 ? (
                        <div className="chapter-image-grid">
                            {item.images.map((img: string, i: number) => {
                                const info = findFrameInfo(img, item);
                                const isGeneratedImage = img.startsWith('generated/');
                                return (
                                    <div key={`${img}-${i}`} style={{ position: 'relative', minWidth: 0 }}>
                                        <img
                                            src={`${getApiBase()}/data/jobs/${folderName}/${img}`}
                                            alt={`Scene ${i}`}
                                            loading="lazy"
                                            decoding="async"
                                            style={{ width: '100%', aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--card-border)', display: 'block', background: '#05070a' }}
                                        />
                                        {!hideSourceImageControls && !isGeneratedImage && (
                                            <div style={{ position: 'absolute', left: '0.5rem', bottom: '0.5rem', display: 'flex', gap: '0.35rem', flexWrap: 'wrap', maxWidth: 'calc(100% - 1rem)' }}>
                                                <span style={{ border: '1px solid rgba(255,255,255,0.24)', borderRadius: '999px', background: 'rgba(0,0,0,0.72)', color: 'var(--foreground)', padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}>
                                                    {formatTimestamp(info?.timestamp)}
                                                </span>
                                                <span style={{ border: '1px solid rgba(255,255,255,0.24)', borderRadius: '999px', background: 'rgba(0,0,0,0.72)', color: 'var(--foreground)', padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}>
                                                    {qualityLabel(info)}
                                                </span>
                                            </div>
                                        )}
                                        {!hideSourceImageControls && !isGeneratedImage && (
                                            <div style={{ position: 'absolute', top: '0.5rem', right: '0.5rem', display: 'flex', gap: '0.4rem' }}>
                                                <button
                                                    onClick={() => replaceInSlicer(idx, img, item.timestamp_start)}
                                                    disabled={Boolean(imageAction)}
                                                    title="Open slicer and replace this image after saving"
                                                    style={{ border: '1px solid rgba(255,255,255,0.3)', borderRadius: '6px', background: 'rgba(0,0,0,0.72)', color: 'var(--foreground)', cursor: 'pointer', padding: '0.25rem 0.45rem', fontSize: '0.75rem' }}
                                                >
                                                    Replace
                                                </button>
                                                <button
                                                    onClick={() => removeImage(idx, img)}
                                                    disabled={Boolean(imageAction)}
                                                    title="Remove this image from chapter context"
                                                    style={{ border: '1px solid rgba(255,255,255,0.3)', borderRadius: '6px', background: 'rgba(0,0,0,0.72)', color: 'var(--foreground)', cursor: 'pointer', width: '1.75rem', height: '1.75rem', fontSize: '1rem', lineHeight: 1 }}
                                                >
                                                    ×
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    ) : !hideSourceImageControls ? (
                        <button
                            onClick={() => openChapterSlicer(idx, item.timestamp_start)}
                            className="btn btn-secondary btn-compact"
                        >
                            Add images in slicer
                        </button>
                    ) : (
                        <p style={{ color: 'var(--muted)', fontSize: '0.85rem', marginTop: '1rem' }}>
                            Group digest image pending.
                        </p>
                    )}
                        {!hideSourceImageControls && (
                            <footer className="chapter-footer">
                                <button
                                    onClick={() => openChapterSlicer(idx, item.timestamp_start)}
                                    title="Open slicer at this chapter to add curated teaching images"
                                    className="btn btn-secondary btn-small"
                                >
                                    Improve images
                                </button>
                                {item._slice_id && (
                                    <button
                                        onClick={() => deleteSlice(item._slice_id)}
                                        title="Remove operator-curated visuals"
                                        className="btn btn-secondary btn-small"
                                    >
                                        Curated remove
                                    </button>
                                )}
                            </footer>
                        )}
                    </section>
                ))}
            </article>
        </div>
    );
}
