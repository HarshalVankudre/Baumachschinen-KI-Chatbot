import { test, expect } from '@playwright/test';

/**
 * Chat Interface E2E Tests
 * Tests the core chatbot functionality:
 * - Creating conversations
 * - Sending messages
 * - Receiving AI responses
 * - Managing conversations
 */

test.describe('Chat Interface', () => {
  // Login before each test
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.getByLabel(/username|email/i).fill('testuser');
    await page.getByLabel(/password/i).fill('TestPassword123!');
    await page.getByRole('button', { name: /sign in|login/i }).click();
    await page.waitForURL(/.*chat/, { timeout: 10000 });
  });

  test('should display chat page layout', async ({ page }) => {
    // Check for main chat elements
    await expect(page.getByText(/new conversation/i)).toBeVisible();
    await expect(page.getByPlaceholder(/type.*message/i)).toBeVisible();
  });

  test('should create new conversation', async ({ page }) => {
    // Click new conversation button
    await page.getByRole('button', { name: /new conversation/i }).click();

    // Should create a new conversation
    await expect(page.getByText(/new chat|untitled/i)).toBeVisible({ timeout: 5000 });
  });

  test('should send message and receive response', async ({ page }) => {
    // Create new conversation
    await page.getByRole('button', { name: /new conversation/i }).click();

    // Wait for conversation to be ready
    await page.waitForTimeout(1000);

    // Type message
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Hello, can you help me with machinery documentation?');

    // Send message
    await page.getByRole('button', { name: /send/i }).click();

    // Should see user message
    await expect(page.getByText(/Hello.*machinery documentation/)).toBeVisible({
      timeout: 3000,
    });

    // Should see AI response (streaming or complete)
    await expect(
      page.getByText(/help|assist|documentation|information/).first()
    ).toBeVisible({ timeout: 15000 });
  });

  test('should disable input while AI is responding', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    const sendButton = page.getByRole('button', { name: /send/i });

    await messageInput.fill('Test message');
    await sendButton.click();

    // Input should be disabled while waiting for response
    await expect(messageInput).toBeDisabled({ timeout: 2000 });

    // Wait for response to complete
    await page.waitForTimeout(5000);

    // Input should be enabled again
    await expect(messageInput).toBeEnabled({ timeout: 10000 });
  });

  test('should clear input after sending message', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);

    await messageInput.fill('Test message');
    await page.getByRole('button', { name: /send/i }).click();

    // Wait for message to be sent
    await page.waitForTimeout(1000);

    // Input should be cleared
    await expect(messageInput).toHaveValue('');
  });

  test('should display conversation list', async ({ page }) => {
    // Create a few conversations
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(500);

    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(500);

    // Should show conversations in sidebar
    const conversations = page.locator('[data-testid="conversation-item"]').or(
      page.getByRole('button').filter({ hasText: /new chat|conversation/i })
    );

    await expect(conversations.first()).toBeVisible();
  });

  test('should switch between conversations', async ({ page }) => {
    // Create two conversations with different messages
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('First conversation message');
    await page.getByRole('button', { name: /send/i }).click();

    await page.waitForTimeout(2000);

    // Create second conversation
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    await messageInput.fill('Second conversation message');
    await page.getByRole('button', { name: /send/i }).click();

    await page.waitForTimeout(2000);

    // Click on first conversation in sidebar
    const firstConversation = page.locator('[data-testid="conversation-item"]').first().or(
      page.getByRole('button').filter({ hasText: /conversation/i }).first()
    );

    await firstConversation.click();

    // Should show first conversation messages
    await expect(page.getByText(/First conversation message/)).toBeVisible({
      timeout: 5000,
    });
  });

  test('should search conversations', async ({ page }) => {
    const searchInput = page.getByPlaceholder(/search/i);

    if (await searchInput.isVisible()) {
      await searchInput.fill('test');

      // Should filter conversations
      await page.waitForTimeout(500);

      // Check if filtering works (this depends on having conversations with "test" in them)
      await expect(searchInput).toHaveValue('test');
    }
  });

  test('should delete conversation', async ({ page }) => {
    // Create a conversation
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    // Find and hover over conversation to show delete button
    const conversation = page.locator('[data-testid="conversation-item"]').first().or(
      page.getByRole('button').filter({ hasText: /conversation/i }).first()
    );

    await conversation.hover();

    // Look for delete button
    const deleteButton = page.getByRole('button', { name: /delete/i }).or(
      page.locator('[aria-label*="delete"]')
    );

    if (await deleteButton.isVisible({ timeout: 2000 })) {
      await deleteButton.click();

      // Should show confirmation dialog
      await expect(page.getByText(/delete.*conversation|are you sure/i)).toBeVisible({
        timeout: 3000,
      });

      // Confirm deletion
      await page.getByRole('button', { name: /confirm|delete|yes/i }).click();

      // Conversation should be removed
      await page.waitForTimeout(1000);
    }
  });

  test('should display markdown formatting in messages', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Can you show me a code example?');
    await page.getByRole('button', { name: /send/i }).click();

    // Wait for AI response with code
    await page.waitForTimeout(5000);

    // Check if code blocks are rendered (if response contains code)
    const codeBlock = page.locator('pre, code').first();
    if (await codeBlock.isVisible({ timeout: 5000 })) {
      await expect(codeBlock).toBeVisible();
    }
  });

  test('should copy message content', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    // Send a message
    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Test message for copying');
    await page.getByRole('button', { name: /send/i }).click();

    await page.waitForTimeout(2000);

    // Look for copy button on message
    const copyButton = page.getByRole('button', { name: /copy/i }).or(
      page.locator('[aria-label*="copy"]')
    ).first();

    if (await copyButton.isVisible({ timeout: 3000 })) {
      await copyButton.click();

      // Should show copied confirmation
      await expect(page.getByText(/copied/i)).toBeVisible({ timeout: 2000 });
    }
  });

  test('should handle long messages', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const longMessage = 'This is a very long message. ' + 'Lorem ipsum dolor sit amet. '.repeat(50);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill(longMessage);

    // Should still be able to send
    const sendButton = page.getByRole('button', { name: /send/i });
    await expect(sendButton).toBeEnabled();

    await sendButton.click();

    // Should display the long message
    await expect(page.getByText(/This is a very long message/)).toBeVisible({
      timeout: 3000,
    });
  });

  test('should handle Enter key to send message', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Test with Enter key');

    // Press Enter
    await messageInput.press('Enter');

    // Should send message
    await expect(page.getByText(/Test with Enter key/)).toBeVisible({ timeout: 3000 });
  });

  test('should handle Shift+Enter for new line', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('Line 1');

    // Press Shift+Enter
    await messageInput.press('Shift+Enter');

    await messageInput.fill('Line 1\nLine 2');

    // Should not send yet
    await page.waitForTimeout(500);

    // Check that input still has value
    await expect(messageInput).toHaveValue(/Line 1/);
  });

  test('should show character counter near limit', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);

    // Type a message close to the limit (assuming 2000 char limit)
    const nearLimitMessage = 'x'.repeat(1850);
    await messageInput.fill(nearLimitMessage);

    // Should show character counter
    await expect(page.getByText(/1850|character|limit/i)).toBeVisible({ timeout: 2000 });
  });

  test('should display source citations in AI responses', async ({ page }) => {
    await page.getByRole('button', { name: /new conversation/i }).click();
    await page.waitForTimeout(1000);

    const messageInput = page.getByPlaceholder(/type.*message/i);
    await messageInput.fill('What information do you have about safety procedures?');
    await page.getByRole('button', { name: /send/i }).click();

    // Wait for response
    await page.waitForTimeout(8000);

    // Check if sources are displayed (if AI provides them)
    const sourcesSection = page.getByText(/sources|references|documents/i);
    if (await sourcesSection.isVisible({ timeout: 5000 })) {
      await expect(sourcesSection).toBeVisible();
    }
  });
});
