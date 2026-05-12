import { ReactNode } from 'react';
import { ChevronRight, Home } from 'lucide-react';
import Link from 'next/link';

interface PageShellProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  breadcrumbs?: { label: string; href?: string }[];
}

export default function PageShell({ title, subtitle, actions, children, breadcrumbs }: PageShellProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="space-y-3">
        {breadcrumbs && (
          <nav className="flex items-center gap-1 text-[11px] text-zinc-500 font-medium" aria-label="Breadcrumb">
            <Link href="/overview" className="hover:text-zinc-300 transition-colors">
              <Home className="h-3 w-3" />
            </Link>
            {breadcrumbs.map((bc, idx) => (
              <span key={idx} className="flex items-center gap-1">
                <ChevronRight className="h-3 w-3 text-zinc-700" />
                {bc.href ? (
                  <Link href={bc.href} className="hover:text-zinc-300 transition-colors">
                    {bc.label}
                  </Link>
                ) : (
                  <span className="text-zinc-400">{bc.label}</span>
                )}
              </span>
            ))}
          </nav>
        )}

        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-white">{title}</h1>
            {subtitle && <p className="text-[13px] text-zinc-500 mt-1">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-3">{actions}</div>}
        </div>
      </div>

      {/* Content */}
      <div className="space-y-6">
        {children}
      </div>
    </div>
  );
}
