'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getApiBase } from '@/lib/api';
import { useToast } from './components/ToastProvider';

type ModelDetail = {
  name: string;
  label?: string;
  size?: string;
  recommended?: boolean;
  installed?: boolean;
};

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState<ModelDetail[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const router = useRouter();
  const toast = useToast();

  useEffect(() => {
    fetch(`${getApiBase()}/models`)
      .then(r => r.json())
      .then(data => {
        const details: ModelDetail[] = data.model_details ?? [];
        const list: ModelDetail[] = details.length
          ? details
          : (data.models ?? []).map((name: string) => ({ name, installed: true }));
        const installed = list.filter(model => model.installed);
        setModels(list);
        setSelectedModel(data.default_model || installed[0]?.name || '');
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

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to create job');
      }

      const data = await res.json();
      router.push(`/reader/${data.id}`);
    } catch (err) {
      console.error(err);
      toast.error(err instanceof Error ? err.message : 'Error creating job');
    } finally {
      setLoading(false);
    }
  };

  const hasInstalledModel = models.some(model => model.installed);
  const modelOptionLabel = (model: ModelDetail) => (
    `${model.label ?? model.name}${model.size ? ` (${model.size})` : ''}${model.recommended ? ' - recommended' : ''}${model.installed ? '' : ' - pull first'}`
  );

  return (
    <main className="container" style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <div className="surface-panel" style={{ width: '100%', maxWidth: '600px', textAlign: 'center' }}>
        <h1 className="page-title" style={{ marginBottom: '1rem' }}>
          Smart Reader
        </h1>
        <p className="muted" style={{ marginBottom: '2rem' }}>
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
              disabled={!hasInstalledModel}
              style={{ cursor: hasInstalledModel ? 'pointer' : 'not-allowed' }}
            >
              {!hasInstalledModel && (
                <option value="">No installed Ollama models</option>
              )}
              {models.map(model => (
                <option key={model.name} value={model.name} disabled={!model.installed}>
                  {modelOptionLabel(model)}
                </option>
              ))}
            </select>
          )}
          <button type="submit" className="btn" disabled={loading || (models.length > 0 && !selectedModel)}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>
    </main>
  );
}
