'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import Card from '@/components/card';
import { Plus } from 'lucide-react';

export default function CreateSystemPanel() {
  const router = useRouter();
  const [showCreate, setShowCreate] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({ name: '', description: '', owner_email: '', next_review_at: '' });

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await api.createSystem({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        owner_email: formData.owner_email.trim() || undefined,
        next_review_at: formData.next_review_at
          ? new Date(`${formData.next_review_at}T12:00:00.000Z`).toISOString()
          : undefined,
        review_status: formData.next_review_at ? 'scheduled' : 'not_started',
      });
      setFormData({ name: '', description: '', owner_email: '', next_review_at: '' });
      setShowCreate(false);
      router.refresh();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to register system');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setShowCreate((c) => !c)}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-500 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
        >
          <Plus className="h-4 w-4" />
          {showCreate ? 'CANCEL' : 'REGISTER SYSTEM'}
        </button>
      </div>

      {showCreate && (
        <Card title="Register AI System">
          {error && <p className="text-sm text-red-400 mb-3">{error}</p>}
          <form
            onSubmit={handleCreate}
            className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-[1fr_1fr_220px_180px_auto] gap-3"
          >
            <input
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="System name"
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
            />
            <input
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Short description"
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
            />
            <input
              type="email"
              value={formData.owner_email}
              onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
              placeholder="Owner email"
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
            />
            <input
              type="date"
              value={formData.next_review_at}
              onChange={(e) => setFormData({ ...formData, next_review_at: e.target.value })}
              className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-indigo-500"
            />
            <button
              disabled={submitting}
              className="rounded-lg bg-indigo-600 px-5 py-2 text-xs font-bold text-white disabled:opacity-50"
            >
              {submitting ? 'Creating...' : 'Create System'}
            </button>
          </form>
        </Card>
      )}
    </div>
  );
}
