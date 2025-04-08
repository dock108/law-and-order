#!/bin/bash

# Install dependencies if needed
npm install

# Make sure we have ts-node installed
if ! command -v ts-node &> /dev/null; then
  echo "ts-node not found, installing..."
  npm install -g ts-node
fi

# Run the seeder
echo "Running database seed script..."
npx ts-node --esm scripts/seed-database.ts

echo "Seed completed!" 