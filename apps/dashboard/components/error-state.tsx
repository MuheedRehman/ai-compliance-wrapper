import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center border border-red-900/20 rounded-xl bg-red-950/5 animate-fade-in">
      <div className="bg-red-950/40 p-3.5 rounded-full mb-3 ring-1 ring-red-500/10">
        <AlertCircle className="h-5 w-5 text-red-500" />
      </div>
      <h3 className="text-sm font-semibold text-red-400">Request Failed</h3>
      <p className="text-[12px] text-red-400/60 mt-1 max-w-xs font-medium leading-relaxed">
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 flex items-center gap-2 rounded-lg bg-card px-4 py-2 text-[11px] font-semibold text-zinc-300 hover:bg-secondary ring-1 ring-border transition-all active:scale-95"
        >
          <RefreshCw className="h-3 w-3" />
          Retry
        </button>
      )}
    </div>
  );
}
