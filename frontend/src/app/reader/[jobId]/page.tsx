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
};

type DigestModel = {
    id: string;
    label: string;
    provider: string;
    requires?: string | null;
    available: boolean;
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
    _slice_id?: string;
    type: 'chapter';
    sortTime: number;
};

type ArchiveMetadata = {
    summary_image?: string;
};

type FrameMetadata = {
    timestamp?: number;
};

export default function ReaderPage() {
    const { jobId } = useParams();
    const [job, setJob] = useState<Job | null>(null);
    const [transcript, setTranscript] = useState<TranscriptLine[] | null>(null);
    const [error, setError] = useState('');
    const [promptCopied, setPromptCopied] = useState(false);
    const [linkCopied, setLinkCopied] = useState(false);
    const [imageTaskCopied, setImageTaskCopied] = useState(false);
    const [digestModels, setDigestModels] = useState<DigestModel[]>([]);
    const [digestModelsLoaded, setDigestModelsLoaded] = useState(false);
    const [digestModel, setDigestModel] = useState('');
    const [digesting, setDigesting] = useState(false);
    const router = useRouter();
    const toast = useToast();

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
- content: full transcript text for the section
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
        if (navigator.clipboard) {
            navigator.clipboard.writeText(prompt).then(onCopied);
        } else {
            // Fallback for non-secure contexts (HTTP over Tailscale)
            const ta = document.createElement('textarea');
            ta.value = prompt;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            onCopied();
        }
    };

    const copyProjectLink = async () => {
        const shareOrigin = await getShareOrigin();
        const url = `${shareOrigin}/reader/${jobId}`;
        const onCopied = () => {
            setLinkCopied(true);
            setTimeout(() => setLinkCopied(false), 2000);
        };

        if (navigator.clipboard) {
            navigator.clipboard.writeText(url).then(onCopied);
            return;
        }

        const ta = document.createElement('textarea');
        ta.value = url;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        onCopied();
    };

    const copyCodexImageTask = (job: Job) => {
        const archiveUrl = `${getApiBase()}/jobs/${job.id}/archive`;
        const baseUrl = `${getApiBase()}/data/jobs/${job.data_folder_name}`;
        const projectFolder = `/Volumes/Extreme SSD/AI-Applications/smart-youtube-reader/data/jobs/${job.data_folder_name}`;
        const prompt = `Create a Smart YouTube Reader summary image for this project by running the local CLI.

The CLI reads archive.json, inspects the attached frame images, creates generated/summary.png, and updates archive.json and manifest.json so the image becomes the dashboard thumbnail.

Video: "${job.title || job.id}"
YouTube: ${job.video_url || '(not available)'}
Archive JSON: ${archiveUrl}
Frame base URL: ${baseUrl}
Local project folder: ${projectFolder}

Command:
python3 tools/create_summary_thumbnail.py "${projectFolder}"

After running it, verify the reader shows "Video Summary Image" and the dashboard uses generated/summary.png as the project thumbnail.`;
        const onCopied = () => {
            setImageTaskCopied(true);
            setTimeout(() => setImageTaskCopied(false), 2000);
        };

        if (navigator.clipboard) {
            navigator.clipboard.writeText(prompt).then(onCopied);
            return;
        }

        const ta = document.createElement('textarea');
        ta.value = prompt;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        onCopied();
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

    useEffect(() => {
        fetch(`${getApiBase()}/digest-models`)
            .then(res => res.ok ? res.json() : Promise.reject(new Error('Failed to load digest models')))
            .then(data => {
                if (Array.isArray(data.models) && data.models.length > 0) {
                    setDigestModels(data.models);
                    const preferred = data.models.find((model: DigestModel) => model.available && model.provider !== 'local')
                        || data.models.find((model: DigestModel) => model.available)
                        || data.models[0];
                    setDigestModel(preferred.id);
                }
                setDigestModelsLoaded(true);
            })
            .catch(err => {
                console.error(err);
                setDigestModelsLoaded(true);
                toast.error('Failed to load AI digest model options');
            });
    }, [toast]);

    const createDigestVersion = async () => {
        if (!job) return;
        if (!digestModel) {
            toast.error('Choose an AI digest model first');
            return;
        }
        const selectedModel = digestModels.find(model => model.id === digestModel);
        if (selectedModel && !selectedModel.available) {
            toast.error(selectedModel.provider === 'ollama' ? 'Build the local Ollama digest model first' : 'Selected digest model is unavailable');
            return;
        }
        setDigesting(true);
        toast.info('Creating AI digest version. The original project will stay unchanged.');

        try {
            const res = await fetch(`${getApiBase()}/jobs/${job.id}/digest`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: digestModel
                })
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => null);
                throw new Error(errorData?.detail || 'AI digest creation failed');
            }

            const digestJob: Job = await res.json();
            toast.success(`Created no-fluff AI digest: ${digestJob.title || digestJob.id}`);
            router.push(`/reader/${digestJob.id}`);
        } catch (err) {
            console.error(err);
            toast.error(err instanceof Error ? err.message : 'AI digest creation failed');
        } finally {
            setDigesting(false);
        }
    };

    if (error) return <div className="container text-red-500">{error}</div>;
    if (!job) return <div className="container">Loading...</div>;

    const selectedDigestModel = digestModels.find(model => model.id === digestModel);
    const selectedDigestModelUnavailable = Boolean(selectedDigestModel && !selectedDigestModel.available);
    const digestModelStatus = (model: DigestModel) => {
        if (model.available) return '';
        if (model.provider === 'ollama') return ' (build Ollama model)';
        if (model.requires) return ' (key required)';
        return ' (unavailable)';
    };

    return (
        <div className="container">
            <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h2 className="title-gradient" style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>Smart Reader</h2>
                    {job.title && <h1 style={{ fontSize: '1.2rem', fontWeight: 500 }}>{job.title}</h1>}
                    {job.kind === 'ai_digest' && (
                        <p style={{ color: 'var(--success)', fontSize: '0.78rem', marginTop: '0.25rem' }}>
                            AI Digest Version{job.source_job_id ? ` from ${job.source_job_id.slice(0, 8)}` : ''}
                        </p>
                    )}
                </div>
                <span className="glass-card" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem', display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                    <strong>{job.status}</strong>
                    {job.status === 'complete' && job.data_folder_name && (
                        <>
                            {job.kind !== 'ai_digest' && (
                                <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                                    <select
                                        value={digestModel}
                                        onChange={(event) => setDigestModel(event.target.value)}
                                        aria-label="AI digest agent model"
                                        style={{ background: 'rgba(255,255,255,0.06)', color: '#fff', border: '1px solid var(--card-border)', borderRadius: '6px', padding: '0.3rem 0.45rem', fontSize: '0.78rem' }}
                                    >
                                        {digestModels.length === 0 ? (
                                            <option value="">No models loaded</option>
                                        ) : (
                                            digestModels.map(model => (
                                                <option key={model.id} value={model.id} disabled={!model.available}>
                                                    {model.label}{digestModelStatus(model)}
                                                </option>
                                            ))
                                        )}
                                    </select>
                                    <button
                                        onClick={createDigestVersion}
                                        disabled={digesting || !digestModelsLoaded || !digestModel || selectedDigestModelUnavailable}
                                        className="btn"
                                        style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: 'var(--success)' }}
                                    >
                                        {!digestModelsLoaded ? 'Loading Models...' : selectedDigestModelUnavailable ? 'Model Unavailable' : digesting ? 'Creating Digest...' : 'Create AI Digest Version'}
                                    </button>
                                </span>
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
                            {job.kind === 'ai_digest' && (
                                <button
                                    onClick={() => copyCodexImageTask(job)}
                                    className="btn"
                                    style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', background: imageTaskCopied ? 'var(--secondary)' : undefined }}
                                >
                                    {imageTaskCopied ? 'Copied Image Task' : 'Copy Codex Image Task'}
                                </button>
                            )}
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

                    <a href={`/slicer/${job.id}`} className="btn" style={{ background: 'var(--secondary)' }}>
                        Open Slicer
                    </a>
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
                        <ArchivePreview jobId={job.id} folderName={job.data_folder_name || undefined} videoUrl={job.video_url || undefined} />
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

function ArchivePreview({ jobId, folderName, videoUrl }: { jobId: string, folderName?: string, videoUrl?: string }) {
    const router = useRouter();
    const toast = useToast();
    const videoId = videoUrl?.match(/[?&]v=([^&]+)/)?.[1];
    const [timeline, setTimeline] = useState<ArchiveChapter[]>([]);
    const [archiveMeta, setArchiveMeta] = useState<ArchiveMetadata>({});
    const [frameMetadata, setFrameMetadata] = useState<Record<string, FrameMetadata>>({});
    const [loading, setLoading] = useState(true);
    const [imageAction, setImageAction] = useState('');

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
                    summary_image: data.summary_image
                });
                fetch(`${getApiBase()}/data/jobs/${folderName}/frames.json`, { cache: 'no-store' })
                    .then(res => res.ok ? res.json() : {})
                    .then((frames: Record<string, FrameMetadata>) => setFrameMetadata(frames || {}))
                    .catch(() => setFrameMetadata({}));
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }, [folderName, jobId]);

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

    const replaceInSlicer = async (chapterIndex: number, imagePath: string, timestampStart: number) => {
        const confirmed = await toast.confirm('Open the slicer to choose a replacement? The current image will stay attached until the replacement is saved.', { confirmLabel: 'Open Slicer' });
        if (!confirmed) return;
        const filename = imagePath.split('/').pop() || imagePath;
        const imageTimestamp = frameMetadata[imagePath]?.timestamp ?? frameMetadata[filename]?.timestamp;
        const replacementStart = typeof imageTimestamp === 'number' ? imageTimestamp - 2 : timestampStart;
        const start = Math.max(0, Math.floor(replacementStart));
        const returnTo = encodeURIComponent(`/reader/${jobId}#chapter-${chapterIndex}`);
        router.push(`/slicer/${jobId}?start=${start}&return=${returnTo}&replaceChapter=${chapterIndex}&replaceImage=${encodeURIComponent(imagePath)}`);
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

    if (loading) return <div className="blink">Loading Archive Preview... (Waiting for file)</div>;
    if (timeline.length === 0) return <div style={{ color: 'red' }}>Archive could not be loaded.</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {archiveMeta.summary_image && (
                <section style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem' }}>
                    <h4 style={{ fontSize: '1.2rem', color: 'var(--foreground)', marginBottom: '0.75rem' }}>Video Summary Image</h4>
                    <img
                        src={`${getApiBase()}/data/jobs/${folderName}/${archiveMeta.summary_image}`}
                        alt="AI-generated video summary"
                        style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)', display: 'block' }}
                    />
                </section>
            )}
            {timeline.map((item: ArchiveChapter, idx: number) => (
                <div id={`chapter-${idx}`} key={`chapter-${idx}`} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem', scrollMarginTop: '5rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <h4 style={{ fontSize: '1.2rem', color: 'var(--foreground)' }}>{item.concept}</h4>
                            {item._slice_id && (
                                <button
                                    onClick={() => deleteSlice(item._slice_id)}
                                    title="Remove operator-curated visuals"
                                    style={{ background: 'none', border: '1px solid var(--secondary)', borderRadius: '4px', color: 'var(--secondary)', cursor: 'pointer', padding: '1px 6px', fontSize: '0.7rem' }}
                                >
                                    ✨ curated — remove
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

                    {item.images && item.images.length > 0 && (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                            {item.images.map((img: string, i: number) => (
                                <div key={`${img}-${i}`} style={{ position: 'relative' }}>
                                    <img
                                        src={`${getApiBase()}/data/jobs/${folderName}/${img}`}
                                        alt={`Scene ${i}`}
                                        style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)', display: 'block' }}
                                    />
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
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
