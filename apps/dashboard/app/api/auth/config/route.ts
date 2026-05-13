import { NextRequest, NextResponse } from 'next/server';
import { getGoogleOidcConfig, isPasswordLoginEnabled } from '@/lib/auth-config';

export const dynamic = 'force-dynamic';
export const runtime = 'nodejs';

export async function GET(request: NextRequest) {
  return NextResponse.json({
    googleEnabled: getGoogleOidcConfig(request).enabled,
    passwordEnabled: isPasswordLoginEnabled(),
  });
}
