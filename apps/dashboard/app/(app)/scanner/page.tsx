'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowRight, ExternalLink, Plus, ScanSearch, ShieldAlert } from 'lucide-react';
import { api } from '@/lib/api';
import Card from '@/components/card';
import EmptyState from '@/components/empty-state';
import ErrorState from '@/components/error-state';
import Loading from '@/components/loading';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';

export default function ScannerPage() {
  const [scans, setScans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [url, setUrl] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    setError(null);
    api.listWebsiteScans()
      .then(setScans)
      .catch((err) => setError(err.body?.detail || err.message || 'Failed to load website scans'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const scan = await api.createWebsiteScan({ url, max_pages: 6 });
      window.location.href = `/scanner/${scan.id}`;
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to scan website');
      setSubmitting(false);
    }
  }

  const completed = scans.filter((scan) => scan.status === 'completed').length;
  const highRisk = scans.filter((scan) => ['high', 'prohibited_review'].includes(scan.classification_json?.risk_level)).length;

  return (
    <PageShell
      title="Website Scanner"
      subtitle="Scan a public SaaS website for AI compliance signals and draft EU AI Act triage."
      breadcrumbs={[{ label: 'Website Scanner' }]}
      actions={
        <button
          onClick={() => setShowForm((current) => !current)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          {showForm ? 'CANCEL' : 'NEW SCAN'}
        </button>
      }
    >
      <div className="space-y-6">
        {showForm && (
          <Card title="Scan Public SaaS Website">
            <form onSubmit={handleSubmit} className="grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-3">
              <input
                required
                type="url"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                placeholder="https://example-saas.com"
                className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
              />
              <button
                disabled={submitting}
                className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50"
              >
                {submitting ? 'Scanning...' : 'Run Scanner'}
              </button>
            </form>
          </Card>
        )}

        {loading ? (
          <Loading />
        ) : error ? (
          <ErrorState message={error} onRetry={load} />
        ) : scans.length === 0 ? (
          <EmptyState
            title="No website scans yet"
            message="Start with a public SaaS URL to generate a preliminary AI compliance snapshot."
            icon={ScanSearch}
            action={
              <button
                onClick={() => setShowForm(true)}
                className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-white text-[11px] font-bold uppercase tracking-widest px-4 py-2 rounded-lg transition-all"
              >
                New Scan
              </button>
            }
          />
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card title="Total Scans" variant="stat">
                <span className="text-3xl font-bold">{scans.length}</span>
              </Card>
              <Card title="Completed" variant="stat">
                <span className="text-3xl font-bold text-emerald-400">{completed}</span>
              </Card>
              <Card title="Needs Review" variant="stat">
                <span className="text-3xl font-bold text-amber-400">{highRisk}</span>
              </Card>
            </div>

            <Card title="Scan History">
              <div className="overflow-x-auto -mx-5 px-5">
                <table>
                  <thead>
                    <tr>
                      <th>Website</th>
                      <th>Status</th>
                      <th>Classification</th>
                      <th>Confidence</th>
                      <th>Created</th>
                      <th />
                    </tr>
                  </thead>
                  <tbody>
                    {scans.map((scan) => (
                      <tr key={scan.id}>
                        <td>
                          <div className="flex flex-col">
                            <span className="font-bold text-zinc-200">{scan.title || scan.normalized_url}</span>
                            <a
                              href={scan.normalized_url}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 text-[10px] text-zinc-500 hover:text-indigo-400"
                            >
                              {scan.normalized_url}
                              <ExternalLink className="h-3 w-3" />
                            </a>
                          </div>
                        </td>
                        <td><StatusBadge value={scan.status} /></td>
                        <td>
                          <div className="flex items-center gap-2">
                            {['high', 'prohibited_review'].includes(scan.classification_json?.risk_level) && (
                              <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />
                            )}
                            <span className="text-[11px] font-bold text-zinc-300">
                              {scan.classification_json?.classification || 'Unknown'}
                            </span>
                          </div>
                        </td>
                        <td className="text-[11px] font-mono text-zinc-400">{scan.confidence_score}%</td>
                        <td className="text-[11px] text-zinc-500">{new Date(scan.created_at).toLocaleDateString()}</td>
                        <td className="text-right">
                          <Link href={`/scanner/${scan.id}`} className="p-2 rounded-lg hover:bg-zinc-800 text-zinc-500 hover:text-white inline-flex">
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </>
        )}
      </div>
    </PageShell>
  );
}
