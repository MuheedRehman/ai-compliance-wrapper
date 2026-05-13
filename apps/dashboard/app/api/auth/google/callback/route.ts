import { NextRequest, NextResponse } from 'next/server';
import { getGoogleOidcConfig } from '@/lib/auth-config';
import {
  exchangeCodeForTokens,
  GOOGLE_OAUTH_NONCE_COOKIE,
  GOOGLE_OAUTH_STATE_COOKIE,
  isGoogleIdentityAllowed,
  verifyGoogleIdToken,
} from '@/lib/google-oidc';
import { cookieOptions, createSessionToken, SESSION_COOKIE } from '@/lib/server-session';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

function redirectToLogin(request: NextRequest, reason: string) {
  return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(reason)}`, request.url));
}

function clearOauthCookies(response: NextResponse) {
  response.cookies.delete(GOOGLE_OAUTH_STATE_COOKIE);
  response.cookies.delete(GOOGLE_OAUTH_NONCE_COOKIE);
}

export async function GET(request: NextRequest) {
  const expectedState = request.cookies.get(GOOGLE_OAUTH_STATE_COOKIE)?.value;
  const expectedNonce = request.cookies.get(GOOGLE_OAUTH_NONCE_COOKIE)?.value;
  const code = request.nextUrl.searchParams.get('code');
  const state = request.nextUrl.searchParams.get('state');

  if (!code || !state || !expectedState || !expectedNonce || state !== expectedState) {
    const response = redirectToLogin(request, 'google_state_invalid');
    clearOauthCookies(response);
    return response;
  }

  const config = getGoogleOidcConfig(request);
  if (!config.enabled) {
    const response = redirectToLogin(request, 'google_not_configured');
    clearOauthCookies(response);
    return response;
  }

  try {
    const tokens = await exchangeCodeForTokens({
      code,
      clientId: config.clientId,
      clientSecret: config.clientSecret,
      redirectUri: config.redirectUri,
    });
    const identity = await verifyGoogleIdToken(tokens.id_token || '', config.clientId, expectedNonce);

    if (!isGoogleIdentityAllowed(identity, config.allowedDomains, config.allowedEmails)) {
      const response = redirectToLogin(request, 'google_account_not_allowed');
      clearOauthCookies(response);
      return response;
    }

    const response = NextResponse.redirect(new URL('/overview', request.url));
    response.cookies.set(
      SESSION_COOKIE,
      createSessionToken(`google:${identity.sub}`, {
        email: identity.email,
        name: identity.name,
        provider: 'google',
      }),
      cookieOptions(),
    );
    clearOauthCookies(response);
    return response;
  } catch {
    const response = redirectToLogin(request, 'google_login_failed');
    clearOauthCookies(response);
    return response;
  }
}
