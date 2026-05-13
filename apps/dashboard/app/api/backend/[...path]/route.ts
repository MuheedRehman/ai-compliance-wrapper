import { NextRequest, NextResponse } from 'next/server';
import { SESSION_COOKIE, verifySessionToken } from '@/lib/server-session';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type RouteContext = {
  params: {
    path: string[];
  };
};

const backendUrl = () => process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const serverApiKey = () => process.env.DASHBOARD_API_KEY || '';
const backendAuthMode = () => process.env.BACKEND_AUTH_MODE || 'none';

async function getGoogleIdentityToken(audience: string) {
  const response = await fetch(
    `http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=${encodeURIComponent(audience)}`,
    {
      headers: { 'Metadata-Flavor': 'Google' },
      cache: 'no-store',
    },
  );
  if (!response.ok) {
    throw new Error(`Could not obtain backend identity token: ${response.status}`);
  }
  return response.text();
}

async function proxy(request: NextRequest, context: RouteContext) {
  const session = verifySessionToken(request.cookies.get(SESSION_COOKIE)?.value);
  if (!session) {
    return NextResponse.json({ detail: 'Authentication required' }, { status: 401 });
  }

  const path = context.params.path.join('/');
  const backendBaseUrl = backendUrl();
  const target = new URL(`/${path}${request.nextUrl.search}`, backendBaseUrl);
  const headers = new Headers(request.headers);
  const apiKey = serverApiKey();
  if (!apiKey) {
    return NextResponse.json({ detail: 'Dashboard backend credential is not configured' }, { status: 500 });
  }

  headers.set('x-api-key', apiKey);
  headers.delete('authorization');
  headers.delete('host');
  headers.delete('connection');

  if (backendAuthMode() === 'google_id_token') {
    headers.set('authorization', `Bearer ${await getGoogleIdentityToken(backendBaseUrl)}`);
  }

  const response = await fetch(target, {
    method: request.method,
    headers,
    body: request.method === 'GET' || request.method === 'HEAD' ? undefined : await request.arrayBuffer(),
    cache: 'no-store',
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete('content-encoding');
  responseHeaders.delete('content-length');

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}
