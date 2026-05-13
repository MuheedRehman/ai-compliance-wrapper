import { NextRequest, NextResponse } from 'next/server';
import { getGoogleOidcConfig, getPublicOrigin } from '@/lib/auth-config';
import { backendServiceFetch } from '@/lib/backend-service';
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
  return NextResponse.redirect(new URL(`/login?error=${encodeURIComponent(reason)}`, getPublicOrigin(request)));
}

function clearOauthCookies(response: NextResponse) {
  response.cookies.delete(GOOGLE_OAUTH_STATE_COOKIE);
  response.cookies.delete(GOOGLE_OAUTH_NONCE_COOKIE);
}

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

    const accessResponse = await backendServiceFetch('/v1/tenant-admin/login/resolve', {
      method: 'POST',
      headers: {
        'x-forwarded-for': request.headers.get('x-forwarded-for') || '',
        'user-agent': request.headers.get('user-agent') || '',
      },
      body: JSON.stringify({
        email: identity.email,
        name: identity.name,
        provider: 'google',
        ip_address: request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || undefined,
        user_agent: request.headers.get('user-agent') || undefined,
      }),
    });

    if (!accessResponse.ok) {
      console.error('Google login tenant policy failed', accessResponse.status, await accessResponse.text());
      const response = redirectToLogin(request, 'google_login_failed');
      clearOauthCookies(response);
      return response;
    }

    const access = (await accessResponse.json()) as LoginResolveResponse;
    if (!access.allowed || !access.user) {
      const response = redirectToLogin(request, access.reason || 'google_account_not_allowed');
      clearOauthCookies(response);
      return response;
    }

    const response = NextResponse.redirect(new URL('/overview', getPublicOrigin(request)));
    response.cookies.set(
      SESSION_COOKIE,
      createSessionToken(`google:${identity.sub}`, {
        email: access.user.email || identity.email,
        name: access.user.name || identity.name,
        provider: 'google',
        tenant_id: access.tenant_id,
        role: access.user.role,
        user_id: access.user.id,
      }),
      cookieOptions(),
    );
    clearOauthCookies(response);
    return response;
  } catch (error) {
    console.error('Google login failed', error instanceof Error ? error.message : 'Unknown error');
    const response = redirectToLogin(request, 'google_login_failed');
    clearOauthCookies(response);
    return response;
  }
}
