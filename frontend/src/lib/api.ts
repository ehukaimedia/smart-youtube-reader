export function getApiBase(): string {
  if (typeof window === 'undefined') return 'http://localhost:8001';
  return `http://${window.location.hostname}:8001`;
}

export type ShareMode = 'local' | 'tailscale';

export type ShareModeInfo = {
  share_origin: string | null;
  available: boolean;
  status?: string;
  install_url?: string;
};

export type ShareInfo = {
  default_mode: ShareMode;
  modes: {
    local: ShareModeInfo;
    tailscale: ShareModeInfo;
  };
  configured_override: boolean;
};

const SHARE_MODE_STORAGE_KEY = 'smart-reader-share-mode';

export function readStoredShareMode(): ShareMode {
  if (typeof window === 'undefined') return 'local';
  const stored = window.localStorage.getItem(SHARE_MODE_STORAGE_KEY);
  return stored === 'tailscale' ? 'tailscale' : 'local';
}

export function writeStoredShareMode(mode: ShareMode): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(SHARE_MODE_STORAGE_KEY, mode);
}

function fallbackShareInfo(): ShareInfo {
  const origin = typeof window === 'undefined' ? 'http://localhost:3001' : window.location.origin;
  return {
    default_mode: 'local',
    modes: {
      local: { share_origin: origin, available: true },
      tailscale: {
        share_origin: null,
        available: false,
        status: 'not_running',
        install_url: 'https://tailscale.com/download/macos',
      },
    },
    configured_override: false,
  };
}

export async function getShareInfo(): Promise<ShareInfo> {
  if (typeof window === 'undefined') return fallbackShareInfo();

  try {
    const res = await fetch(`${getApiBase()}/share-info`);
    if (!res.ok) return fallbackShareInfo();
    const data = await res.json();
    if (data && typeof data === 'object' && data.modes) {
      return data as ShareInfo;
    }
    return fallbackShareInfo();
  } catch (err) {
    console.error('Failed to load share info', err);
    return fallbackShareInfo();
  }
}

export function resolveShareOrigin(info: ShareInfo, mode: ShareMode): string | null {
  const modeInfo = info.modes[mode];
  if (modeInfo.available && modeInfo.share_origin) return modeInfo.share_origin;
  // Caller decides how to handle unavailability; return null so they can react.
  return null;
}
