/** @type {import('jest').Config} */
export default {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',

  // Globals
  globals: {
    'import.meta': {
      env: {
        VITE_API_URL: 'http://localhost:8000',
        DEV: false,
        PROD: false,
        MODE: 'test',
      },
    },
  },

  // Module resolution
  moduleNameMapper: {
    // Path aliases (needs to be first to transform imports)
    '^@/(.*)$': '<rootDir>/src/$1',

    // CSS modules
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',

    // Static assets
    '\\.(jpg|jpeg|png|gif|svg|webp)$': '<rootDir>/src/__mocks__/fileMock.js',
  },

  // Automatically mock modules
  automock: false,

  // Setup files - run before test environment is installed
  setupFiles: ['<rootDir>/src/test-utils/setup-before-env.ts'],

  // Setup files - run after test environment is installed
  setupFilesAfterEnv: ['<rootDir>/src/test-utils/setup.ts'],

  // Test match patterns
  testMatch: [
    '**/__tests__/**/*.{ts,tsx}',
    '**/*.{spec,test}.{ts,tsx}'
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/main.tsx',
    '!src/vite-env.d.ts',
    '!src/**/__tests__/**',
    '!src/test-utils/**',
    '!src/__mocks__/**',
  ],

  coverageThreshold: {
    global: {
      branches: 60,
      functions: 60,
      lines: 60,
      statements: 60,
    },
  },

  // Transform files
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: {
        jsx: 'react-jsx',
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
        module: 'commonjs',
        target: 'ES2020',
        lib: ['ES2020', 'DOM', 'DOM.Iterable'],
        moduleResolution: 'node',
        types: ['jest', '@testing-library/jest-dom', '@types/jest', 'node', 'vite/client'],
        baseUrl: '.',
        paths: {
          '@/*': ['./src/*'],
        },
      },
      diagnostics: {
        ignoreCodes: [1343, 2339],
      },
    }],
  },

  // Module file extensions
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],

  // Ignore patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/dist/',
    '/build/',
  ],

  // Clear mocks between tests
  clearMocks: true,

  // Verbose output
  verbose: true,
};
