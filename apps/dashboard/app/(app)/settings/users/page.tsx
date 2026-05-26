'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Activity, KeyRound, RefreshCw, Save, ShieldCheck, UserPlus, Users } from 'lucide-react';
import { api, CurrentSession, TenantAdminSummary, TenantRole, TenantUser } from '@/lib/api';
import Card from '@/components/card';
import ErrorState from '@/components/error-state';
import Loading from '@/components/loading';
import PageShell from '@/components/page-shell';
import StatusBadge from '@/components/status-badge';

const roles: TenantRole[] = ['owner', 'admin', 'reviewer', 'auditor', 'viewer'];
const statuses: TenantUser['status'][] = ['active', 'invited', 'disabled'];

function csvToList(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function listToCsv(values: string[] = []) {
  return values.join(', ');
}

function formatDate(value?: string | null) {
  if (!value) return 'Never';
  return new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export default function TenantUsersPage() {
  const [summary, setSummary] = useState<TenantAdminSummary | null>(null);
  const [session, setSession] = useState<CurrentSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingPolicy, setSavingPolicy] = useState(false);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [inviting, setInviting] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<TenantRole>('viewer');
  const [allowedDomains, setAllowedDomains] = useState('');
  const [allowedEmails, setAllowedEmails] = useState('');
  const [googleEnabled, setGoogleEnabled] = useState(true);
  const [passwordEnabled, setPasswordEnabled] = useState(true);
  const [autoProvision, setAutoProvision] = useState(true);
  const [defaultRole, setDefaultRole] = useState<TenantRole>('viewer');

  const load = () => {
    setLoading(true);
    setError(null);
    Promise.all([api.getTenantAdminSummary(), api.getCurrentSession().catch(() => null)])
      .then(([data, sessionData]) => {
        setSummary(data);
        setSession(sessionData);
        setAllowedDomains(listToCsv(data.auth_policy.allowed_domains));
        setAllowedEmails(listToCsv(data.auth_policy.allowed_emails));
        setGoogleEnabled(data.auth_policy.google_login_enabled);
        setPasswordEnabled(data.auth_policy.password_login_enabled);
        setAutoProvision(data.auth_policy.auto_provision_google_users);
        setDefaultRole(data.auth_policy.default_role);
      })
      .catch((err) => setError(err.body?.detail || err.message || 'Failed to load tenant administration data'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const stats = useMemo(() => {
    const users = summary?.users || [];
    const invitations = summary?.invitations || [];
    const events = summary?.login_events || [];
    const actionEvents = summary?.action_events || [];
    return {
      activeUsers: users.filter((user) => user.status === 'active').length,
      pendingInvites: invitations.filter((invite) => invite.status === 'pending').length,
      allowedRules: (summary?.auth_policy.allowed_domains.length || 0) + (summary?.auth_policy.allowed_emails.length || 0),
      failedLogins: events.filter((event) => event.outcome === 'failure').length,
      actionEvents: actionEvents.length,
    };
  }, [summary]);

  const permissions = session?.permissions || [];
  const canManageUsers = permissions.includes('users:write') || session?.role === 'owner' || session?.role === 'admin';
  const canManagePolicy = permissions.includes('policy:write') || session?.role === 'owner' || session?.role === 'admin';

  async function handlePolicySave(event: FormEvent) {
    event.preventDefault();
    setSavingPolicy(true);
    setError(null);
    try {
      const policy = await api.updateTenantAuthPolicy({
        allowed_domains: csvToList(allowedDomains),
        allowed_emails: csvToList(allowedEmails),
        google_login_enabled: googleEnabled,
        password_login_enabled: passwordEnabled,
        auto_provision_google_users: autoProvision,
        default_role: defaultRole,
      });
      setSummary((current) => current ? { ...current, auth_policy: policy } : current);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to update authentication policy');
    } finally {
      setSavingPolicy(false);
    }
  }

  async function handleInvite(event: FormEvent) {
    event.preventDefault();
    if (!inviteEmail.trim()) return;
    setInviting(true);
    setError(null);
    try {
      const invitation = await api.inviteTenantUser({ email: inviteEmail, role: inviteRole });
      setSummary((current) => current ? {
        ...current,
        invitations: [invitation, ...current.invitations.filter((item) => item.id !== invitation.id)],
      } : current);
      setInviteEmail('');
      setInviteRole('viewer');
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to invite user');
    } finally {
      setInviting(false);
    }
  }

  async function handleUserChange(user: TenantUser, changes: Partial<Pick<TenantUser, 'role' | 'status' | 'name'>>) {
    setSavingUserId(user.id);
    setError(null);
    try {
      const updated = await api.updateTenantUser(user.id, changes);
      setSummary((current) => current ? {
        ...current,
        users: current.users.map((item) => item.id === updated.id ? updated : item),
      } : current);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to update user');
    } finally {
      setSavingUserId(null);
    }
  }

  async function revokeInvitation(id: string) {
    setError(null);
    try {
      const invitation = await api.revokeTenantInvitation(id);
      setSummary((current) => current ? {
        ...current,
        invitations: current.invitations.map((item) => item.id === invitation.id ? invitation : item),
      } : current);
      load();
    } catch (err: any) {
      setError(err.body?.detail || err.message || 'Failed to revoke invitation');
    }
  }

  if (loading) return <Loading />;
  if (error && !summary) return <ErrorState message={error} onRetry={load} />;
  if (!summary) return null;

  return (
    <PageShell
      title="Users & Access"
      subtitle="Tenant users, Google login policy, invitations, and access audit."
      breadcrumbs={[{ label: 'Users & Access' }]}
      actions={
        <button
          onClick={load}
          className="flex items-center gap-2 rounded-lg border border-zinc-800 px-3 py-2 text-xs font-bold text-zinc-300 hover:bg-zinc-900"
        >
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      }
    >
      <div className="space-y-6">
        {error && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-xs font-semibold text-red-300">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          <Card title="Active Users" variant="stat">
            <div className="flex items-center gap-3">
              <Users className="h-6 w-6 text-emerald-400" />
              <span className="text-3xl font-bold">{stats.activeUsers}</span>
            </div>
          </Card>
          <Card title="Pending Invites" variant="stat">
            <div className="flex items-center gap-3">
              <UserPlus className="h-6 w-6 text-amber-400" />
              <span className="text-3xl font-bold">{stats.pendingInvites}</span>
            </div>
          </Card>
          <Card title="Allow Rules" variant="stat">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-6 w-6 text-indigo-400" />
              <span className="text-3xl font-bold">{stats.allowedRules}</span>
            </div>
          </Card>
          <Card title="Failed Logins" variant="stat">
            <div className="flex items-center gap-3">
              <KeyRound className="h-6 w-6 text-red-400" />
              <span className="text-3xl font-bold">{stats.failedLogins}</span>
            </div>
          </Card>
          <Card title="Admin Actions" variant="stat">
            <div className="flex items-center gap-3">
              <Activity className="h-6 w-6 text-cyan-400" />
              <span className="text-3xl font-bold">{stats.actionEvents}</span>
            </div>
          </Card>
          <Card title="Your Access" variant="stat">
            <div className="flex items-center gap-3">
              <ShieldCheck className="h-6 w-6 text-indigo-400" />
              <div>
                <span className="block text-xl font-bold capitalize">{session?.role || 'unknown'}</span>
                <span className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
                  {session?.access_label || `${permissions.length} permissions`}
                </span>
              </div>
            </div>
          </Card>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[1.4fr_0.9fr] gap-6">
          <Card title="Tenant Users">
            <div className="overflow-x-auto -mx-5 px-5">
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Provider</th>
                    <th>Last Login</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.users.map((user) => (
                    <tr key={user.id}>
                      <td>
                        <div className="flex flex-col">
                          <span className="font-bold text-zinc-200">{user.name || user.email}</span>
                          <span className="text-[10px] text-zinc-500">{user.email}</span>
                        </div>
                      </td>
                      <td>
                        <select
                          value={user.role}
                          disabled={!canManageUsers || savingUserId === user.id}
                          onChange={(event) => handleUserChange(user, { role: event.target.value as TenantRole })}
                          className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs font-semibold text-zinc-200 outline-none disabled:opacity-50"
                        >
                          {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                        </select>
                      </td>
                      <td>
                        <select
                          value={user.status}
                          disabled={!canManageUsers || savingUserId === user.id}
                          onChange={(event) => handleUserChange(user, { status: event.target.value as TenantUser['status'] })}
                          className="rounded-md border border-zinc-800 bg-zinc-950 px-2 py-1 text-xs font-semibold text-zinc-200 outline-none disabled:opacity-50"
                        >
                          {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                        </select>
                      </td>
                      <td><StatusBadge value={user.auth_provider} /></td>
                      <td className="text-[11px] text-zinc-500">{formatDate(user.last_login_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Invite User">
            <form onSubmit={handleInvite} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2">Email</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(event) => setInviteEmail(event.target.value)}
                  disabled={!canManageUsers || inviting}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 disabled:opacity-50"
                  placeholder="user@company.com"
                  required
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2">Role</label>
                <select
                  value={inviteRole}
                  onChange={(event) => setInviteRole(event.target.value as TenantRole)}
                  disabled={!canManageUsers || inviting}
                  className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 disabled:opacity-50"
                >
                  {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                </select>
              </div>
              <button
                disabled={!canManageUsers || inviting}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2.5 text-xs font-bold uppercase tracking-widest text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                <UserPlus className="h-4 w-4" />
                {inviting ? 'Inviting' : 'Invite User'}
              </button>
            </form>
          </Card>
        </div>

        <Card title="Google Login Policy">
          <form onSubmit={handlePolicySave} className="grid grid-cols-1 xl:grid-cols-[1fr_1fr_auto] gap-4 items-end">
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2">Allowed Domains</label>
              <input
                value={allowedDomains}
                onChange={(event) => setAllowedDomains(event.target.value)}
                disabled={!canManagePolicy || savingPolicy}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 disabled:opacity-50"
                placeholder="company.com, subsidiary.eu"
              />
            </div>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2">Allowed Emails</label>
              <input
                value={allowedEmails}
                onChange={(event) => setAllowedEmails(event.target.value)}
                disabled={!canManagePolicy || savingPolicy}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 disabled:opacity-50"
                placeholder="owner@company.com, auditor@partner.eu"
              />
            </div>
            <button
              disabled={!canManagePolicy || savingPolicy}
              className="flex items-center justify-center gap-2 rounded-lg bg-zinc-100 px-4 py-2.5 text-xs font-bold uppercase tracking-widest text-zinc-950 hover:bg-white disabled:opacity-50"
            >
              <Save className="h-4 w-4" />
              {savingPolicy ? 'Saving' : 'Save'}
            </button>
            <label className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-semibold text-zinc-300">
              <input
                type="checkbox"
                checked={googleEnabled}
                onChange={(event) => setGoogleEnabled(event.target.checked)}
                disabled={!canManagePolicy || savingPolicy}
                className="h-4 w-4 accent-indigo-600"
              />
              Google login enabled
            </label>
            <label className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-semibold text-zinc-300">
              <input
                type="checkbox"
                checked={passwordEnabled}
                onChange={(event) => setPasswordEnabled(event.target.checked)}
                disabled={!canManagePolicy || savingPolicy}
                className="h-4 w-4 accent-indigo-600"
              />
              Password login enabled
            </label>
            <label className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-xs font-semibold text-zinc-300">
              <input
                type="checkbox"
                checked={autoProvision}
                onChange={(event) => setAutoProvision(event.target.checked)}
                disabled={!canManagePolicy || savingPolicy}
                className="h-4 w-4 accent-indigo-600"
              />
              Auto-provision Google users
            </label>
            <div>
              <label className="block text-[10px] font-bold uppercase tracking-widest text-zinc-500 mb-2">Default Role</label>
              <select
                value={defaultRole}
                onChange={(event) => setDefaultRole(event.target.value as TenantRole)}
                disabled={!canManagePolicy || savingPolicy}
                className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-white outline-none focus:border-indigo-500 disabled:opacity-50"
              >
                {roles.filter((role) => role !== 'owner').map((role) => <option key={role} value={role}>{role}</option>)}
              </select>
            </div>
          </form>
        </Card>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <Card title="Invitations">
            <div className="overflow-x-auto -mx-5 px-5">
              <table>
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Status</th>
                    <th>Created</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {summary.invitations.map((invite) => (
                    <tr key={invite.id}>
                      <td className="font-semibold text-zinc-300">{invite.email}</td>
                      <td><StatusBadge value={invite.role} /></td>
                      <td><StatusBadge value={invite.status} /></td>
                      <td className="text-[11px] text-zinc-500">{formatDate(invite.created_at)}</td>
                      <td className="text-right">
                        {invite.status === 'pending' && (
                          <button
                            onClick={() => revokeInvitation(invite.id)}
                            disabled={!canManageUsers}
                            className="rounded-md border border-zinc-800 px-2 py-1 text-[10px] font-bold uppercase tracking-widest text-zinc-400 hover:bg-zinc-900 disabled:opacity-50"
                          >
                            Revoke
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card title="Login Audit">
            <div className="overflow-x-auto -mx-5 px-5">
              <table>
                <thead>
                  <tr>
                    <th>Time</th>
                    <th>Email</th>
                    <th>Provider</th>
                    <th>Outcome</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.login_events.map((event) => (
                    <tr key={event.id}>
                      <td className="text-[11px] text-zinc-500">{formatDate(event.created_at)}</td>
                      <td className="font-semibold text-zinc-300">{event.email || 'Unknown'}</td>
                      <td><StatusBadge value={event.provider} /></td>
                      <td><StatusBadge value={event.outcome} /></td>
                      <td className="text-[11px] text-zinc-500">{event.reason || 'None'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        <Card title="Admin Action Audit">
          <div className="overflow-x-auto -mx-5 px-5">
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Actor</th>
                  <th>Action</th>
                  <th>Target</th>
                  <th>Role</th>
                </tr>
              </thead>
              <tbody>
                {(summary.action_events || []).map((event) => (
                  <tr key={event.id}>
                    <td className="text-[11px] text-zinc-500">{formatDate(event.created_at)}</td>
                    <td className="font-semibold text-zinc-300">{event.actor_email || 'API key'}</td>
                    <td><StatusBadge value={event.action} /></td>
                    <td className="text-[11px] text-zinc-500">{event.target_email || event.target_id || event.target_type}</td>
                    <td>{event.actor_role ? <StatusBadge value={event.actor_role} /> : <span className="text-[11px] text-zinc-600">None</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
    </PageShell>
  );
}
