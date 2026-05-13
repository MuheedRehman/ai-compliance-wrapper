export const backendUrl = () => process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const serverApiKey = () => process.env.DASHBOARD_API_KEY || '';
export const backendAuthMode = () => process.env.BACKEND_AUTH_MODE || 'none';

export async function getGoogleIdentityToken(audience: string) {
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

export async function backendServiceFetch(path: string, init: RequestInit = {}) {
  const apiKey = serverApiKey();
  if (!apiKey) {
    throw new Error('Dashboard backend credential is not configured');
  }

  const baseUrl = backendUrl();
  const target = new URL(path, baseUrl);
  const headers = new Headers(init.headers);
  headers.set('x-api-key', apiKey);
  if (init.body && !headers.has('content-type')) {
    headers.set('content-type', 'application/json');
  }
  if (backendAuthMode() === 'google_id_token') {
    headers.set('authorization', `Bearer ${await getGoogleIdentityToken(baseUrl)}`);
  }

  return fetch(target, {
    ...init,
    headers,
    cache: 'no-store',
  });
}
