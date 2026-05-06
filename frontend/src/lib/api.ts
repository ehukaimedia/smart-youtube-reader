export function getApiBase(): string {
  if (typeof window === 'undefined') return 'http://localhost:8001';
  return `http://${window.location.hostname}:8001`;
}

export async function getShareOrigin(): Promise<string> {
  if (typeof window === 'undefined') return 'http://localhost:3001';

  try {
    const res = await fetch(`${getApiBase()}/share-info`);
    if (res.ok) {
      const data = await res.json();
      if (typeof data.share_origin === 'string' && data.share_origin) {
        return data.share_origin;
      }
    }
  } catch (err) {
    console.error('Failed to load share origin', err);
  }

  return window.location.origin;
}
