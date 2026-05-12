'use client';

import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';
import Card from '@/components/card';
import Loading from '@/components/loading';
import ErrorState from '@/components/error-state';
import EmptyState from '@/components/empty-state';
import { CreditCard, ExternalLink, Zap, CheckCircle2 } from 'lucide-react';

export default function BillingPage() {
  const [sub, setSub] = useState<any>(null);
  const [entitlements, setEntitlements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.getSubscription(), api.getEntitlements()])
      .then(([subData, entData]) => {
        setSub(subData);
        setEntitlements(entData);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleCheckout = async (planId: string) => {
    setActionLoading(true);
    try {
      const data = await api.createCheckoutSession(planId);
      window.open(data.checkout_url, '_blank');
    } catch (err: any) {
      alert(`Checkout error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handlePortal = async () => {
    setActionLoading(true);
    try {
      const data = await api.createPortalSession();
      window.open(data.portal_url, '_blank');
    } catch (err: any) {
      alert(`Portal error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <PageShell 
      title="Subscription Management" 
      subtitle="Overview of your organization's service tier and feature entitlements."
      breadcrumbs={[{ label: 'Subscription' }]}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Current Plan Overview */}
        <div className="lg:col-span-2 space-y-6">
          <Card title="Current Plan Identity">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="bg-indigo-600/10 p-3 rounded-2xl ring-1 ring-indigo-500/20">
                  <Zap className="h-8 w-8 text-indigo-500" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold capitalize text-white">{sub?.plan_id || 'Free Tier'}</h2>
                  <p className="text-xs text-zinc-500 font-medium">Global AI Compliance Operations</p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-2">
                <StatusBadge value={sub?.status || 'active'} className="scale-110 origin-right" />
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
                  Status: {sub?.status?.toUpperCase() || 'PROVISIONED'}
                </p>
              </div>
            </div>
            
            <div className="mt-8 pt-8 border-t border-border grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Renewal Date</p>
                <p className="text-sm font-semibold text-zinc-300">
                  {sub?.current_period_end
                    ? new Date(sub.current_period_end).toLocaleDateString(undefined, { dateStyle: 'full' })
                    : 'End of active period'}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Billing Cycle</p>
                <p className="text-sm font-semibold text-zinc-300">Monthly Recurrence</p>
              </div>
            </div>
          </Card>

          <Card title="Entitlement Matrix" subtitle="Active feature flags and operational limits per tier.">
            {entitlements.length === 0 ? (
              <EmptyState title="No entitlements provisioned" message="Feature access will appear here once your tier is updated." />
            ) : (
              <div className="space-y-3">
                {entitlements.map((e: any, i: number) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg border border-border bg-zinc-950/40 hover:bg-zinc-950 transition-colors group">
                    <div className="flex items-center gap-3">
                      <div className={`p-1.5 rounded ${e.is_enabled ? 'bg-emerald-500/10 text-emerald-500' : 'bg-zinc-800 text-zinc-500'}`}>
                        <CheckCircle2 className="h-3.5 w-3.5" />
                      </div>
                      <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">{e.feature_key}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-tighter">Quota</p>
                        <p className="text-[10px] font-mono text-zinc-400">{e.limit_value ?? 'Unlimited'}</p>
                      </div>
                      <div className="w-px h-6 bg-border" />
                      <StatusBadge value={e.is_enabled ? 'enabled' : 'disabled'} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions & Upgrade */}
        <div className="space-y-6">
          <Card className="bg-gradient-to-br from-indigo-600 to-indigo-800 border-none relative overflow-hidden group">
            <div className="relative z-10 space-y-4">
              <h3 className="text-white font-bold tracking-tight">Scale Operations</h3>
              <p className="text-indigo-100 text-xs leading-relaxed">
                Upgrade to Enterprise for advanced risk modeling, unlimited feature registry, and dedicated audit support.
              </p>
              <button
                onClick={() => handleCheckout('price_pro_monthly')}
                disabled={actionLoading}
                className="w-full py-3 rounded-xl bg-white text-indigo-700 text-xs font-bold uppercase tracking-widest hover:bg-indigo-50 transition-all shadow-xl shadow-black/20 active:scale-[0.98] disabled:opacity-50"
              >
                {actionLoading ? 'Connecting...' : 'UPGRADE TO PRO'}
              </button>
            </div>
            {/* Decorative background element */}
            <div className="absolute -bottom-12 -right-12 h-40 w-40 bg-white/10 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-700" />
          </Card>

          <Card title="Billing Controls">
            <button
              onClick={handlePortal}
              disabled={actionLoading}
              className="w-full py-2.5 rounded-lg border border-border bg-zinc-900 text-zinc-300 text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 hover:text-white transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              <ExternalLink className="h-3.5 w-3.5" />
              {actionLoading ? 'Verifying...' : 'Stripe Customer Portal'}
            </button>
            <p className="mt-4 text-[10px] text-zinc-600 leading-relaxed text-center italic">
              Manage payment methods, download invoices, and update billing details securely via Stripe.
            </p>
          </Card>
        </div>
      </div>
    </PageShell>
  );
}
