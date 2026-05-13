import { NextRequest, NextResponse } from 'next/server';
import { isPasswordLoginEnabled } from '@/lib/auth-config';
import { cookieOptions, createSessionToken, isValidDashboardPassword, SESSION_COOKIE } from '@/lib/server-session';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  if (!isPasswordLoginEnabled()) {
    return NextResponse.json({ detail: 'Password login is disabled' }, { status: 403 });
  }

  const body = await request.json().catch(() => ({}));
  const password = typeof body.password === 'string' ? body.password : '';

  if (!isValidDashboardPassword(password)) {
    return NextResponse.json({ detail: 'Invalid dashboard password' }, { status: 401 });
  }

  const response = NextResponse.json({ ok: true });
  response.cookies.set(
    SESSION_COOKIE,
    createSessionToken('dashboard-admin', {
      email: process.env.DASHBOARD_OWNER_EMAIL || 'dashboard-admin@local',
      provider: 'password',
      tenant_id: process.env.DASHBOARD_TENANT_ID || 'tenant-dashboard-dev',
      role: 'owner',
    }),
    cookieOptions(),
  );
  return response;
}
