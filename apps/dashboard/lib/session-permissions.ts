export type TenantRole = 'owner' | 'admin' | 'reviewer' | 'auditor' | 'viewer';

export type DashboardPermission =
  | 'tenant:read'
  | 'tenant:admin'
  | 'users:write'
  | 'policy:write'
  | 'billing:manage'
  | 'governance:read'
  | 'governance:review'
  | 'governance:write'
  | 'evidence:read'
  | 'evidence:write'
  | 'reports:read'
  | 'reports:write'
  | 'scanner:run'
  | 'runtime:execute';

export type PermissionDecision = {
  allowed: boolean;
  requiredPermission?: DashboardPermission;
  detail?: string;
};

const ROLE_PERMISSIONS: Record<TenantRole, DashboardPermission[]> = {
  owner: [
    'tenant:read',
    'tenant:admin',
    'users:write',
    'policy:write',
    'billing:manage',
    'governance:read',
    'governance:review',
    'governance:write',
    'evidence:read',
    'evidence:write',
    'reports:read',
    'reports:write',
    'scanner:run',
    'runtime:execute',
  ],
  admin: [
    'tenant:read',
    'tenant:admin',
    'users:write',
    'policy:write',
    'billing:manage',
    'governance:read',
    'governance:review',
    'governance:write',
    'evidence:read',
    'evidence:write',
    'reports:read',
    'reports:write',
    'scanner:run',
    'runtime:execute',
  ],
  reviewer: [
    'tenant:read',
    'governance:read',
    'governance:review',
    'governance:write',
    'evidence:read',
    'evidence:write',
    'reports:read',
    'reports:write',
    'scanner:run',
  ],
  auditor: ['tenant:read', 'governance:read', 'evidence:read', 'reports:read'],
  viewer: ['tenant:read', 'governance:read', 'evidence:read', 'reports:read'],
};

const READ_METHODS = new Set(['GET', 'HEAD', 'OPTIONS']);

export function isTenantRole(role: string | undefined): role is TenantRole {
  return role === 'owner' || role === 'admin' || role === 'reviewer' || role === 'auditor' || role === 'viewer';
}

export function permissionsForRole(role: string | undefined): DashboardPermission[] {
  if (!isTenantRole(role)) return [];
  return [...ROLE_PERMISSIONS[role]];
}

export function hasPermission(role: string | undefined, permission: DashboardPermission): boolean {
  return permissionsForRole(role).includes(permission);
}

export function accessLabel(role: string | undefined): string {
  if (role === 'owner' || role === 'admin') return 'Full access';
  if (role === 'reviewer') return 'Contributor access';
  if (role === 'auditor' || role === 'viewer') return 'Read-only access';
  return 'Session required';
}

export function requiredPermissionForRequest(method: string, rawPath: string): DashboardPermission {
  const normalizedMethod = method.toUpperCase();
  const path = rawPath.startsWith('/') ? rawPath : `/${rawPath}`;
  const isRead = READ_METHODS.has(normalizedMethod);

  if (path.startsWith('/v1/tenant-admin')) {
    if (isRead) return 'tenant:read';
    if (path.includes('/auth-policy')) return 'policy:write';
    if (path.includes('/users') || path.includes('/invitations')) return 'users:write';
    return 'tenant:admin';
  }

  if (path.startsWith('/v1/billing')) return 'billing:manage';
  if (path.startsWith('/v1/chat')) return isRead ? 'tenant:read' : 'runtime:execute';
  if (path.startsWith('/v1/evidence') || path.startsWith('/v1/logs')) {
    return isRead ? 'evidence:read' : 'evidence:write';
  }
  if (path.startsWith('/v1/reports')) return isRead ? 'reports:read' : 'reports:write';
  if (path.startsWith('/v1/website-scans')) {
    if (isRead) return 'governance:read';
    if (path.endsWith('/report')) return 'reports:write';
    if (path.endsWith('/convert')) return 'governance:write';
    return 'scanner:run';
  }
  if (path.startsWith('/v1/review-tasks') && !isRead) return 'governance:review';
  if (
    path.startsWith('/v1/ai-systems') ||
    path.startsWith('/v1/compliance') ||
    path.startsWith('/v1/features') ||
    path.startsWith('/v1/intake') ||
    path.startsWith('/v1/obligations')
  ) {
    return isRead ? 'governance:read' : 'governance:write';
  }

  return isRead ? 'tenant:read' : 'governance:write';
}

export function decideSessionRequestAccess(
  role: string | undefined,
  method: string,
  path: string,
): PermissionDecision {
  if (!isTenantRole(role)) {
    return {
      allowed: false,
      detail: 'Dashboard tenant role is required',
    };
  }

  const requiredPermission = requiredPermissionForRequest(method, path);
  if (hasPermission(role, requiredPermission)) {
    return { allowed: true, requiredPermission };
  }

  return {
    allowed: false,
    requiredPermission,
    detail: `Dashboard role ${role} does not have ${requiredPermission}`,
  };
}
