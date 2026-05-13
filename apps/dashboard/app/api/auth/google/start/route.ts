import { NextRequest, NextResponse } from 'next/server';
import { getGoogleOidcConfig, getPublicOrigin } from '@/lib/auth-config';
import {
  createOauthValue,
  GOOGLE_OAUTH_NONCE_COOKIE,
  GOOGLE_OAUTH_STATE_COOKIE,
} from '@/lib/google-oidc';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function oauthCookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
    maxAge: 60 * 10,
  };
}

export async function GET(request: NextRequest) {
  const config = getGoogleOidcConfig(request);
  if (!config.enabled) {
    return NextResponse.redirect(new URL('/login?error=google_not_configured', getPublicOrigin(request)));
  }

  const state = createOauthValue();
  const nonce = createOauthValue();
  const url = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  url.searchParams.set('client_id', config.clientId);
  url.searchParams.set('redirect_uri', config.redirectUri);
  url.searchParams.set('response_type', 'code');
  url.searchParams.set('scope', 'openid email profile');
  url.searchParams.set('state', state);
  url.searchParams.set('nonce', nonce);
  url.searchParams.set('prompt', 'select_account');

  const response = NextResponse.redirect(url);
  response.cookies.set(GOOGLE_OAUTH_STATE_COOKIE, state, oauthCookieOptions());
  response.cookies.set(GOOGLE_OAUTH_NONCE_COOKIE, nonce, oauthCookieOptions());
  return response;
}
