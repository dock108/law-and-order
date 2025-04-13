import { NextRequest, NextResponse } from 'next/server';
import NextAuth, { type NextAuthOptions } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import bcrypt from 'bcryptjs';

// IMPORTANT: Store the hashed password securely, e.g., in environment variables or a database.
// For this MVP, we'll hash the hardcoded password 'password123'.
// You can generate this hash once using a script or online tool.
// Example hash for 'password123' (use a real generated hash):
const HASHED_PASSWORD = '$2b$10$Q/WdriKeHXKHgmgCR.0Tuuh3lsyu2UNVVipJzozmJB28C8SUxx26O'; // Replace with a real hash
const USERNAME = 'lawyer';

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        username: { label: 'Username', type: 'text', placeholder: 'lawyer' },
        password: { label: 'Password', type: 'password' },
      },
      async authorize(credentials, req) {
        // Basic validation
        if (!credentials?.username || !credentials?.password) {
          console.error('Missing username or password');
          return null;
        }

        // Check if username matches the hardcoded one
        if (credentials.username !== USERNAME) {
          console.error('Invalid username');
          return null;
        }

        // Compare the provided password with the stored hash
        // NOTE: Never store plain text passwords! Always hash them.
        const passwordMatch = await bcrypt.compare(
          credentials.password,
          HASHED_PASSWORD
        );

        if (passwordMatch) {
          // Return user object if credentials are valid
          // You can add more user details here if needed (e.g., from a database)
          console.log('Authentication successful for user:', credentials.username);
          return { id: '1', name: 'Lawyer User', email: 'lawyer@example.com' }; // Example user object
        } else {
          console.error('Invalid password');
          // Return null if authentication fails
          return null;
        }
      },
    }),
  ],
  // Use JWT strategy for session management in this basic setup
  session: {
    strategy: 'jwt',
  },
  // Secret for signing JWTs, session encryption, etc.
  // Should be set in .env.local
  secret: process.env.NEXTAUTH_SECRET,

  // Optional: Add custom pages if needed
  // pages: {
  //   signIn: '/auth/signin', // Example: Custom sign-in page
  // },

  // Optional: Callbacks for customizing behavior (e.g., JWT content)
  // callbacks: {
  //   async jwt({ token, user }) {
  //     // Add custom claims to JWT
  //     if (user) {
  //       token.id = user.id;
  //     }
  //     return token;
  //   },
  //   async session({ session, token }) {
  //     // Add custom claims to session from JWT
  //     if (session.user) {
  //        // Type assertion needed if extending session user type
  //       (session.user as any).id = token.id;
  //     }
  //     return session;
  //   },
  // },
};

// Correctly type the handler parameters, even if req isn't used internally by NextAuth
const handler = (req: NextRequest, res: NextResponse) => NextAuth(req, res, authOptions);

export { handler as GET, handler as POST }; 