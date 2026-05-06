'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { getApiBase, getShareOrigin } from '@/lib/api';

type Job = {
    id: string;
    status: string;
    video_url?: string | null;
    title?: string | null;
    created_at: number;
    error?: string | null;
    data_folder_name?: string | null;
    current_step?: string | null;
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

export default function ReaderPage() {
    const { jobId } = useParams();
    const [job, setJob] = useState<Job | null>(null);
    const [transcript, setTranscript] = useState<TranscriptLine[] | null>(null);
    const [error, setError] = useState('');
    const [promptCopied, setPromptCopied] = useState(false);
    const [linkCopied, setLinkCopied] = useState(false);

    const copyLearningPrompt = (job: Job) => {
        const archiveUrl = `${getApiBase()}/data/jobs/${job.data_folder_name}/archive.json`;
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
                </div>
                <span className="glass-card" style={{ padding: '0.5rem 1rem', fontSize: '0.8rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <strong>{job.status}</strong>
                    {job.status === 'complete' && job.data_folder_name && (
                        <>
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
                        <ArchivePreview jobId={job.id} folderName={job.data_folder_name} videoUrl={job.video_url} />
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
    const videoId = videoUrl?.match(/[?&]v=([^&]+)/)?.[1];
    const [timeline, setTimeline] = useState<ArchiveChapter[]>([]);
    const [loading, setLoading] = useState(true);

    const deleteSlice = async (sliceId: string) => {
        if (!confirm('Remove curated visuals from this chapter? The AI-selected images will be cleared.')) return;
        await fetch(`${getApiBase()}/jobs/${jobId}/slices/${sliceId}`, { method: 'DELETE' });
        // Clear images and _slice_id from the matching chapter in local state
        setTimeline(prev => prev.map(item =>
            item._slice_id === sliceId ? { ...item, images: [], _slice_id: undefined } : item
        ));
    };

    useEffect(() => {
        if (!folderName) return;

        const fetchData = async () => {
            try {
                const archiveRes = await fetch(`${getApiBase()}/data/jobs/${folderName}/archive.json`);
                if (archiveRes.ok) {
                    const data = await archiveRes.json();
                    const chapters = ((data.archive || []) as Omit<ArchiveChapter, 'type' | 'sortTime'>[]).map((a) => ({
                        ...a,
                        type: 'chapter',
                        sortTime: a.timestamp_start
                    }));
                    setTimeline(chapters);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [jobId, folderName]);

    if (loading) return <div className="blink">Loading Archive Preview... (Waiting for file)</div>;
    if (timeline.length === 0) return <div style={{ color: 'red' }}>Archive could not be loaded.</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {timeline.map((item: ArchiveChapter, idx: number) => (
                <div key={`chapter-${idx}`} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem' }}>
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
                                <img
                                    key={i}
                                    src={`${getApiBase()}/data/jobs/${folderName}/${img}`}
                                    alt={`Scene ${i}`}
                                    style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)' }}
                                />
                            ))}
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
}
