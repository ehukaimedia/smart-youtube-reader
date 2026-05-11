'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { getApiBase, getShareOrigin } from '@/lib/api';
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

    const copyText = (text: string, onCopied: () => void) => {
        const fallbackCopy = () => {
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            onCopied();
        };

        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(onCopied).catch(fallbackCopy);
            return;
        }

        fallbackCopy();
    };

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

        const fetchStatus = async () => {
            try {
                const res = await fetch(`${getApiBase()}/jobs/${jobId}`);
                if (!res.ok) throw new Error('Failed to fetch job');
                const data = await res.json();
                setJob(data);

                if (data.status === 'complete' && !transcript) {
                    // Fetch transcript
                    const tres = await fetch(`${getApiBase()}/jobs/${jobId}/transcript`);
                    if (tres.ok) {
                        const tdata = await tres.json();
                        setTranscript(tdata);
                    }
                }
            } catch (err) {
                console.error(err);
                setError('Failed to load job');
            }
        };

        fetchStatus();
        const interval = setInterval(fetchStatus, 2000);
        return () => clearInterval(interval);
    }, [jobId, transcript]);

    if (error) return <div className="container text-red-500">{error}</div>;
    if (!job) return <div className="container">Loading...</div>;

    return (
        <div className="container">
            <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 className="title-gradient" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Smart Reader</h2>
                    {job.title && <h1 style={{ fontSize: '1.2rem', fontWeight: 500 }}>{job.title}</h1>}
                    {(job.kind === 'ai_digest' || job.kind === 'group_ai_digest') && (
                        <p style={{ color: 'var(--success)', fontSize: '0.78rem', marginTop: '0.25rem' }}>
                            {job.kind === 'group_ai_digest' ? 'Group AI Digest' : 'AI Digest Version'}
                            {job.source_job_id ? ` from ${job.source_job_id.slice(0, 8)}` : ''}
                        </p>
                    )}
                </div>
                <span className="glass-card" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    <strong>{job.status}</strong>
                    {job.status === 'complete' && job.data_folder_name && (
                        <>
                            {!job.kind && (
                                <>
                                    <button
                                        onClick={() => copyAiDigestTask(job)}
                                        className="btn"
                                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: digestTaskCopied ? 'var(--secondary)' : 'var(--success)' }}
                                    >
                                        {digestTaskCopied ? 'Copied Digest Task' : 'Copy AI Digest CLI Task'}
                                    </button>
                                    <button
                                        onClick={() => copyAiDigestWithImagesTask(job)}
                                        className="btn"
                                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: digestWithImagesTaskCopied ? 'var(--secondary)' : undefined }}
                                    >
                                        {digestWithImagesTaskCopied ? 'Copied Images Task' : 'Copy AI Digest with Images CLI Task'}
                                    </button>
                                </>
                            )}
                            <button
                                onClick={() => copyLearningPrompt(job)}
                                className="btn"
                                style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: promptCopied ? 'var(--secondary)' : undefined }}
                            >
                                {promptCopied ? '✓ Copied!' : '⊕ Copy Learning Prompt'}
                            </button>
                            <button
                                onClick={copyProjectLink}
                                className="btn"
                                style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: linkCopied ? 'var(--secondary)' : undefined }}
                            >
                                {linkCopied ? 'Copied Link' : 'Copy Project Link'}
                            </button>
                            <a
                                href={`${getApiBase()}/jobs/${job.id}/download`}
                                download={`${job.data_folder_name || job.id}.zip`}
                                className="btn"
                                style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', textDecoration: 'none' }}
                            >
                                Download Project ZIP
                            </a>
                        </>
                    )}

                    {job.kind !== 'group_ai_digest' && job.media_policy !== 'lightweight_generated_images_only' && (
                        <a href={`/slicer/${job.id}`} className="btn" style={{ background: 'var(--secondary)' }}>
                            Open Slicer
                        </a>
                    )}
                </span>
            </header>

            {job.status === 'processing' && (
                <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem' }}>
                    <div className="spinner"></div>
                    <div>
                        <h3 className="blink" style={{ marginBottom: '0.5rem' }}>
                            {job.current_step || 'Processing Video...'}
                        </h3>
                        <p style={{ color: '#888' }}>Please wait while the AI analyzes the content.</p>
                    </div>
                </div>
            )}

            {job.status === 'failed' && (
                <div className="glass-card" style={{ textAlign: 'center', padding: '4rem', borderColor: 'var(--error)' }}>
                    <h3 style={{ color: 'var(--error)' }}>Job Failed</h3>
                    <p>{job.error}</p>
                </div>
            )}

            {job.status === 'complete' && transcript && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '2rem' }}>
                    {/* AI Archive — primary content */}
                    <div className="glass-card" style={{ borderColor: 'var(--secondary)' }}>
                        <h3 className="title-gradient" style={{ marginBottom: '1rem' }}>AI Archive</h3>
                        <ArchivePreview jobId={job.id} folderName={job.data_folder_name || undefined} videoUrl={job.video_url || undefined} kind={job.kind || undefined} />
                    </div>

                    {/* Raw Transcript — collapsible secondary */}
                    <details className="glass-card">
                        <summary style={{ cursor: 'pointer', fontWeight: 600, marginBottom: '0.5rem' }}>Raw Transcript</summary>
                        <div style={{ marginTop: '1rem' }}>
                            {transcript.map((line: TranscriptLine, idx: number) => {
                                const videoId = job.video_url?.match(/[?&]v=([^&]+)/)?.[1];
                                const tsUrl = videoId
                                    ? `https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(line.start)}`
                                    : null;
                                return (
                                    <div key={idx} style={{ marginBottom: '0.75rem' }}>
                                        {tsUrl ? (
                                            <a href={tsUrl} target="_blank" rel="noopener noreferrer"
                                                style={{ color: '#555', fontSize: '0.8rem', marginRight: '1rem', userSelect: 'none', textDecoration: 'none' }}>
                                                {Math.floor(line.start / 60)}:{String(Math.floor(line.start % 60)).padStart(2, '0')}
                                            </a>
                                        ) : (
                                            <span style={{ color: '#555', fontSize: '0.8rem', marginRight: '1rem', userSelect: 'none' }}>
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
    if (timeline.length === 0) return <div style={{ color: 'red' }}>Archive could not be loaded.</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {archiveMeta.summary_image && (
                <section style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem' }}>
                    <h4 style={{ fontSize: '1.2rem', color: 'var(--foreground)', marginBottom: '0.75rem' }}>
                        {usesGeneratedOnlyImages
                            ? 'Group Summary Image'
                            : usesLightweightGeneratedImages
                                ? 'AI Digest Summary Image'
                                : 'Video Summary Image'}
                    </h4>
                    <img
                        src={`${getApiBase()}/data/jobs/${folderName}/${archiveMeta.summary_image}`}
                        alt={usesGeneratedOnlyImages
                            ? 'AI-generated group summary'
                            : usesLightweightGeneratedImages
                                ? 'AI-generated digest teaching summary'
                                : 'AI-generated video summary'}
                        style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)', display: 'block' }}
                    />
                </section>
            )}
            {timeline.map((item: ArchiveChapter, idx: number) => (
                <div id={`chapter-${idx}`} key={`chapter-${idx}`} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem', scrollMarginTop: '5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <h4 style={{ fontSize: '1.2rem', color: 'var(--foreground)' }}>{item.concept}</h4>
                            {!hideSourceImageControls && (
                                <button
                                    onClick={() => openChapterSlicer(idx, item.timestamp_start)}
                                    title="Open slicer at this chapter to add curated teaching images"
                                    style={{ background: 'none', border: '1px solid var(--card-border)', borderRadius: '4px', color: '#bbb', cursor: 'pointer', padding: '1px 6px', fontSize: '0.7rem' }}
                                >
                                    Improve images
                                </button>
                            )}
                            {!hideSourceImageControls && item._slice_id && (
                                <button
                                    onClick={() => deleteSlice(item._slice_id)}
                                    title="Remove operator-curated visuals"
                                    style={{ background: 'none', border: '1px solid var(--secondary)', borderRadius: '4px', color: 'var(--secondary)', cursor: 'pointer', padding: '1px 6px', fontSize: '0.7rem' }}
                                >
                                    curated - remove
                                </button>
                            )}
                        </div>
                        {videoId ? (
                            <a
                                href={`https://www.youtube.com/watch?v=${videoId}&t=${Math.floor(item.timestamp_start)}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{ fontSize: '0.8rem', color: '#666', textDecoration: 'none' }}
                            >
                                {Math.floor(item.timestamp_start / 60)}:{String(Math.floor(item.timestamp_start % 60)).padStart(2, '0')} ↗
                            </a>
                        ) : (
                            <span style={{ fontSize: '0.8rem', color: '#666' }}>
                                {Math.floor(item.timestamp_start / 60)}:{String(Math.floor(item.timestamp_start % 60)).padStart(2, '0')}
                            </span>
                        )}
                    </div>
                    <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1rem' }}>{item.summary}</p>
                    <p style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>{item.content}</p>

                    {item.images && item.images.length > 0 ? (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                            {item.images.map((img: string, i: number) => {
                                const info = findFrameInfo(img, item);
                                const isGeneratedImage = img.startsWith('generated/');
                                return (
                                    <div key={`${img}-${i}`} style={{ position: 'relative', minWidth: 0 }}>
                                        <img
                                            src={`${getApiBase()}/data/jobs/${folderName}/${img}`}
                                            alt={`Scene ${i}`}
                                            style={{ width: '100%', aspectRatio: '16 / 9', objectFit: 'cover', borderRadius: '8px', border: '1px solid var(--card-border)', display: 'block', background: '#000' }}
                                        />
                                        {!hideSourceImageControls && !isGeneratedImage && (
                                            <div style={{ position: 'absolute', left: '0.5rem', bottom: '0.5rem', display: 'flex', gap: '0.35rem', flexWrap: 'wrap', maxWidth: 'calc(100% - 1rem)' }}>
                                                <span style={{ border: '1px solid rgba(255,255,255,0.24)', borderRadius: '999px', background: 'rgba(0,0,0,0.72)', color: '#fff', padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}>
                                                    {formatTimestamp(info?.timestamp)}
                                                </span>
                                                <span style={{ border: '1px solid rgba(255,255,255,0.24)', borderRadius: '999px', background: 'rgba(0,0,0,0.72)', color: '#fff', padding: '0.15rem 0.45rem', fontSize: '0.7rem' }}>
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
                                                    style={{ border: '1px solid rgba(255,255,255,0.3)', borderRadius: '6px', background: 'rgba(0,0,0,0.72)', color: '#fff', cursor: 'pointer', padding: '0.25rem 0.45rem', fontSize: '0.75rem' }}
                                                >
                                                    Replace
                                                </button>
                                                <button
                                                    onClick={() => removeImage(idx, img)}
                                                    disabled={Boolean(imageAction)}
                                                    title="Remove this image from chapter context"
                                                    style={{ border: '1px solid rgba(255,255,255,0.3)', borderRadius: '6px', background: 'rgba(0,0,0,0.72)', color: '#fff', cursor: 'pointer', width: '1.75rem', height: '1.75rem', fontSize: '1rem', lineHeight: 1 }}
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
                            className="btn"
                            style={{ marginTop: '1rem', background: '#333', fontSize: '0.85rem' }}
                        >
                            Add images in slicer
                        </button>
                    ) : (
                        <p style={{ color: '#777', fontSize: '0.85rem', marginTop: '1rem' }}>
                            Group digest image pending.
                        </p>
                    )}
                </div>
            ))}
        </div>
    );
}
