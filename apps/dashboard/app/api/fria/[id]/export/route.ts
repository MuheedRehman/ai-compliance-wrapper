import { NextRequest, NextResponse } from 'next/server';
import { backendServiceFetch } from '@/lib/backend-service';
import { SESSION_COOKIE, verifySessionToken } from '@/lib/server-session';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } },
) {
  const session = verifySessionToken(request.cookies.get(SESSION_COOKIE)?.value);
  if (!session) {
    return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
  }

  const upstream = await backendServiceFetch(`/v1/obligations/fria/${params.id}/export`);

  const headers = new Headers();
  const contentType = upstream.headers.get('content-type');
  const contentDisposition = upstream.headers.get('content-disposition');
  if (contentType) headers.set('content-type', contentType);
  if (contentDisposition) headers.set('content-disposition', contentDisposition);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers,
  });
}
