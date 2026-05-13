import { NextRequest } from 'next/server';

function parseList(value?: string) {
  return (value || '')
    .split(',')
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

export function isPasswordLoginEnabled() {
  return process.env.AUTH_PASSWORD_ENABLED !== 'false';
}

export function getPublicOrigin(request?: NextRequest) {
  const configuredRedirect = process.env.GOOGLE_OIDC_REDIRECT_URI;
  if (configuredRedirect) {
    return new URL(configuredRedirect).origin;
  }

  const forwardedHost = request?.headers.get('x-forwarded-host');
  const forwardedProto = request?.headers.get('x-forwarded-proto') || 'https';
  return forwardedHost ? `${forwardedProto}://${forwardedHost}` : request?.nextUrl.origin;
}

export function getGoogleOidcConfig(request?: NextRequest) {
  const origin = getPublicOrigin(request);
  const redirectUri = process.env.GOOGLE_OIDC_REDIRECT_URI || (origin ? `${origin}/api/auth/google/callback` : '');
  const clientId = process.env.GOOGLE_OIDC_CLIENT_ID || '';
  const clientSecret = process.env.GOOGLE_OIDC_CLIENT_SECRET || '';

  return {
    clientId,
    clientSecret,
    redirectUri,
    enabled: Boolean(clientId && clientSecret && redirectUri),
    allowedDomains: parseList(process.env.GOOGLE_OIDC_ALLOWED_DOMAINS),
    allowedEmails: parseList(process.env.GOOGLE_OIDC_ALLOWED_EMAILS),
  };
}
