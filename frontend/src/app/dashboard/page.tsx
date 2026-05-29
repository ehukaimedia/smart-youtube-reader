"use client";

import { useEffect, useState } from 'react';
import Link from 'next/link';
import {
    getApiBase,
    getShareInfo,
    readStoredShareMode,
    resolveShareOrigin,
    type ShareInfo,
    type ShareMode,
} from '@/lib/api';
import { copyText } from '@/lib/clipboard';
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
    const [digestTaskCopiedJobId, setDigestTaskCopiedJobId] = useState<string | null>(null);
    const [groupTaskCopied, setGroupTaskCopied] = useState(false);
    const [groupTitle, setGroupTitle] = useState('Combined Learning Digest');
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState<'all' | 'complete' | 'processing' | 'failed'>('all');
    const [sortOrder, setSortOrder] = useState<'newest' | 'oldest' | 'title'>('newest');
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
    const [shareInfo, setShareInfo] = useState<ShareInfo | null>(null);
    const [shareMode] = useState<ShareMode>(() => readStoredShareMode());
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
        getShareInfo().then(setShareInfo);
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
        const info = shareInfo ?? await getShareInfo();
        if (!shareInfo) setShareInfo(info);
        const origin = resolveShareOrigin(info, shareMode);
        if (!origin) {
            const reason = info.modes.tailscale.status;
            const message = reason === 'not_installed'
                ? 'Tailscale is not installed. Switch to Local or install Tailscale.'
                : reason === 'no_tailnet_ip'
                    ? 'Tailscale is installed but no tailnet IP is available. Run `tailscale up` and retry.'
                    : 'Tailscale is not running. Start the Tailscale app or run `tailscale up`.';
            toast.error(message);
            return;
        }
        const url = `${origin}/reader/${id}`;
        const onCopied = () => {
            setCopiedJobId(id);
            setTimeout(() => setCopiedJobId(null), 2000);
        };

        copyText(url, onCopied);
    };

    const copyAiDigestWithImagesTask = (job: Job) => {
        if (!job.data_folder_name) {
            toast.error('This project is missing its data folder.');
            return;
        }
        const projectFolder = `data/jobs/${job.data_folder_name}`;
        const draftPath = `${projectFolder}/generated/ai-digest-draft.json`;
        const prompt = `Create the default Smart YouTube Reader AI digest version with generated WebP teaching images for this project using the local CLI.

Do not use an in-app model option. You are the digest-and-image agent. Codex GPT 5.5 image generation is the recommended setup.
Run commands from the smart-youtube-reader repo root.

Important:
- Infographic style is a human choice. Before generating images, set one style for the whole digest:
  - simple: use .codex/skills/simple-infographic for quiet text-led card-strip teaching images.
  - premium: use .codex/skills/premium-infographic and GPT 5.5 image generation for full-color, concept-adaptive visual-learning images that teach the chapter idea.
  If the human has not chosen, pick the style that best fits the material and record the choice in operator_image_note.
- Read archive.json and inspect the attached frame images before deciding what to keep.
- Create a new digestible chapter structure, not a light paraphrase.
- Create one novel generated WebP teaching image per digest chapter.
- Keep the digest to at most 6 chapters/images. If the material truly needs more than 6 images, explain the needed count in operator_image_note and still produce the best 6-image digest.
- Do not copy, crop, trace, or reuse source frames, screenshots, or YouTube thumbnails.
- Do not include fake plus buttons, carousel arrows, pagination dots, or navigation controls inside static infographic images.
- Save and reference only generated/*.webp output images in the draft.

Workflow:
1. Run this command to print the default image-rich digest task:
   python3 tools/create_ai_digest_version.py "${projectFolder}"
2. Read archive.json and inspect the attached frame images as evidence.
3. Cut fluff, repetition, sponsor chatter, intros/outros, and low-value transitions.
4. Preserve durable facts, theory, procedures, examples, caveats, failure modes, and useful visual explanations.
5. Save the generated WebP images under:
   ${projectFolder}/generated/
6. Write the required JSON draft to:
   ${draftPath}
7. Materialize the new AI digest project:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --draft "${draftPath}"
8. Verify the dashboard shows the new project with an AI Digest badge and the reader opens it with one generated image per chapter.

Source project:
${projectFolder}`;
        copyText(prompt, () => {
            setDigestTaskCopiedJobId(job.id);
            setTimeout(() => setDigestTaskCopiedJobId(null), 2000);
        });
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
    const visibleJobs = jobs
        .filter(job => {
            const query = searchTerm.trim().toLowerCase();
            const searchable = `${job.title || ''} ${job.video_url || ''} ${job.kind || ''} ${job.digest_model || ''}`.toLowerCase();
            const matchesQuery = !query || searchable.includes(query);
            const matchesStatus = statusFilter === 'all' || job.status === statusFilter;
            return matchesQuery && matchesStatus;
        })
        .sort((a, b) => {
            if (sortOrder === 'oldest') return a.created_at - b.created_at;
            if (sortOrder === 'title') return (a.title || a.video_url).localeCompare(b.title || b.video_url);
            return b.created_at - a.created_at;
        });
    const completeCount = jobs.filter(job => job.status === 'complete').length;
    const aiDigestCount = jobs.filter(job => job.kind === 'ai_digest' || job.kind === 'group_ai_digest').length;
    const copyGroupAiDigestTask = () => {
        if (selectedJobs.length < 2) {
            toast.error('Select at least two completed projects for a group digest.');
            return;
        }

        const projectFolders = selectedJobs.map(job => `data/jobs/${job.data_folder_name}`);
        const quotedProjects = projectFolders.map(path => `"${path}"`).join(' ');
        const prompt = `Create a Smart YouTube Reader GROUP AI digest using the local CLI.

Do not use an in-app model option. You are the group digest agent.
Run commands from the smart-youtube-reader repo root.

Important: this is not a source-frame merge. Read all source archives and inspect the attached frame images as evidence, then create one novel, intuitive combined transcript and exactly 3 novel WebP AI teaching images from that new transcript.

Infographic style is a human choice. Before generating images, set one style for the whole group digest:
- simple: use .codex/skills/simple-infographic for quiet text-led card-strip teaching images.
- premium: use .codex/skills/premium-infographic and GPT 5.5 image generation for full-color, concept-adaptive visual-learning images that teach the combined lesson.
If the human has not chosen, pick the style that best fits the material and record the choice in the image prompts.

Teaching goal:
- Teach digestible facts, theory, and testable hypotheses.
- Do not concatenate or lightly paraphrase the source transcripts.
- Build a new mental model that explains what is true, why it works, when it fails, and what evidence confirms it.

Workflow:
1. Run this command to print the exact group digest task:
   python3 tools/create_group_ai_digest_version.py ${quotedProjects} --title "${groupTitle || 'Combined Learning Digest'}"
2. Read every archive.json and inspect the attached frame images before deciding what to keep.
3. Merge repeated lessons across videos into a new transcript with chapter-level facts, theory, and hypotheses. Cut fluff, repetition, intros/outros, and low-value transitions.
4. Create exactly 3 new WebP AI teaching images from the new combined transcript. Do not copy original frames, screenshots, or YouTube thumbnails into the output. Do not include fake plus buttons, carousel arrows, pagination dots, or navigation controls inside static infographic images.
5. Write the required JSON draft and the 3 generated WebP images to the staging paths printed by the CLI.
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
        <div className="container dashboard-page">
            <header className="page-header">
                <div>
                    <h1 className="page-title">Learning library</h1>
                    <p className="muted">Search, group, share, and open projects without printing long URLs on every card.</p>
                </div>
                <Link href="/" className="btn btn-primary btn-compact">
                    New Project
                </Link>
            </header>

            {loading ? (
                <div className="surface-panel">Loading projects...</div>
            ) : (
                <>
                <section className="stats-grid" aria-label="Library stats">
                    <div className="stat-tile">
                        <strong>{jobs.length}</strong>
                        <span>Projects</span>
                    </div>
                    <div className="stat-tile">
                        <strong>{aiDigestCount}</strong>
                        <span>AI digests</span>
                    </div>
                    <div className="stat-tile">
                        <strong>{selectedJobs.length}</strong>
                        <span>Selected</span>
                    </div>
                    <div className="stat-tile">
                        <strong>{completeCount}</strong>
                        <span>Complete</span>
                    </div>
                </section>

                <section className="library-toolbar" aria-label="Project filters">
                    <input
                        type="search"
                        className="input"
                        value={searchTerm}
                        onChange={(event) => setSearchTerm(event.target.value)}
                        placeholder="Search projects"
                    />
                    <div className="filter-pills" aria-label="Status filter">
                        {(['all', 'complete', 'processing', 'failed'] as const).map(status => (
                            <button
                                key={status}
                                type="button"
                                className={`pill-button ${statusFilter === status ? 'active' : ''}`}
                                onClick={() => setStatusFilter(status)}
                            >
                                {status === 'all' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                        ))}
                    </div>
                    <select className="input sort-select" value={sortOrder} onChange={(event) => setSortOrder(event.target.value as typeof sortOrder)}>
                        <option value="newest">Newest first</option>
                        <option value="oldest">Oldest first</option>
                        <option value="title">Title A-Z</option>
                    </select>
                </section>

                {selectedJobs.length > 0 && (
                    <section className="group-bar">
                        <input
                            value={groupTitle}
                            onChange={(event) => setGroupTitle(event.target.value)}
                            placeholder="Group digest title"
                            className="input"
                            aria-label="Group digest title"
                        />
                        <strong>{selectedJobs.length} selected for group digest</strong>
                        <div className="action-row">
                            <button
                                onClick={copyGroupAiDigestTask}
                                disabled={selectedJobs.length < 2}
                                className="btn btn-success btn-compact"
                            >
                                {groupTaskCopied ? 'Copied Group Task' : 'Copy Group AI Digest Task'}
                            </button>
                            <button
                                onClick={() => setSelectedGroupIds([])}
                                className="btn btn-secondary btn-compact"
                            >
                                Clear
                            </button>
                        </div>
                    </section>
                )}

                <div className="project-grid">
                    {jobs.length === 0 && (
                        <div className="empty-state">
                            <p>No projects yet.</p>
                            <Link href="/" className="btn">Start your first project</Link>
                        </div>
                    )}

                    {visibleJobs.map(job => {
                        const thumbnailUrl = job.summary_image && job.data_folder_name
                            ? `${getApiBase()}/data/jobs/${job.data_folder_name}/${job.summary_image}`
                            : getYouTubeThumbnailUrl(job.video_url);
                        const isYouTubeUrl = Boolean(getYouTubeVideoId(job.video_url));
                        const isSelectedForGroup = selectedGroupIds.includes(job.id);
                        const canGroup = job.status === 'complete' && Boolean(job.data_folder_name);
                        const canCreateAiDigest = job.status === 'complete' && Boolean(job.data_folder_name) && !job.kind;
                        const kindLabel = job.kind === 'group_ai_digest'
                            ? 'Group AI Digest'
                            : job.kind === 'ai_digest'
                                ? 'AI Digest'
                                : job.summary_image
                                    ? 'AI Summary'
                                    : null;

                        return (
                        <article key={job.id} className={`project-card ${isSelectedForGroup ? 'selected' : ''}`}>
                            <div
                                className="project-thumb"
                                style={{
                                    background: thumbnailUrl
                                        ? `linear-gradient(rgba(0,0,0,0.02), rgba(0,0,0,0.18)), url(${thumbnailUrl}) center / cover`
                                        : undefined
                                }}
                            >
                                {!thumbnailUrl && (
                                    <div className="thumb-empty">
                                        No thumbnail
                                    </div>
                                )}
                            </div>

                            <div className="project-body">
                                <div className="badge-row">
                                    <span className={`status-badge status-${job.status}`}>
                                        {job.status}
                                    </span>
                                    {kindLabel && (
                                        <span className="status-badge badge-success">
                                            {kindLabel}
                                        </span>
                                    )}
                                    {isSelectedForGroup && (
                                        <span className="status-badge badge-success">
                                            Grouped
                                        </span>
                                    )}
                                </div>

                                <h2 className="project-title">
                                    {job.title || job.video_url}
                                </h2>

                                <p className="project-meta">
                                    {new Date(job.created_at * 1000).toLocaleDateString()}
                                    {job.kind === 'ai_digest' && job.digest_model ? ` · ${job.digest_model.replace(/^.*:/, '')}` : ''}
                                </p>
                            </div>

                            <div className={`project-actions ${canCreateAiDigest ? 'has-digest-action' : ''}`}>
                                <Link href={`/reader/${job.id}`} className="btn btn-primary btn-compact">
                                    Open Project
                                </Link>
                                {canCreateAiDigest && (
                                    <button
                                        onClick={() => copyAiDigestWithImagesTask(job)}
                                        className="btn btn-success btn-compact"
                                        title="Copy the default generated-WebP AI digest task"
                                    >
                                        {digestTaskCopiedJobId === job.id ? 'Copied Digest' : 'AI Digest'}
                                    </button>
                                )}
                                {job.video_url && (
                                    <a href={job.video_url} target="_blank" rel="noopener noreferrer" className="btn btn-secondary btn-compact">
                                        {isYouTubeUrl ? 'Open YouTube' : 'Open Source'}
                                    </a>
                                )}
                                <details className="overflow-menu">
                                    <summary aria-label="Project actions">⋯</summary>
                                    <div className="overflow-content">
                                        <button onClick={() => copyProjectLink(job.id)}>
                                            {copiedJobId === job.id ? 'Copied Link' : 'Copy Project Link'}
                                        </button>
                                        {job.status === 'complete' && (
                                            <a
                                                href={`${getApiBase()}/jobs/${job.id}/download`}
                                                download={`${job.data_folder_name || job.id}.zip`}
                                            >
                                                Download ZIP
                                            </a>
                                        )}
                                        {canGroup && (
                                            <button onClick={() => toggleGroupSelection(job)}>
                                                {isSelectedForGroup ? 'Remove from Group' : 'Add to Group'}
                                            </button>
                                        )}
                                        <button className="danger-item" onClick={(e) => handleDelete(job.id, e)}>
                                            Delete Project
                                        </button>
                                    </div>
                                </details>
                            </div>
                        </article>
                    )})}
                    {jobs.length > 0 && visibleJobs.length === 0 && (
                        <div className="empty-state">
                            <p>No projects match the current filters.</p>
                            <button className="btn btn-secondary" onClick={() => { setSearchTerm(''); setStatusFilter('all'); }}>
                                Clear filters
                            </button>
                        </div>
                    )}
                </div>
                </>
            )}
        </div>
    );
}
