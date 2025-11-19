/**
 * Playwright global setup
 * Polyfills for missing Web APIs in Node.js
 */

// Polyfill TransformStream for Playwright MCP integration
if (typeof globalThis.TransformStream === 'undefined') {
  try {
    const { TransformStream } = require('node:stream/web');
    globalThis.TransformStream = TransformStream;
  } catch (error) {
    console.warn('Could not load TransformStream polyfill:', error);
  }
}

export default function globalSetup() {
  console.log('Playwright global setup complete');
}
