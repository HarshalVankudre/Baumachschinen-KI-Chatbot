import { test, expect } from '@playwright/test';

/**
 * Authentication Flow E2E Tests
 * Tests the complete user authentication journey:
 * - Registration
 * - Email verification
 * - Login
 * - Logout
 */

test.describe('Authentication Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should display login page', async ({ page }) => {
    await expect(page).toHaveURL(/.*login/);
    await expect(page.getByRole('heading', { name: /sign in/i })).toBeVisible();
  });

  test('should validate login form fields', async ({ page }) => {
    await page.goto('/login');

    // Try to submit empty form
    const loginButton = page.getByRole('button', { name: /sign in|login/i });
    await loginButton.click();

    // Should show validation errors
    await expect(page.getByText(/required|field.*required/i).first()).toBeVisible();
  });

  test('should display error on invalid credentials', async ({ page }) => {
    await page.goto('/login');

    // Fill in invalid credentials
    await page.getByLabel(/username|email/i).fill('invalid@example.com');
    await page.getByLabel(/password/i).fill('wrongpassword');

    // Submit form
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Should show error message
    await expect(page.getByText(/invalid credentials|incorrect password/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test('should navigate to registration page', async ({ page }) => {
    await page.goto('/login');

    // Click on register link
    await page.getByRole('link', { name: /sign up|register|create account/i }).click();

    // Should navigate to registration page
    await expect(page).toHaveURL(/.*register/);
    await expect(page.getByRole('heading', { name: /create account|sign up|register/i })).toBeVisible();
  });

  test('should validate registration form', async ({ page }) => {
    await page.goto('/register');

    // Submit empty form
    await page.getByRole('button', { name: /create account|sign up|register/i }).click();

    // Should show validation errors
    await expect(page.getByText(/required/).first()).toBeVisible();
  });

  test('should validate password strength', async ({ page }) => {
    await page.goto('/register');

    const passwordInput = page.getByLabel(/^password$/i);

    // Type weak password
    await passwordInput.fill('weak');

    // Should show strength indicator
    await expect(page.getByText(/weak|too short/i)).toBeVisible();

    // Type stronger password
    await passwordInput.fill('StrongP@ssw0rd123');

    // Should show strong indicator
    await expect(page.getByText(/strong|good/i)).toBeVisible();
  });

  test('should validate password confirmation match', async ({ page }) => {
    await page.goto('/register');

    await page.getByLabel(/^password$/i).fill('Password123!');
    await page.getByLabel(/confirm.*password/i).fill('DifferentPassword123!');

    // Move focus away to trigger validation
    await page.getByLabel(/username|email/i).click();

    // Should show mismatch error
    await expect(page.getByText(/passwords.*match|passwords.*same/i)).toBeVisible();
  });

  test('should show success message after registration', async ({ page }) => {
    await page.goto('/register');

    const timestamp = Date.now();
    const testEmail = `test${timestamp}@example.com`;
    const testUsername = `testuser${timestamp}`;

    // Fill in registration form
    await page.getByLabel(/email/i).fill(testEmail);
    await page.getByLabel(/username/i).fill(testUsername);
    await page.getByLabel(/^password$/i).fill('TestPassword123!');
    await page.getByLabel(/confirm.*password/i).fill('TestPassword123!');

    // Accept terms if checkbox exists
    const termsCheckbox = page.getByLabel(/terms|agree/i);
    if (await termsCheckbox.isVisible()) {
      await termsCheckbox.check();
    }

    // Submit form
    await page.getByRole('button', { name: /create account|sign up|register/i }).click();

    // Should show success message or redirect to verification page
    await expect(
      page.getByText(/check.*email|verification.*sent|account.*created/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test('should handle email verification', async ({ page }) => {
    // Navigate to verification page with mock token
    await page.goto('/verify-email/mock-token-123');

    // Should show processing or result
    await expect(
      page.getByText(/verifying|verified|pending approval|invalid token/i).first()
    ).toBeVisible({ timeout: 10000 });
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login');

    // Use existing test account (assumes one exists in the system)
    await page.getByLabel(/username|email/i).fill('testuser');
    await page.getByLabel(/password/i).fill('TestPassword123!');

    // Check remember me
    const rememberCheckbox = page.getByLabel(/remember/i);
    if (await rememberCheckbox.isVisible()) {
      await rememberCheckbox.check();
    }

    // Submit form
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Should redirect to chat page
    await expect(page).toHaveURL(/.*chat/, { timeout: 10000 });
  });

  test('should show pending approval message for unverified users', async ({ page }) => {
    await page.goto('/login');

    // Try to login with pending account
    await page.getByLabel(/username|email/i).fill('pendinguser');
    await page.getByLabel(/password/i).fill('Password123!');

    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Should show pending approval message
    await expect(
      page.getByText(/pending.*approval|awaiting.*approval|not.*approved/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test('should logout successfully', async ({ page }) => {
    // First login (skip if already logged in)
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('testuser');
    await page.getByLabel(/password/i).fill('TestPassword123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Wait for navigation
    await page.waitForURL(/.*chat/, { timeout: 10000 });

    // Open user menu
    await page.getByRole('button', { name: /menu|profile|account/i }).click();

    // Click logout
    await page.getByRole('menuitem', { name: /logout|sign out/i }).click();

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
  });

  test('should persist session across page reloads', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('testuser');
    await page.getByLabel(/password/i).fill('TestPassword123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();

    await page.waitForURL(/.*chat/, { timeout: 10000 });

    // Reload page
    await page.reload();

    // Should still be logged in (not redirected to login)
    await expect(page).toHaveURL(/.*chat/);
  });

  test('should protect routes from unauthenticated access', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/chat');

    // Should redirect to login
    await expect(page).toHaveURL(/.*login/, { timeout: 5000 });
  });

  test('should protect admin routes from non-admin users', async ({ page }) => {
    // Login as regular user
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('regularuser');
    await page.getByLabel(/password/i).fill('Password123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();

    await page.waitForURL(/.*chat/, { timeout: 10000 });

    // Try to access admin page
    await page.goto('/admin');

    // Should show forbidden or redirect
    await expect(
      page.getByText(/forbidden|not authorized|access denied/i)
    ).toBeVisible({ timeout: 5000 });
  });
});
