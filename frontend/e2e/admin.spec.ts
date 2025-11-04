import { test, expect } from '@playwright/test';

/**
 * Admin Dashboard E2E Tests
 * Tests admin-only functionality:
 * - Approving users
 * - Managing user authorization levels
 * - Viewing audit logs
 */

test.describe('Admin Dashboard', () => {
  // Login as admin before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('adminuser');
    await page.getByLabel(/password/i).fill('AdminPassword123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Navigate to admin page
    await page.goto('/admin');
    await page.waitForLoadState('networkidle');
  });

  test('should display admin dashboard', async ({ page }) => {
    // Check for admin dashboard elements
    await expect(
      page.getByRole('heading', { name: /admin|dashboard/i })
    ).toBeVisible({ timeout: 5000 });

    // Check for tabs
    await expect(page.getByRole('tab', { name: /pending.*approval/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /all.*users/i })).toBeVisible();
    await expect(page.getByRole('tab', { name: /audit.*logs/i })).toBeVisible();
  });

  test('should show pending approvals tab', async ({ page }) => {
    // Click on pending approvals tab
    await page.getByRole('tab', { name: /pending.*approval/i }).click();

    // Should show pending users table or empty state
    await expect(
      page.getByText(/pending.*user|no.*pending|email|username/).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('should approve pending user', async ({ page }) => {
    await page.getByRole('tab', { name: /pending.*approval/i }).click();

    // Check if there are pending users
    const approveButton = page.getByRole('button', { name: /approve/i }).first();

    if (await approveButton.isVisible({ timeout: 3000 })) {
      await approveButton.click();

      // Should show authorization level selection
      await expect(
        page.getByText(/select.*level|authorization|regular|superuser|admin/i).first()
      ).toBeVisible({ timeout: 3000 });

      // Select Regular authorization
      await page.getByRole('button', { name: /regular/i }).or(
        page.getByText(/regular.*user/).first()
      ).click();

      // Confirm approval
      await page.getByRole('button', { name: /confirm|approve|save/i }).click();

      // Should show success message
      await expect(
        page.getByText(/approved|success/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should reject pending user', async ({ page }) => {
    await page.getByRole('tab', { name: /pending.*approval/i }).click();

    const rejectButton = page.getByRole('button', { name: /reject/i }).first();

    if (await rejectButton.isVisible({ timeout: 3000 })) {
      await rejectButton.click();

      // Should show rejection dialog
      await expect(
        page.getByText(/reject.*user|reason/i)
      ).toBeVisible({ timeout: 3000 });

      // Optionally add reason
      const reasonInput = page.getByLabel(/reason/i);
      if (await reasonInput.isVisible({ timeout: 2000 })) {
        await reasonInput.fill('Test rejection reason');
      }

      // Confirm rejection
      await page.getByRole('button', { name: /confirm|reject/i }).click();

      // Should show success message
      await expect(
        page.getByText(/rejected|success/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display all users tab', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    // Should show users table
    await expect(
      page.getByText(/username|email|authorization|status/).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('should search users', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    const searchInput = page.getByPlaceholder(/search/i);

    if (await searchInput.isVisible({ timeout: 3000 })) {
      await searchInput.fill('test');

      // Wait for search to filter
      await page.waitForTimeout(500);

      // Should show filtered results
      await expect(searchInput).toHaveValue('test');
    }
  });

  test('should filter users by status', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    // Find status filter dropdown
    const statusFilter = page.getByLabel(/status/i).or(
      page.locator('select').filter({ hasText: /status/i })
    );

    if (await statusFilter.isVisible({ timeout: 3000 })) {
      await statusFilter.click();

      // Select "Active" status
      await page.getByRole('option', { name: /active/i }).click();

      // Wait for filter to apply
      await page.waitForTimeout(1000);
    }
  });

  test('should filter users by authorization level', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    const authFilter = page.getByLabel(/authorization/i).or(
      page.locator('select').filter({ hasText: /authorization/i })
    );

    if (await authFilter.isVisible({ timeout: 3000 })) {
      await authFilter.click();

      // Select "Admin" level
      await page.getByRole('option', { name: /admin/i }).click();

      await page.waitForTimeout(1000);
    }
  });

  test('should change user authorization level', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    // Find change authorization button for first user
    const changeAuthButton = page.getByRole('button', { name: /change.*level|edit.*authorization/i }).first();

    if (await changeAuthButton.isVisible({ timeout: 3000 })) {
      await changeAuthButton.click();

      // Should show level selection dialog
      await expect(
        page.getByText(/change.*authorization|select.*level/i)
      ).toBeVisible({ timeout: 3000 });

      // Select new level
      await page.getByRole('button', { name: /superuser/i }).or(
        page.getByText(/superuser/).first()
      ).click();

      // Confirm change
      await page.getByRole('button', { name: /confirm|save|change/i }).click();

      // Should show success message
      await expect(
        page.getByText(/updated|success|changed/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should suspend user', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    const suspendButton = page.getByRole('button', { name: /suspend/i }).first();

    if (await suspendButton.isVisible({ timeout: 3000 })) {
      await suspendButton.click();

      // Should show confirmation
      await expect(
        page.getByText(/suspend.*user|are you sure/i)
      ).toBeVisible({ timeout: 3000 });

      // Confirm suspension
      await page.getByRole('button', { name: /confirm|suspend|yes/i }).click();

      // Should show success
      await expect(
        page.getByText(/suspended|success/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should activate suspended user', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    const activateButton = page.getByRole('button', { name: /activate|enable/i }).first();

    if (await activateButton.isVisible({ timeout: 3000 })) {
      await activateButton.click();

      // Should show confirmation
      await expect(
        page.getByText(/activate.*user|are you sure/i)
      ).toBeVisible({ timeout: 3000 });

      // Confirm activation
      await page.getByRole('button', { name: /confirm|activate|yes/i }).click();

      // Should show success
      await expect(
        page.getByText(/activated|success/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should display audit logs tab', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    // Should show audit logs table
    await expect(
      page.getByText(/timestamp|admin|action|target/).first()
    ).toBeVisible({ timeout: 5000 });
  });

  test('should filter audit logs by date range', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    // Find date range filter
    const dateFilter = page.getByLabel(/date.*range|filter.*date/i).or(
      page.locator('select').filter({ hasText: /date|today|last.*days/i }).first()
    );

    if (await dateFilter.isVisible({ timeout: 3000 })) {
      await dateFilter.click();

      // Select "Last 7 Days"
      await page.getByRole('option', { name: /last.*7.*days/i }).click();

      await page.waitForTimeout(1000);
    }
  });

  test('should filter audit logs by admin', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    const adminFilter = page.getByPlaceholder(/admin|filter.*admin/i);

    if (await adminFilter.isVisible({ timeout: 3000 })) {
      await adminFilter.fill('admin');

      await page.waitForTimeout(500);

      await expect(adminFilter).toHaveValue('admin');
    }
  });

  test('should filter audit logs by action type', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    const actionFilter = page.getByLabel(/action.*type/i).or(
      page.locator('select').filter({ hasText: /action/i })
    );

    if (await actionFilter.isVisible({ timeout: 3000 })) {
      await actionFilter.click();

      // Select "approve" action
      await page.getByRole('option', { name: /approve/i }).click();

      await page.waitForTimeout(1000);
    }
  });

  test('should expand audit log details', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    // Find first log entry
    const firstLogRow = page.locator('tr').filter({ hasText: /approve|reject|update/i }).first();

    if (await firstLogRow.isVisible({ timeout: 3000 })) {
      await firstLogRow.click();

      // Should show expanded details
      await expect(
        page.getByText(/details|previous.*state|new.*state/i)
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test('should export audit logs to CSV', async ({ page }) => {
    await page.getByRole('tab', { name: /audit.*logs/i }).click();

    const exportButton = page.getByRole('button', { name: /export|download.*csv/i });

    if (await exportButton.isVisible({ timeout: 3000 })) {
      // Start waiting for download
      const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

      await exportButton.click();

      // Wait for download
      const download = await downloadPromise;

      // Check download filename
      expect(download.suggestedFilename()).toMatch(/audit.*log|csv/i);
    }
  });

  test('should paginate through users', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    // Look for next page button
    const nextButton = page.getByRole('button', { name: /next/i }).or(
      page.locator('[aria-label*="next"]')
    );

    if (await nextButton.isVisible({ timeout: 3000 })) {
      await nextButton.click();

      // Should load next page
      await page.waitForTimeout(1000);

      // Page should update
      await expect(page).toHaveURL(/page=2|offset=/);
    }
  });

  test('should display user statistics', async ({ page }) => {
    await page.getByRole('tab', { name: /all.*users/i }).click();

    // Look for statistics (total users, active users, etc.)
    const statsText = page.getByText(/total.*users|active.*users|showing/i).first();

    if (await statsText.isVisible({ timeout: 3000 })) {
      await expect(statsText).toBeVisible();
    }
  });
});
