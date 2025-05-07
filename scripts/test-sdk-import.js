// Simple script to test importing the SDK package.
(async () => {
  try {
    // Attempt to dynamically import the package.
    // If this runs without error, the package is resolvable.
    await import('@pi-monorepo/api-client');
    console.log('SDK loaded successfully');
    process.exit(0); // Explicitly exit with success code
  } catch (err) {
    console.error('Failed to load SDK:', err);
    process.exit(1); // Explicitly exit with failure code
  }
})();
