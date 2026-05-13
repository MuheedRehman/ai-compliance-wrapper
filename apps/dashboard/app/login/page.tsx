'use client';

import { FormEvent, useState } from 'react';
import { ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError(null);

    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ password }),
    });

    if (!response.ok) {
      setError('Invalid dashboard password');
      setLoading(false);
      return;
    }

    window.location.href = '/overview';
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex items-center gap-3">
          <div className="bg-indigo-600 p-2 rounded-lg shadow-md shadow-indigo-600/20">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">AI Compliance</h1>
            <p className="text-[11px] uppercase tracking-[0.18em] text-zinc-500">Secure Dashboard Access</p>
          </div>
        </div>

        <form onSubmit={submit} className="rounded-lg border border-zinc-800 bg-zinc-950 p-5 shadow-2xl">
          <label className="block text-xs font-bold uppercase tracking-widest text-zinc-500 mb-2">
            Dashboard Password
          </label>
          <input
            autoFocus
            required
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-2.5 text-sm text-white outline-none focus:border-indigo-500"
          />
          {error && <p className="mt-3 text-xs font-medium text-red-400">{error}</p>}
          <button
            disabled={loading}
            className="mt-5 w-full rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-bold uppercase tracking-widest text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
      </div>
    </main>
  );
}
