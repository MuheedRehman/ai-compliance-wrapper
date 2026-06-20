import type { DashboardPermission, TenantRole } from './session-permissions';
export type { DashboardPermission, TenantRole } from './session-permissions';

// Central API client for the AI Compliance Dashboard.
// All backend calls go through this module.

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/backend';

export class ApiError extends Error {
  status: number;
  body: any;
  constructor(status: number, body: any) {
    super(`API Error ${status}`);
    this.status = status;
    this.body = body;
  }
}

export type TenantUserStatus = 'active' | 'invited' | 'disabled';

export type TenantUser = {
  id: string;
  tenant_id: string;
  email: string;
  name?: string | null;
  role: TenantRole;
  status: TenantUserStatus;
  auth_provider: string;
  last_login_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type TenantInvitation = {
  id: string;
  tenant_id: string;
  email: string;
  role: TenantRole;
  status: 'pending' | 'accepted' | 'revoked' | 'expired';
  invited_by_email?: string | null;
  accepted_at?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
};

export type TenantAuthPolicy = {
  tenant_id: string;
  google_login_enabled: boolean;
  password_login_enabled: boolean;
  allowed_domains: string[];
  allowed_emails: string[];
  auto_provision_google_users: boolean;
  default_role: TenantRole;
  created_at: string;
  updated_at: string;
};

export type TenantLoginAudit = {
  id: string;
  tenant_id?: string | null;
  email?: string | null;
  provider: string;
  outcome: 'success' | 'failure';
  reason?: string | null;
  ip_address?: string | null;
  user_agent?: string | null;
  created_at: string;
};

export type TenantActionAudit = {
  id: string;
  tenant_id: string;
  actor_user_id?: string | null;
  actor_email?: string | null;
  actor_role?: string | null;
  action: string;
  target_type: string;
  target_id?: string | null;
  target_email?: string | null;
  before_json?: Record<string, any> | null;
  after_json?: Record<string, any> | null;
  metadata_json: Record<string, any>;
  created_at: string;
};

export type TenantAdminSummary = {
  users: TenantUser[];
  invitations: TenantInvitation[];
  auth_policy: TenantAuthPolicy;
  login_events: TenantLoginAudit[];
  action_events: TenantActionAudit[];
};

export type CurrentSession = {
  authenticated: boolean;
  email?: string;
  name?: string;
  provider?: 'password' | 'google';
  tenant_id?: string;
  role?: TenantRole;
  user_id?: string;
  permissions?: DashboardPermission[];
  access_label?: string;
};

// ── Domain types for the top-5 API endpoints ───────────────

export type AiSystem = {
  id: string;
  tenant_id: string;
  name: string;
  description?: string | null;
  owner_email?: string | null;
  technical_owner_email?: string | null;
  legal_owner_email?: string | null;
  review_status?: string | null;
  next_review_at?: string | null;
  lifecycle_notes?: string | null;
  risk_level?: string | null;
  annex_iii_category?: string | null;
  lifecycle_status?: string | null;
  created_at: string;
  updated_at: string;
};

export type ComplianceControl = {
  id: string;
  tenant_id: string;
  ai_system_id?: string | null;
  control_key: string;
  title: string;
  article: string;
  category?: string | null;
  status: string;
  severity?: string | null;
  owner_email?: string | null;
  evidence_required?: boolean | null;
  review_cadence_days?: number | null;
  last_reviewed_at?: string | null;
  details_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
};

export type EvidenceItem = {
  id: string;
  tenant_id: string;
  ai_system_id?: string | null;
  control_domain?: string | null;
  title: string;
  status: string;
  owner_email?: string | null;
  collected_at?: string | null;
  notes?: string | null;
  artifact_count?: number;
  created_at: string;
  updated_at: string;
};

export type ReportRecord = {
  id: string;
  tenant_id: string;
  report_type: string;
  title: string;
  status: string;
  ai_system_id?: string | null;
  feature_id?: string | null;
  report_json: Record<string, any>;
  source_refs_json: Record<string, any>[];
  artifact_metadata: Record<string, string>;
  legal_basis_json: Record<string, any>[];
  generation_manifest_json: Record<string, any>;
  created_at: string;
  updated_at: string;
};

export type FRIARecord = {
  id: string;
  tenant_id: string;
  ai_system_id: string;
  ai_system_name?: string | null;
  status: 'draft' | 'in_review' | 'approved' | 'rejected';
  completion_percent: number;
  sections_json?: Record<string, any> | null;
  approval_json?: Record<string, any> | null;
  created_at: string;
  updated_at: string;
};

export async function fetchApi<T = any>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
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
  listSystems: () => fetchApi<AiSystem[]>('/v1/ai-systems'),
  getSystem: (id: string) => fetchApi<AiSystem>(`/v1/ai-systems/${id}`),
  getSystemWorkspace: (id: string) => fetchApi<any>(`/v1/ai-systems/${id}/workspace`),
  createSystem: (body: {
    name: string;
    description?: string;
    owner_email?: string;
    technical_owner_email?: string;
    legal_owner_email?: string;
    review_status?: string;
    next_review_at?: string;
    lifecycle_notes?: string;
  }) =>
    fetchApi<any>('/v1/ai-systems', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateSystem: (id: string, body: any) =>
    fetchApi<any>(`/v1/ai-systems/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  createSystemReview: (id: string, body: any) =>
    fetchApi<any>(`/v1/ai-systems/${id}/reviews`, {
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
  closeReviewTask: (id: string, resolution_note?: string) =>
    fetchApi<any>(`/v1/review-tasks/${id}/close`, {
      method: 'PATCH',
      body: JSON.stringify({ resolution_note }),
    }),

  // Evidence / Logs
  listLogs: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<{ tenant_id: string; logs: any[] }>(`/v1/logs${qs}`);
  },
  listEvidenceItems: (params?: Record<string, string>) => {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return fetchApi<EvidenceItem[]>(`/v1/evidence/items${qs}`);
  },
  getEvidenceSummary: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any>(`/v1/evidence/summary${qs}`);
  },
  createEvidenceItem: (body: any) =>
    fetchApi<any>('/v1/evidence/items', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateEvidenceItem: (id: string, body: any) =>
    fetchApi<any>(`/v1/evidence/items/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  uploadEvidenceArtifact: (itemId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetchApi<any>(`/v1/evidence/items/${itemId}/artifacts`, {
      method: 'POST',
      body: formData,
    });
  },
  getEvidenceArtifactUrl: (itemId: string, artifactId: string) =>
    `${API_BASE_URL}/v1/evidence/items/${itemId}/artifacts/${artifactId}/download`,
  getEvidenceArtifactPreviewUrl: (itemId: string, artifactId: string) =>
    `${API_BASE_URL}/v1/evidence/items/${itemId}/artifacts/${artifactId}/preview`,

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
  materializeIntakeControlPlan: (id: string, aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any[]>(`/v1/intake/${id}/control-plan${qs}`, { method: 'POST' });
  },

  // Obligations (Phase 4)
  listObligationDimensions: () => fetchApi<any[]>('/v1/obligations/dimensions'),
  explainIntakeObligations: (id: string) => fetchApi<any>(`/v1/obligations/explain/intake/${id}`),

  // FRIA
  listFrias: () => fetchApi<FRIARecord[]>('/v1/obligations/fria'),
  getFria: (id: string) => fetchApi<FRIARecord>(`/v1/obligations/fria/${id}`),
  createFria: (body: any) => fetchApi<any>('/v1/obligations/fria', { method: 'POST', body: JSON.stringify(body) }),
  updateFria: (id: string, body: any) => fetchApi<any>(`/v1/obligations/fria/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
  deleteFria: (id: string) => fetchApi<any>(`/v1/obligations/fria/${id}`, { method: 'DELETE' }),
  updateFriaSections: (id: string, body: any) => fetchApi<any>(`/v1/obligations/fria/${id}/sections`, { method: 'PATCH', body: JSON.stringify(body) }),
  submitFria: (id: string, body: any) => fetchApi<any>(`/v1/obligations/fria/${id}/submit`, { method: 'POST', body: JSON.stringify(body) }),
  reviewFria: (id: string, body: any) => fetchApi<any>(`/v1/obligations/fria/${id}/review`, { method: 'POST', body: JSON.stringify(body) }),
  exportFriaUrl: (id: string) => `/v1/obligations/fria/${id}/export`,

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
  listReports: () => fetchApi<ReportRecord[]>('/v1/reports'),
  getReport: (id: string) => fetchApi<ReportRecord>(`/v1/reports/${id}`),
  createReport: (body: any) => fetchApi<any>('/v1/reports', { method: 'POST', body: JSON.stringify(body) }),
  getArtifactUrl: (id: string, artifact: string) => `${API_BASE_URL}/v1/reports/${id}/artifacts/${artifact}`,
  downloadArtifact: async (id: string, artifact: string) => {
    const res = await fetch(`${API_BASE_URL}/v1/reports/${id}/artifacts/${artifact}`, {
      cache: 'no-store',
    });

    if (!res.ok) {
      let body: any;
      try { body = await res.json(); } catch { body = await res.text(); }
      throw new ApiError(res.status, body);
    }

    const contentType = res.headers.get('content-type') || 'text/plain';
    const isBinary = contentType.includes('pdf') || contentType.includes('octet-stream') || contentType.includes('zip');
    return {
      content: isBinary ? await res.arrayBuffer() : await res.text(),
      contentType,
      isBinary,
    };
  },

  downloadBundle: async (id: string) => {
    const res = await fetch(`${API_BASE_URL}/v1/reports/${id}/bundle`, { cache: 'no-store' });
    if (!res.ok) {
      let body: any;
      try { body = await res.json(); } catch { body = await res.text(); }
      throw new ApiError(res.status, body);
    }
    return { content: await res.arrayBuffer(), contentType: 'application/zip' };
  },

  // Compliance Controls
  listControls: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<ComplianceControl[]>(`/v1/compliance/controls${qs}`);
  },
  listControlTemplates: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any[]>(`/v1/compliance/control-templates${qs}`);
  },
  seedBaselineControls: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any[]>(`/v1/compliance/controls/seed-baseline${qs}`, { method: 'POST' });
  },
  applyControlTemplates: (body: any) =>
    fetchApi<any[]>('/v1/compliance/controls/apply-templates', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateControl: (id: string, body: any) =>
    fetchApi<any>(`/v1/compliance/controls/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  recordControlReview: (id: string, body: any) =>
    fetchApi<any>(`/v1/compliance/controls/${id}/reviews`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  listControlEvidence: (id: string) =>
    fetchApi<any[]>(`/v1/compliance/controls/${id}/evidence`),
  attachEvidenceToControl: (controlId: string, itemId: string) =>
    fetchApi<any>(`/v1/compliance/controls/${controlId}/evidence/${itemId}`, {
      method: 'POST',
    }),
  getScorecard: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any>(`/v1/compliance/scorecard${qs}`);
  },
  getControlAuditStatus: (aiSystemId?: string) => {
    const qs = aiSystemId ? `?${new URLSearchParams({ ai_system_id: aiSystemId }).toString()}` : '';
    return fetchApi<any>(`/v1/compliance/audit-status${qs}`);
  },

  // Website / SaaS Scanner
  listWebsiteScans: () => fetchApi<any[]>('/v1/website-scans'),
  getWebsiteScan: (id: string) => fetchApi<any>(`/v1/website-scans/${id}`),
  createWebsiteScan: (body: { url: string; max_pages?: number }) =>
    fetchApi<any>('/v1/website-scans', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  convertWebsiteScan: (id: string, body?: { actor_role?: string }) =>
    fetchApi<any>(`/v1/website-scans/${id}/convert`, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),
  generateWebsiteScanReport: (id: string, body?: { actor_role?: string }) =>
    fetchApi<any>(`/v1/website-scans/${id}/report`, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  // Tenant / User Administration
  getCurrentSession: () => fetch('/api/auth/me', { cache: 'no-store' }).then((res) => {
    if (!res.ok) throw new ApiError(res.status, {});
    return res.json() as Promise<CurrentSession>;
  }),
  getTenantAdminSummary: () => fetchApi<TenantAdminSummary>('/v1/tenant-admin/summary'),
  listTenantActionAudit: () => fetchApi<TenantActionAudit[]>('/v1/tenant-admin/action-audit'),
  listTenantUsers: () => fetchApi<TenantUser[]>('/v1/tenant-admin/users'),
  createTenantUser: (body: { email: string; name?: string; role: TenantRole; status: TenantUserStatus }) =>
    fetchApi<TenantUser>('/v1/tenant-admin/users', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  updateTenantUser: (id: string, body: Partial<Pick<TenantUser, 'name' | 'role' | 'status'>>) =>
    fetchApi<TenantUser>(`/v1/tenant-admin/users/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  inviteTenantUser: (body: { email: string; role: TenantRole }) =>
    fetchApi<TenantInvitation>('/v1/tenant-admin/invitations', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
  revokeTenantInvitation: (id: string) =>
    fetchApi<TenantInvitation>(`/v1/tenant-admin/invitations/${id}/revoke`, {
      method: 'POST',
    }),
  updateTenantAuthPolicy: (body: Partial<Pick<TenantAuthPolicy, 'google_login_enabled' | 'password_login_enabled' | 'allowed_domains' | 'allowed_emails' | 'auto_provision_google_users' | 'default_role'>>) =>
    fetchApi<TenantAuthPolicy>('/v1/tenant-admin/auth-policy', {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
};
