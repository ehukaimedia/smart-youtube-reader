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
    const [groupTaskCopied, setGroupTaskCopied] = useState(false);
    const [groupTitle, setGroupTitle] = useState('Combined Learning Digest');
    const [selectedGroupIds, setSelectedGroupIds] = useState<string[]>(() => {
        if (typeof window === 'undefined') return [];
        const stored = window.localStorage.getItem('smart-reader-group-selection');
        if (!stored) return [];
        try {
            const parsed = JSON.parse(stored);
            return Array.isArray(parsed) ? parsed.filter(item => typeof item === 'string') : [];
        } catch {
            window.localStorage.removeItem('smart-reader-group-selection');
            return [];
        }
    });
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

    useEffect(() => {
        window.localStorage.setItem('smart-reader-group-selection', JSON.stringify(selectedGroupIds));
    }, [selectedGroupIds]);

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

    const toggleGroupSelection = (job: Job) => {
        if (job.status !== 'complete' || !job.data_folder_name) return;
        setSelectedGroupIds(prev => (
            prev.includes(job.id)
                ? prev.filter(id => id !== job.id)
                : [...prev, job.id]
        ));
    };

    const selectedJobs = jobs.filter(job => selectedGroupIds.includes(job.id) && job.status === 'complete' && job.data_folder_name);
    const copyGroupAiDigestTask = () => {
        if (selectedJobs.length < 2) {
            toast.error('Select at least two completed projects for a group digest.');
            return;
        }

        const projectFolders = selectedJobs.map(job => `/Volumes/Extreme SSD/AI-Applications/smart-youtube-reader/data/jobs/${job.data_folder_name}`);
        const quotedProjects = projectFolders.map(path => `"${path}"`).join(' ');
        const prompt = `Create a Smart YouTube Reader GROUP AI digest using the local CLI.

Do not use an in-app model option. You are the group digest agent.

Important: this is not a source-frame merge. Read all source archives and inspect the attached frame images as evidence, then create one novel, intuitive combined transcript and exactly 3 novel AI teaching images from that new transcript.

Teaching goal:
- Teach digestible facts, theory, and testable hypotheses.
- Do not concatenate or lightly paraphrase the source transcripts.
- Build a new mental model that explains what is true, why it works, when it fails, and what evidence confirms it.

Workflow:
1. Run this command to print the exact group digest task:
   python3 tools/create_group_ai_digest_version.py ${quotedProjects} --title "${groupTitle || 'Combined Learning Digest'}"
2. Read every archive.json and inspect the attached frame images before deciding what to keep.
3. Merge repeated lessons across videos into a new transcript with chapter-level facts, theory, and hypotheses. Cut fluff, repetition, intros/outros, and low-value transitions.
4. Create exactly 3 new AI teaching images from the new combined transcript. Do not copy original frames, screenshots, or YouTube thumbnails into the output.
5. Write the required JSON draft and the 3 generated images to the staging paths printed by the CLI.
6. Materialize the group AI digest with the command printed by the CLI.
7. Verify the dashboard shows the new project with a Group AI Digest badge and the reader opens it.

Source projects:
${projectFolders.join('\n')}`;
        copyText(prompt, () => {
            setGroupTaskCopied(true);
            setTimeout(() => setGroupTaskCopied(false), 2000);
        });
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
                <>
                <section className="glass-card" style={{ marginBottom: '2rem', display: 'grid', gridTemplateColumns: 'minmax(220px, 1fr) auto auto', gap: '0.75rem', alignItems: 'center' }}>
                    <input
                        value={groupTitle}
                        onChange={(event) => setGroupTitle(event.target.value)}
                        placeholder="Group digest title"
                        style={{
                            width: '100%',
                            padding: '0.75rem 0.9rem',
                            borderRadius: '6px',
                            border: '1px solid var(--card-border)',
                            background: 'rgba(255,255,255,0.04)',
                            color: 'var(--foreground)'
                        }}
                    />
                    <button
                        onClick={copyGroupAiDigestTask}
                        disabled={selectedJobs.length < 2}
                        className="btn"
                        style={{ background: groupTaskCopied ? 'var(--secondary)' : 'var(--success)', opacity: selectedJobs.length < 2 ? 0.5 : 1 }}
                    >
                        {groupTaskCopied ? 'Copied Group Task' : `Copy Group AI Digest CLI Task (${selectedJobs.length})`}
                    </button>
                    <button
                        onClick={() => setSelectedGroupIds([])}
                        className="btn"
                        style={{ background: 'rgba(255,255,255,0.08)' }}
                    >
                        Clear Group
                    </button>
                </section>

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
                        const isSelectedForGroup = selectedGroupIds.includes(job.id);
                        const canGroup = job.status === 'complete' && Boolean(job.data_folder_name);
                        const kindLabel = job.kind === 'group_ai_digest'
                            ? 'Group AI Digest'
                            : job.kind === 'ai_digest'
                                ? 'AI Digest'
                                : job.summary_image
                                    ? 'AI Summary'
                                    : null;

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
                                    {kindLabel && (
                                        <span style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem', borderRadius: '4px', background: 'rgba(16,185,129,0.16)', color: 'var(--success)', border: '1px solid rgba(16,185,129,0.35)' }}>
                                            {kindLabel}
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

                            {canGroup && (
                                <button
                                    onClick={() => toggleGroupSelection(job)}
                                    className="btn"
                                    style={{ textAlign: 'center', fontSize: '0.85rem', padding: '0.5rem 0.75rem', background: isSelectedForGroup ? 'var(--success)' : 'rgba(255,255,255,0.08)' }}
                                >
                                    {isSelectedForGroup ? 'Added to Group' : 'Add to Group'}
                                </button>
                            )}

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
                </>
            )}
        </div>
    );
}
