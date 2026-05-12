import { LucideIcon, Search } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  message?: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export default function EmptyState({ title, message, icon: Icon = Search, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center border-2 border-dashed border-zinc-800/60 rounded-xl bg-card/30 animate-fade-in">
      <div className="bg-secondary p-3.5 rounded-full mb-3">
        <Icon className="h-5 w-5 text-zinc-500" />
      </div>
      <h3 className="text-sm font-semibold text-zinc-300">{title}</h3>
      {message && <p className="text-[12px] text-zinc-500 mt-1 max-w-xs leading-relaxed">{message}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
