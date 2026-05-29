"use client";

import { useEffect, useState } from 'react';
import {
    getShareInfo,
    readStoredShareMode,
    resolveShareOrigin,
    writeStoredShareMode,
    type ShareInfo,
    type ShareMode,
} from '@/lib/api';
import { useToast } from './ToastProvider';

function isModeMatchingLocation(mode: ShareMode): boolean {
    if (typeof window === 'undefined') return true;
    const host = window.location.hostname;
    const isTailscaleHost = host.startsWith('100.') || host.endsWith('.tailscale.net');
    if (mode === 'tailscale') return isTailscaleHost;
    return !isTailscaleHost;
}

export default function ShareModeToggle() {
    const [shareInfo, setShareInfo] = useState<ShareInfo | null>(null);
    const [shareMode, setShareMode] = useState<ShareMode>(() => readStoredShareMode());
    const toast = useToast();

    useEffect(() => {
        getShareInfo().then(setShareInfo);
    }, []);

    useEffect(() => {
        if (!shareInfo || shareInfo.configured_override) return;
        if (isModeMatchingLocation(shareMode)) return;
        const origin = resolveShareOrigin(shareInfo, shareMode);
        if (!origin || window.location.origin === origin) return;
        window.location.replace(`${origin}${window.location.pathname}${window.location.search}${window.location.hash}`);
    }, [shareInfo, shareMode]);

    const updateShareMode = async (mode: ShareMode) => {
        const info = shareInfo ?? await getShareInfo();
        if (!shareInfo) setShareInfo(info);
        const origin = resolveShareOrigin(info, mode);
        if (!origin) {
            const reason = info.modes.tailscale.status;
            const message = reason === 'not_installed'
                ? 'Tailscale is not installed. Install Tailscale or stay on Local.'
                : reason === 'no_tailnet_ip'
                    ? 'Tailscale is installed but no tailnet IP is available. Run `tailscale up` and retry.'
                    : 'Tailscale is not running. Start the Tailscale app or run `tailscale up`.';
            toast.error(message);
            return;
        }

        setShareMode(mode);
        writeStoredShareMode(mode);
        if (window.location.origin !== origin) {
            window.location.assign(`${origin}${window.location.pathname}${window.location.search}${window.location.hash}`);
        }
    };

    if (!shareInfo || shareInfo.configured_override) return null;

    return (
        <div className="nav-share-toggle" role="radiogroup" aria-label="App host mode">
            <button
                type="button"
                role="radio"
                aria-checked={shareMode === 'local'}
                className={`pill-button ${shareMode === 'local' ? 'active' : ''}`}
                onClick={() => updateShareMode('local')}
            >
                Local
            </button>
            <button
                type="button"
                role="radio"
                aria-checked={shareMode === 'tailscale'}
                className={`pill-button ${shareMode === 'tailscale' ? 'active' : ''}`}
                onClick={() => updateShareMode('tailscale')}
                title={shareInfo.modes.tailscale.available ? 'Open the app through your tailnet IP' : 'Tailscale is not currently available on this machine'}
            >
                Tailscale{!shareInfo.modes.tailscale.available && ' (unavailable)'}
            </button>
        </div>
    );
}
