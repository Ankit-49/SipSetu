import { defineConfig } from "@playwright/test";

/**
 * Playwright E2E configuration for SipSetu.
 *
 * Expects the full stack (backend + frontend) to be running locally:
 *   docker compose up
 * or via the dev override:
 *   docker compose -f docker-compose.yml -f docker-compose.override.yml up
 *
 * Environment variables (all optional, shown with defaults):
 *   BASE_URL  — frontend URL   (default: http://localhost:5173)
 *   API_URL   — backend URL    (default: http://localhost:5000/api)
 */
export default defineConfig({
  testDir: "./tests",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 1,
  workers: 1,
  reporter: [["html", { open: "never" }]],

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:5173",
    headless: true,
    screenshot: "only-on-failure",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { browserName: "chromium" },
    },
  ],
});
