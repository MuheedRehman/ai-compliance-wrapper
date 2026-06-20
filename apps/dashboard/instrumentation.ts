export async function register() {
  const required: Record<string, number> = {
    DASHBOARD_SESSION_SECRET: 32,
    DASHBOARD_API_KEY: 16,
    DASHBOARD_ADMIN_PASSWORD: 8,
  };

  const errors: string[] = [];

  for (const [key, minLength] of Object.entries(required)) {
    const value = process.env[key];
    if (!value) {
      errors.push(`${key} is not set`);
    } else if (value.length < minLength) {
      errors.push(`${key} is too short (min ${minLength} chars)`);
    }
  }

  if (!process.env.BACKEND_URL && !process.env.NEXT_PUBLIC_API_URL) {
    errors.push('BACKEND_URL is not set');
  }

  if (errors.length > 0) {
    const message = `Dashboard startup failed — missing required configuration:\n  ${errors.join('\n  ')}`;
    // In production throw to prevent a misconfigured instance from serving traffic.
    if (process.env.NODE_ENV === 'production') {
      throw new Error(message);
    } else {
      console.warn(`[config] ${message}`);
    }
  }
}
