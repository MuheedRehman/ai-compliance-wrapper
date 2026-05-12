// Auth helpers for the dashboard MVP.
//
// Auth strategy (staging):
//   1. On first load, the API key comes from NEXT_PUBLIC_API_TOKEN env var.
//   2. If a key is stored in localStorage (via the settings UI or manual override),
//      that takes priority over the env var.
//   3. In production, this module would be replaced with OAuth/JWT.

const STORAGE_KEY = 'api_key';

/** Return the active API key. localStorage overrides the env default. */
export function getApiKey(): string {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) return stored;
  }
  return process.env.NEXT_PUBLIC_API_TOKEN || '';
}

/** Persist a user-supplied API key (overrides env default). */
export function setApiKey(key: string): void {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, key);
}

/** Clear the stored key; falls back to env default. */
export function clearApiKey(): void {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(STORAGE_KEY);
}

/** True if any API key is available (stored or env). */
export function isAuthenticated(): boolean {
  return !!getApiKey();
}
