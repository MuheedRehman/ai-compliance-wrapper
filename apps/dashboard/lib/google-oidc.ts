import crypto from 'crypto';

export const GOOGLE_OAUTH_STATE_COOKIE = 'dashboard_google_oauth_state';
export const GOOGLE_OAUTH_NONCE_COOKIE = 'dashboard_google_oauth_nonce';

type TokenResponse = {
  access_token?: string;
  id_token?: string;
  error?: string;
  error_description?: string;
};

export type GoogleIdentity = {
  sub: string;
  email: string;
  emailVerified: boolean;
  name?: string;
  hostedDomain?: string;
};

type TokenInfoResponse = {
  aud?: string;
  sub?: string;
  email?: string;
  email_verified?: string | boolean;
  name?: string;
  hd?: string;
  nonce?: string;
  exp?: string;
  error?: string;
  error_description?: string;
};

export function createOauthValue() {
  return crypto.randomBytes(32).toString('base64url');
}

export async function exchangeCodeForTokens(input: {
  code: string;
  clientId: string;
  clientSecret: string;
  redirectUri: string;
}) {
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      code: input.code,
      client_id: input.clientId,
      client_secret: input.clientSecret,
      redirect_uri: input.redirectUri,
      grant_type: 'authorization_code',
    }),
  });

  const tokens = (await response.json().catch(() => ({}))) as TokenResponse;
  if (!response.ok || !tokens.id_token) {
    throw new Error(tokens.error_description || tokens.error || 'Google token exchange failed');
  }

  return tokens;
}

export async function verifyGoogleIdToken(idToken: string, expectedAudience: string, expectedNonce: string) {
  const response = await fetch(`https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(idToken)}`);
  const tokenInfo = (await response.json().catch(() => ({}))) as TokenInfoResponse;

  if (!response.ok || tokenInfo.error) {
    throw new Error(tokenInfo.error_description || tokenInfo.error || 'Google token validation failed');
  }

  if (tokenInfo.aud !== expectedAudience) {
    throw new Error('Google token audience mismatch');
  }

  if (tokenInfo.nonce && tokenInfo.nonce !== expectedNonce) {
    throw new Error('Google token nonce mismatch');
  }

  const exp = Number(tokenInfo.exp || 0);
  if (!exp || exp < Math.floor(Date.now() / 1000)) {
    throw new Error('Google token is expired');
  }

  const emailVerified = tokenInfo.email_verified === true || tokenInfo.email_verified === 'true';
  if (!tokenInfo.sub || !tokenInfo.email || !emailVerified) {
    throw new Error('Google account email is not verified');
  }

  return {
    sub: tokenInfo.sub,
    email: tokenInfo.email.toLowerCase(),
    emailVerified,
    name: tokenInfo.name,
    hostedDomain: tokenInfo.hd?.toLowerCase(),
  } satisfies GoogleIdentity;
}

export function isGoogleIdentityAllowed(
  identity: GoogleIdentity,
  allowedDomains: string[],
  allowedEmails: string[],
) {
  if (!allowedDomains.length && !allowedEmails.length) return true;
  if (allowedEmails.includes(identity.email)) return true;

  const emailDomain = identity.email.split('@')[1]?.toLowerCase();
  return allowedDomains.some((domain) => domain === identity.hostedDomain || domain === emailDomain);
}
