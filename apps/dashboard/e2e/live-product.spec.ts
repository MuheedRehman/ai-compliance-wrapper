import { expect, type APIRequestContext, type Locator, type Page, test } from '@playwright/test';

const DASHBOARD_PASSWORD = process.env.DASHBOARD_PASSWORD || process.env.DASHBOARD_ADMIN_PASSWORD || '';

const routes = [
  '/',
  '/overview',
  '/systems',
  '/features',
  '/reviews',
  '/evidence',
  '/controls',
  '/intake',
  '/scanner',
  '/fria',
  '/oversight',
  '/incidents',
  '/reports',
  '/runtime',
  '/billing',
];

const apiChecks = [
  '/v1/ai-systems',
  '/v1/features',
  '/v1/review-tasks',
  '/v1/logs',
  '/v1/billing/subscription',
  '/v1/billing/entitlements',
  '/v1/intake',
  '/v1/website-scans',
  '/v1/obligations/fria',
  '/v1/obligations/oversight',
  '/v1/obligations/incidents',
  '/v1/reports',
  '/v1/compliance/controls',
  '/v1/compliance/scorecard',
];

const visibleErrorPhrases = [
  'API Error',
  'Failed to load',
  'Failed to submit',
  'Failed to generate',
  'Request failed',
  'Invalid or revoked API key',
  'Missing API key',
  'Service Error',
  'Access Restricted',
  'Application error',
];

test.describe.configure({ mode: 'serial' });

test('backend API preflight endpoints are healthy', async ({ request }) => {
  await loginRequest(request);

  for (const path of apiChecks) {
    const response = await request.get(`/api/backend${path}`);

    expect(response.ok(), `${path} returned ${response.status()}: ${(await response.text()).slice(0, 240)}`).toBeTruthy();
  }
});

test('main navigation pages render without visible API failures', async ({ page }) => {
  await loginPage(page);
  const diagnostics = installPageDiagnostics(page);
  const buttonInventory: Record<string, { text: string; disabled: boolean }[]> = {};

  for (const route of routes) {
    await gotoAndSettle(page, route);
    buttonInventory[route] = await inventoryButtons(page);
    await expectNoVisibleErrors(page, route);
    await clickSafeButtons(page, route);
    await expectNoVisibleErrors(page, route);
  }

  await test.info().attach('button-inventory.json', {
    body: JSON.stringify(buttonInventory, null, 2),
    contentType: 'application/json',
  });

  diagnostics.expectClean();
});

