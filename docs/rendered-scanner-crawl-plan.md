# Module 1 Rendered SaaS Crawl Upgrade

This document records the scanner rendering strategy so future sessions can continue the work without relying on chat history.

## Why This Exists

The original website scanner fetched raw HTML and parsed readable text. That is fast and still useful for server-rendered SaaS pages, privacy pages, terms, and many trust centers. It misses content when modern SaaS sites use client-side rendering, lazy-loaded sections, accordions, or app-shell frameworks where the initial HTML contains little meaningful text.

The upgraded scanner uses a hybrid strategy:

1. Fetch raw HTML first.
2. Detect JavaScript-dependent or shallow pages.
3. Render only successfully fetched likely-problem pages with headless Chromium through Playwright.
4. Scroll in bounded steps until text/page height stop changing.
5. Safely expand non-destructive controls such as "show more" and accordions.
6. Prefer rendered text only when it materially improves extracted evidence.
7. Record extraction metadata so evidence and reports explain how content was obtained.

## Trigger Rules

Rendered crawling is selective. The scanner does not render missing/404 candidate URLs. A successfully fetched page becomes a render candidate when one or more of these conditions apply:

- The raw page looks like a JavaScript app shell (`__next`, `__nuxt`, `id="root"`, `id="app"`, React/Angular/Vite markers) and has shallow readable text.
- The page has many scripts and little readable text.
- The page is a high-value compliance path such as `/ai`, `/responsible-ai`, `/trust`, `/security`, `/compliance`, `/privacy`, `/dpa`, `/subprocessors`, `/docs`, or `/help`.

This keeps normal static crawling fast while improving quality on modern SaaS pages.

## Smart Scroll Behavior

The renderer:

- Opens the page in headless Chromium.
- Waits for DOM content and briefly for network idle.
- Clicks only safe expansion controls (`button`, `summary`, `[role=button]`, `[aria-expanded=false]`) whose labels match phrases like "show more", "read more", "expand", or "details".
- Scrolls down in viewport-sized steps.
- Waits briefly after each step.
- Stops when both page height and extracted text stop changing for two passes, or when the configured maximum scroll steps is reached.
- Returns to the top before extraction finishes.

This avoids blind infinite scrolling while still triggering lazy-loaded SaaS sections.

## Evidence Metadata

Each source page now records:

- `extraction_mode`: `raw_html`, `rendered_dom`, `rendered_scrolled`, or `rendered_interacted`.
- `render_metadata`: script count, app-shell detection, render reason, rendered text size, scroll steps, safe expansion clicks, render errors, and text gain.

Scanner evidence refs also carry `extraction_mode`, so downstream reports can distinguish raw HTML evidence from rendered/scrolled evidence.

## Runtime Controls

Environment variables:

- `SCANNER_RENDERED_CRAWL_ENABLED`: defaults to `true`. Set to `false` to disable Playwright rendering.
- `SCANNER_RENDER_TIMEOUT_MS`: defaults to `9000`, clamped between 2000 and 20000.
- `SCANNER_RENDER_SCROLL_STEPS`: defaults to `6`, clamped between 0 and 12.

The backend Docker image installs Playwright Chromium so Cloud Run staging can execute rendered crawls. The Cloud Build deploy step assigns the backend service `1Gi` memory because headless Chromium is materially heavier than raw HTTP parsing.

## Fallback Rules

If Playwright is unavailable or rendering fails:

- The scanner falls back to raw HTML when available.
- The page records `render_error`.
- The scan can produce a "Rendered crawl fallback used on some pages" gap so users know scan quality may be limited.

## Next Hardening Ideas

- Add multilingual signal catalogs.
- Add screenshot capture for rendered evidence.
- Add per-domain crawl politeness controls and robots policy notes.
- Add deeper safe interaction support for tabs/accordions with ARIA relationships.
- Add a dashboard badge for extraction mode on scanner source pages.
