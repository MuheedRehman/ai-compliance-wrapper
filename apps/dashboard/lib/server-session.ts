import crypto from 'crypto';

export const SESSION_COOKIE = 'dashboard_session';
const SESSION_TTL_SECONDS = 60 * 60 * 8;

type SessionPayload = {
  sub: string;
  email?: string;
  name?: string;
  provider?: 'password' | 'google';
  iat: number;
  exp: number;
};

type SessionClaims = Pick<SessionPayload, 'email' | 'name' | 'provider'>;

function sessionSecret() {
  return process.env.DASHBOARD_SESSION_SECRET || process.env.DASHBOARD_API_KEY || 'dev-session-secret';
}

function base64url(input: string | Buffer) {
  return Buffer.from(input).toString('base64url');
}

function sign(payload: string) {
  return crypto.createHmac('sha256', sessionSecret()).update(payload).digest('base64url');
}

export function createSessionToken(subject = 'dashboard-admin', claims: Partial<SessionClaims> = {}) {
  const now = Math.floor(Date.now() / 1000);
  const payload = base64url(JSON.stringify({ ...claims, sub: subject, iat: now, exp: now + SESSION_TTL_SECONDS }));
  return `${payload}.${sign(payload)}`;
}

export function verifySessionToken(token?: string | null): SessionPayload | null {
  if (!token) return null;
  const [payload, signature] = token.split('.');
  if (!payload || !signature) return null;

  const expected = sign(payload);
  const providedBuffer = Buffer.from(signature);
  const expectedBuffer = Buffer.from(expected);
  if (providedBuffer.length !== expectedBuffer.length || !crypto.timingSafeEqual(providedBuffer, expectedBuffer)) {
    return null;
  }

  try {
    const parsed = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')) as SessionPayload;
    if (!parsed.exp || parsed.exp < Math.floor(Date.now() / 1000)) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function cookieOptions() {
  return {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax' as const,
    path: '/',
    maxAge: SESSION_TTL_SECONDS,
  };
}

export function isValidDashboardPassword(password: string) {
  const expected = process.env.DASHBOARD_ADMIN_PASSWORD || '';
  if (!expected || !password) return false;
  const expectedBuffer = Buffer.from(expected);
  const providedBuffer = Buffer.from(password);
  return expectedBuffer.length === providedBuffer.length && crypto.timingSafeEqual(providedBuffer, expectedBuffer);
}
