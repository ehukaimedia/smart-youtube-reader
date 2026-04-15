"use client";

import { useEffect, useState, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function SlicerPage() {
    const { jobId } = useParams();
    const router = useRouter(); // Although not explicitly used in view, preserving imports if needed, otherwise clean up.
    // Actually router was unused in the view, but imported. Let's keep it clean.
    const [job, setJob] = useState<any>(null);
    const [videoSrc, setVideoSrc] = useState('');
    const videoRef = useRef<HTMLVideoElement>(null);

    // UI State
    const [step, setStep] = useState<'input' | 'review' | 'done'>('input');
    const [processing, setProcessing] = useState(false);

    // Input State
    const [duration, setDuration] = useState(0);
    const [start, setStart] = useState(0);
    const [end, setEnd] = useState(5);
    const [fps, setFps] = useState(24);
    const [format, setFormat] = useState<'mp4' | 'sequence'>('sequence');

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
        fetch(`http://127.0.0.1:8001/jobs/${jobId}`)
            .then(res => res.json())
            .then(data => {
                setJob(data);
                if (data.data_folder_name) {
                    const ext = data.video_ext || 'mp4';
                    setVideoSrc(`http://127.0.0.1:8001/data/jobs/${data.data_folder_name}/video.${ext}`);
                }
            });
    }, [jobId]);

    const onLoadedMetadata = () => {
        if (videoRef.current) {
            setDuration(videoRef.current.duration);
            setEnd(Math.min(5, videoRef.current.duration));
        }
    };

    // --- Actions ---

    const handlePreview = async () => {
        if (!job) return;
        if ((end - start) > 10) {
            alert("Max duration is 10 seconds");
            return;
        }

        setProcessing(true);
        try {
            if (format === 'mp4') {
                // Direct MP4 export (legacy flow)
                const res = await fetch(`http://127.0.0.1:8001/jobs/${job.id}/slice`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start, end, format: 'mp4' })
                });
                const result = await res.json();
                setDownloadUrl(`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/${result.path}`);
                setStep('done');
            } else {
                // Generate Frames Preview
                const res = await fetch(`http://127.0.0.1:8001/jobs/${job.id}/slicer/preview`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ start, end, fps })
                });
                if (!res.ok) throw new Error("Preview failed");
                const data = await res.json();
                setPreviewId(data.preview_id);
                setPreviewFrames(data.frames);
                setPreviewBaseUrl(data.base_url); // relative e.g. "previews/123"
                setExcludedFrames(new Set(data.frames)); // start with all deselected
                setStep('review');
            }
        } catch (e) {
            console.error(e);
            alert("Failed");
        } finally {
            setProcessing(false);
        }
    };

    const handleFinalize = async () => {
        const selected = previewFrames.filter(f => !excludedFrames.has(f));
        if (selected.length === 0) {
            alert("No frames selected!");
            return;
        }

        setProcessing(true);
        try {
            const res = await fetch(`http://127.0.0.1:8001/jobs/${job.id}/slicer/finalize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    preview_id: previewId,
                    selected_files: selected
                })
            });
            if (!res.ok) throw new Error("Finalize failed");
            const result = await res.json();
            setDownloadUrl(`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/${result.path}`);
            setStep('done');
        } catch (e) {
            console.error(e);
            alert("Failed to create zip");
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

    const [sliceDuration, setSliceDuration] = useState(5);
    const [syncToPlayhead, setSyncToPlayhead] = useState(true);
    const [isPreviewing, setIsPreviewing] = useState(false);

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
        const selected = previewFrames.filter(f => !excludedFrames.has(f));
        if (selected.length === 0) {
            alert("No frames selected!");
            return;
        }

        setProcessing(true);
        try {
            const res = await fetch(`http://127.0.0.1:8001/jobs/${job.id}/slicer/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    preview_id: previewId,
                    selected_files: selected
                })
            });
            if (!res.ok) throw new Error("Save failed");
            await res.json();
            alert("Slice saved to project!");
        } catch (e) {
            console.error(e);
            alert("Failed to save slice");
        } finally {
            setProcessing(false);
        }
    };

    if (!job) return <div className="container">Loading...</div>;

    return (
        <div className="container">
            <header style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="title-gradient">Video Slicer</h1>
                    <p style={{ color: '#888' }}>{job.title}</p>
                </div>
                <a href={`/reader/${job.id}`} className="btn" style={{ background: '#333', fontSize: '0.9rem' }}>
                    &larr; Back to Project
                </a>
            </header>

            {/* STEP 1: INPUT */}
            {step === 'input' && (
                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                    <div className="glass-card">
                        <div style={{ position: 'relative', width: '100%', aspectRatio: '16/9', background: '#000', borderRadius: '8px', overflow: 'hidden' }}>
                            {videoSrc && (
                                <video
                                    ref={videoRef}
                                    src={videoSrc}
                                    controls
                                    style={{ width: '100%', height: '100%' }}
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
                                <button className="btn" onClick={videoPreview} style={{ background: '#444', height: 'fit-content', alignSelf: 'end' }}>Preview Play</button>
                            </div>
                            <div style={{ marginTop: '0.5rem' }}>
                                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.9rem', color: '#aaa' }}>
                                    <input type="checkbox" checked={syncToPlayhead} onChange={e => setSyncToPlayhead(e.target.checked)} />
                                    Sync Selection to Playhead while Scrubbing
                                </label>
                            </div>
                        </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="glass-card">
                            <h3>Format</h3>
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
                                                style={{ flex: 1, padding: '0.5rem', background: fps === val ? 'var(--primary)' : '#444' }}
                                                onClick={() => setFps(val)}>{val}</button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <button className="btn" style={{ width: '100%', marginTop: '2rem' }} onClick={handlePreview} disabled={processing}>
                                {processing ? 'Processing...' : (format === 'sequence' ? 'Generate Preview' : 'Export MP4')}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* STEP 2: REVIEW (FILMSTRIP) */}
            {step === 'review' && (
                <div className="glass-card">
                    <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                        <h3>{previewFrames.length - excludedFrames.size} of {previewFrames.length} frames selected — click to toggle</h3>
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button className="btn" style={{ background: '#444' }} onClick={selectAll}>Select All</button>
                            <button className="btn" style={{ background: '#444' }} onClick={deselectAll}>Clear All</button>
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
                                        border: isExcluded ? '2px solid #555' : '2px solid var(--primary)',
                                        borderRadius: '4px',
                                        overflow: 'hidden',
                                        width: `${thumbSize}px`
                                    }}
                                >
                                    <img
                                        onClick={() => toggleFrame(frame)}
                                        src={`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/${previewBaseUrl}/${frame}`}
                                        style={{ width: '100%', height: 'auto', display: 'block', filter: isExcluded ? 'grayscale(100%)' : 'none' }}
                                    />

                                    {/* Overlay Controls */}
                                    <div style={{
                                        position: 'absolute', bottom: 0, left: 0, right: 0,
                                        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                                        background: 'rgba(0,0,0,0.8)', padding: '4px 8px'
                                    }}>
                                        <span style={{ fontSize: '10px', color: '#fff' }}>{frame}</span>
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
                        <button className="btn" style={{ background: '#444' }} onClick={() => setStep('input')}>Back</button>
                        <button className="btn" style={{ background: 'var(--secondary)' }} onClick={handleSaveToProject} disabled={processing}>
                            Add to Project
                        </button>
                        <button className="btn" onClick={handleFinalize} disabled={processing}>
                            {processing ? 'Processing...' : 'Download ZIP'}
                        </button>
                    </div>
                </div>
            )}

            {/* STEP 3: DONE */}
            {step === 'done' && (
                <div className="glass-card" style={{ textAlign: 'center', padding: '4rem' }}>
                    <h2 style={{ color: 'var(--success)', marginBottom: '1rem' }}>Expert Ready!</h2>
                    <a href={downloadUrl} className="btn" style={{ fontSize: '1.2rem', padding: '1rem 2rem' }}>
                        Download {format === 'sequence' ? 'ZIP' : 'MP4'}
                    </a>
                    <br /><br />
                    <button className="btn" style={{ background: '#444' }} onClick={() => setStep('input')}>Create Another Slice</button>
                </div>
            )}

            {/* LIGHTBOX MODAL */}
            {viewingFrame && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.95)', zIndex: 1000,
                    display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
                }} onClick={() => setViewingFrame(null)}>

                    {/* Navigation Buttons */}
                    <button
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
                        src={`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/${previewBaseUrl}/${viewingFrame}`}
                        style={{ maxWidth: '80%', maxHeight: '80vh', objectFit: 'contain', borderRadius: '4px' }}
                        onClick={(e) => e.stopPropagation()}
                    />

                    <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', zIndex: 1001 }} onClick={(e) => e.stopPropagation()}>
                        <span style={{ color: 'white', alignSelf: 'center' }}>{viewingFrame} ({previewFrames.indexOf(viewingFrame) + 1}/{previewFrames.length})</span>
                        <button className="btn" onClick={() => toggleFrame(viewingFrame)}>
                            {excludedFrames.has(viewingFrame) ? 'Include Frame' : 'Exclude Frame'}
                        </button>
                        <button className="btn" style={{ background: '#444' }} onClick={() => setViewingFrame(null)}>Close</button>
                    </div>
                </div>
            )}
        </div>
    );
}


