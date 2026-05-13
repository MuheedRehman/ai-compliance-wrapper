'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Cpu,
  Layers,
  ClipboardCheck,
  FileSearch,
  ScanSearch,
  CreditCard,
  Terminal,
  ShieldCheck,
  ChevronRight,
  Menu,
  X,
  LayoutDashboard,
  AlertCircle,
  ListChecks,
  LogOut,
} from 'lucide-react';

const navSections = [
  {
    label: 'Overview',
    items: [
      { href: '/overview', label: 'Dashboard', icon: LayoutDashboard },
    ],
  },
  {
    label: 'Registry',
    items: [
      { href: '/intake',   label: 'Intake',        icon: ClipboardCheck },
      { href: '/scanner',  label: 'Scanner',       icon: ScanSearch },
      { href: '/systems',  label: 'AI Systems',    icon: Cpu },
      { href: '/features', label: 'Features',      icon: Layers },
    ],
  },
  {
    label: 'Governance',
    items: [
      { href: '/reviews',  label: 'Review Tasks',  icon: ClipboardCheck },
      { href: '/evidence', label: 'Evidence Logs', icon: FileSearch },
    ],
  },
  {
    label: 'Compliance',
    items: [
      { href: '/fria',      label: 'FRIAs',         icon: ShieldCheck },
      { href: '/oversight', label: 'Oversight',     icon: ClipboardCheck },
      { href: '/incidents', label: 'Incidents',     icon: AlertCircle },
      { href: '/controls',  label: 'Controls',      icon: ListChecks },
      { href: '/reports',   label: 'Reports',       icon: FileSearch },
    ],
  },
  {
    label: 'Operations',
    items: [
      { href: '/billing',  label: 'Subscription',  icon: CreditCard },
      { href: '/runtime',  label: 'Playground',    icon: Terminal },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);

  async function logout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  }

  // Close mobile nav on route change
  useEffect(() => { setMobileOpen(false); }, [pathname]);

  // Lock body scroll when mobile nav is open
  useEffect(() => {
    document.body.style.overflow = mobileOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [mobileOpen]);

  const navContent = (
    <>
      {/* Brand */}
      <div className="h-16 flex items-center px-5 border-b border-border/60 shrink-0">
        <Link href="/overview" className="flex items-center gap-2.5 group">
          <div className="bg-indigo-600 p-1.5 rounded-lg shadow-md shadow-indigo-600/20 group-hover:shadow-indigo-600/40 transition-shadow">
            <ShieldCheck className="h-[18px] w-[18px] text-white" />
          </div>
          <div className="flex flex-col">
            <span className="text-[13px] font-bold tracking-tight text-white leading-none">
              AI Compliance
            </span>
            <span className="text-[9px] font-medium text-zinc-500 uppercase tracking-[0.12em] mt-0.5">
              Governance Platform
            </span>
          </div>
        </Link>
      </div>

      {/* Nav Sections */}
      <nav className="flex-1 overflow-y-auto py-5 px-3 space-y-6">
        {navSections.map((section) => (
          <div key={section.label}>
            <div className="px-3 mb-2 text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.15em]">
              {section.label}
            </div>
            <div className="space-y-0.5">
              {section.items.map(({ href, label, icon: Icon }) => {
                const active = pathname === href || pathname.startsWith(href + '/');
                return (
                  <Link
                    key={href}
                    href={href}
                    className={`
                      group flex items-center justify-between px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150
                      ${active
                        ? 'bg-zinc-800/80 text-white shadow-sm'
                        : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/40'}
                    `}
                  >
                    <div className="flex items-center gap-2.5">
                      <Icon className={`h-[15px] w-[15px] transition-colors duration-150 ${active ? 'text-indigo-400' : 'text-zinc-500 group-hover:text-zinc-400'}`} />
                      {label}
                    </div>
                    {active && <ChevronRight className="h-3 w-3 text-zinc-600" />}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Environment Badge */}
      <div className="p-3 border-t border-border/60 shrink-0">
        <div className="rounded-lg bg-zinc-900/60 p-3 border border-zinc-800/40">
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
            <span className="text-[10px] font-semibold text-zinc-400 uppercase tracking-wider">Staging</span>
          </div>
          <p className="text-[10px] text-zinc-600 mt-1 leading-relaxed font-medium">
            EU AI Act Compliance v0.5.0
          </p>
          <button
            onClick={logout}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-md border border-zinc-800 px-2 py-1.5 text-[10px] font-bold uppercase tracking-widest text-zinc-500 hover:text-zinc-200 hover:bg-zinc-900"
          >
            <LogOut className="h-3 w-3" />
            Sign Out
          </button>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile Toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white transition-colors"
        aria-label="Open navigation"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile Sidebar */}
      <aside className={`
        fixed top-0 left-0 bottom-0 z-50 w-64 bg-zinc-950 border-r border-border/60 flex flex-col
        lg:hidden transition-transform duration-300 ease-in-out
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-md text-zinc-500 hover:text-white transition-colors"
          aria-label="Close navigation"
        >
          <X className="h-4 w-4" />
        </button>
        {navContent}
      </aside>

      {/* Desktop Sidebar */}
      <aside className="hidden lg:flex fixed top-0 left-0 bottom-0 z-40 w-[260px] bg-zinc-950/80 backdrop-blur-xl border-r border-border/60 flex-col">
        {navContent}
      </aside>
    </>
  );
}
