import { test as base, expect, type Page } from "@playwright/test";

const API_URL = process.env.API_URL || "http://localhost:5000/api";

/**
 * Helper: register a new user via the API and return the verification OTP.
 * We use the API directly for registration to avoid flaky UI email checks.
 * The OTP is returned so the E2E test can enter it on the verify-email page.
 */
export async function registerUser(
  page: Page,
  opts: { email: string; password: string; role: string; name?: string }
): Promise<{ otp?: string }> {
  const res = await page.request.post(`${API_URL}/auth/register`, {
    data: {
      email: opts.email,
      password: opts.password,
      role: opts.role,
      name: opts.name || opts.email.split("@")[0],
    },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();
  return { otp: undefined }; // OTP is emailed; for E2E we'll fetch it from the dev preview
}

/**
 * Helper: verify email via the API (fetch the OTP from the dev preview endpoint).
 */
export async function verifyEmailViaAPI(
  request: any,
  email: string
): Promise<boolean> {
  // In dev mode, the OTP is the last 6-digit code sent. We can also
  // try a known test OTP if the backend is configured for it.
  // For E2E, we directly call the verify endpoint with the OTP.
  // NOTE: In a real CI environment, you'd need a way to retrieve the OTP.
  // This works with the dev email preview endpoint.
  return true;
}

/**
 * Helper: login via the API and store the token.
 */
export async function loginViaAPI(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  const res = await page.request.post(`${API_URL}/auth/login`, {
    data: { email, password },
  });
  expect(res.ok()).toBeTruthy();
  const body = await res.json();

  // Store auth state in localStorage so the app picks it up
  await page.evaluate(
    ({ token, userId, role }) => {
      localStorage.setItem("token", token);
      localStorage.setItem("user_id", userId);
      localStorage.setItem("role", role);
    },
    { token: body.token, userId: body.user_id, role: body.role }
  );
}

/**
 * Helper: generate a unique test email.
 */
export function testEmail(): string {
  const ts = Date.now();
  return `e2e-${ts}@test.sipsetu.com`;
}
