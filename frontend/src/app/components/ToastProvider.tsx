"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

type ToastTone = 'info' | 'success' | 'error';

type ToastItem = {
    id: number;
    message: string;
    tone: ToastTone;
    confirm?: {
        confirmLabel: string;
        cancelLabel: string;
        resolve: (confirmed: boolean) => void;
    };
};

type ToastApi = {
    info: (message: string) => void;
    success: (message: string) => void;
    error: (message: string) => void;
    confirm: (message: string, options?: { confirmLabel?: string, cancelLabel?: string }) => Promise<boolean>;
};

const ToastContext = createContext<ToastApi | null>(null);

const toneStyles: Record<ToastTone, { border: string, accent: string }> = {
    info: { border: 'rgba(59,130,246,0.6)', accent: 'var(--primary)' },
    success: { border: 'rgba(16,185,129,0.65)', accent: 'var(--success)' },
    error: { border: 'rgba(239,68,68,0.65)', accent: 'var(--error)' },
};

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<ToastItem[]>([]);
    const pendingConfirmResolvers = useRef(new Map<number, (confirmed: boolean) => void>());

    useEffect(() => {
        const resolvers = pendingConfirmResolvers.current;
        return () => {
            resolvers.forEach(resolve => resolve(false));
            resolvers.clear();
        };
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(toast => toast.id !== id));
    }, []);

    const showToast = useCallback((message: string, tone: ToastTone) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev, { id, message, tone }]);
        window.setTimeout(() => removeToast(id), 4000);
    }, [removeToast]);

    const api = useMemo<ToastApi>(() => ({
        info: (message) => showToast(message, 'info'),
        success: (message) => showToast(message, 'success'),
        error: (message) => showToast(message, 'error'),
        confirm: (message, options) => new Promise<boolean>((resolve) => {
            const id = Date.now() + Math.random();
            pendingConfirmResolvers.current.forEach(existingResolve => existingResolve(false));
            pendingConfirmResolvers.current.clear();
            pendingConfirmResolvers.current.set(id, resolve);
            setToasts(prev => [...prev.filter(toast => !toast.confirm), {
                id,
                message,
                tone: 'info',
                confirm: {
                    confirmLabel: options?.confirmLabel || 'Confirm',
                    cancelLabel: options?.cancelLabel || 'Cancel',
                    resolve: (confirmed) => {
                        pendingConfirmResolvers.current.delete(id);
                        resolve(confirmed);
                    },
                },
            }]);
        }),
    }), [showToast]);

    const handleConfirm = (toast: ToastItem, confirmed: boolean) => {
        toast.confirm?.resolve(confirmed);
        removeToast(toast.id);
    };

    return (
        <ToastContext.Provider value={api}>
            {children}
            <div
                aria-live="polite"
                aria-atomic="false"
                style={{
                    position: 'fixed',
                    right: '1rem',
                    bottom: '1rem',
                    zIndex: 10000,
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '0.75rem',
                    width: 'min(420px, calc(100vw - 2rem))',
                    pointerEvents: 'none',
                }}
            >
                {toasts.map(toast => {
                    const styles = toneStyles[toast.tone];
                    return (
                        <div
                            key={toast.id}
                            role={toast.confirm ? 'dialog' : 'alert'}
                            aria-label={toast.confirm ? 'Confirmation' : 'Notification'}
                            style={{
                                pointerEvents: 'auto',
                                background: 'var(--surface)',
                                border: `1px solid ${styles.border}`,
                                borderRadius: '8px',
                                color: 'var(--foreground)',
                                padding: '0.85rem 0.95rem',
                            }}
                        >
                            <div style={{ fontSize: '0.92rem', lineHeight: 1.45 }}>{toast.message}</div>
                            {toast.confirm ? (
                                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem', marginTop: '0.85rem' }}>
                                    <button
                                        type="button"
                                        onClick={() => handleConfirm(toast, false)}
                                        style={{ border: '1px solid var(--card-border)', borderRadius: '6px', background: 'transparent', color: 'var(--muted)', padding: '0.45rem 0.7rem', cursor: 'pointer' }}
                                    >
                                        {toast.confirm.cancelLabel}
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => handleConfirm(toast, true)}
                                        style={{ border: 'none', borderRadius: '6px', background: 'var(--primary)', color: 'var(--button-primary-text)', padding: '0.45rem 0.8rem', cursor: 'pointer', fontWeight: 600 }}
                                    >
                                        {toast.confirm.confirmLabel}
                                    </button>
                                </div>
                            ) : (
                                <button
                                    type="button"
                                    aria-label="Dismiss notification"
                                    onClick={() => removeToast(toast.id)}
                                    style={{ marginTop: '0.6rem', border: 'none', background: 'transparent', color: 'var(--muted)', cursor: 'pointer', padding: 0, fontSize: '0.8rem' }}
                                >
                                    Dismiss
                                </button>
                            )}
                        </div>
                    );
                })}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
}
