/* eslint-env node */
module.exports = {
  root: true,
  env: { browser: true, es2020: true, node: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: ['react-hooks', 'react-refresh', '@typescript-eslint'],
  ignorePatterns: ['dist', 'node_modules', '.eslintrc.cjs', 'coverage'],
  settings: {
    react: { version: '18.3' },
  },
  rules: {
    ...require('eslint-plugin-react-hooks').configs.recommended.rules,
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-unused-vars': [
      'error',
      { argsIgnorePattern: '^_', varsIgnorePattern: '^_' },
    ],
    '@typescript-eslint/consistent-type-imports': [
      'warn',
      { prefer: 'type-imports' },
    ],
  },
  overrides: [
    {
      // Idiomatic co-location: useAuth hook beside AuthProvider, and a local
      // fallback component inside ErrorBoundary. Fast-refresh DX trade-off.
      files: ['src/auth/AuthContext.tsx', 'src/components/ErrorBoundary.tsx'],
      rules: { 'react-refresh/only-export-components': 'off' },
    },
  ],
};
