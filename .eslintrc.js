module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  plugins: [
    '@typescript-eslint',
    'prettier', // Runs Prettier as an ESLint rule
  ],
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'prettier', // Disables rules that conflict with Prettier
  ],
  rules: {
    'prettier/prettier': 'error', // Report Prettier violations as ESLint errors
    // Add any custom rules here
  },
  env: {
    node: true,
    es2022: true,
  },
  ignorePatterns: ['node_modules', 'dist', 'packages/*/dist'],
};
