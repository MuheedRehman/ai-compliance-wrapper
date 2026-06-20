import { NextRequest, NextResponse } from 'next/server';
import { isPasswordLoginEnabled } from '@/lib/auth-config';
import { backendServiceFetch } from '@/lib/backend-service';
import { cookieOptions, createSessionToken, isValidDashboardPassword, SESSION_COOKIE } from '@/lib/server-session';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type LoginResolveResponse = {
  allowed: boolean;
  reason?: string | null;
  tenant_id: string;
  user?: {
    id: string;
    email: string;
    name?: string | null;
    role: 'owner' | 'admin' | 'reviewer' | 'auditor' | 'viewer';
  } | null;
};

export async function POST(request: NextRequest) {
  if (!isPasswordLoginEnabled()) {
    return NextResponse.json({ detail: 'Password login is disabled' }, { status: 403 });
  }

  const body = await request.json().catch(() => ({}));
  const password = typeof body.password === 'string' ? body.password : '';

  if (!isValidDashboardPassword(password)) {
    return NextResponse.json({ detail: 'Invalid dashboard password' }, { status: 401 });
  }

  const email = process.env.DASHBOARD_OWNER_EMAIL || 'dashboard-admin@local';
  const name = process.env.DASHBOARD_OWNER_NAME || 'Dashboard Owner';
  const accessResponse = await backendServiceFetch('/v1/tenant-admin/login/resolve', {
    method: 'POST',
    headers: {
      'x-forwarded-for': request.headers.get('x-forwarded-for') || '',
      'user-agent': request.headers.get('user-agent') || '',
    },
    body: JSON.stringify({
      email,
      name,
      provider: 'password',
      ip_address: request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || undefined,
      user_agent: request.headers.get('user-agent') || undefined,
    }),
  });

  if (!accessResponse.ok) {
    console.error({ event: 'login_policy_failure', status: accessResponse.status });
    return NextResponse.json({ detail: 'Tenant login policy check failed' }, { status: 403 });
  }

  const access = (await accessResponse.json()) as LoginResolveResponse;
  if (!access.allowed || !access.user) {
    return NextResponse.json({ detail: access.reason || 'Tenant login policy denied access' }, { status: 403 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(
    SESSION_COOKIE,
    createSessionToken(`password:${access.user.id}`, {
      email: access.user.email,
      name: access.user.name || name,
      provider: 'password',
      tenant_id: access.tenant_id,
      role: access.user.role,
      user_id: access.user.id,
    }),
    cookieOptions(),
  );
  return response;
}
