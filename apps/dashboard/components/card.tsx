import { ReactNode } from 'react';

interface CardProps {
  title?: string;
  subtitle?: string;
  className?: string;
  children: ReactNode;
  variant?: 'default' | 'stat';
}

export default function Card({ title, subtitle, className = '', children, variant = 'default' }: CardProps) {
  if (variant === 'stat') {
    return (
      <div className={`group relative overflow-hidden rounded-xl border border-border bg-card p-5 transition-colors duration-150 hover:border-zinc-700 ${className}`}>
        {title && <p className="text-[10px] font-semibold text-zinc-500 uppercase tracking-[0.12em] mb-1.5">{title}</p>}
        <div>{children}</div>
      </div>
    );
  }

  return (
    <div className={`overflow-hidden rounded-xl border border-border bg-card ${className}`}>
      {(title || subtitle) && (
        <div className="px-5 py-3.5 border-b border-border/60">
          {title && <h3 className="text-[13px] font-semibold tracking-tight">{title}</h3>}
          {subtitle && <p className="text-[11px] text-zinc-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}
