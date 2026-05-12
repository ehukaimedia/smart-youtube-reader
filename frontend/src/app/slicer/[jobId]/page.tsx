"use client";

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter, useSearchParams } from 'next/navigation';
import { getApiBase } from '@/lib/api';
import { useToast } from '../../components/ToastProvider';

type Job = {
    id: string;
    title?: string | null;
    data_folder_name?: string | null;
    video_ext?: string | null;
};

export default function SlicerPage() {
    const { jobId } = useParams();
    const router = useRouter();
    const searchParams = useSearchParams();
    const toast = useToast();
    const returnTo = searchParams.get('return');
    const startParam = searchParams.get('start');
    const replaceChapterParam = searchParams.get('replaceChapter');
    const replaceImagePath = searchParams.get('replaceImage');
    const targetChapterIndex = replaceChapterParam === null ? null : Number(replaceChapterParam);
    const isReplacingImage = Number.isInteger(targetChapterIndex) && Boolean(replaceImagePath);
    const appliedStartParam = useRef<string | null>(null);
    const [job, setJob] = useState<Job | null>(null);
    const [videoSrc, setVideoSrc] = useState('');
    const [loadError, setLoadError] = useState('');
    const videoRef = useRef<HTMLVideoElement>(null);

    // UI State
    const [step, setStep] = useState<'input' | 'review' | 'done'>('input');
    const [processing, setProcessing] = useState(false);

    // Input State
    const [start, setStart] = useState(0);
    const [end, setEnd] = useState(5);
    const [fps, setFps] = useState(24);
    const [format, setFormat] = useState<'mp4' | 'sequence'>('sequence');
    const [sliceDuration, setSliceDuration] = useState(5);
    const [syncToPlayhead, setSyncToPlayhead] = useState(true);
    const [isPreviewing, setIsPreviewing] = useState(false);

    // Review State
    const [previewId, setPreviewId] = useState('');
    const [previewFrames, setPreviewFrames] = useState<string[]>([]); // filenames
    const [previewBaseUrl, setPreviewBaseUrl] = useState('');
    const [excludedFrames, setExcludedFrames] = useState<Set<string>>(new Set());
    const [thumbSize, setThumbSize] = useState(250);

    // Result State
    const [downloadUrl, setDownloadUrl] = useState('');

    useEffect(() => {
        if (!jobId) return;
        fetch(`${getApiBase()}/jobs/${jobId}`)
            .then(async res => {
                const data = await res.json().catch(() => null);
                if (!res.ok) {
                    throw new Error(data?.detail || 'Project not found');
                }
                return data;
            })
            .then((data: Job) => {
                setJob(data);
                setLoadError('');
                if (data.data_folder_name) {
                    const ext = data.video_ext || 'mp4';
                    setVideoSrc(`${getApiBase()}/data/jobs/${data.data_folder_name}/video.${ext}`);
                }
            })
            .catch(err => {
                const message = err instanceof Error ? err.message : 'Failed to load project';
                setLoadError(message);
                toast.error(message);
            });
    }, [jobId, toast]);

    useEffect(() => {
        if (!startParam) return;
        if (appliedStartParam.current === startParam) return;
        const nextStart = Number(startParam);
        if (!Number.isFinite(nextStart)) return;

        appliedStartParam.current = startParam;
        setStart(nextStart);
        setEnd(nextStart + sliceDuration);
        setSyncToPlayhead(false);
        if (videoRef.current) {
            videoRef.current.currentTime = nextStart;
        }
    }, [startParam, sliceDuration]);

    const onLoadedMetadata = () => {
        const duration = videoRef.current?.duration;
        if (!Number.isFinite(duration) || !duration) return;
        if (videoRef.current && start < duration) {
            videoRef.current.currentTime = start;
        }

        setEnd(prevEnd => {
            if (start >= duration) return duration;
            const minimumEnd = start + sliceDuration;
            const nextEnd = Math.min(Math.max(prevEnd, minimumEnd), duration);
            return Number(nextEnd.toFixed(3));
        });
    };

    // --- Actions ---

    const handlePreview = async () => {
        if (!job?.id) {
            toast.error(loadError || 'Project is not loaded');
            return;
        }
        if (!Number.isFinite(start) || !Number.isFinite(end)) {
            toast.error("Slice start and end must be valid numbers");
            return;
        }
        const videoDuration = videoRef.current?.duration;
        if (Number.isFinite(videoDuration) && videoDuration && start >= videoDuration) {
            toast.error("Slice start time is beyond the video duration");
            return;
        }
        if (end <= start) {
            toast.error("Slice end time must be after start time");
            return;
        }
        if ((end - start) > 10) {
            toast.error("Max duration is 10 seconds");
            return;
        }

        setProcessing(true);
        try {
            if (format === 'mp4') {
                // Direct MP4 export (legacy flow)
                const res = await fetch(`${getApiBase()}/jobs/${job.id}/slice`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start, end, format: 'mp4' })
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => null);
                    throw new Error(errorData?.detail || 'Video export failed');
                }
                const result = await res.json();
                setDownloadUrl(`${getApiBase()}/data/jobs/${job.data_folder_name}/${result.path}`);
                setStep('done');
            } else {
                // Generate Frames Preview
                const res = await fetch(`${getApiBase()}/jobs/${job.id}/slicer/preview`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start, end, fps })
                });
                if (!res.ok) {
                    const errorData = await res.json().catch(() => null);
                    throw new Error(errorData?.detail || 'Preview failed');
                }
                const data = await res.json();
                setPreviewId(data.preview_id);
                setPreviewFrames(data.frames);
                setPreviewBaseUrl(data.base_url); // relative e.g. "previews/123"
                setExcludedFrames(new Set(data.frames)); // start with all deselected
                setStep('review');
            }
        } catch (e) {
            toast.error(e instanceof Error ? e.message : "Failed to generate slice");
        } finally {
            setProcessing(false);
        }
    };

    const handleFinalize = async () => {
        if (!job) return;
        const selected = previewFrames.filter(f => !excludedFrames.has(f));
        if (selected.length === 0) {
            toast.error("No frames selected");
            return;
        }

        setProcessing(true);
        try {
            const res = await fetch(`${getApiBase()}/jobs/${job.id}/slicer/finalize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    preview_id: previewId,
                    selected_files: selected
                })
            });
            if (!res.ok) {
                const errorData = await res.json().catch(() => null);
                throw new Error(errorData?.detail || "Finalize failed");
            }
            const result = await res.json();
            setDownloadUrl(`${getApiBase()}/data/jobs/${job.data_folder_name}/${result.path}`);
            setStep('done');
        } catch (e) {
            toast.error(e instanceof Error ? e.message : "Failed to create zip");
        } finally {
            setProcessing(false);
        }
    };

    const toggleFrame = (filename: string) => {
        const next = new Set(excludedFrames);
        if (next.has(filename)) next.delete(filename);
        else next.add(filename);
        setExcludedFrames(next);
    };

    const selectAll = () => setExcludedFrames(new Set());
    const deselectAll = () => {
        const next = new Set<string>();
        previewFrames.forEach(f => next.add(f));
        setExcludedFrames(next);
    };

    const [viewingFrame, setViewingFrame] = useState<string | null>(null);

    useEffect(() => {
        if (!viewingFrame) return;

        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === 'Escape') {
                setViewingFrame(null);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [viewingFrame]);

    // Helpers to preview video
    const previewTimeout = useRef<NodeJS.Timeout | null>(null);
    const videoPreview = () => {
        const video = videoRef.current;
        if (video) {
            setIsPreviewing(true);
            if (previewTimeout.current) clearTimeout(previewTimeout.current);
            video.currentTime = start;
            video.play();
            const durationMs = (end - start) * 1000;
            if (durationMs > 0) {
                previewTimeout.current = setTimeout(() => {
                    video.pause();
                    setIsPreviewing(false);
                }, durationMs);
            }
        }
    }

    const handleTimeUpdate = () => {
        const video = videoRef.current;
        if (video && syncToPlayhead && !isPreviewing) {
            const now = video.currentTime;
            setStart(Number(now.toFixed(1)));
            setEnd(Number((now + sliceDuration).toFixed(1)));
        }
    }

    const handleSaveToProject = async () => {
        if (!job) return;
        const selected = previewFrames.filter(f => !excludedFrames.has(f));
        if (selected.length === 0) {
            toast.error("No frames selected");
            return;
        }

        setProcessing(true);
        try {
            const res = await fetch(`${getApiBase()}/jobs/${job.id}/slicer/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    preview_id: previewId,
                    selected_files: selected,
                    target_chapter_index: Number.isInteger(targetChapterIndex) ? targetChapterIndex : undefined,
                    replace_image_path: replaceImagePath || undefined
                })
            });
            const result = await res.json().catch(() => null);
            if (!res.ok) {
                throw new Error(result?.detail || "Save failed");
            }
            if (isReplacingImage && !result?.images_added) {
                throw new Error("No replacement images were attached to the project");
            }
            toast.success(isReplacingImage ? "Replacement image saved to project" : "Slice saved to project");
            if (returnTo) {
                router.push(returnTo);
            }
        } catch (e) {
            toast.error(e instanceof Error ? e.message : "Failed to save slice");
        } finally {
            setProcessing(false);
        }
    };

    if (loadError) return <div className="container">{loadError}</div>;
    if (!job) return <div className="container">Loading...</div>;
    const stepItems = [
        { id: 'input', label: '1. Set range' },
        { id: 'review', label: '2. Review frames' },
        { id: 'done', label: '3. Done' }
    ] as const;

    return (
        <div className="container slicer-page">
            <header className="page-header">
                <div>
                    <h1 className="page-title">Choose teaching frames</h1>
                    <p className="muted">{job.title}</p>
                    {isReplacingImage && (
                        <p className="muted" style={{ marginTop: '0.35rem' }}>
                            Replacing one image in chapter {(targetChapterIndex ?? 0) + 1}. The original remains until you save selected frames.
                        </p>
                    )}
                </div>
                <a href={returnTo || `/reader/${job.id}`} className="btn btn-secondary btn-compact">
                    Back to Project
                </a>
            </header>

            <nav className="step-strip" aria-label="Slicer progress">
                {stepItems.map(item => (
                    <span key={item.id} className={`step-chip ${step === item.id ? 'active' : ''}`}>
                        {item.label}
                    </span>
                ))}
            </nav>

            {/* STEP 1: INPUT */}
            {step === 'input' && (
                <div className="slicer-grid">
                    <div className="surface-panel">
                        <div className="video-shell">
                            {videoSrc && (
                                <video
                                    ref={videoRef}
                                    src={videoSrc}
                                    controls
                                    className="slicer-video"
                                    onLoadedMetadata={onLoadedMetadata}
                                    onTimeUpdate={handleTimeUpdate}
                                    onPause={() => setIsPreviewing(false)}
                                    onSeeking={() => setIsPreviewing(false)}
                                />
                            )}
                        </div>
                        <div style={{ marginTop: '1rem' }}>
                            <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                                <label style={{ display: 'flex', flexDirection: 'column' }}>
                                    Start
                                    <input type="number" className="input" step="0.1" value={start} onChange={e => {
                                        const val = Number(e.target.value);
                                        setStart(val);
                                        if (syncToPlayhead) setEnd(val + sliceDuration);
                                    }} />
                                </label>
                                <label style={{ display: 'flex', flexDirection: 'column' }}>
                                    End
                                    <input type="number" className="input" step="0.1" value={end} onChange={e => setEnd(Number(e.target.value))} />
                                </label>
                                <label style={{ display: 'flex', flexDirection: 'column' }}>
                                    Duration
                                    <input type="number" className="input" min="0.5" max="10" step="0.5" value={sliceDuration} onChange={e => {
                                        const val = Number(e.target.value);
                                        setSliceDuration(val);
                                        setEnd(start + val);
                                    }} />
                                </label>
                                <button className="btn btn-secondary" onClick={videoPreview} style={{ height: 'fit-content', alignSelf: 'end' }}>Preview Play</button>
                            </div>
                            <div style={{ marginTop: '0.5rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem', color: 'var(--muted)' }}>
                                    <input type="checkbox" checked={syncToPlayhead} onChange={e => setSyncToPlayhead(e.target.checked)} />
                                    Sync Selection to Playhead while Scrubbing
                                </label>
                            </div>
                        </div>
                    </div>

                    <div className="format-column">
                        <div className="surface-panel">
                            <h2 className="section-title">Format</h2>
                            <div style={{ display: 'flex', gap: '1rem', margin: '1rem 0' }}>
                                <label><input type="radio" checked={format === 'sequence'} onChange={() => setFormat('sequence')} /> Image Sequence</label>
                                <label><input type="radio" checked={format === 'mp4'} onChange={() => setFormat('mp4')} /> MP4 Video</label>
                            </div>

                            {format === 'sequence' && (
                                <div>
                                    <label>Frame Rate (FPS)</label>
                                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                        {[10, 24, 60].map(val => (
                                            <button key={val} className="btn"
                                                style={{ flex: 1, padding: '0.5rem', background: fps === val ? 'var(--primary)' : 'var(--surface-raised)' }}
                                                onClick={() => setFps(val)}>{val}</button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {isReplacingImage && replaceImagePath && job.data_folder_name && (
                                <div style={{ marginTop: '1rem', borderTop: '1px solid var(--card-border)', paddingTop: '1rem' }}>
                                    <div style={{ fontSize: '0.78rem', color: 'var(--muted)', marginBottom: '0.5rem' }}>Current image being replaced</div>
                                    <img
                                        src={`${getApiBase()}/data/jobs/${job.data_folder_name}/${replaceImagePath}`}
                                        alt="Current image being replaced"
                                        loading="lazy"
                                        decoding="async"
                                        style={{ width: '100%', borderRadius: '6px', border: '1px solid var(--card-border)', display: 'block' }}
                                    />
                                </div>
                            )}

                            <button className="btn btn-primary" style={{ width: '100%', marginTop: '2rem' }} onClick={handlePreview} disabled={processing}>
                                {processing ? 'Processing...' : (format === 'sequence' ? 'Generate Preview' : 'Export MP4')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 2: REVIEW (FILMSTRIP) */}
            {step === 'review' && (
                <div className="surface-panel">
                    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>{previewFrames.length - excludedFrames.size} of {previewFrames.length} frames selected — click to toggle</h3>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button className="btn btn-secondary" onClick={selectAll}>Select All</button>
                            <button className="btn btn-secondary" onClick={deselectAll}>Clear All</button>
                        </div>
                    </header>

                    <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.5rem', background: 'rgba(255,255,255,0.05)', borderRadius: '4px' }}>
                        <label style={{ minWidth: 'max-content', fontSize: '0.9rem' }}>Thumbnail Size:</label>
                        <input type="range" min="100" max="600" value={thumbSize} onChange={e => setThumbSize(Number(e.target.value))} style={{ flex: 1 }} />
                    </div>

                    <div style={{
                        display: 'flex',
                        gap: '10px',
                        overflowX: 'auto',
                        padding: '10px',
                        background: 'rgba(0,0,0,0.3)',
                        borderRadius: '8px',
                        minHeight: '150px'
                    }}>
                        {previewFrames.map(frame => {
                            const isExcluded = excludedFrames.has(frame);
                            return (
                                <div key={frame}
                                    style={{
                                        flex: '0 0 auto',
                                        position: 'relative',
                                        cursor: 'pointer',
                                        opacity: isExcluded ? 0.5 : 1,
                                        border: isExcluded ? '2px solid var(--border-strong)' : '2px solid var(--primary)',
                                        borderRadius: '4px',
                                        overflow: 'hidden',
                                        width: `${thumbSize}px`
                                    }}
                                >
                                    <img
                                        onClick={() => toggleFrame(frame)}
                                        src={`${getApiBase()}/data/jobs/${job.data_folder_name}/${previewBaseUrl}/${frame}`}
                                        alt={`Preview frame ${frame}`}
                                        loading="lazy"
                                        decoding="async"
                                        style={{ width: '100%', height: 'auto', display: 'block', filter: isExcluded ? 'grayscale(100%)' : 'none' }}
                                    />

                                    {/* Overlay Controls */}
                                    <div style={{
                                        position: 'absolute', bottom: 0, left: 0, right: 0,
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        background: 'rgba(0,0,0,0.8)', padding: '4px 8px'
                                    }}>
                                        <span style={{ fontSize: '10px', color: 'var(--foreground)' }}>{frame}</span>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); setViewingFrame(frame); }}
                                            className="btn"
                                            style={{ padding: '2px 6px', fontSize: '10px', background: 'var(--secondary)' }}
                                        >
                                            View
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>

                    <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                        <button className="btn btn-secondary" onClick={() => setStep('input')}>Back</button>
                        <button className="btn btn-success" onClick={handleSaveToProject} disabled={processing}>
                            {isReplacingImage ? 'Save Replacement & Return' : returnTo ? 'Add to Project & Return' : 'Add to Project'}
                        </button>
                        <button className="btn btn-primary" onClick={handleFinalize} disabled={processing}>
                            {processing ? 'Processing...' : 'Download ZIP'}
                        </button>
                    </div>
                </div>
            )}

            {/* STEP 3: DONE */}
            {step === 'done' && (
                <div className="surface-panel done-panel">
                    <h2 style={{ color: 'var(--success)', marginBottom: '1rem' }}>Export Ready!</h2>
                    <a href={downloadUrl} className="btn btn-primary" style={{ fontSize: '1.2rem', padding: '1rem 2rem' }}>
                        Download {format === 'sequence' ? 'ZIP' : 'MP4'}
                    </a>
                    <br /><br />
                    <button className="btn btn-secondary" onClick={() => setStep('input')}>Create Another Slice</button>
                </div>
            )}

            {/* LIGHTBOX MODAL */}
            {viewingFrame && (
                <div
                    role="dialog"
                    aria-modal="true"
                    aria-label="Preview frame"
                    style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.95)', zIndex: 1000,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
                }} onClick={() => setViewingFrame(null)}>

                    {/* Navigation Buttons */}
                    <button
                        aria-label="Previous frame"
                        className="btn"
                        style={{ position: 'absolute', left: '20px', top: '50%', transform: 'translateY(-50%)', fontSize: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.5)' }}
                        onClick={(e) => {
                            e.stopPropagation();
                            const idx = previewFrames.indexOf(viewingFrame);
                            if (idx > 0) setViewingFrame(previewFrames[idx - 1]);
                        }}
                        disabled={previewFrames.indexOf(viewingFrame) <= 0}
                    >
                        ‹
                    </button>
                    <button
                        aria-label="Next frame"
                        className="btn"
                        style={{ position: 'absolute', right: '20px', top: '50%', transform: 'translateY(-50%)', fontSize: '2rem', padding: '1rem', background: 'rgba(0,0,0,0.5)' }}
                        onClick={(e) => {
                            e.stopPropagation();
                            const idx = previewFrames.indexOf(viewingFrame);
                            if (idx < previewFrames.length - 1) setViewingFrame(previewFrames[idx + 1]);
                        }}
                        disabled={previewFrames.indexOf(viewingFrame) >= previewFrames.length - 1}
                    >
                        ›
                    </button>

                    <img
                        src={`${getApiBase()}/data/jobs/${job.data_folder_name}/${previewBaseUrl}/${viewingFrame}`}
                        alt={`Selected preview frame ${viewingFrame}`}
                        decoding="async"
                        style={{ maxWidth: '80%', maxHeight: '80vh', objectFit: 'contain', borderRadius: '4px' }}
                        onClick={(e) => e.stopPropagation()}
                    />

                    <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', zIndex: 1001 }} onClick={(e) => e.stopPropagation()}>
                        <span style={{ color: 'var(--foreground)', alignSelf: 'center' }}>{viewingFrame} ({previewFrames.indexOf(viewingFrame) + 1}/{previewFrames.length})</span>
                        <button className="btn" onClick={() => toggleFrame(viewingFrame)}>
                            {excludedFrames.has(viewingFrame) ? 'Include Frame' : 'Exclude Frame'}
                        </button>
                        <button className="btn btn-secondary" onClick={() => setViewingFrame(null)}>Close</button>
                    </div>
                </div>
            )}
        </div>
    );
}
