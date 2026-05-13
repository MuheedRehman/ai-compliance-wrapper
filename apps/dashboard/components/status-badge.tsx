'use client';

const colorMap: Record<string, string> = {
  // statuses
  active:       'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  success:      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  open:         'bg-amber-500/10 text-amber-400 border-amber-500/20',
  pending:      'bg-amber-500/10 text-amber-400 border-amber-500/20',
  closed:       'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  draft:        'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  deployed:     'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  retired:      'bg-red-500/10 text-red-400 border-red-500/20',
  registered:   'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  rejected:     'bg-red-500/10 text-red-400 border-red-500/20',
  revoked:      'bg-red-500/10 text-red-400 border-red-500/20',
  failure:      'bg-red-500/10 text-red-400 border-red-500/20',
  completed:    'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  blocked:      'bg-red-500/10 text-red-400 border-red-500/20',
  error:        'bg-red-500/10 text-red-400 border-red-500/20',
  allow:        'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  flag:         'bg-amber-500/10 text-amber-400 border-amber-500/20',
  quarantined:  'bg-orange-500/10 text-orange-400 border-orange-500/20',
  // risk
  high:         'bg-red-500/10 text-red-400 border-red-500/20',
  medium:       'bg-amber-500/10 text-amber-400 border-amber-500/20',
  low:          'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  unknown:      'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  // billing
  free:         'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
  past_due:     'bg-red-500/10 text-red-400 border-red-500/20',
  canceled:     'bg-red-500/10 text-red-400 border-red-500/20',
  trialing:     'bg-indigo-500/10 text-indigo-400 border-indigo-500/20',
  // entitlements
  enabled:      'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  disabled:     'bg-zinc-500/10 text-zinc-400 border-zinc-500/20',
};

const fallback = 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20';

interface StatusBadgeProps {
  value: string;
  className?: string;
}

export default function StatusBadge({ value, className = '' }: StatusBadgeProps) {
  const colors = colorMap[value?.toLowerCase()] || fallback;
  return (
    <span
      className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${colors} ${className}`}
    >
      {value}
    </span>
  );
}
