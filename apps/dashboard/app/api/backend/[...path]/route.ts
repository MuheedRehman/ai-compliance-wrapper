import { NextRequest, NextResponse } from 'next/server';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

type RouteContext = {
  params: {
    path: string[];
  };
};

const backendUrl = () => process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const serverApiKey = () => process.env.DASHBOARD_API_KEY || process.env.NEXT_PUBLIC_API_TOKEN || '';

async function proxy(request: NextRequest, context: RouteContext) {
  const path = context.params.path.join('/');
  const target = new URL(`/${path}${request.nextUrl.search}`, backendUrl());
  const headers = new Headers(request.headers);
  const apiKey = serverApiKey() || headers.get('x-api-key') || '';

  headers.set('x-api-key', apiKey);
  headers.delete('host');
  headers.delete('connection');

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
