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

// The effective share mode is derived from where the app is actually served:
// switching modes redirects to the other origin, so the served host is the source
// of truth (a localStorage preference would only ever be written, never read).
export function inferShareModeFromLocation(): ShareMode {
  if (typeof window === 'undefined') return 'local';
  const host = window.location.hostname;
  if (host.startsWith('100.') || host.endsWith('.tailscale.net')) return 'tailscale';
  return 'local';
}

function fallbackShareInfo(): ShareInfo {
  return {
    default_mode: 'local',
    modes: {
      local: { share_origin: 'http://localhost:3001', available: true },
      tailscale: {
        share_origin: null,
        available: false,
        status: 'not_running',
        install_url: 'https://tailscale.com/download',
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

function getShareRestartCommand(): string {
  if (typeof navigator !== 'undefined' && navigator.platform.toLowerCase().includes('win')) {
    return 'start.bat -Share';
  }
  return 'SYR_SHARE=1 ./start.command';
}

export function describeTailscaleUnavailable(info: ShareInfo): string {
  const reason = info.modes.tailscale.status;
  if (reason === 'not_share_enabled') {
    return `Tailscale is connected, but Smart Reader was started in Local mode. Restart with \`${getShareRestartCommand()}\`, then try Tailscale again.`;
  }
  if (reason === 'not_installed') {
    return 'Tailscale is not installed. Install Tailscale or stay on Local.';
  }
  if (reason === 'no_tailnet_ip') {
    return 'Tailscale is installed but no tailnet IP is available. Run `tailscale up` and retry.';
  }
  return 'Tailscale is not running. Start the Tailscale app or run `tailscale up`.';
}

export function getTailscaleModeLabel(info: ShareInfo): string {
  if (info.modes.tailscale.available) return 'Tailscale';
  if (info.modes.tailscale.status === 'not_share_enabled') return 'Tailscale (share off)';
  return 'Tailscale (unavailable)';
}
