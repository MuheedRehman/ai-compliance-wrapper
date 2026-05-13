import { defineConfig, devices } from '@playwright/test';

const dashboardUrl = process.env.DASHBOARD_URL || 'http://localhost:3000';
const traceMode = process.env.CI ? 'retain-on-failure' : 'on-first-retry';

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: {
    timeout: 10_000,
  },
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [['list'], ['html', { open: 'never' }]] : [['list']],
  use: {
    baseURL: dashboardUrl,
    viewport: { width: 1440, height: 1000 },
    actionTimeout: 15_000,
    navigationTimeout: 60_000,
    trace: traceMode,
    screenshot: 'only-on-failure',
    video: process.env.PLAYWRIGHT_VIDEO ? 'retain-on-failure' : 'off',
    launchOptions: process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH }
      : undefined,
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: process.env.E2E_START_SERVER
    ? {
        command: 'npm run dev',
        url: dashboardUrl,
        reuseExistingServer: !process.env.CI,
        timeout: 120_000,
      }
    : undefined,
});
