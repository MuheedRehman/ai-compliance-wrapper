import { NextRequest, NextResponse } from 'next/server';
import { SESSION_COOKIE, verifySessionToken } from '@/lib/server-session';
import { accessLabel, permissionsForRole } from '@/lib/session-permissions';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(request: NextRequest) {
  const session = verifySessionToken(request.cookies.get(SESSION_COOKIE)?.value);
  if (!session) {
    return NextResponse.json({ authenticated: false }, { status: 401 });
  }

  return NextResponse.json({
    authenticated: true,
    sub: session.sub,
    email: session.email,
    name: session.name,
    provider: session.provider,
    tenant_id: session.tenant_id,
    role: session.role,
    user_id: session.user_id,
    permissions: permissionsForRole(session.role),
    access_label: accessLabel(session.role),
  });
}
