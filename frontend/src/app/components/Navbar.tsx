"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Navbar() {
    const pathname = usePathname();

    return (
        <nav className="navbar">
            <div className="container" style={{ padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Link href="/" className="nav-logo">
                    Smart Reader
                </Link>
                <div style={{ display: 'flex', gap: '2rem' }}>
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
