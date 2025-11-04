// This file runs BEFORE the test environment is set up
// Mock import.meta for Vite - Jest doesn't support import.meta natively
Object.defineProperty(globalThis, 'import', {
  value: {
    meta: {
      env: {
        VITE_API_URL: 'http://localhost:8000',
        DEV: false,
        PROD: false,
        MODE: 'test',
      },
    },
  },
  writable: false,
  configurable: true,
});
