/**
 * tests/api-url.test.mjs
 *
 * Tests the VITE_API_URL → API_BASE URL construction logic used in
 * src/services/api.ts and frontend/src/services/api.ts.
 *
 * We replicate the logic here in pure JS (no bundler/Vite needed) so it
 * can run with `node --test` without any additional tooling.
 */
import test from 'node:test';
import assert from 'node:assert/strict';

/**
 * Replicated from src/services/api.ts — keep in sync if you change the formula.
 */
function buildApiBase(VITE_API_URL) {
  const raw = (VITE_API_URL ?? '').replace(/\/+$/, '');
  return raw ? `${raw}/api` : '/api';
}

// ── Correct Render production URL ────────────────────────────────────────────

test('Production URL: strips trailing slash and appends /api', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com/');
  assert.equal(base, 'https://mailguard-ai-oyh4.onrender.com/api');
});

test('Production URL: no trailing slash — appends /api correctly', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com');
  assert.equal(base, 'https://mailguard-ai-oyh4.onrender.com/api');
});

test('Production URL: strips multiple trailing slashes', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com///');
  assert.equal(base, 'https://mailguard-ai-oyh4.onrender.com/api');
});

// ── No double /api prefix ──────────────────────────────────────────────────

test('Does NOT produce /api/api when URL already contains no /api suffix', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com');
  assert.doesNotMatch(base, /\/api\/api/);
});

test('Endpoint concatenation produces the correct full URL', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com');
  const dashboardUrl = `${base}/dashboard`;
  assert.equal(dashboardUrl, 'https://mailguard-ai-oyh4.onrender.com/api/dashboard');
});

test('Predict endpoint concatenation is correct', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com');
  assert.equal(`${base}/predict`, 'https://mailguard-ai-oyh4.onrender.com/api/predict');
});

test('Model evaluation endpoint concatenation is correct', () => {
  const base = buildApiBase('https://mailguard-ai-oyh4.onrender.com');
  assert.equal(`${base}/model/evaluation`, 'https://mailguard-ai-oyh4.onrender.com/api/model/evaluation');
});

// ── Local dev / unset VITE_API_URL fallback ──────────────────────────────────

test('Fallback: undefined VITE_API_URL gives relative /api for dev proxy', () => {
  assert.equal(buildApiBase(undefined), '/api');
});

test('Fallback: empty string VITE_API_URL gives relative /api', () => {
  assert.equal(buildApiBase(''), '/api');
});

test('Fallback: dev proxy endpoint produces /api/dashboard', () => {
  const base = buildApiBase(undefined);
  assert.equal(`${base}/dashboard`, '/api/dashboard');
});

// ── Edge cases ────────────────────────────────────────────────────────────────

test('Works with custom/staging URLs', () => {
  const base = buildApiBase('https://staging.example.com');
  assert.equal(base, 'https://staging.example.com/api');
});

test('Works with localhost for manual testing', () => {
  const base = buildApiBase('http://localhost:5000');
  assert.equal(base, 'http://localhost:5000/api');
});
