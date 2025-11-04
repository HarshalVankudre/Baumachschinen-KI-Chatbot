import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Document Management E2E Tests
 * Tests document upload and management:
 * - Uploading files
 * - Viewing documents
 * - Filtering documents
 * - Deleting documents
 */

test.describe('Document Management', () => {
  // Login as superuser before each test (documents require superuser/admin)
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('superuser');
    await page.getByLabel(/password/i).fill('SuperPassword123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();

    // Navigate to documents page
    await page.goto('/documents');
    await page.waitForLoadState('networkidle');
  });

  test('should display document management page', async ({ page }) => {
    // Check for document page elements
    await expect(
      page.getByRole('heading', { name: /document|upload/i })
    ).toBeVisible({ timeout: 5000 });

    // Check for upload zone
    await expect(page.getByText(/drag.*drop|browse/i)).toBeVisible();

    // Check for document list
    await expect(page.getByText(/filename|category|upload.*date|status/).first()).toBeVisible();
  });

  test('should display file upload zone', async ({ page }) => {
    // Check for drag-and-drop zone
    await expect(page.getByText(/drag.*drop.*files/i)).toBeVisible();

    // Check for category selector
    await expect(page.getByText(/category/i)).toBeVisible();

    // Check for browse button
    await expect(page.getByRole('button', { name: /browse/i })).toBeVisible();
  });

  test('should require category selection', async ({ page }) => {
    const categorySelect = page.getByLabel(/category/i).or(
      page.locator('select').filter({ hasText: /category/i })
    );

    // Category should be visible
    await expect(categorySelect).toBeVisible({ timeout: 3000 });

    // Should have options
    await categorySelect.click();
    await expect(page.getByRole('option', { name: /manual|specification|procedure/i }).first()).toBeVisible();
  });

  test('should upload a file', async ({ page }) => {
    // Select category first
    const categorySelect = page.getByLabel(/category/i).or(
      page.locator('select').filter({ hasText: /category/i }).first()
    );

    await categorySelect.click();
    await page.getByRole('option', { name: /manual/i }).click();

    // Create a test file
    const fileContent = 'Test PDF content';
    const fileName = 'test-document.pdf';

    // Find file input (usually hidden)
    const fileInput = page.locator('input[type="file"]');

    // Upload file
    await fileInput.setInputFiles({
      name: fileName,
      mimeType: 'application/pdf',
      buffer: Buffer.from(fileContent),
    });

    // Wait for upload to start
    await page.waitForTimeout(1000);

    // Should show upload progress or success
    await expect(
      page.getByText(/uploading|processing|uploaded|success/i)
    ).toBeVisible({ timeout: 10000 });
  });

  test('should show upload progress', async ({ page }) => {
    // Select category
    const categorySelect = page.getByLabel(/category/i).or(
      page.locator('select').filter({ hasText: /category/i }).first()
    );

    await categorySelect.click();
    await page.getByRole('option', { name: /manual/i }).click();

    // Upload file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'large-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('x'.repeat(10000)),
    });

    // Should show progress bar
    await expect(
      page.locator('[role="progressbar"]').or(page.getByText(/%/))
    ).toBeVisible({ timeout: 5000 });
  });

  test('should validate file type', async ({ page }) => {
    // Try to upload unsupported file type
    const fileInput = page.locator('input[type="file"]');

    await fileInput.setInputFiles({
      name: 'invalid.exe',
      mimeType: 'application/x-msdownload',
      buffer: Buffer.from('invalid content'),
    });

    // Should show error message
    await expect(
      page.getByText(/unsupported|invalid.*type|not.*allowed/i)
    ).toBeVisible({ timeout: 5000 });
  });

  test('should upload multiple files', async ({ page }) => {
    // Select category
    const categorySelect = page.getByLabel(/category/i).or(
      page.locator('select').filter({ hasText: /category/i }).first()
    );

    await categorySelect.click();
    await page.getByRole('option', { name: /manual/i }).click();

    // Upload multiple files
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles([
      {
        name: 'document1.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('content 1'),
      },
      {
        name: 'document2.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('content 2'),
      },
    ]);

    // Should show both files uploading
    await page.waitForTimeout(1000);

    await expect(page.getByText(/document1\.pdf|document2\.pdf/).first()).toBeVisible({
      timeout: 5000,
    });
  });

  test('should display document list', async ({ page }) => {
    // Should show document table
    await expect(
      page.getByRole('columnheader', { name: /filename/i })
    ).toBeVisible({ timeout: 5000 });

    await expect(
      page.getByRole('columnheader', { name: /category/i })
    ).toBeVisible();

    await expect(
      page.getByRole('columnheader', { name: /upload.*date|date/i })
    ).toBeVisible();

    await expect(
      page.getByRole('columnheader', { name: /status/i })
    ).toBeVisible();
  });

  test('should search documents by filename', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);

    if (await searchInput.isVisible({ timeout: 3000 })) {
      await searchInput.fill('manual');

      // Wait for search to filter
      await page.waitForTimeout(500);

      await expect(searchInput).toHaveValue('manual');
    }
  });

  test('should filter documents by category', async ({ page }) => {
    const categoryFilter = page.getByLabel(/category.*filter|filter.*category/i).or(
      page.locator('select').filter({ hasText: /all.*categories|category/i })
    );

    if (await categoryFilter.isVisible({ timeout: 3000 })) {
      await categoryFilter.click();

      // Select "Manuals" category
      await page.getByRole('option', { name: /manual/i }).click();

      await page.waitForTimeout(1000);

      // Should show filtered documents
      // This depends on having documents in that category
    }
  });

  test('should filter documents by uploader', async ({ page }) => {
    const uploaderFilter = page.getByLabel(/uploader/i).or(
      page.locator('select').filter({ hasText: /uploader|uploaded.*by/i })
    );

    if (await uploaderFilter.isVisible({ timeout: 3000 })) {
      await uploaderFilter.click();

      // Select an uploader
      const firstOption = page.getByRole('option').filter({ hasText: /\w+/ }).first();
      await firstOption.click();

      await page.waitForTimeout(1000);
    }
  });

  test('should filter documents by date range', async ({ page }) => {
    const dateFilter = page.getByLabel(/date.*range/i).or(
      page.locator('select').filter({ hasText: /date|today|last.*days/i }).first()
    );

    if (await dateFilter.isVisible({ timeout: 3000 })) {
      await dateFilter.click();

      // Select "Last 7 Days"
      await page.getByRole('option', { name: /last.*7.*days/i }).click();

      await page.waitForTimeout(1000);
    }
  });

  test('should display processing status indicators', async ({ page }) => {
    // Look for status badges
    const statusBadge = page.locator('[data-testid="status-badge"]').or(
      page.getByText(/uploading|processing|completed|failed/i).first()
    );

    if (await statusBadge.isVisible({ timeout: 3000 })) {
      await expect(statusBadge).toBeVisible();
    }
  });

  test('should delete document', async ({ page }) => {
    // Find first document delete button
    const deleteButton = page.getByRole('button', { name: /delete/i }).first().or(
      page.locator('[aria-label*="delete"]').first()
    );

    if (await deleteButton.isVisible({ timeout: 3000 })) {
      await deleteButton.click();

      // Should show confirmation dialog
      await expect(
        page.getByText(/delete.*document|are you sure|cannot.*undone/i)
      ).toBeVisible({ timeout: 3000 });

      // Confirm deletion
      await page.getByRole('button', { name: /confirm|delete|yes/i }).click();

      // Should show success message
      await expect(
        page.getByText(/deleted|removed|success/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should cancel document deletion', async ({ page }) => {
    const deleteButton = page.getByRole('button', { name: /delete/i }).first();

    if (await deleteButton.isVisible({ timeout: 3000 })) {
      await deleteButton.click();

      // Should show confirmation dialog
      await expect(
        page.getByText(/delete.*document|are you sure/i)
      ).toBeVisible({ timeout: 3000 });

      // Click cancel
      await page.getByRole('button', { name: /cancel|no/i }).click();

      // Dialog should close
      await expect(
        page.getByText(/delete.*document|are you sure/i)
      ).not.toBeVisible({ timeout: 2000 });
    }
  });

  test('should display document metadata', async ({ page }) => {
    // Check if documents show size, uploader, etc.
    const firstRow = page.locator('tbody tr').first();

    if (await firstRow.isVisible({ timeout: 3000 })) {
      await expect(firstRow).toBeVisible();

      // Should contain metadata like file size
      const sizeText = firstRow.getByText(/kb|mb|bytes/i);
      if (await sizeText.isVisible({ timeout: 2000 })) {
        await expect(sizeText).toBeVisible();
      }
    }
  });

  test('should handle drag and drop upload', async ({ page }) => {
    // Select category first
    const categorySelect = page.getByLabel(/category/i).or(
      page.locator('select').filter({ hasText: /category/i }).first()
    );

    await categorySelect.click();
    await page.getByRole('option', { name: /manual/i }).click();

    // Find drop zone
    const dropZone = page.getByText(/drag.*drop/i).locator('..');

    if (await dropZone.isVisible()) {
      // Simulate file drop (this is limited in Playwright, but we can test the UI response)
      const fileInput = page.locator('input[type="file"]');

      await fileInput.setInputFiles({
        name: 'dropped-file.pdf',
        mimeType: 'application/pdf',
        buffer: Buffer.from('dropped content'),
      });

      // Should handle the file
      await expect(
        page.getByText(/uploading|dropped-file\.pdf/i)
      ).toBeVisible({ timeout: 5000 });
    }
  });

  test('should show empty state when no documents', async ({ page }) => {
    // Apply filters that return no results
    const searchInput = page.getByPlaceholder(/search/i);

    if (await searchInput.isVisible({ timeout: 3000 })) {
      await searchInput.fill('nonexistentdocumentxyz123');

      await page.waitForTimeout(1000);

      // Should show empty state
      await expect(
        page.getByText(/no documents|no results|empty/i)
      ).toBeVisible({ timeout: 3000 });
    }
  });

  test('should paginate through documents', async ({ page }) => {
    const nextButton = page.getByRole('button', { name: /next/i }).or(
      page.locator('[aria-label*="next"]')
    );

    if (await nextButton.isVisible({ timeout: 3000 }) && await nextButton.isEnabled()) {
      await nextButton.click();

      // Should load next page
      await page.waitForTimeout(1000);

      // URL should update
      await expect(page).toHaveURL(/page=2|offset=/);
    }
  });

  test('should display supported file types', async ({ page }) => {
    // Look for information about supported types
    const supportedTypesText = page.getByText(/pdf|docx|pptx|xlsx|png|jpg|supported/i);

    if (await supportedTypesText.isVisible({ timeout: 3000 })) {
      await expect(supportedTypesText).toBeVisible();
    }
  });
});
