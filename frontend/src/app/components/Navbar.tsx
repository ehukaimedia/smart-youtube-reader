"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import ShareModeToggle from './ShareModeToggle';
import { DEFAULT_DEMO_JOB_ID, DEMO_JOB_IDS } from './demoProviders';

export default function Navbar() {
    const pathname = usePathname();
    const helpActive = DEMO_JOB_IDS.some((jobId) => pathname === `/reader/${jobId}`);

    return (
        <nav className="navbar">
            <div className="container" style={{ padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Link href="/" className="nav-logo">
                    Smart Reader
                </Link>
                <div className="nav-actions">
                    <ShareModeToggle />
                    <Link href={`/reader/${DEFAULT_DEMO_JOB_ID}`} className={`nav-link ${helpActive ? 'active' : ''}`} title="Open the Smart YouTube Reader demo digest">
                        Help
                    </Link>
                    <Link href="/" className={`nav-link ${pathname === '/' ? 'active' : ''}`}>
                        New Project
                    </Link>
                    <Link href="/dashboard" className={`nav-link ${pathname === '/dashboard' ? 'active' : ''}`}>
                        Dashboard
                    </Link>
                </div>
            </div>
        </nav>
    );
}
