import Sidebar from '@/components/sidebar';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-zinc-950 flex">
      <Sidebar />

      {/* Main Content Area */}
      <main className="flex-1 lg:ml-[260px] min-h-screen flex flex-col">
        <div className="flex-1 w-full max-w-[1360px] mx-auto px-4 pt-16 pb-8 sm:px-6 lg:px-10 lg:pt-10 lg:pb-12">
          {children}
        </div>

        {/* Footer */}
        <footer className="border-t border-border/40 px-4 sm:px-6 lg:px-10 py-6">
          <div className="max-w-[1360px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] font-medium text-zinc-600">
            <span>© {new Date().getFullYear()} AI Compliance & Governance Platform</span>
            <div className="flex items-center gap-3">
              <span className="flex items-center gap-1.5">
                <span className="h-1 w-1 rounded-full bg-emerald-600" />
                All Systems Operational
              </span>
              <span className="text-zinc-800">·</span>
              <span>Region EU-West</span>
            </div>
          </div>
        </footer>
      </main>
    </div>
  );
}
