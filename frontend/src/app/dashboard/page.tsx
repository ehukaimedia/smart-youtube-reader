"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getApiBase, getShareOrigin } from '@/lib/api';
import { useToast } from '../components/ToastProvider';

type Job = {
    id: string;
    status: string;
    video_url: string;
    title?: string | null;
    created_at: number;
    data_folder_name?: string | null;
    kind?: string | null;
    source_job_id?: string | null;
    digest_model?: string | null;
    summary_image?: string | null;
};

function getYouTubeVideoId(videoUrl: string): string | null {
    try {
        const url = new URL(videoUrl);
        if (url.hostname.includes('youtu.be')) {
            return url.pathname.split('/').filter(Boolean)[0] || null;
        }
        if (url.pathname.startsWith('/shorts/') || url.pathname.startsWith('/embed/')) {
            return url.pathname.split('/').filter(Boolean)[1] || null;
        }
        return url.searchParams.get('v');
    } catch {
        const match = videoUrl.match(/(?:v=|youtu\.be\/|shorts\/|embed\/)([A-Za-z0-9_-]{6,})/);
        return match?.[1] || null;
    }
}

function getYouTubeThumbnailUrl(videoUrl: string): string | null {
    const videoId = getYouTubeVideoId(videoUrl);
    return videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : null;
}

export default function DashboardPage() {
    const [jobs, setJobs] = useState<Job[]>([]);
    const [loading, setLoading] = useState(true);
    const [copiedJobId, setCopiedJobId] = useState<string | null>(null);
    const [shareOrigin, setShareOrigin] = useState('');
    const toast = useToast();

    const fetchJobs = () => {
        fetch(`${getApiBase()}/jobs`)
            .then(res => res.json())
            .then(data => {
                setJobs(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    };

    useEffect(() => {
        fetchJobs();
        getShareOrigin().then(setShareOrigin);
    }, []);

    const handleDelete = async (id: string, e: React.MouseEvent) => {
        e.preventDefault();
        const confirmed = await toast.confirm('Are you sure you want to delete this project?', { confirmLabel: 'Delete Project' });
        if (!confirmed) return;

        try {
            await fetch(`${getApiBase()}/jobs/${id}`, { method: 'DELETE' });
            fetchJobs(); // Refresh
        } catch (err) {
            console.error(err);
            toast.error('Failed to delete project');
        }
    };

    const copyProjectLink = async (id: string) => {
        const origin = shareOrigin || await getShareOrigin();
        const url = `${origin}/reader/${id}`;
        const onCopied = () => {
            setCopiedJobId(id);
            setTimeout(() => setCopiedJobId(null), 2000);
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

    return (
        <div className="container" style={{ padding: '2rem' }}>
            <header style={{ marginBottom: '3rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                    <h1 className="title-gradient" style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>Your Projects</h1>
                    <p style={{ color: '#888' }}>Manage and view your analyzed videos</p>
                </div>
                <Link href="/" className="btn btn-primary">
                    + New Project
                </Link>
            </header>

            {loading ? (
                <div>Loading projects...</div>
            ) : (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '2rem' }}>
                    {jobs.length === 0 && (
                        <div style={{ gridColumn: '1/-1', textAlign: 'center', padding: '4rem', border: '1px dashed var(--card-border)', borderRadius: '12px' }}>
                            <p style={{ marginBottom: '1rem', color: '#888' }}>No projects yet.</p>
                            <Link href="/" className="btn">Start your first project</Link>
                        </div>
                    )}

                    {jobs.map(job => {
                        const projectShareUrl = `${shareOrigin || window.location.origin}/reader/${job.id}`;
                        const thumbnailUrl = job.summary_image && job.data_folder_name
                            ? `${getApiBase()}/data/jobs/${job.data_folder_name}/${job.summary_image}`
                            : getYouTubeThumbnailUrl(job.video_url);

                        return (
                        <div key={job.id} className="glass-card" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', transition: 'transform 0.2s' }}>
                            <div
                                style={{
                                    position: 'relative',
                                    aspectRatio: '16 / 9',
                                    borderRadius: '8px',
                                    overflow: 'hidden',
                                    border: '1px solid var(--card-border)',
                                    background: thumbnailUrl
                                        ? `linear-gradient(rgba(0,0,0,0.02), rgba(0,0,0,0.18)), url(${thumbnailUrl}) center / cover`
                                        : 'linear-gradient(135deg, rgba(59,130,246,0.25), rgba(139,92,246,0.16))'
                                }}
                            >
                                {!thumbnailUrl && (
                                    <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888', fontSize: '0.85rem' }}>
                                        No thumbnail
                                    </div>
                                )}
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
                                    <span className={`status-badge status-${job.status}`} style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(255,255,255,0.1)' }}>
                                        {job.status}
                                    </span>
                                    {job.kind === 'ai_digest' && (
                                        <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(16,185,129,0.16)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.35)' }}>
                                            AI Digest
                                        </span>
                                    )}
                                </div>
                                <button
                                    onClick={(e) => handleDelete(job.id, e)}
                                    style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '1.2rem' }}
                                    title="Delete Project"
                                >
                                    &times;
                                </button>
                            </div>

                            <h3 style={{ fontSize: '1.2rem', fontWeight: 500, lineHeight: 1.4, flex: 1 }}>
                                {job.title || job.video_url}
                            </h3>

                            <p style={{ fontSize: '0.8rem', color: '#666' }}>
                                {new Date(job.created_at * 1000).toLocaleDateString()}
                                {job.kind === 'ai_digest' && job.digest_model ? ` • ${job.digest_model.replace(/^.*:/, '')}` : ''}
                            </p>

                            <Link href={`/reader/${job.id}`} className="btn" style={{ textAlign: 'center' }}>
                                Open Project
                            </Link>

                            <a
                                href={projectShareUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                    color: 'var(--primary)',
                                    fontSize: '0.8rem',
                                    lineHeight: 1.4,
                                    overflowWrap: 'anywhere',
                                    textDecoration: 'none',
                                    border: '1px solid var(--card-border)',
                                    borderRadius: '6px',
                                    padding: '0.6rem 0.75rem',
                                    background: 'rgba(255,255,255,0.04)'
                                }}
                            >
                                Tailscale Link: {projectShareUrl}
                            </a>

                            <div style={{ display: 'grid', gridTemplateColumns: job.status === 'complete' ? '1fr 1fr' : '1fr', gap: '0.75rem' }}>
                                <button
                                    onClick={() => copyProjectLink(job.id)}
                                    className="btn"
                                    style={{ textAlign: 'center', fontSize: '0.85rem', padding: '0.5rem 0.75rem' }}
                                >
                                    {copiedJobId === job.id ? 'Copied Link' : 'Copy Tailscale Link'}
                                </button>

                                {job.status === 'complete' && (
                                    <a
                                        href={`${getApiBase()}/jobs/${job.id}/download`}
                                        download={`${job.data_folder_name || job.id}.zip`}
                                        className="btn"
                                        style={{ textAlign: 'center', fontSize: '0.85rem', padding: '0.5rem 0.75rem', textDecoration: 'none' }}
                                    >
                                        Download ZIP
                                    </a>
                                )}
                            </div>
                        </div>
                    )})}
                </div>
            )}
        </div>
    );
}
