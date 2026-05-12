// Central API client for the AI Compliance Dashboard.
// All backend calls go through this module.
//
// Auth: uses getApiKey() from lib/auth.ts which reads
// localStorage first, then falls back to NEXT_PUBLIC_API_TOKEN.

import { getApiKey } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  body: any;
  constructor(status: number, body: any) {
    super(`API Error ${status}`);
    this.status = status;
    this.body = body;
  }
}

export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    'x-api-key': getApiKey(),
    ...(options.headers as Record<string, string> || {}),
  };

  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(url, {
    ...options,
    headers,
    cache: 'no-store',
  });

  if (!res.ok) {
    let body: any;
    try { body = await res.json(); } catch { body = await res.text(); }
    throw new ApiError(res.status, body);
  }

  return res.json();
}

// ── Typed helpers ──────────────────────────────────────────

export const api = {
  // AI Systems
  listSystems: () => fetchApi<any[]>('/v1/ai-systems'),
  getSystem: (id: string) => fetchApi<any>(`/v1/ai-systems/${id}`),
  createSystem: (body: { name: string; description?: string }) =>
    fetchApi<any>('/v1/ai-systems', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Features
  listFeatures: () => fetchApi<{ tenant_id: string; features: any[] }>('/v1/features'),
  createFeature: (body: {
    feature_id: string;
    name: string;
    description?: string;
    owner_email?: string;
    ai_system_id?: string;
    approved_models?: string[];
  }) =>
    fetchApi<any>('/v1/features', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  getFeature: (featureId: string) => fetchApi<any>(`/v1/features/${featureId}`),
  getFeatureVersions: (featureId: string) =>
    fetchApi<{ feature_id: string; versions: any[] }>(`/v1/features/${featureId}/versions`),

  // Reviews
  listReviews: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<{ tenant_id: string; review_tasks: any[] }>(`/v1/review-tasks${qs}`);
  },

  // Evidence / Logs
  listLogs: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<{ tenant_id: string; logs: any[] }>(`/v1/logs${qs}`);
  },

  // Billing
  getSubscription: () => fetchApi<any>('/v1/billing/subscription'),
  getEntitlements: () => fetchApi<any[]>('/v1/billing/entitlements'),
  createCheckoutSession: (planId: string) =>
    fetchApi<{ checkout_url: string }>('/v1/billing/checkout-session', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId }),
    }),
  createPortalSession: () =>
    fetchApi<{ portal_url: string }>('/v1/billing/portal-session', {
      method: 'POST',
    }),

  // Runtime (governed chat)
  sendChat: (body: {
    messages: { role: string; content: string }[];
    feature_id?: string;
    model?: string;
    max_tokens?: number;
  }) =>
    fetchApi<any>('/v1/chat/completions', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Intake & Classification
  listIntakes: () => fetchApi<any[]>('/v1/intake'),
  getIntake: (id: string) => fetchApi<any>(`/v1/intake/${id}`),
  createIntake: (body: { title: string; answers: any }) =>
    fetchApi<any>('/v1/intake', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  // Obligations (Phase 4)
  // FRIA
  listFrias: () => fetchApi<any[]>('/v1/obligations/fria'),
  getFria: (id: string) => fetchApi<any>(`/v1/obligations/fria/${id}`),
  createFria: (body: any) => fetchApi<any>('/v1/obligations/fria', { method: 'POST', body: JSON.stringify(body) }),
  updateFria: (id: string, body: any) => fetchApi<any>(`/v1/obligations/fria/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteFria: (id: string) => fetchApi<any>(`/v1/obligations/fria/${id}`, { method: 'DELETE' }),

  // Oversight
  listOversight: () => fetchApi<any[]>('/v1/obligations/oversight'),
  createOversight: (body: any) => fetchApi<any>('/v1/obligations/oversight', { method: 'POST', body: JSON.stringify(body) }),
  updateOversight: (id: string, body: any) => fetchApi<any>(`/v1/obligations/oversight/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteOversight: (id: string) => fetchApi<any>(`/v1/obligations/oversight/${id}`, { method: 'DELETE' }),

  // Incidents
  listIncidents: () => fetchApi<any[]>('/v1/obligations/incidents'),
  getIncident: (id: string) => fetchApi<any>(`/v1/obligations/incidents/${id}`),
  createIncident: (body: any) => fetchApi<any>('/v1/obligations/incidents', { method: 'POST', body: JSON.stringify(body) }),
  updateIncident: (id: string, body: any) => fetchApi<any>(`/v1/obligations/incidents/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteIncident: (id: string) => fetchApi<any>(`/v1/obligations/incidents/${id}`, { method: 'DELETE' }),

  // Reports (Phase 4.5)
  listReports: () => fetchApi<any[]>('/v1/reports'),
  getReport: (id: string) => fetchApi<any>(`/v1/reports/${id}`),
  createReport: (body: any) => fetchApi<any>('/v1/reports', { method: 'POST', body: JSON.stringify(body) }),
  getArtifactUrl: (id: string, artifact: string) => `${API_BASE_URL}/v1/reports/${id}/artifacts/${artifact}`,
  downloadArtifact: async (id: string, artifact: string) => {
    const res = await fetch(`${API_BASE_URL}/v1/reports/${id}/artifacts/${artifact}`, {
      headers: { 'x-api-key': getApiKey() },
      cache: 'no-store',
    });

    if (!res.ok) {
      let body: any;
      try { body = await res.json(); } catch { body = await res.text(); }
      throw new ApiError(res.status, body);
    }

    return {
      content: await res.text(),
      contentType: res.headers.get('content-type') || 'text/plain',
    };
  },

  // Compliance Controls
  listControls: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any[]>(`/v1/compliance/controls${qs}`);
  },
  seedBaselineControls: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any[]>(`/v1/compliance/controls/seed-baseline${qs}`, { method: 'POST' });
  },
  updateControl: (id: string, body: any) =>
    fetchApi<any>(`/v1/compliance/controls/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  getScorecard: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any>(`/v1/compliance/scorecard${qs}`);
  },
};
