'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';

export default function ReaderPage() {
    const { jobId } = useParams();
    const [job, setJob] = useState<any>(null);
    const [transcript, setTranscript] = useState<any[] | null>(null);
    const [error, setError] = useState('');

    useEffect(() => {
        if (!jobId) return;

        const fetchStatus = async () => {
            try {
                const res = await fetch(`http://127.0.0.1:8001/jobs/${jobId}`);
                if (!res.ok) throw new Error('Failed to fetch job');
                const data = await res.json();
                setJob(data);

                if (data.status === 'complete' && !transcript) {
                    // Fetch transcript
                    const tres = await fetch(`http://127.0.0.1:8001/jobs/${jobId}/transcript`);
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
                        <a
                            href={`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/archive.json`}
                            target="_blank"
                            download="archive.json"
                            className="btn"
                            style={{ padding: '0.25rem 0.75rem', fontSize: '0.8rem', textDecoration: 'none' }}
                        >
                            Download AI Archive
                        </a>
                    )}

                    <a href={`/slicer?id=${job.id}`} className="btn" style={{ background: 'var(--secondary)' }}>
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
                    <div className="glass-card">
                        <h3 style={{ marginBottom: '1rem' }}>Raw Transcript & Context</h3>
                        {transcript.map((line: any, idx: number) => (
                            <div key={idx} style={{ marginBottom: '1rem' }}>
                                <span style={{ color: '#555', fontSize: '0.8rem', marginRight: '1rem', userSelect: 'none' }}>
                                    {Math.floor(line.start / 60)}:{String(Math.floor(line.start % 60)).padStart(2, '0')}
                                </span>
                                <span>{line.text}</span>
                                {line.image && job.data_folder_name && (
                                    <div style={{ marginTop: '0.5rem', marginBottom: '1rem' }}>
                                        <img
                                            src={`http://127.0.0.1:8001/data/jobs/${job.data_folder_name}/frames/${line.image}`}
                                            alt="Context"
                                            style={{ borderRadius: '8px', maxWidth: '100%', maxHeight: '400px', border: '1px solid var(--card-border)' }}
                                        />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>

                    {/* AI Archive Visualization (New) */}
                    <div className="glass-card" style={{ borderColor: 'var(--secondary)' }}>
                        <h3 className="title-gradient" style={{ marginBottom: '1rem' }}>AI Archive Preview</h3>
                        <p style={{ marginBottom: '1rem', color: '#888' }}>
                            This is a preview of the structured <code>archive.json</code> data.
                        </p>
                        <ArchivePreview jobId={job.id} folderName={job.data_folder_name} />
                    </div>
                </div>
            )}
        </div>
    );
}

function ArchivePreview({ jobId, folderName }: { jobId: string, folderName?: string }) {
    const [timeline, setTimeline] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!folderName) return;

        const fetchData = async () => {
            try {
                let archiveData: any[] = [];
                let slicesData: any[] = [];

                // Fetch Archive
                const archiveRes = await fetch(`http://127.0.0.1:8001/data/jobs/${folderName}/archive.json`);
                if (archiveRes.ok) {
                    const data = await archiveRes.json();
                    archiveData = data.archive || [];
                }

                // Fetch Slices
                const slicesRes = await fetch(`http://127.0.0.1:8001/jobs/${jobId}/slices`);
                if (slicesRes.ok) {
                    slicesData = await slicesRes.json();
                }

                // Merge and Sort
                const united = [
                    ...archiveData.map((a: any) => ({ ...a, type: 'chapter', sortTime: a.timestamp_start })),
                    ...slicesData.map((s: any) => ({ ...s, type: 'slice', sortTime: s.base_start_time }))
                ].sort((a, b) => a.sortTime - b.sortTime);

                setTimeline(united);
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
            {timeline.map((item: any, idx: number) => {
                if (item.type === 'slice') {
                    // RENDER SLICE
                    return (
                        <div key={`slice-${item.id}`} style={{ borderBottom: '2px dashed var(--secondary)', paddingBottom: '2rem', background: 'rgba(var(--secondary-rgb), 0.05)', padding: '1.5rem', borderRadius: '8px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                                <h4 style={{ fontSize: '1.1rem', color: 'var(--secondary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    ✨ Custom Slice
                                    <span style={{ fontSize: '0.8rem', opacity: 0.8, fontWeight: 'normal' }}>
                                        ({item.frames.length} frames @ {item.fps} FPS)
                                    </span>
                                </h4>
                                <span style={{ fontSize: '0.8rem', color: '#888' }}>
                                    Starts at {Math.floor(item.base_start_time / 60)}:{String(Math.floor(item.base_start_time % 60)).padStart(2, '0')}
                                </span>
                            </div>

                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
                                {item.frames.map((frame: any, i: number) => (
                                    <div key={i} style={{ position: 'relative' }}>
                                        <img
                                            src={`http://127.0.0.1:8001/data/jobs/${folderName}/slices/${item.id}/frames/${frame.filename}`}
                                            alt={`Frame ${frame.timestamp}`}
                                            style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)' }}
                                        />
                                        <div style={{ position: 'absolute', bottom: 0, right: 0, background: 'rgba(0,0,0,0.7)', color: 'white', fontSize: '0.7rem', padding: '2px 4px', borderTopLeftRadius: '4px' }}>
                                            {frame.timestamp}s
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    );
                } else {
                    // RENDER CHAPTER
                    return (
                        <div key={`chapter-${idx}`} style={{ borderBottom: '1px solid var(--card-border)', paddingBottom: '2rem' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                                <h4 style={{ fontSize: '1.2rem', color: 'var(--foreground)' }}>{item.concept}</h4>
                                <span style={{ fontSize: '0.8rem', color: '#666' }}>
                                    {Math.floor(item.timestamp_start / 60)}:{String(Math.floor(item.timestamp_start % 60)).padStart(2, '0')}
                                </span>
                            </div>
                            <p style={{ color: '#888', fontSize: '0.9rem', marginBottom: '1rem' }}>{item.summary}</p>
                            <p style={{ marginBottom: '1rem', fontSize: '0.95rem' }}>{item.content}</p>

                            {/* Image Grid */}
                            {item.images && item.images.length > 0 && (
                                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                                    {item.images.map((img: string, i: number) => (
                                        <img
                                            key={i}
                                            src={`http://127.0.0.1:8001/data/jobs/${folderName}/frames/${img}`}
                                            alt={`Scene ${i}`}
                                            style={{ width: '100%', borderRadius: '8px', border: '1px solid var(--card-border)' }}
                                        />
                                    ))}
                                </div>
                            )}
                            {/* Legacy Single Image Fallback */}
                            {item.image && !item.images && (
                                <div style={{ marginTop: '1rem' }}>
                                    <img
                                        src={`http://127.0.0.1:8001/data/jobs/${folderName}/frames/${item.image}`}
                                        alt="Scene"
                                        style={{ width: '100%', maxWidth: '400px', borderRadius: '8px', border: '1px solid var(--card-border)' }}
                                    />
                                </div>
                            )}
                        </div>
                    );
                }
            })}
        </div>
    );
}


