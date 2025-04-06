import { PrismaClient } from '@prisma/client';

// Declare a global variable to hold the PrismaClient instance
declare global {
  // eslint-disable-next-line no-var
  var prisma: PrismaClient | undefined;
}

// Instantiate PrismaClient, reusing the instance in development
const prisma = global.prisma || new PrismaClient({
  // Optional: Log Prisma queries
  // log: ['query', 'info', 'warn', 'error'],
});

// In development, store the instance on the global object
if (process.env.NODE_ENV !== 'production') {
  global.prisma = prisma;
}

export default prisma; 