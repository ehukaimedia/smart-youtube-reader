'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8001/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_url: url }),
      });

      if (!res.ok) throw new Error('Failed to create job');

      const data = await res.json();
      router.push(`/reader/${data.id}`);
    } catch (err) {
      console.error(err);
      alert('Error creating job');
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
          De-duplicated, intelligent YouTube summaries powered by Gemini 3 Flash.
        </p>

        <div style={{ marginBottom: '2rem' }}>
          <a href="/dashboard" style={{ color: 'var(--primary)', textDecoration: 'none', borderBottom: '1px dashed' }}>
            Go to Project Dashboard &rarr;
          </a>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
          <input
            type="url"
            className="input"
            placeholder="Paste YouTube URL..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
          <button type="submit" className="btn" disabled={loading}>
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </form>
      </div>
    </main>
  );
}
