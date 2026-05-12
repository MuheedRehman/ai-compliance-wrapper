export default function Loading({ label = 'Retrieving compliance data…' }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-28 animate-fade-in">
      <div className="relative flex items-center justify-center">
        <div className="h-10 w-10 border-2 border-zinc-800 rounded-full" />
        <div className="absolute h-10 w-10 border-t-2 border-indigo-500 rounded-full animate-spin" />
      </div>
      <span className="mt-4 text-[11px] font-semibold text-zinc-500 uppercase tracking-[0.12em]">{label}</span>
    </div>
  );
}
