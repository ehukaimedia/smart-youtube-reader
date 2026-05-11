'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/api';
import { useToast } from './components/ToastProvider';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const router = useRouter();
  const toast = useToast();

  useEffect(() => {
    fetch(`${getApiBase()}/models`)
      .then(r => r.json())
      .then(data => {
        const list: string[] = data.models ?? [];
        setModels(list);
        if (list.length > 0) setSelectedModel(list[0]);
      })
      .catch(() => {});
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    try {
      const payload: { video_url: string; model?: string } = { video_url: url };
      if (selectedModel) payload.model = selectedModel;

      const res = await fetch(`${getApiBase()}/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error('Failed to create job');

      const data = await res.json();
      router.push(`/reader/${data.id}`);
    } catch (err) {
      console.error(err);
      toast.error('Error creating job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <div className="glass-card" style={{ width: '100%', maxWidth: '600px', textAlign: 'center' }}>
        <h1 style={{ fontSize: '3rem', fontWeight: 800, marginBottom: '1rem' }} className="title-gradient">
          Smart Reader
        </h1>
        <p style={{ color: '#888', marginBottom: '2rem' }}>
          De-duplicated, intelligent YouTube summaries powered by local AI.
        </p>

        <div style={{ marginBottom: '2rem' }}>
          <a href="/dashboard" style={{ color: 'var(--primary)', textDecoration: 'none', borderBottom: '1px dashed' }}>
            Go to Project Dashboard &rarr;
          </a>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input
            type="url"
            className="input"
            placeholder="Paste YouTube URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          {models.length > 0 && (
            <select
              className="input"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              style={{ cursor: 'pointer' }}
            >
              {models.map(m => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          )}
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>
    </main>
  );
}