test('critical product workflows create records and run governed runtime', async ({ page }) => {
  await loginPage(page);
  const diagnostics = installPageDiagnostics(page);
  const stamp = Date.now();

  await gotoAndSettle(page, '/systems');
  await page.getByRole('button', { name: /register system/i }).click();
  await page.locator('input[placeholder="System name"]').fill(`E2E System ${stamp}`);
  await page.locator('input[placeholder="Short description"]').fill('Created by product E2E automation');
  await page.getByRole('button', { name: /create system/i }).click();
  await expect(page.getByText(`E2E System ${stamp}`)).toBeVisible();

  await gotoAndSettle(page, '/features');
  await page.getByRole('button', { name: /create feature/i }).click();
  await page.locator('input[placeholder="feature_id"]').fill(`e2e_feature_${stamp}`);
  await page.locator('input[placeholder="Feature name"]').fill(`E2E Feature ${stamp}`);
  await page.locator('input[placeholder="owner@company.com"]').fill(`qa-feature-${stamp}@example.com`);
  await selectFirstAvailableOption(page.locator('select').first(), false);
  await page.getByRole('button', { name: /^create$/i }).click();
  await expect(page.getByText(`E2E Feature ${stamp}`)).toBeVisible();

  await gotoAndSettle(page, '/scanner');
  await page.getByRole('button', { name: /^new scan$/i }).first().click();
  await page.locator('input[placeholder="https://example-saas.com"]').fill('https://example.com');
  await page.getByRole('button', { name: /run scanner/i }).click();
  await expect(page).toHaveURL(/\/scanner\/scan-/);
  await expect(page.getByText(/Preliminary Classification/i)).toBeVisible();
  await page.getByRole('button', { name: /create system \+ intake/i }).click();
  await expect(page.getByText(/converted/i)).toBeVisible();

  await gotoAndSettle(page, '/controls');
  await page.getByRole('button', { name: /seed baseline/i }).first().click();
  await gotoAndSettle(page, '/controls');
  await expect(page.locator('tbody tr').first()).toBeVisible();
  const ownerInput = page.locator('input[placeholder="owner@company.com"]').first();
  if (await ownerInput.isVisible()) {
    await ownerInput.fill(`qa-control-${stamp}@example.com`);
    const statusSelect = page.locator('tbody select').first();
    if (await statusSelect.isVisible()) {
      await statusSelect.selectOption('in_progress');
    }
    await page.getByRole('button', { name: /save/i }).first().click();
  }

  await gotoAndSettle(page, '/intake');
  const startAssessment = page.getByRole('button', { name: /new assessment|start assessment/i }).first();
  if (await startAssessment.isVisible()) {
    await startAssessment.click();
  }
  await page.locator('input[placeholder*="Hiring Tool"]').fill(`E2E Assessment ${stamp}`);
  await page.getByRole('button', { name: /^next/i }).click();
  await page.getByRole('button', { name: /deployer/i }).click();
  await page.getByRole('button', { name: /^next/i }).click();
  await page.getByRole('button', { name: /High-Risk/i }).click();
  await page.getByRole('button', { name: /Transparency Risk/i }).click();
  await page.getByRole('button', { name: /^next/i }).click();
  await page.getByRole('button', { name: /generate classification/i }).click();
  await expect(page).toHaveURL(/\/intake\//);

  await gotoAndSettle(page, '/oversight');
  await page.getByRole('button', { name: /add oversight/i }).click();
  await selectFirstAvailableOption(page.locator('select[required]').first());
  await page.locator('input[type="email"]').fill(`qa-oversight-${stamp}@example.com`);
  await page.getByRole('button', { name: /create assignment/i }).click();
  await expect(page.getByText(`qa-oversight-${stamp}@example.com`)).toBeVisible();

  await gotoAndSettle(page, '/incidents');
  await page.getByRole('button', { name: /report incident/i }).click();
  await selectFirstAvailableOption(page.locator('select[required]').first());
  await page.locator('textarea').fill(`E2E incident ${stamp}`);
  await page.getByRole('button', { name: /submit report/i }).click();
  await expect(page.getByText(`E2E incident ${stamp}`)).toBeVisible();

  await gotoAndSettle(page, '/reports');
  const newReport = page.getByRole('button', { name: /new report|start assessment/i }).first();
  if (await newReport.isVisible()) {
    await newReport.click();
  }
  const titleInput = page.locator('input[placeholder*="Q3 Governance Review"]');
  if (await titleInput.isVisible()) {
    await titleInput.fill(`E2E Report ${stamp}`);
  }
  await selectFirstAvailableOption(page.locator('select').nth(1), false);
  await page.getByRole('button', { name: /generate compliance report/i }).click();
  await expect(page.getByText(`E2E Report ${stamp}`)).toBeVisible();

  await gotoAndSettle(page, '/runtime');
  await page.getByRole('button', { name: /execute governed request/i }).click();
  await expect(page.getByText(/allow|completed|governed response/i)).toBeVisible();
  await expectNoVisibleErrors(page, '/runtime');

  diagnostics.expectClean();
});

async function gotoAndSettle(page: Page, route: string) {
  await page.goto(route, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('networkidle', { timeout: 6_000 }).catch(() => undefined);
  await page.waitForTimeout(400);
}

async function loginRequest(request: APIRequestContext) {
  test.skip(!DASHBOARD_PASSWORD, 'DASHBOARD_PASSWORD or DASHBOARD_ADMIN_PASSWORD is required for product E2E tests.');
  const response = await request.post('/api/auth/login', {
    data: { password: DASHBOARD_PASSWORD },
  });
  expect(response.ok(), `Login failed with ${response.status()}: ${await response.text()}`).toBeTruthy();
}

async function loginPage(page: Page) {
  test.skip(!DASHBOARD_PASSWORD, 'DASHBOARD_PASSWORD or DASHBOARD_ADMIN_PASSWORD is required for product E2E tests.');
  const response = await page.request.post('/api/auth/login', {
    data: { password: DASHBOARD_PASSWORD },
  });
  expect(response.ok(), `Login failed with ${response.status()}: ${await response.text()}`).toBeTruthy();
  await page.goto('/overview', { waitUntil: 'domcontentloaded' });
  await expect(page).toHaveURL(/\/overview/);
  await expect(page.locator('body')).toContainText('Dashboard');
}

async function expectNoVisibleErrors(page: Page, route: string) {
  const text = (await page.locator('body').innerText()).replace(/\s+/g, ' ');
  for (const phrase of visibleErrorPhrases) {
    expect(text, `${route} contains visible error phrase: ${phrase}`).not.toContain(phrase);
  }
}

async function inventoryButtons(page: Page) {
  return page.locator('button').evaluateAll((buttons) =>
    buttons
      .filter((button) => {
        const rect = button.getBoundingClientRect();
        const style = window.getComputedStyle(button);
        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';
      })
      .map((button) => ({
        text: (button.innerText || button.getAttribute('aria-label') || button.title || '').replace(/\s+/g, ' ').trim(),
        disabled: (button as HTMLButtonElement).disabled,
      })),
  );
}

async function clickSafeButtons(page: Page, route: string) {
  const unsafe =
    /delete|remove|submit|generate|execute|upgrade|portal|report incident|add oversight|new report|new assessment|start assessment|create assignment|seed baseline|save|cancel/i;
  const buttons = page.locator('button');
  const count = await buttons.count();

  for (let index = 0; index < count; index += 1) {
    const button = buttons.nth(index);
    if (!(await button.isVisible().catch(() => false))) continue;
    if (await button.isDisabled().catch(() => true)) continue;

    const label = ((await button.innerText().catch(() => '')) || '').replace(/\s+/g, ' ').trim();
    if (!label || unsafe.test(label)) continue;

    await button.click({ timeout: 5_000 });
    await page.waitForTimeout(150);
    await expectNoVisibleErrors(page, route);
  }
}

async function selectFirstAvailableOption(select: Locator, required = true) {
  if (!(await select.isVisible().catch(() => false))) {
    expect(required, 'Required select is not visible').toBeFalsy();
    return;
  }

  const values = await select.locator('option').evaluateAll((options) =>
    options.map((option) => (option as HTMLOptionElement).value).filter(Boolean),
  );

  if (!values.length) {
    expect(required, 'Required select has no selectable options').toBeFalsy();
    return;
  }

  await select.selectOption(values[0]);
}

function installPageDiagnostics(page: Page) {
  const httpErrors: string[] = [];
  const requestFailures: string[] = [];
  const consoleErrors: string[] = [];

  page.on('response', (response) => {
    const status = response.status();
    const url = response.url();
    if (status >= 400 && !url.includes('/favicon.ico')) {
      httpErrors.push(`${status} ${url}`);
    }
  });

  page.on('requestfailed', (request) => {
    const failure = request.failure()?.errorText || 'unknown failure';
    if (!failure.includes('net::ERR_ABORTED')) {
      requestFailures.push(`${request.method()} ${request.url()} ${failure}`);
    }
  });

  page.on('console', (message) => {
    const text = message.text();
    const browserStatic404 = /Failed to load resource: the server responded with a status of 404/.test(text);
    const rscPrefetchFallback = /Failed to fetch RSC payload/.test(text);
    if (message.type() === 'error' && !text.includes('favicon') && !browserStatic404 && !rscPrefetchFallback) {
      consoleErrors.push(text);
    }
  });

  return {
    expectClean() {
      expect(httpErrors, `HTTP errors:\n${httpErrors.join('\n')}`).toEqual([]);
      expect(requestFailures, `Request failures:\n${requestFailures.join('\n')}`).toEqual([]);
      expect(consoleErrors, `Console errors:\n${consoleErrors.join('\n')}`).toEqual([]);
    },
  };
}
